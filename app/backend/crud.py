# app/backend/crud.py
from __future__ import annotations
import datetime
import csv
import hashlib
import io
import bcrypt
import uuid
from datetime import datetime, date, time

from sqlalchemy import func, cast, Date, and_, or_
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from passlib.context import CryptContext

from . import models
from . import schemas


# =========================================================
# Password hashing (HASH, not encryption)
# =========================================================

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    sha = hashlib.sha256(password.encode("utf-8")).digest()
    hashed = bcrypt.hashpw(sha, bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_in_db: str) -> bool:
    """
    Weryfikacja wielopoziomowa:
    1. Próba: SHA256 + BCrypt (Twoja metoda)
    2. Próba: Standardowy BCrypt (bez SHA256)
    3. Próba: Plain Text (dla testowych kont)
    """
    if not hashed_in_db:
        return False

    # Jeśli wygląda na hash BCrypt (zaczyna się od $2)
    if hashed_in_db.startswith('$2'):
        try:
            # PRÓBA 1: Twoja metoda (SHA256 digest + BCrypt)
            sha = hashlib.sha256(plain_password.encode("utf-8")).digest()
            if bcrypt.checkpw(sha, hashed_in_db.encode("utf-8")):
                return True

            # PRÓBA 2: Standardowy BCrypt (sam tekst + BCrypt)
            # To na wypadek, gdyby Jan Kowalski był stworzony inaczej
            if bcrypt.checkpw(plain_password.encode("utf-8"), hashed_in_db.encode("utf-8")):
                return True

        except Exception as e:
            print(f"Błąd weryfikacji hasha: {e}")
            return False

    # PRÓBA 3: Czysty tekst (fallback)
    return plain_password == hashed_in_db


# =========================================================
# Employees (Kierownik use-case)
# =========================================================

def create_employee(db: Session, payload: schemas.EmployeeCreate) -> models.Pracownik:
    # 1) Tworzenie bazy pracownika (bez daty zatrudnienia, bo nie ma jej w tej tabeli)
    pracownik = models.Pracownik(
        imie=payload.imie,
        nazwisko=payload.nazwisko,
        pesel=payload.pesel,
        adres=payload.adres,
        telefon=payload.telefon,
        email=str(payload.email) if payload.email else None,
        login=payload.login,
        haslo=hash_password(payload.haslo),
    )
    db.add(pracownik)

    try:
        db.flush()
    except IntegrityError as e:
        db.rollback()
        raise ValueError("PESEL/email/login już istnieje.") from e

    # Pobieramy datę z payloadu lub używamy obecnej
    hire_date = payload.data_zatrudnienia or datetime.datetime.utcnow()

    # 2) Przypisanie roli wraz z datą zatrudnienia do konkretnej tabeli podtypu [cite: 157, 180]
    if payload.rola == "KIEROWNIK":
        role_row = models.Kierownik(pracownik_id=pracownik.id, data_zatrudnienia=hire_date)
    elif payload.rola == "MAGAZYNIER":
        role_row = models.Magazynier(pracownik_id=pracownik.id, data_zatrudnienia=hire_date)
    elif payload.rola == "SERWISANT":
        role_row = models.Serwisant(pracownik_id=pracownik.id, data_zatrudnienia=hire_date)
    else:
        db.rollback()
        raise ValueError("Nieznana rola.")

    db.add(role_row)
    db.commit()
    db.refresh(pracownik)
    return pracownik

# =========================================================
# Employees – update / change role / delete
# =========================================================

def update_employee(
    db: Session,
    employee_id: int,
    payload: schemas.EmployeeUpdate,
) -> models.Pracownik:
    """
    Updates basic employee data (without password change).
    """
    pracownik = db.get(models.Pracownik, employee_id)
    if not pracownik:
        raise ValueError("Pracownik nie istnieje.")

    # aktualizacja pól (tylko jeśli podane)
    for field, value in payload.model_dump(exclude_unset=True).items():
        if field == "rola":
            continue  # rola obsługiwana osobno
        setattr(pracownik, field, value)

    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise ValueError("Błąd aktualizacji danych pracownika.") from e

    db.refresh(pracownik)
    return pracownik


def change_employee_role(
    db: Session,
    employee_id: int,
    new_role: schemas.EmployeeRole,
    data_startu: datetime.datetime = None # Opcjonalna data
) -> None:
    pracownik = db.get(models.Pracownik, employee_id)
    if not pracownik:
        raise ValueError("Pracownik nie istnieje.")

    # 1) Usuwamy rekordy z tabel podtypów
    db.query(models.Kierownik).filter_by(pracownik_id=employee_id).delete()
    db.query(models.Magazynier).filter_by(pracownik_id=employee_id).delete()
    db.query(models.Serwisant).filter_by(pracownik_id=employee_id).delete()
    db.flush()

    # 2) Ustawiamy datę (jeśli nie podano, bierzemy teraz)
    start_date = data_startu or datetime.datetime.utcnow()

    # 3) Wstawiamy nową rolę z datą
    if new_role == "KIEROWNIK":
        db.add(models.Kierownik(pracownik_id=employee_id, data_zatrudnienia=start_date))
    elif new_role == "MAGAZYNIER":
        db.add(models.Magazynier(pracownik_id=employee_id, data_zatrudnienia=start_date))
    elif new_role == "SERWISANT":
        db.add(models.Serwisant(pracownik_id=employee_id, data_zatrudnienia=start_date))

    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise ValueError("Nie można zmienić roli pracownika.") from e


