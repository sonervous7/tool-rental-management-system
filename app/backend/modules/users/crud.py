from datetime import datetime

from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.backend.core.security import _pwd_context, hash_password, verify_password

from . import models, schemas


def authenticate_user(db: Session, identifier: str, password: str):
    emp = (
        db.query(models.Pracownik)
        .filter(or_(models.Pracownik.login == identifier, models.Pracownik.email == identifier))
        .first()
    )

    if emp and verify_password(password, emp.haslo):
        role = "PRACOWNIK"
        if emp.kierownik:
            role = "KIEROWNIK"
        elif emp.magazynier:
            role = "MAGAZYNIER"
        elif emp.serwisant:
            role = "SERWISANT"
        return emp, role

    cust = db.query(models.Klient).filter(models.Klient.email == identifier).first()
    if cust and verify_password(password, cust.haslo):
        return cust, "KLIENT"

    return None, None


def create_employee(db: Session, payload: schemas.EmployeeCreate) -> models.Pracownik:
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
    except IntegrityError as exc:
        db.rollback()
        raise ValueError("PESEL, email lub login już istnieje w bazie.") from exc

    hire_date = payload.data_zatrudnienia or datetime.utcnow()

    if payload.rola == "KIEROWNIK":
        role_row = models.Kierownik(pracownik_id=pracownik.id, data_zatrudnienia=hire_date)
    elif payload.rola == "MAGAZYNIER":
        role_row = models.Magazynier(pracownik_id=pracownik.id, data_zatrudnienia=hire_date)
    elif payload.rola == "SERWISANT":
        role_row = models.Serwisant(pracownik_id=pracownik.id, data_zatrudnienia=hire_date)
    else:
        db.rollback()
        raise ValueError("Nieznana rola pracownika.")

    db.add(role_row)
    db.commit()
    db.refresh(pracownik)
    return pracownik


def update_employee(db: Session, employee_id: int, payload: schemas.EmployeeUpdate) -> models.Pracownik:
    pracownik = db.get(models.Pracownik, employee_id)
    if not pracownik:
        raise ValueError("Pracownik nie istnieje.")

    for field, value in payload.model_dump(exclude_unset=True).items():
        if field == "rola":
            continue
        setattr(pracownik, field, value)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ValueError("Błąd podczas aktualizacji danych pracownika (np. duplikat email).") from exc

    db.refresh(pracownik)
    return pracownik


def change_employee_role(db: Session, employee_id: int, new_role: str, start_date: datetime = None):
    pracownik = db.get(models.Pracownik, employee_id)
    if not pracownik:
        raise ValueError("Pracownik nie istnieje.")

    db.query(models.Kierownik).filter_by(pracownik_id=employee_id).delete()
    db.query(models.Magazynier).filter_by(pracownik_id=employee_id).delete()
    db.query(models.Serwisant).filter_by(pracownik_id=employee_id).delete()
    db.flush()

    date_val = start_date or datetime.utcnow()
    role_classes = {
        "KIEROWNIK": models.Kierownik,
        "MAGAZYNIER": models.Magazynier,
        "SERWISANT": models.Serwisant,
    }

    if new_role in role_classes:
        db.add(role_classes[new_role](pracownik_id=employee_id, data_zatrudnienia=date_val))
        db.commit()
    else:
        db.rollback()
        raise ValueError("Nieprawidłowa nazwa roli.")


def delete_employee(db: Session, employee_id: int):
    pracownik = db.get(models.Pracownik, employee_id)
    if not pracownik:
        raise ValueError("Pracownik nie istnieje.")

    try:
        db.delete(pracownik)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ValueError("Nie można usunąć pracownika - posiada powiązane rekordy w systemie.") from exc


def list_employees(db: Session) -> list[dict]:
    pracownicy = db.query(models.Pracownik).all()
    result = []

    for p in pracownicy:
        info_roli = ("BRAK", None)

        if p.kierownik:
            info_roli = ("KIEROWNIK", p.kierownik.data_zatrudnienia)
        elif p.magazynier:
            info_roli = ("MAGAZYNIER", p.magazynier.data_zatrudnienia)
        elif p.serwisant:
            info_roli = ("SERWISANT", p.serwisant.data_zatrudnienia)

        result.append(
            {
                "id": p.id,
                "imie": p.imie,
                "nazwisko": p.nazwisko,
                "login": p.login,
                "pesel": p.pesel,
                "email": p.email,
                "telefon": p.telefon,
                "adres": p.adres,
                "rola": info_roli[0],
                "zatrudniony_od": info_roli[1],
            }
        )
    return result


def create_customer(db: Session, payload: schemas.CustomerCreate):
    if db.query(models.Klient).filter_by(email=payload.email).first():
        raise ValueError("Użytkownik z tym adresem e-mail już istnieje.")

    hashed_pwd = _pwd_context.hash(payload.haslo)

    new_customer = models.Klient(
        imie=payload.imie,
        nazwisko=payload.nazwisko,
        email=payload.email,
        telefon=payload.telefon,
        haslo=hashed_pwd,
        pytanie_pomocnicze=payload.pytanie_pomocnicze,
        odp_na_pytanie_pom=payload.odpowiedz_pomocnicza,
    )

    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)
    return new_customer


def update_user_password(db: Session, user_obj, payload: schemas.PasswordChange):
    db_user = db.merge(user_obj)

    if not verify_password(payload.current_password, db_user.haslo):
        raise ValueError("Aktualne hasło jest niepoprawne.")

    db_user.haslo = hash_password(payload.new_password)
    db.commit()
    db.refresh(db_user)
    return db_user


def verify_security_answer(db: Session, email: str, answer: str):
    user = (
        db.query(models.Klient)
        .filter(
            models.Klient.email == email,
            models.Klient.odp_na_pytanie_pom == answer,
        )
        .first()
    )
    return user is not None


def get_security_question_by_email(db: Session, email: str):
    user = db.query(models.Klient).filter(models.Klient.email == email).first()
    if user:
        return user.pytanie_pomocnicze

    employee = db.query(models.Pracownik).filter(models.Pracownik.email == email).first()
    if employee:
        return employee.pytanie_pomocnicze

    return None
