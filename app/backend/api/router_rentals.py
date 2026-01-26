from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.backend.core.database import get_db
from app.backend.modules.inventory import models as inv_models
from app.backend.modules.rentals import crud as rent_crud
from app.backend.modules.rentals import schemas as rent_schemas

router = APIRouter(prefix="/rentals", tags=["Rentals & Service"])


def _iso(dt):
    return dt.isoformat() if dt else None


def _rental_position_payload(pos) -> dict:
    egz = pos.egzemplarz
    return {
        "egzemplarz": {
            "model_id": egz.model_id,
            "model": {"nazwa_modelu": egz.model.nazwa_modelu},
            "numer_seryjny": egz.numer_seryjny,
        }
    }


def _rental_history_row(rental) -> dict:
    pozycje = [p for p in rental.pozycje if p.egzemplarz]

    suma_kaucji = sum(p.egzemplarz.model.kaucja for p in pozycje)
    suma_dniowki = sum(p.egzemplarz.model.cena_za_dobe for p in pozycje)

    dni = (rental.data_plan_zwrotu - rental.data_plan_wydania).days
    if dni <= 0:
        dni = 1

    koszt_najmu = dni * suma_dniowki
    return {
        "id": rental.id,
        "status": rental.status,
        "koszt_najmu": koszt_najmu,
        "suma_kaucji": suma_kaucji,
        "koszt_calkowity": koszt_najmu + suma_kaucji,
        "data_plan_wydania": _iso(rental.data_plan_wydania),
        "data_plan_zwrotu": _iso(rental.data_plan_zwrotu),
        "data_faktyczna_wydania": _iso(rental.data_faktyczna_wydania),
        "data_faktyczna_zwrotu": _iso(rental.data_faktyczna_zwrotu),
        "pozycje": [_rental_position_payload(p) for p in rental.pozycje],
    }


def _issued_item_row(pos) -> dict:
    egz = pos.egzemplarz
    wyp = pos.wypozyczenie
    return {
        "id": pos.id,
        "model_name": egz.model.nazwa_modelu if egz else "Nieznany model",
        "sn": egz.numer_seryjny if egz else "Brak SN",
        "data_plan_zwrotu": _iso(wyp.data_plan_zwrotu) if wyp else None,
        "wypozyczenie_id": pos.wypozyczenie_id,
        "stan": egz.stan_techniczny if egz else "SPRAWNY",
    }


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_reservation(
    client_id: int,
    model_id: int,
    qty: int,
    start_dt: datetime,
    end_dt: datetime,
    db: Session = Depends(get_db),
):
    try:
        return rent_crud.create_reservation(db, client_id, model_id, qty, start_dt, end_dt)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/customer/{client_id}")
def get_history(client_id: int, db: Session = Depends(get_db)):
    rentals = rent_crud.get_customer_rentals(db, client_id)
    return [_rental_history_row(r) for r in rentals]


@router.get("/customer/{client_id}/issued")
def get_issued_items(client_id: int, db: Session = Depends(get_db)):
    positions = rent_crud.get_issued_rental_items(db, client_id)
    return [_issued_item_row(p) for p in positions]


@router.post("/faults")
def report_fault(pozycja_id: int, opis: str, db: Session = Depends(get_db)):
    success = rent_crud.report_tool_fault(db, pozycja_id, opis)
    if not success:
        raise HTTPException(status_code=404, detail="Nie znaleziono pozycji wypożyczenia")
    return {"message": "Usterka została pomyślnie zgłoszona"}


@router.post("/opinions")
def post_opinion(
    client_id: int,
    model_id: int,
    rating: int,
    comment: str,
    db: Session = Depends(get_db),
):
    try:
        return rent_crud.create_opinion(db, client_id, model_id, rating, comment)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/workshop", tags=["Technician"])
def get_workshop_items(
    search: Optional[str] = None,
    category: Optional[str] = None,
    producer: Optional[str] = None,
    status_tech: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = (
        db.query(inv_models.EgzemplarzNarzedzia)
        .filter(inv_models.EgzemplarzNarzedzia.status == "W_WARSZTACIE")
        .join(inv_models.ModelNarzedzia)
    )

    if search:
        query = query.filter(
            inv_models.ModelNarzedzia.nazwa_modelu.ilike(f"%{search}%")
            | inv_models.EgzemplarzNarzedzia.numer_seryjny.ilike(f"%{search}%")
        )

    if category and category != "Wszystkie":
        query = query.filter(inv_models.ModelNarzedzia.category == category)

    if producer and producer != "Wszyscy":
        query = query.filter(inv_models.ModelNarzedzia.producent == producer)

    if status_tech and status_tech != "Wszystkie":
        query = query.filter(inv_models.EgzemplarzNarzedzia.stan_techniczny == status_tech)

    return query.all()


@router.post("/service-action", tags=["Technician"])
def create_service_action(
    payload: rent_schemas.ServiceActionCreate,
    nowy_stan: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    try:
        rent_crud.add_service_action(
            db=db,
            egzemplarz_id=payload.egzemplarz_id,
            serwisant_id=payload.serwisant_id,
            rodzaj=payload.rodzaj,
            notatka=payload.notatka_opis,
            nowy_stan=nowy_stan,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"status": "success", "message": "Czynność serwisowa zarejestrowana"}


@router.get("/pending", tags=["Warehouse"])
def get_pending_operations(db: Session = Depends(get_db)):
    return rent_crud.list_pending_operations(db)


@router.post("/{rental_id}/process", tags=["Warehouse"])
def process_rental(rental_id: int, action: str, db: Session = Depends(get_db)):
    try:
        rent_crud.process_rental_action(db, rental_id, action)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"status": "success", "new_status": action}