def delete_employee(db: Session, employee_id: int) -> None:
    """
    Deletes employee if not referenced in rentals.
    """
    pracownik = db.get(models.Pracownik, employee_id)
    if not pracownik:
        raise ValueError("Pracownik nie istnieje.")

    # zabezpieczenie: jeśli brał udział w wypożyczeniach – blokuj
    used_in_rentals = (
        db.query(models.Wypozyczenie)
        .filter(
            (models.Wypozyczenie.magazynier_wydaj_id == employee_id)
            | (models.Wypozyczenie.magazynier_przyjmij_id == employee_id)
        )
        .first()
    )

    if used_in_rentals:
        raise ValueError(
            "Nie można usunąć pracownika, który brał udział w wypożyczeniach."
        )

    try:
        db.delete(pracownik)
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise ValueError("Błąd podczas usuwania pracownika.") from e


# =========================================================
# Employees – listing (for Streamlit UI)
# =========================================================

def _build_role_map(db: Session) -> dict[int, str]:
    """
    Helper: returns {pracownik_id: 'KIEROWNIK'|'MAGAZYNIER'|'SERWISANT'}
    """
    role_map: dict[int, str] = {}

    for r in db.query(models.Kierownik.pracownik_id).all():
        role_map[r.pracownik_id] = "KIEROWNIK"

    for r in db.query(models.Magazynier.pracownik_id).all():
        role_map[r.pracownik_id] = "MAGAZYNIER"

    for r in db.query(models.Serwisant.pracownik_id).all():
        role_map[r.pracownik_id] = "SERWISANT"

    return role_map


def list_employees(db: Session, role: str | None = None, query: str | None = None) -> list[dict]:
    pracownicy = db.query(models.Pracownik).all()
    result = []

    for p in pracownicy:
        info_roli = ("BRAK", None)

        # Sprawdzamy, która tabela podtypu posiada rekord dla tego pracownika
        if p.kierownik:
            info_roli = ("KIEROWNIK", p.kierownik.data_zatrudnienia)
        elif p.magazynier:
            info_roli = ("MAGAZYNIER", p.magazynier.data_zatrudnienia)
        elif p.serwisant:
            info_roli = ("SERWISANT", p.serwisant.data_zatrudnienia)

        result.append({
            "id": p.id,
            "imie": p.imie,
            "nazwisko": p.nazwisko,
            "login": p.login,
            "pesel": p.pesel,
            "email": p.email,
            "telefon": p.telefon,
            "adres": p.adres,
            "rola": info_roli[0],
            "zatrudniony_od": info_roli[1]  # Data pochodzi prosto z tabeli roli [cite: 291, 316, 335]
        })
    return result


def get_employee_with_role(db: Session, employee_id: int) -> dict | None:
    """
    Single employee with role (for edit form).
    """
    role_map = _build_role_map(db)

    p = db.get(models.Pracownik, employee_id)
    if not p:
        return None

    return {
        "id": p.id,
        "imie": p.imie,
        "nazwisko": p.nazwisko,
        "login": p.login,
        "email": p.email,
        "telefon": p.telefon,
        "adres": p.adres,
        "pesel": p.pesel,
        "rola": role_map.get(p.id),
        "data_utworzenia": p.data_utworzenia,
    }

# =========================================================
# Tool models (Kierownik) – create / update / withdraw / list
# =========================================================

def create_tool_model(db: Session, payload: schemas.ToolModelCreate) -> models.ModelNarzedzia:
    model = models.ModelNarzedzia(
        nazwa_modelu=payload.nazwa_modelu,
        producent=payload.producent,
        kategoria=payload.kategoria,
        opis=payload.opis,
        cena_za_dobe=payload.cena_za_dobe,
        kaucja=payload.kaucja,
        wycofany=False,
    )
    db.add(model)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise ValueError("Nie można dodać modelu narzędzia.") from e
    db.refresh(model)
    return model


def update_tool_model(db: Session, model_id: int, payload: schemas.ToolModelUpdate) -> models.ModelNarzedzia:
    model = db.get(models.ModelNarzedzia, model_id)
    if not model:
        raise ValueError("Model narzędzia nie istnieje.")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(model, field, value)

    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise ValueError("Nie można zaktualizować modelu narzędzia.") from e

    db.refresh(model)
    return model


def can_withdraw_model(db: Session, model_id: int) -> bool:
    """Sprawdza, czy model nie ma przypisanych żadnych egzemplarzy."""
    count = db.query(models.EgzemplarzNarzedzia).filter(
        models.EgzemplarzNarzedzia.model_id == model_id
    ).count()
    return count == 0


