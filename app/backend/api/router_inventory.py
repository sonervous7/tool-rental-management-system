from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.backend.core.database import get_db
from app.backend.modules.inventory import crud as inv_crud
from app.backend.modules.inventory import models as inv_models
from app.backend.modules.inventory import schemas as inv_schemas
from app.backend.modules.rentals import crud as rent_crud

router = APIRouter(prefix="/inventory", tags=["Inventory & Catalog"])


def _model_count_row(model, count: int) -> dict:
    return {"ModelNarzedzia": model, "liczba_sztuk": count}


def _item_to_flat_json(item: inv_models.EgzemplarzNarzedzia) -> dict:
    return {
        "id": item.id,
        "model_name": item.model.nazwa_modelu,
        "category": item.model.kategoria,
        "producer": item.model.producent,
        "sn": item.numer_seryjny,
        "stan": item.stan_techniczny,
        "status": item.status,
        "licznik": item.licznik_wypozyczen,
    }


@router.get("/models", response_model=List[inv_schemas.ToolModelSummaryRead])
def get_catalog(
    search: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
):
    results = inv_crud.list_models_with_available_counts(db, search=search, category=category)
    return [_model_count_row(model, count) for model, count in results]


@router.get("/models/{model_id}/availability")
def check_availability(
    model_id: int,
    start_dt: datetime,
    end_dt: datetime,
    db: Session = Depends(get_db),
):
    available = inv_crud.get_available_items_for_term(db, model_id, start_dt, end_dt)
    return {"count": len(available)}


@router.get("/models/{model_id}/opinions")
def get_opinions(model_id: int, db: Session = Depends(get_db)):
    results = rent_crud.get_model_opinions(db, model_id)
    return [
        {
            "id": row.Opinia.id,
            "ocena": row.Opinia.ocena,
            "komentarz": row.Opinia.komentarz,
            "data_wystawienia": (
                row.Opinia.created_at.isoformat() if hasattr(row.Opinia, "created_at") else ""
            ),
            "autor": row.imie,
        }
        for row in results
    ]


@router.get("/models/{model_id}/opinions/exists")
def check_opinion_exists(model_id: int, client_id: int, db: Session = Depends(get_db)):
    exists = rent_crud.check_if_opinion_exists(db, client_id, model_id)
    return {"exists": exists}


@router.get("/models/summary", response_model=List[inv_schemas.ToolModelSummaryRead])
def get_models_summary(db: Session = Depends(get_db)):
    results = inv_crud.list_models_with_counts(db)
    return [_model_count_row(model, count) for model, count in results]


@router.post("/items/bulk", status_code=status.HTTP_201_CREATED)
def bulk_add_items(model_id: int, quantity: int, db: Session = Depends(get_db)):
    try:
        inv_crud.bulk_create_items(db, model_id, quantity)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"message": f"Pomyślnie dodano {quantity} egzemplarzy do bazy."}


@router.get("/items", response_model=List[dict])
def list_all_items(
    search: Optional[str] = None,
    category: Optional[str] = None,
    producer: Optional[str] = None,
    location: Optional[str] = None,
    tech_state: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(inv_models.EgzemplarzNarzedzia).join(inv_models.ModelNarzedzia)

    if search:
        query = query.filter(
            inv_models.ModelNarzedzia.nazwa_modelu.ilike(f"%{search}%")
            | inv_models.EgzemplarzNarzedzia.numer_seryjny.ilike(f"%{search}%")
        )

    if category and category != "Wszystkie":
        query = query.filter(inv_models.ModelNarzedzia.kategoria == category)

    if producer and producer != "Wszyscy":
        query = query.filter(inv_models.ModelNarzedzia.producent == producer)

    if location and location != "Wszystkie":
        query = query.filter(inv_models.EgzemplarzNarzedzia.status == location)

    if tech_state and tech_state != "Wszystkie":
        query = query.filter(inv_models.EgzemplarzNarzedzia.stan_techniczny == tech_state)

    return [_item_to_flat_json(item) for item in query.all()]


@router.patch("/items/{item_id}/state")
def update_item_technical_state(item_id: int, new_state: str, db: Session = Depends(get_db)):
    item = inv_crud.update_technical_state(db, item_id, new_state)
    if not item:
        raise HTTPException(status_code=404, detail="Egzemplarz o podanym ID nie istnieje.")
    return {"message": "Stan techniczny został zaktualizowany."}


@router.post("/items/{item_id}/send-to-service")
def send_to_service(item_id: int, db: Session = Depends(get_db)):
    item = inv_crud.send_to_service(db, item_id)
    if not item:
        raise HTTPException(status_code=400, detail="Błąd podczas przekazywania do serwisu.")
    return {"message": "Narzędzie przekazane do warsztatu."}


@router.post("/items/{item_id}/receive-from-service")
def receive_from_service(item_id: int, db: Session = Depends(get_db)):
    item = inv_crud.receive_from_service(db, item_id)
    if not item:
        raise HTTPException(
            status_code=400,
            detail="Nie można przyjąć tego narzędzia (prawdopodobnie nie jest w warsztacie).",
        )
    return {"message": "Narzędzie zostało przyjęte do magazynu i jest gotowe do wypożyczenia."}


@router.post("/models", status_code=status.HTTP_201_CREATED)
def add_tool_model(payload: inv_schemas.ToolModelCreate, db: Session = Depends(get_db)):
    return inv_crud.create_tool_model(db, payload)


@router.patch("/models/{model_id}")
def update_tool_model(
    model_id: int,
    payload: inv_schemas.ToolModelUpdate,
    db: Session = Depends(get_db),
):
    try:
        return inv_crud.update_tool_model(db, model_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/models/{model_id}")
def withdraw_model(model_id: int, db: Session = Depends(get_db)):
    try:
        inv_crud.withdraw_tool_model(db, model_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"message": "Model został wycofany z oferty."}
