from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from app.backend.core.schemas import ORMBase


class CreateRentalRequest(BaseModel):
    klient_id: int
    data_plan_wydania: Optional[datetime] = None
    data_plan_zwrotu: Optional[datetime] = None


class ReturnedItemFault(BaseModel):
    egzemplarz_id: int
    czy_zgloszono_usterke: bool = False
    opis_usterki: Optional[str] = None


class RegisterReturnRequest(BaseModel):
    magazynier_przyjmij_id: int
    zwroty: List[ReturnedItemFault] = Field(..., min_length=1)


class ServiceActionCreate(BaseModel):
    """Schemat do rejestracji nowej czynności serwisowej przez technika."""
    egzemplarz_id: int
    serwisant_id: int
    rodzaj: str = Field(..., max_length=50)
    notatka_opis: Optional[str] = None

    class Config:
        from_attributes = True