def withdraw_tool_model(db: Session, model_id: int):
    """Wycofuje model, jeśli nie ma egzemplarzy."""
    if not can_withdraw_model(db, model_id):
        raise ValueError("Nie można wycofać modelu, który posiada przypisane egzemplarze!")

    model = db.get(models.ModelNarzedzia, model_id)
    if model:
        model.wycofany = True
        db.commit()
    return model


def list_tool_models_for_manager(
    db: Session,
    include_withdrawn: bool = False,
    query: str | None = None,
    category: str | None = None,
) -> list[dict]:
    """
    Listing modeli narzędzi dokładnie pod UI Kierownika:
    ID | NAZWA | KATEGORIA | PRODUCENT | CENA | KAUCJA | AKCJA
    """

    q = db.query(models.ModelNarzedzia)

    if not include_withdrawn:
        q = q.filter(models.ModelNarzedzia.wycofany.is_(False))

    if query:
        like = f"%{query.lower()}%"
        q = q.filter(
            (models.ModelNarzedzia.nazwa_modelu.ilike(like))
            | (models.ModelNarzedzia.producent.ilike(like))
            | (models.ModelNarzedzia.kategoria.ilike(like))
        )

    if category:
        q = q.filter(models.ModelNarzedzia.kategoria == category)

    models_list = q.order_by(models.ModelNarzedzia.nazwa_modelu).all()

    return [
        {
            "id_modelu": m.id,
            "nazwa": m.nazwa_modelu,
            "kategoria": m.kategoria,
            "producent": m.producent,
            "cena_za_dobe": float(m.cena_za_dobe),
            "kaucja": float(m.kaucja) if m.kaucja is not None else None,
            # AKCJA jest obsługiwana w UI (przyciski)
            "wycofany": m.wycofany,
        }
        for m in models_list
    ]


def list_tool_models_extended(
        db: Session,
        search: str = "",
        cat: str = "Wszystkie",
        prod: str = "Wszyscy",
        min_price: float = 0.0,
        max_price: float = 1000.0
) -> list[models.ModelNarzedzia]:
    query = db.query(models.ModelNarzedzia).filter(models.ModelNarzedzia.wycofany == False)

    if search:
        query = query.filter(models.ModelNarzedzia.nazwa_modelu.ilike(f"%{search}%"))
    if cat != "Wszystkie":
        query = query.filter(models.ModelNarzedzia.kategoria == cat)
    if prod != "Wszyscy":
        query = query.filter(models.ModelNarzedzia.producent == prod)

    query = query.filter(models.ModelNarzedzia.cena_za_dobe.between(min_price, max_price))

    return query.order_by(models.ModelNarzedzia.nazwa_modelu).all()

def get_tool_model(db: Session, model_id: int) -> dict | None:
    m = db.get(models.ModelNarzedzia, model_id)
    if not m:
        return None
    return {
        "id": m.id,
        "nazwa_modelu": m.nazwa_modelu,
        "producent": m.producent,
        "kategoria": m.kategoria,
        "opis": m.opis,
        "cena_za_dobe": m.cena_za_dobe,
        "kaucja": m.kaucja,
        "wycofany": getattr(m, "wycofany", False),
        "data_utworzenia": m.data_utworzenia,
    }


# =========================================================
# Kierownik – analytics
# =========================================================

def analytics_summary(db: Session, date_from, date_to) -> dict:
    """Podsumowanie ogólne przychodów i rezerwacji."""
    # Konwersja dat na zakres czasowy (od 00:00 do 23:59)
    start_dt = datetime.combine(date_from, datetime.min.time())
    end_dt = datetime.combine(date_to, datetime.max.time())

    # Liczba rezerwacji
    total_rentals = (
        db.query(func.count(models.Wypozyczenie.id))
        .filter(models.Wypozyczenie.data_rezerwacji.between(start_dt, end_dt))
        .scalar() or 0
    )

    # Całkowity przychód (COALESCE chroni przed None)
    total_revenue = (
        db.query(func.coalesce(func.sum(models.Wypozyczenie.koszt_calkowity), 0))
        .filter(models.Wypozyczenie.data_rezerwacji.between(start_dt, end_dt))
        .scalar() or 0
    )

    return {
        "total_rentals": int(total_rentals),
        "total_revenue": float(total_revenue),
    }

def analytics_daily(db: Session, date_from, date_to):
    """Dzienny przychód dla wykresu."""
    start_dt = datetime.combine(date_from, datetime.min.time())
    end_dt = datetime.combine(date_to, datetime.max.time())

    return (
        db.query(
            func.date(models.Wypozyczenie.data_rezerwacji).label("dzien"),
            func.coalesce(func.sum(models.Wypozyczenie.koszt_calkowity), 0).label("suma")
        )
        .filter(models.Wypozyczenie.data_rezerwacji.between(start_dt, end_dt))
        .group_by(func.date(models.Wypozyczenie.data_rezerwacji))
        .order_by("dzien")
        .all()
    )


