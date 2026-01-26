from typing import Optional, Literal
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from app.backend.core.schemas import ORMBase

ToolItemStatus = Literal["W_MAGAZYNIE", "W_WARSZTACIE", "U_KLIENTA", "WYCOFANY"]


class ToolModelCreate(BaseModel):
    nazwa_modelu: str = Field(..., max_length=100)
    producent: str = Field(..., max_length=50)
    kategoria: str = Field(..., max_length=50)  # Wymagany string
    opis: Optional[str] = Field(None, max_length=500)  # Opcjonalny string
    cena_za_dobe: Decimal = Field(..., ge=Decimal("0.00"))
    kaucja: Optional[Decimal] = Field(None, ge=Decimal("0.00"))


class ToolItemRead(ORMBase):
    id: int
    numer_seryjny: str
    status: ToolItemStatus
    stan_techniczny: str
    licznik_wypozyczen: int


class ToolModelRead(ORMBase):
    id: int
    nazwa_modelu: str
    producent: str
    kategoria: str
    cena_za_dobe: float
    kaucja: float


class ToolModelUpdate(BaseModel):
    """Wszystkie pola są opcjonalne, aby umożliwić aktualizację tylko wybranych danych."""
    nazwa_modelu: Optional[str] = Field(None, max_length=100)
    producent: Optional[str] = Field(None, max_length=50)
    kategoria: Optional[str] = Field(None, max_length=50)
    opis: Optional[str] = None
    cena_za_dobe: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    kaucja: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    wycofany: Optional[bool] = None


class ToolModelSummaryRead(BaseModel):
    """Specjalny schemat dla wyników zliczania sztuk."""
    ModelNarzedzia: ToolModelRead
    liczba_sztuk: int

    model_config = ConfigDict(from_attributes=True)
