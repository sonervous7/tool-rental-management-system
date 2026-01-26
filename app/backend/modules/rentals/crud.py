from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session, joinedload

from app.backend.modules.inventory import crud as inv_crud
from app.backend.modules.inventory import models as inv_models
from app.backend.modules.rentals import models as rent_models
from app.backend.modules.users import models as user_models

from . import models


def create_reservation(db: Session, client_id: int, model_id: int, qty: int, start_dt: datetime, end_dt: datetime):
    available = inv_crud.get_available_items_for_term(db, model_id, start_dt, end_dt)
    if len(available) < qty:
        raise ValueError(f"Brak wystarczającej liczby wolnych sztuk ({len(available)} dostępnych).")

    tool_model = db.get(inv_models.ModelNarzedzia, model_id)
    if not tool_model:
        raise ValueError("Nie znaleziono modelu narzędzia.")

    delta = end_dt.date() - start_dt.date()
    days = max(delta.days, 1)
    total_cost = days * tool_model.cena_za_dobe * qty

    new_rental = models.Wypozyczenie(
        klient_id=client_id,
        status="REZERWACJA",
        data_plan_wydania=start_dt,
        data_plan_zwrotu=end_dt,
        koszt_calkowity=total_cost,
    )
    db.add(new_rental)
    db.flush()

    for i in range(qty):
        pos = models.PozycjaWypozyczenia(
            wypozyczenie_id=new_rental.id,
            egzemplarz_id=available[i].id,
        )
        db.add(pos)

    db.commit()
    return new_rental


def process_rental_action(db: Session, wypozyczenie_id: int, nowy_status: str):
    wyp_obj = db.query(models.Wypozyczenie).filter(models.Wypozyczenie.id == wypozyczenie_id).first()
    if not wyp_obj:
        raise ValueError("Nie znaleziono wypożyczenia.")

    wyp_obj.status = nowy_status

    if nowy_status == "WYDANE":
        wyp_obj.data_faktyczna_wydania = datetime.utcnow()
        for p in wyp_obj.pozycje:
            p.egzemplarz.status = "U_KLIENTA"

    elif nowy_status == "ZAKOŃCZONA":
        wyp_obj.data_faktyczna_zwrotu = datetime.utcnow()
        for p in wyp_obj.pozycje:
            egz = p.egzemplarz
            egz.status = "W_MAGAZYNIE"
            egz.licznik_wypozyczen += 1

            if p.czy_zgloszono_usterke:
                egz.stan_techniczny = "AWARIA"
            elif egz.licznik_wypozyczen >= 5:
                egz.stan_techniczny = "WYMAGA_PRZEGLADU"
            else:
                egz.stan_techniczny = "SPRAWNY"

    db.commit()
    return wyp_obj


def add_service_action(
    db: Session,
    egzemplarz_id: int,
    serwisant_id: int,
    rodzaj: str,
    notatka: str,
    nowy_stan: str = None,
):
    egzemplarz = db.get(inv_models.EgzemplarzNarzedzia, egzemplarz_id)
    if not egzemplarz:
        raise ValueError("Nie znaleziono egzemplarza.")

    nowa_czynnosc = models.CzynnoscSerwisowa(
        egzemplarz_id=egzemplarz_id,
        serwisant_id=serwisant_id,
        rodzaj=rodzaj,
        notatka_opis=notatka,
        data_zakonczenia=datetime.utcnow(),
    )
    db.add(nowa_czynnosc)

    if nowy_stan:
        egzemplarz.stan_techniczny = nowy_stan
        if nowy_stan == "SPRAWNY":
            egzemplarz.licznik_wypozyczen = 0

    db.commit()


def report_tool_fault(db: Session, pozycja_id: int, opis: str):
    pozycja = db.get(models.PozycjaWypozyczenia, pozycja_id)
    if not pozycja:
        return False

    pozycja.czy_zgloszono_usterke = True
    pozycja.opis_usterki = opis
    pozycja.egzemplarz.stan_techniczny = "AWARIA"

    db.commit()
    return True


def get_customer_rentals(db: Session, klient_id: int):
    return (
        db.query(models.Wypozyczenie)
        .options(
            joinedload(models.Wypozyczenie.pozycje)
            .joinedload(models.PozycjaWypozyczenia.egzemplarz)
            .joinedload(inv_models.EgzemplarzNarzedzia.model)
        )
        .filter(models.Wypozyczenie.klient_id == klient_id)
        .order_by(models.Wypozyczenie.data_rezerwacji.desc())
        .all()
    )


def create_opinion(db: Session, klient_id: int, model_id: int, ocena: int, komentarz: str):
    if db.query(models.Opinia).filter_by(klient_id=klient_id, model_id=model_id).first():
        raise ValueError("Już wystawiłeś opinię dla tego modelu.")

    new_opinion = models.Opinia(
        klient_id=klient_id,
        model_id=model_id,
        ocena=ocena,
        komentarz=komentarz,
    )
    db.add(new_opinion)
    db.commit()
    return new_opinion


def list_pending_operations(db: Session):
    rentals = (
        db.query(models.Wypozyczenie)
        .options(
            joinedload(models.Wypozyczenie.klient),
            joinedload(models.Wypozyczenie.pozycje)
            .joinedload(models.PozycjaWypozyczenia.egzemplarz)
            .joinedload(inv_models.EgzemplarzNarzedzia.model),
        )
        .filter(models.Wypozyczenie.status.in_(["REZERWACJA", "WYDANE"]))
        .all()
    )

    results = []
    for r in rentals:
        modele = ", ".join(list(set([p.egzemplarz.model.nazwa_modelu for p in r.pozycje])))
        typ = "WYDANIE" if r.status == "REZERWACJA" else "ZWROT"
        data = r.data_plan_wydania if r.status == "REZERWACJA" else r.data_plan_zwrotu

        results.append(
            {
                "id": r.id,
                "typ": typ,
                "data_planowana": data,
                "klient": f"{r.klient.imie} {r.klient.nazwisko}",
                "model": modele,
                "obj": r,
            }
        )
    return results


def get_issued_rental_items(db: Session, client_id: Optional[int] = None):
    query = (
        db.query(rent_models.PozycjaWypozyczenia)
        .join(rent_models.Wypozyczenie)
        .options(
            joinedload(rent_models.PozycjaWypozyczenia.egzemplarz).joinedload(inv_models.EgzemplarzNarzedzia.model),
            joinedload(rent_models.PozycjaWypozyczenia.wypozyczenie),
        )
        .filter(rent_models.Wypozyczenie.status == "WYDANE")
    )

    if client_id:
        query = query.filter(rent_models.Wypozyczenie.klient_id == client_id)

    return query.all()


def get_model_opinions(db: Session, model_id: int):
    return (
        db.query(
            rent_models.Opinia,
            user_models.Klient.imie,
        )
        .join(user_models.Klient, rent_models.Opinia.klient_id == user_models.Klient.id)
        .filter(rent_models.Opinia.model_id == model_id)
        .all()
    )


def check_if_opinion_exists(db: Session, client_id: int, model_id: int) -> bool:
    result = (
        db.query(rent_models.Opinia)
        .filter(
            rent_models.Opinia.klient_id == client_id,
            rent_models.Opinia.model_id == model_id,
        )
        .first()
    )
    return result is not None