def analytics_top_models(
    db: Session,
    date_from: Date,
    date_to: Date,
    limit: int = 10,
) -> list[dict]:
    """
    Top modele w okresie wg liczby wypożyczonych egzemplarzy (pozycje wypożyczenia).
    """
    start_dt = datetime.combine(date_from, datetime.min.time())
    end_dt = datetime.combine(date_to, datetime.max.time())

    rows = (
        db.query(
            models.ModelNarzedzia.id.label("model_id"),
            models.ModelNarzedzia.nazwa_modelu.label("nazwa"),
            func.count(models.PozycjaWypozyczenia.id).label("liczba_pozycji"),
        )
        .join(models.EgzemplarzNarzedzia, models.EgzemplarzNarzedzia.model_id == models.ModelNarzedzia.id)
        .join(models.PozycjaWypozyczenia, models.PozycjaWypozyczenia.egzemplarz_id == models.EgzemplarzNarzedzia.id)
        .join(models.Wypozyczenie, models.Wypozyczenie.id == models.PozycjaWypozyczenia.wypozyczenie_id)
        .filter(models.Wypozyczenie.data_rezerwacji.between(start_dt, end_dt))
        .group_by(models.ModelNarzedzia.id, models.ModelNarzedzia.nazwa_modelu)
        .order_by(func.count(models.PozycjaWypozyczenia.id).desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "model_id": int(r.model_id),
            "nazwa": r.nazwa,
            "liczba_pozycji": int(r.liczba_pozycji),
        }
        for r in rows
    ]


# =========================================================
# Kierownik – export CSV (safe whitelist)
# =========================================================

_EXPORT_TABLES = {
    "pracownicy": models.Pracownik,
    "klienci": models.Klient,
    "modele_narzedzi": models.ModelNarzedzia,
    "egzemplarze_narzedzi": models.EgzemplarzNarzedzia,
    "wypozyczenia": models.Wypozyczenie,
    "pozycje_wypozyczenia": models.PozycjaWypozyczenia,
    "czynnosci_serwisowe": models.CzynnoscSerwisowa,
    "opinie": models.Opinia,
    "magazyny": models.Magazyn,
    "warsztaty": models.Warsztat,
}


def export_table_to_csv(
    db: Session,
    table_name: str,
    filters: dict | None = None,
    date_from: Date | None = None,
    date_to: Date | None = None,
) -> str:
    """
    Eksportuje wskazaną tabelę do CSV.
    - table_name: tylko z whitelisty (_EXPORT_TABLES)
    - filters: proste filtry równości, np. {"status": "WYDANE", "klient_id": 3}
    - date_from/date_to: jeśli tabela ma pole 'data_rezerwacji' lub 'data_utworzenia' / 'data_wystawienia' (best-effort)
    Zwraca string CSV gotowy do st.download_button w Streamlit.
    """
    if table_name not in _EXPORT_TABLES:
        raise ValueError("Nieobsługiwana tabela do eksportu.")

    Model = _EXPORT_TABLES[table_name]
    q = db.query(Model)

    # proste filtry = equality
    if filters:
        for key, val in filters.items():
            if not hasattr(Model, key):
                continue
            q = q.filter(getattr(Model, key) == val)

    # filtr po dacie (best-effort: wybieramy pierwsze pasujące pole)
    if date_from and date_to:
        start_dt = datetime.combine(date_from, datetime.min.time())
        end_dt = datetime.combine(date_to, datetime.max.time())

        date_field = None
        for candidate in ("data_rezerwacji", "data_utworzenia", "data_rejestracji", "data_wystawienia", "data_rozpoczecia"):
            if hasattr(Model, candidate):
                date_field = getattr(Model, candidate)
                break

        if date_field is not None:
            q = q.filter(date_field.between(start_dt, end_dt))

    rows = q.all()

    # kolumny tabeli
    columns = [c.name for c in Model.__table__.columns]

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(columns)

    for r in rows:
        writer.writerow([getattr(r, col) for col in columns])

    return buf.getvalue()


