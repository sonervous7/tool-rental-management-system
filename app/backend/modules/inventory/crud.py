from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.backend.modules.rentals import models as rental_models

from . import models, schemas


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
    db.commit()
    db.refresh(model)
    return model


def update_tool_model(db: Session, model_id: int, payload: schemas.ToolModelUpdate) -> models.ModelNarzedzia:
    model = db.get(models.ModelNarzedzia, model_id)
    if not model:
        raise ValueError("Model narzędzia nie istnieje.")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(model, field, value)

    db.commit()
    db.refresh(model)
    return model


def withdraw_tool_model(db: Session, model_id: int):
    count = (
        db.query(models.EgzemplarzNarzedzia)
        .filter(models.EgzemplarzNarzedzia.model_id == model_id)
        .count()
    )

    if count > 0:
        raise ValueError("Nie można wycofać modelu, który posiada przypisane egzemplarze!")

    model = db.get(models.ModelNarzedzia, model_id)
    if model:
        model.wycofany = True
        db.commit()
    return model


def list_models_with_available_counts(db: Session, search: str = None, category: str = None):
    from sqlalchemy import func, or_
    from app.backend.modules.inventory import models as inv_models

    subquery = (
        db.query(
            inv_models.EgzemplarzNarzedzia.model_id,
            func.count(inv_models.EgzemplarzNarzedzia.id).label("dostępne_sztuki"),
        )
        .filter(
            inv_models.EgzemplarzNarzedzia.status == "W_MAGAZYNIE",
            inv_models.EgzemplarzNarzedzia.stan_techniczny == "SPRAWNY",
        )
        .group_by(inv_models.EgzemplarzNarzedzia.model_id)
        .subquery()
    )

    query = (
        db.query(
            inv_models.ModelNarzedzia,
            func.coalesce(subquery.c.dostępne_sztuki, 0).label("liczba_sztuk"),
        )
        .outerjoin(subquery, inv_models.ModelNarzedzia.id == subquery.c.model_id)
    )

    if search:
        query = query.filter(
            or_(
                inv_models.ModelNarzedzia.nazwa_modelu.ilike(f"%{search}%"),
                inv_models.ModelNarzedzia.producent.ilike(f"%{search}%"),
            )
        )

    if category and category != "Wszystkie":
        query = query.filter(inv_models.ModelNarzedzia.kategoria == category)

    return query.all()


def list_models_with_counts(db: Session, search: str = "", cat: str = "Wszystkie"):
    count_subquery = (
        db.query(
            models.EgzemplarzNarzedzia.model_id,
            func.count(models.EgzemplarzNarzedzia.id).label("total"),
        )
        .group_by(models.EgzemplarzNarzedzia.model_id)
        .subquery()
    )

    query = (
        db.query(
            models.ModelNarzedzia,
            func.coalesce(count_subquery.c.total, 0).label("liczba_sztuk"),
        )
        .outerjoin(count_subquery, models.ModelNarzedzia.id == count_subquery.c.model_id)
    )

    if search:
        query = query.filter(models.ModelNarzedzia.nazwa_modelu.ilike(f"%{search}%"))
    if cat != "Wszystkie":
        query = query.filter(models.ModelNarzedzia.kategoria == cat)

    return query.filter(models.ModelNarzedzia.wycofany == False).all()


def bulk_create_items(db: Session, model_id: int, count: int):
    for _ in range(count):
        temp_sn = f"SN-{uuid.uuid4().hex[:6].upper()}"
        db_item = models.EgzemplarzNarzedzia(
            model_id=model_id,
            numer_seryjny=temp_sn,
            status="W_MAGAZYNIE",
            stan_techniczny="SPRAWNY",
        )
        db.add(db_item)
    db.commit()


def update_technical_state(db: Session, item_id: int, new_state: str):
    item = db.get(models.EgzemplarzNarzedzia, item_id)
    if item:
        if new_state in ["SPRAWNY", "AWARIA", "WYMAGA_PRZEGLADU"]:
            item.stan_techniczny = new_state
            db.commit()
    return item


def mark_for_inspection(db: Session, item_id: int):
    item = db.get(models.EgzemplarzNarzedzia, item_id)
    if item:
        item.stan_techniczny = "WYMAGA_PRZEGLADU"
        item.status = "W_WARSZTACIE"
        db.commit()
    return item


def receive_from_service(db: Session, item_id: int, warehouse_id: int = 1):
    item = db.get(models.EgzemplarzNarzedzia, item_id)
    if item and item.status == "W_WARSZTACIE":
        item.status = "W_MAGAZYNIE"
        item.stan_techniczny = "SPRAWNY"
        item.licznik_wypozyczen = 0
        item.warsztat_id = None
        item.magazyn_id = warehouse_id
        db.commit()
    return item


def send_to_service(db: Session, item_id: int, workshop_id: int = 1):
    item = db.get(models.EgzemplarzNarzedzia, item_id)
    if item:
        item.status = "W_WARSZTACIE"
        item.magazyn_id = None
        item.warsztat_id = workshop_id
        db.commit()
    return item


def count_physical_in_stock(db: Session, model_id: int):
    return (
        db.query(models.EgzemplarzNarzedzia)
        .filter(
            models.EgzemplarzNarzedzia.model_id == model_id,
            models.EgzemplarzNarzedzia.status == "W_MAGAZYNIE",
            models.EgzemplarzNarzedzia.stan_techniczny == "SPRAWNY",
        )
        .count()
    )


def get_available_items_for_term(db: Session, model_id: int, start_dt: datetime, end_dt: datetime):
    all_functional = (
        db.query(models.EgzemplarzNarzedzia)
        .filter(
            models.EgzemplarzNarzedzia.model_id == model_id,
            models.EgzemplarzNarzedzia.stan_techniczny == "SPRAWNY",
            models.EgzemplarzNarzedzia.status != "W_WARSZTACIE",
        )
        .all()
    )

    busy_items_query = (
        db.query(rental_models.PozycjaWypozyczenia.egzemplarz_id)
        .join(rental_models.Wypozyczenie)
        .filter(
            rental_models.Wypozyczenie.status.in_(["REZERWACJA", "WYDANE"]),
            and_(
                rental_models.Wypozyczenie.data_plan_wydania <= end_dt,
                rental_models.Wypozyczenie.data_plan_zwrotu >= start_dt,
            ),
        )
    )

    busy_ids = [r[0] for r in busy_items_query.all()]
    return [item for item in all_functional if item.id not in busy_ids]
