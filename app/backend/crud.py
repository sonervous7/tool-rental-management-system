# app/backend/crud.py
from __future__ import annotations
import datetime
import csv
import hashlib
import io
import bcrypt

from sqlalchemy import func, cast, Date
from sqlalchemy.orm import Session
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


def verify_password(password: str, hashed: str) -> bool:
    sha = hashlib.sha256(password.encode("utf-8")).digest()
    return bcrypt.checkpw(sha, hashed.encode("utf-8"))


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


def withdraw_tool_model(db: Session, model_id: int) -> None:
    """
    Soft-withdraw: sets wycofany=True.
    """
    model = db.get(models.ModelNarzedzia, model_id)
    if not model:
        raise ValueError("Model narzędzia nie istnieje.")

    model.wycofany = True
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise ValueError("Nie można wycofać modelu narzędzia.") from e


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

def analytics_summary(
    db: Session,
    date_from: Date,
    date_to: Date,
) -> dict:
    """
    Zwraca podsumowanie w okresie [date_from, date_to] po dacie rezerwacji.
    """
    start_dt = datetime.combine(date_from, datetime.min.time())
    end_dt = datetime.combine(date_to, datetime.max.time())

    total_rentals = (
        db.query(func.count(models.Wypozyczenie.id))
        .filter(models.Wypozyczenie.data_rezerwacji.between(start_dt, end_dt))
        .scalar()
        or 0
    )

    total_revenue = (
        db.query(func.coalesce(func.sum(models.Wypozyczenie.koszt_calkowity), 0))
        .filter(models.Wypozyczenie.data_rezerwacji.between(start_dt, end_dt))
        .scalar()
        or 0
    )

    return {
        "date_from": date_from,
        "date_to": date_to,
        "total_rentals": int(total_rentals),
        "total_revenue": float(total_revenue),
    }


def analytics_daily(
    db: Session,
    date_from: Date,
    date_to: Date,
) -> list[dict]:
    """
    Dzienna liczba wypożyczeń + dzienny przychód.
    """
    start_dt = datetime.combine(date_from, datetime.min.time())
    end_dt = datetime.combine(date_to, datetime.max.time())

    rows = (
        db.query(
            cast(models.Wypozyczenie.data_rezerwacji, Date).label("dzien"),
            func.count(models.Wypozyczenie.id).label("liczba_wypozyczen"),
            func.coalesce(func.sum(models.Wypozyczenie.koszt_calkowity), 0).label("przychod"),
        )
        .filter(models.Wypozyczenie.data_rezerwacji.between(start_dt, end_dt))
        .group_by("dzien")
        .order_by("dzien")
        .all()
    )

    return [
        {
            "dzien": r.dzien,
            "liczba_wypozyczen": int(r.liczba_wypozyczen),
            "przychod": float(r.przychod),
        }
        for r in rows
    ]


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