def authenticate_user(db: Session, identifier: str, password: str):
    """Logowanie uniwersalne z pełnym debugowaniem w konsoli."""

    print("\n" + "=" * 50)
    print(f"[DEBUG] PROCES LOGOWANIA")
    print(f"[DEBUG] Wpisany identyfikator: {repr(identifier)}")
    print(f"[DEBUG] Długość wpisanego hasła: {len(password)} znaków")
    print("=" * 50)

    # 1. Szukamy w pracownikach
    emp = db.query(models.Pracownik).filter(
        or_(models.Pracownik.login == identifier, models.Pracownik.email == identifier)
    ).first()

    if emp:
        print(f"[DEBUG] [PRACOWNIK] Znaleziono rekord: {repr(emp.login)} (ID: {emp.id})")
        print(f"[DEBUG] [PRACOWNIK] Hash w bazie: {repr(emp.haslo)}")

        # Weryfikacja hasła
        check = verify_password(password, emp.haslo)
        print(f"[DEBUG] [PRACOWNIK] Wynik weryfikacji hasła: {check}")

        if check:
            # Sprawdzanie roli
            role = "PRACOWNIK"
            if emp.kierownik:
                role = "KIEROWNIK"
            elif emp.magazynier:
                role = "MAGAZYNIER"
            elif emp.serwisant:
                role = "SERWISANT"

            print(f"[DEBUG] [SUCCESS] Zalogowano jako: {role}")
            print("=" * 50 + "\n")
            return emp, role
        else:
            print(f"[DEBUG] [FAIL] Hasło pracownika nie pasuje.")
    else:
        print("[DEBUG] [PRACOWNIK] Nie znaleziono pracownika o tym loginie/emailu.")

    # 2. Szukamy w klientach
    print("-" * 30)
    cust = db.query(models.Klient).filter(models.Klient.email == identifier).first()
    if cust:
        print(f"[DEBUG] [KLIENT] Znaleziono rekord: {repr(cust.email)} (ID: {cust.id})")
        print(f"[DEBUG] [KLIENT] Hash w bazie: {repr(cust.haslo)}")

        check = verify_password(password, cust.haslo)
        print(f"[DEBUG] [KLIENT] Wynik weryfikacji hasła: {check}")

        if check:
            print("[DEBUG] [SUCCESS] Zalogowano jako: KLIENT")
            print("=" * 50 + "\n")
            return cust, "KLIENT"
        else:
            print(f"[DEBUG] [FAIL] Hasło klienta nie pasuje.")
    else:
        print("[DEBUG] [KLIENT] Nie znaleziono klienta o tym emailu.")

    print("[DEBUG] [FINAL] Logowanie odrzucone.")
    print("=" * 50 + "\n")
    return None, None

# SERWISANT

def add_service_action(
        db: Session,
        egzemplarz_id: int,
        serwisant_id: int,
        rodzaj: str,
        notatka: str,
        nowy_stan: str = None
):
    """Rejestruje czynność i zeruje licznik przy zmianie na SPRAWNY."""
    egzemplarz = db.get(models.EgzemplarzNarzedzia, egzemplarz_id)
    if not egzemplarz:
        raise ValueError("Nie znaleziono takiego egzemplarza.")

    # 1. Tworzymy wpis w historii czynności
    nowa_czynnosc = models.CzynnoscSerwisowa(
        egzemplarz_id=egzemplarz_id,
        serwisant_id=serwisant_id,
        rodzaj=rodzaj,
        notatka_opis=notatka,
        data_rozpoczecia=datetime.utcnow(),
        data_zakonczenia=datetime.utcnow()
    )
    db.add(nowa_czynnosc)

    # 2. Aktualizacja stanu i ewentualny reset licznika
    if nowy_stan:
        egzemplarz.stan_techniczny = nowy_stan

        if nowy_stan == "SPRAWNY":
            egzemplarz.licznik_wypozyczen = 0  # Reset przebiegu

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise e


def list_pending_operations(db: Session):
    """Poprawiona funkcja dla Magazyniera - używa Twoich nazw pól dat."""
    from sqlalchemy.orm import joinedload

    rentals = db.query(models.Wypozyczenie).options(
        joinedload(models.Wypozyczenie.klient),
        joinedload(models.Wypozyczenie.pozycje).joinedload(models.PozycjaWypozyczenia.egzemplarz).joinedload(
            models.EgzemplarzNarzedzia.model)
    ).filter(models.Wypozyczenie.status.in_(["REZERWACJA", "WYDANE"])).all()

    results = []
    for r in rentals:
        modele_napis = ", ".join(list(set([p.egzemplarz.model.nazwa_modelu for p in r.pozycje])))

        if r.status == "REZERWACJA":
            results.append({
                "id": r.id,
                "typ": "WYDANIE",
                "data_planowana": r.data_plan_wydania,  # Poprawione
                "klient": f"{r.klient.imie} {r.klient.nazwisko}",
                "model": modele_napis,
                "obj": r
            })
        elif r.status == "WYDANE":
            results.append({
                "id": r.id,
                "typ": "ZWROT",
                "data_planowana": r.data_plan_zwrotu,  # Poprawione
                "klient": f"{r.klient.imie} {r.klient.nazwisko}",
                "model": modele_napis,
                "obj": r
            })
    return results


# app/backend/crud.py

def process_rental_action(db: Session, wypozyczenie_id: int, nowy_status_db: str):
    """
    Zarządza statusem rezerwacji (REZERWACJA -> WYDANE -> ZAKOŃCZONA).
    Przy okazji aktualizuje stan techniczny i lokalizację narzędzi.
    """
    wyp_obj = db.query(models.Wypozyczenie).filter(models.Wypozyczenie.id == wypozyczenie_id).first()
    if not wyp_obj:
        return

    # Ustawiamy status wypożyczenia (ten, który widzi klient w historii)
    wyp_obj.status = nowy_status_db

    if nowy_status_db == "WYDANE":
        for p in wyp_obj.pozycje:
            # Lokalizacja narzędzia zmienia się na "U_KLIENTA"
            p.egzemplarz.status = "U_KLIENTA"

    elif nowy_status_db == "ZAKOŃCZONA":  # Zmienione z ZWRÓCONE na ZAKOŃCZONA
        for p in wyp_obj.pozycje:
            egz = p.egzemplarz

            # 1. Narzędzie wraca fizycznie do magazynu
            egz.status = "W_MAGAZYNIE"

            # 2. Zwiększamy licznik (przebieg)
            egz.licznik_wypozyczen += 1

            # 3. Ustalamy stan techniczny (Hierarchia)
            if p.czy_zgloszono_usterke:
                egz.stan_techniczny = "AWARIA"
            elif egz.licznik_wypozyczen >= 5:
                egz.stan_techniczny = "WYMAGA_PRZEGLADU"
            else:
                egz.stan_techniczny = "SPRAWNY"

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise e

def update_item_status(db: Session, item_id: int, new_status: str):
    """Aktualizuje status lokalizacji egzemplarza (np. przekazanie do warsztatu)."""
    item = db.get(models.EgzemplarzNarzedzia, item_id)
    if item:
        item.status = new_status
        db.commit()
        db.refresh(item)
    return item


def list_models_with_counts(db: Session, search: str = "", cat: str = "Wszystkie", prod: str = "Wszyscy"):
    """Pobiera listę modeli wraz z aktualną liczbą posiadanych egzemplarzy."""
    # Podzapytanie liczące sztuki dla każdego modelu
    count_subquery = db.query(
        models.EgzemplarzNarzedzia.model_id,
        func.count(models.EgzemplarzNarzedzia.id).label('total')
    ).group_by(models.EgzemplarzNarzedzia.model_id).subquery()

    query = db.query(
        models.ModelNarzedzia,
        func.coalesce(count_subquery.c.total, 0).label('liczba_sztuk')
    ).outerjoin(count_subquery, models.ModelNarzedzia.id == count_subquery.c.model_id).filter(
        models.ModelNarzedzia.wycofany == False)

    if search:
        query = query.filter(models.ModelNarzedzia.nazwa_modelu.ilike(f"%{search}%"))
    if cat != "Wszystkie":
        query = query.filter(models.ModelNarzedzia.kategoria == cat)
    if prod != "Wszyscy":
        query = query.filter(models.ModelNarzedzia.producent == prod)

    return query.all()


def bulk_create_items(db: Session, model_id: int, count: int):
    """Tworzy zadaną liczbę egzemplarzy zgodnie z modelem bazy danych."""
    for _ in range(count):
        # Generujemy unikalny ciąg, aby spełnić wymóg unikalności numeru seryjnego
        temp_sn = f"SN-{uuid.uuid4().hex[:6].upper()}"

        db_item = models.EgzemplarzNarzedzia(
            model_id=model_id,
            numer_seryjny=temp_sn,  # Wymagane przez model
            status="W_MAGAZYNIE",  # Domyślnie
            stan_techniczny="SPRAWNY"  # Domyślnie
        )
        db.add(db_item)

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise ValueError(f"Błąd bazy danych: {str(e)}")

def mark_for_inspection(db: Session, item_id: int):
    """Zmienia stan na WYMAGA_PRZEGLADU i PRZENOSI do warsztatu."""
    item = db.get(models.EgzemplarzNarzedzia, item_id)
    # Usuwamy warunek status == "W_MAGAZYNIE" jeśli chcemy pozwolić na oznaczenie
    # narzędzia, które np. właśnie wróciło od klienta
    if item:
        item.stan_techniczny = "WYMAGA_PRZEGLADU"
        item.status = "W_WARSZTACIE"  # <--- KLUCZOWA ZMIANA: Przenosimy do warsztatu
        db.commit()
    return item


def receive_from_service(db: Session, item_id: int):
    """
    Używane przez Magazyniera: Fizyczny odbiór z warsztatu.
    To jedyne miejsce, gdzie resetujemy licznik i przywracamy status W_MAGAZYNIE.
    """
    item = db.get(models.EgzemplarzNarzedzia, item_id)
    if item and item.status == "W_WARSZTACIE":
        item.status = "W_MAGAZYNIE"
        item.warsztat_id = None

        # Bezpiecznik: przy powrocie do magazynu sprzęt musi być czysty i sprawny
        item.stan_techniczny = "SPRAWNY"
        item.licznik_wypozyczen = 0  # <--- RESET LICZNIKA

        db.commit()
    return item


def update_technical_state(db: Session, item_id: int, new_state: str):
    """Zmienia stan techniczny egzemplarza i resetuje licznik jeśli sprawny."""
    item = db.get(models.EgzemplarzNarzedzia, item_id)
    if item:
        item.stan_techniczny = new_state

        # LOGIKA RESETU: Jeśli przywracamy do sprawności, zerujemy licznik wypożyczeń
        if new_state == "SPRAWNY":
            item.licznik_wypozyczen = 0

        db.commit()
    return item


def count_physical_in_stock(db: Session, model_id: int):
    """Szybki licznik dla tabeli głównej: fizycznie w magazynie i sprawne."""
    return db.query(models.EgzemplarzNarzedzia).filter(
        models.EgzemplarzNarzedzia.model_id == model_id,
        models.EgzemplarzNarzedzia.status == "W_MAGAZYNIE",
        models.EgzemplarzNarzedzia.stan_techniczny == "SPRAWNY"
    ).count()


def get_available_items_for_term(db: Session, model_id: int, start_dt: datetime, end_dt: datetime):
    """Wylicza dostępność na podstawie Twoich pól: data_plan_wydania i data_plan_zwrotu."""
    # 1. Wszystkie sprawne egzemplarze (poza warsztatem)
    functional_items = db.query(models.EgzemplarzNarzedzia).filter(
        models.EgzemplarzNarzedzia.model_id == model_id,
        models.EgzemplarzNarzedzia.stan_techniczny == "SPRAWNY",
        models.EgzemplarzNarzedzia.status != "W_WARSZTACIE"
    ).all()

    # 2. Sprawdzanie kolizji terminów w aktywnych wypożyczeniach
    # Kolizja: planowany start <= wybrany koniec ORAZ planowany koniec >= wybrany start
    busy_items_query = db.query(models.PozycjaWypozyczenia.egzemplarz_id).join(models.Wypozyczenie).filter(
        models.Wypozyczenie.status.in_(["REZERWACJA", "WYDANE"]),
        and_(
            models.Wypozyczenie.data_plan_wydania <= end_dt,
            models.Wypozyczenie.data_plan_zwrotu >= start_dt
        )
    )
    busy_ids = [r[0] for r in busy_items_query.all()]

    return [item for item in functional_items if item.id not in busy_ids]


# app/backend/crud.py

# app/backend/crud.py

def create_reservation(db: Session, client_id: int, model_id: int, qty: int, start_dt: datetime, end_dt: datetime):
    # 1. Sprawdzamy dostępność
    available = get_available_items_for_term(db, model_id, start_dt, end_dt)

    if len(available) < qty:
        raise ValueError(f"Brak wolnych sztuk.")

    # 2. Pobieramy model, aby wyciągnąć cenę za dobę
    tool_model = db.query(models.ModelNarzedzia).filter(models.ModelNarzedzia.id == model_id).first()
    if not tool_model:
        raise ValueError("Nie znaleziono modelu narzędzia.")

    # 3. Obliczamy czas trwania (liczba dni)
    # Jeśli start i end to ten sam dzień, liczymy jako 1 dobę
    delta = end_dt.date() - start_dt.date()
    days = max(delta.days, 1)

    # 4. Wyliczamy koszt całkowity
    total_cost = days * tool_model.cena_za_dobe * qty

    # 5. Tworzymy nagłówek z poprawnym kosztem
    new_rental = models.Wypozyczenie(
        klient_id=client_id,
        status="REZERWACJA",
        data_plan_wydania=start_dt,
        data_plan_zwrotu=end_dt,
        magazynier_wydaj_id=None,
        magazynier_przyjmij_id=None,
        koszt_calkowity=total_cost  # <--- TUTAJ WPISUJEMY WYLICZONĄ KWOTĘ
    )

    db.add(new_rental)
    db.flush() # Pobieramy ID dla pozycji

    # 6. Dodajemy pozycje (egzemplarze)
    for i in range(qty):
        pos = models.PozycjaWypozyczenia(
            wypozyczenie_id=new_rental.id,
            egzemplarz_id=available[i].id
        )
        db.add(pos)

    db.commit()
    return new_rental


def create_customer(db: Session, payload: schemas.CustomerCreate):
    existing = db.query(models.Klient).filter(models.Klient.email == payload.email).first()
    if existing:
        raise ValueError("Użytkownik o tym adresie email już istnieje.")

    # TWORZYMY KLIENTA Z HASZOWANYM HASŁEM
    db_customer = models.Klient(
        imie=payload.imie,
        nazwisko=payload.nazwisko,
        email=payload.email,
        telefon=payload.telefon,
        haslo=hash_password(payload.haslo), # <--- UŻYWAMY HASHOWANIA
        pytanie_pomocnicze=payload.pytanie_pomocnicze,
        odp_na_pytanie_pom=payload.odpowiedz_pomocnicza
    )

    try:
        db.add(db_customer)
        db.commit()
        db.refresh(db_customer)
        return db_customer
    except Exception as e:
        db.rollback()
        raise e



def get_security_question_by_email(db: Session, email: str):
    """Szuka klienta po emailu i zwraca jego pytanie pomocnicze."""
    user = db.query(models.Klient).filter(models.Klient.email == email).first()
    if user:
        return user.pytanie_pomocnicze
    return None

def verify_security_answer(db: Session, email: str, answer: str):
    """Sprawdza, czy odpowiedź na pytanie pomocnicze się zgadza."""
    user = db.query(models.Klient).filter(
        models.Klient.email == email,
        models.Klient.odp_na_pytanie_pom == answer
    ).first()
    return user is not None


# app/backend/crud.py

def update_user_password(db: Session, user_obj: any, role: str, payload: schemas.PasswordChange):
    # 1. Łączymy obiekt z bieżącą sesją
    db_user = db.merge(user_obj)

    # 2. Weryfikacja starego hasła
    if not verify_password(payload.current_password, db_user.haslo):
        raise ValueError("Aktualne hasło jest niepoprawne")

    # 3. Hashowanie i zapis nowego hasła
    db_user.haslo = hash_password(payload.new_password)

    try:
        db.commit()
        db.refresh(db_user)
        # Zwracamy zaktualizowany obiekt, aby widok mógł go zapisać w sesji
        return db_user
    except Exception as e:
        db.rollback()
        raise e

def get_customer_rentals(db: Session, klient_id: int):
    """Pobiera historię wypożyczeń klienta wraz z pozycjami i modelami narzędzi."""
    return db.query(models.Wypozyczenie)\
        .options(
            joinedload(models.Wypozyczenie.pozycje)
            .joinedload(models.PozycjaWypozyczenia.egzemplarz)
            .joinedload(models.EgzemplarzNarzedzia.model)
        )\
        .filter(models.Wypozyczenie.klient_id == klient_id)\
        .order_by(models.Wypozyczenie.data_rezerwacji.desc())\
        .all()

def create_opinion(db: Session, klient_id: int, model_id: int, ocena: int, komentarz: str):
    """Zapisuje nową opinię klienta o modelu narzędzia."""
    new_opinion = models.Opinia(
        klient_id=klient_id,
        model_id=model_id,
        ocena=ocena,
        komentarz=komentarz,
        data_wystawienia=datetime.now()
    )
    db.add(new_opinion)
    db.commit()
    db.refresh(new_opinion)
    return new_opinion


def get_active_rental_items(db: Session, klient_id: int):
    """
    Pobiera wszystkie aktywne pozycje wypożyczeń dla klienta.
    Statusy: 'REZERWACJA' lub 'WYDANE' (czyli Twoje 'Aktywna').
    """
    return db.query(models.PozycjaWypozyczenia) \
        .join(models.Wypozyczenie) \
        .filter(
        models.Wypozyczenie.klient_id == klient_id,
        models.Wypozyczenie.status.in_(["REZERWACJA", "WYDANE"]),
        models.PozycjaWypozyczenia.czy_zgloszono_usterke == False
    ) \
        .all()


def report_tool_fault(db: Session, pozycja_id: int, opis: str):
    """
    Realizuje zgłoszenie usterki:
    1. Aktualizuje pozycję wypożyczenia.
    2. Zmienia status egzemplarza na AWARIA.
    """
    pozycja = db.query(models.PozycjaWypozyczenia).filter(models.PozycjaWypozyczenia.id == pozycja_id).first()
    if not pozycja:
        return False

    # 1. Aktualizacja pozycji
    pozycja.czy_zgloszono_usterke = True
    pozycja.opis_usterki = opis

    # 2. Zmiana statusu fizycznego egzemplarza
    # Zakładam, że w modelu EgzemplarzNarzedzia pole nazywa się 'status'
    pozycja.egzemplarz.status = "AWARIA"

    # Opcjonalnie: można tu dodać logikę zmiany statusu całego wypożyczenia,
    # ale zazwyczaj wypożyczenie trwa dalej dla pozostałych przedmiotów.

    try:
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise e

    # app/backend/crud.py

# app/backend/crud.py

def get_issued_rental_items(db: Session, klient_id: int):
    """
    Pobiera tylko te pozycje wypożyczeń, które są fizycznie u klienta.
    Filtrujemy po statusie wypożyczenia 'WYDANE'.
    """
    return db.query(models.PozycjaWypozyczenia)\
        .join(models.Wypozyczenie)\
        .filter(
            models.Wypozyczenie.klient_id == klient_id,
            models.Wypozyczenie.status == "WYDANE", # <--- Kluczowa zmiana
            models.PozycjaWypozyczenia.czy_zgloszono_usterke == False
        )\
        .all()

# app/backend/crud.py

def check_if_opinion_exists(db: Session, client_id: int, model_id: int) -> bool:
    """Sprawdza, czy ten klient już kiedykolwiek ocenił ten model narzędzia."""
    from . import models
    return db.query(models.Opinia).filter(
        models.Opinia.klient_id == client_id,
        models.Opinia.model_id == model_id
    ).first() is not None

# app/backend/crud.py

def get_model_opinions(db: Session, model_id: int):
    """Pobiera wszystkie opinie dla danego modelu wraz z danymi klientów."""
    return db.query(models.Opinia).filter(models.Opinia.model_id == model_id).all()