# app/backend/schemas.py
# Pydantic v2 schemas (minimal set) covering mockups / use-cases
from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, validator, field_validator


def validate_password_strength(v: str) -> str:
    if len(v) < 8:
        raise ValueError("musi mieć co najmniej 8 znaków")
    if not re.search(r"[A-Z]", v):
        raise ValueError("musi zawierać co najmniej jedną wielką literę")
    if not re.search(r"\d", v):
        raise ValueError("musi zawierać co najmniej jedną cyfrę")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>|]", v):
        raise ValueError("musi zawierać co najmniej jeden znak specjalny")
    return v

# =========================================================
# Base config for SQLAlchemy ORM objects
# =========================================================

class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# =========================================================
# AUTH
# =========================================================

class LoginRequest(BaseModel):
    login: str = Field(..., max_length=30)
    haslo: str = Field(..., max_length=255)


class TokenResponse(BaseModel):
    # If you decide not to implement JWT now, you can still return a dummy token/string.
    access_token: str
    token_type: str = "bearer"
    user_type: Literal["pracownik", "klient"]
    user_id: int


class ChangePasswordRequest(BaseModel):
    aktualne_haslo: str = Field(..., max_length=255)
    nowe_haslo: str = Field(..., max_length=255)
    powtorz_nowe_haslo: str = Field(..., max_length=255)  # can be validated in frontend too


class PasswordResetRequest(BaseModel):
    email: EmailStr
    odp_na_pytanie_pom: str = Field(..., max_length=255)
    nowe_haslo: str = Field(..., max_length=255)
    powtorz_nowe_haslo: str = Field(..., max_length=255)


# =========================================================
# EMPLOYEE MANAGEMENT (Kierownik)
# =========================================================

EmployeeRole = Literal["KIEROWNIK", "MAGAZYNIER", "SERWISANT"]


class EmployeeCreate(BaseModel):
    imie: str = Field(..., max_length=50)
    nazwisko: str = Field(..., max_length=50)
    pesel: str = Field(..., min_length=11, max_length=11)
    telefon: Optional[str] = Field(None, max_length=15)
    email: Optional[EmailStr] = None
    adres: Optional[str] = Field(None, max_length=255)
    login: str = Field(..., max_length=30)
    haslo: str = Field(..., max_length=255) # Walidacja poniżej
    rola: str # EmployeeRole (zależy jak masz zdefiniowany Enum)
    data_zatrudnienia: Optional[datetime] = None

    @field_validator("haslo")
    @classmethod
    def check_password_strength(cls, v):
        return validate_password_strength(v)

class EmployeeUpdate(BaseModel):
    imie: Optional[str] = Field(None, min_length=1, max_length=50)
    nazwisko: Optional[str] = Field(None, min_length=1, max_length=50)
    telefon: Optional[str] = Field(None, min_length=1, max_length=15)
    email: Optional[EmailStr] = None
    adres: Optional[str] = Field(None, min_length=1, max_length=255)
    login: Optional[str] = Field(None, min_length=1, max_length=30)
    rola: Optional[EmployeeRole] = None


class EmployeeRead(ORMBase):
    id: int
    imie: str
    nazwisko: str
    pesel: str
    telefon: Optional[str]
    email: Optional[EmailStr]
    adres: Optional[str]
    login: str
    data_utworzenia: datetime


# =========================================================
# CLIENT (self-registration)
# =========================================================

class CustomerCreate(BaseModel):
    imie: str = Field(..., min_length=2, max_length=50)
    nazwisko: str = Field(..., min_length=2, max_length=50)
    email: EmailStr
    telefon: str = Field(..., pattern=r"^\+?[0-9\s\-]{9,15}$")
    pytanie_pomocnicze: str
    odpowiedz_pomocnicza: str = Field(..., min_length=1)
    haslo: str
    haslo_powtorz: str

    @field_validator("haslo")
    @classmethod
    def password_rules(cls, v):
        return validate_password_strength(v)

    @field_validator("haslo_powtorz")
    @classmethod
    def passwords_match(cls, v, info):
        if "haslo" in info.data and v != info.data["haslo"]:
            raise ValueError("Hasła nie są identyczne")
        return v

class ClientRead(ORMBase):
    id: int
    imie: str
    nazwisko: str
    telefon: Optional[str]
    email: EmailStr
    odp_na_pytanie_pom: Optional[str]
    data_rejestracji: datetime


# =========================================================
# TOOL MODELS (Kierownik)
# =========================================================

class ToolModelCreate(BaseModel):
    nazwa_modelu: str = Field(..., max_length=100)
    producent: Optional[str] = Field(None, max_length=50)
    kategoria: Optional[str] = Field(None, max_length=50)
    opis: Optional[str] = None

    cena_za_dobe: Decimal = Field(..., ge=Decimal("0.00"))
    kaucja: Optional[Decimal] = Field(None, ge=Decimal("0.00"))


class ToolModelUpdate(BaseModel):
    nazwa_modelu: Optional[str] = Field(None, max_length=100)
    producent: Optional[str] = Field(None, max_length=50)
    kategoria: Optional[str] = Field(None, max_length=50)
    opis: Optional[str] = None

    cena_za_dobe: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    kaucja: Optional[Decimal] = Field(None, ge=Decimal("0.00"))

    # Optional: soft-withdraw (matches your "wycofaj model")
    wycofany: Optional[bool] = None


class ToolModelRead(ORMBase):
    id: int
    nazwa_modelu: str
    producent: Optional[str]
    kategoria: Optional[str]
    opis: Optional[str]
    cena_za_dobe: Decimal
    kaucja: Optional[Decimal]
    data_utworzenia: datetime


# =========================================================
# TOOL ITEMS (Magazynier/Serwisant views)
# =========================================================

ToolItemStatus = Literal["W_MAGAZYNIE", "W_WARSZTACIE", "U_KLIENTA", "WYCOFANY"]
ToolItemCondition = Literal["SPRAWNY", "DO_SERWISU", "USZKODZONY"]


class ToolItemRead(ORMBase):
    id: int
    model_id: int
    numer_seryjny: str
    status: ToolItemStatus
    stan_techniczny: ToolItemCondition
    data_zakupu: Optional[datetime]
    licznik_wypozyczen: int
    magazyn_id: Optional[int]
    warsztat_id: Optional[int]


class ToolItemUpdateTechnicalRequest(BaseModel):
    # Serwisant: "zmień stan" + "dodaj notatkę"
    stan_techniczny: ToolItemCondition
    notatka: Optional[str] = None


# =========================================================
# SERVICE (Serwisant)
# =========================================================

ServiceType = Literal["NAPRAWA", "PRZEGLAD", "KONSERWACJA", "WYMIANA"]


class ServiceActionCreate(BaseModel):
    egzemplarz_id: int
    serwisant_id: int  # FK to serwisanci.pracownik_id
    rodzaj: ServiceType
    notatka_opis: Optional[str] = None


# =========================================================
# RENTALS (Magazynier + Klient)
# =========================================================

RentalStatus = Literal["REZERWACJA", "WYDANE", "ZWROCONE", "ANULOWANE"]


class CreateRentalRequest(BaseModel):
    # Client makes reservation (or Magazynier creates on behalf)
    klient_id: int
    data_plan_wydania: Optional[datetime] = None
    data_plan_zwrotu: Optional[datetime] = None


class RentalRead(ORMBase):
    id: int
    klient_id: int
    magazynier_wydaj_id: Optional[int]
    magazynier_przyjmij_id: Optional[int]
    data_rezerwacji: datetime
    data_plan_wydania: Optional[datetime]
    data_plan_zwrotu: Optional[datetime]
    data_faktyczna_wydania: Optional[datetime]
    data_faktyczna_zwrotu: Optional[datetime]
    status: RentalStatus
    koszt_calkowity: Decimal


class RegisterIssueRequest(BaseModel):
    # Magazynier registers issue (wydanie)
    magazynier_wydaj_id: int
    data_faktyczna_wydania: Optional[datetime] = None
    # Optionally, if you issue specific items here:
    egzemplarze_ids: Optional[List[int]] = None


class ReturnedItemFault(BaseModel):
    egzemplarz_id: int
    czy_zgloszono_usterke: bool = False
    opis_usterki: Optional[str] = None


class RegisterReturnRequest(BaseModel):
    # Magazynier registers return (zwrot)
    magazynier_przyjmij_id: int
    data_faktyczna_zwrotu: Optional[datetime] = None
    zwroty: List[ReturnedItemFault] = Field(..., min_length=1)
    magazyn_id_docelowy: Optional[int] = None  # where to place good items after return


# =========================================================
# TOOL FLOW ACTIONS (Magazynier)
# =========================================================

LocationAction = Literal["PRZEKAZ_DO_SERWISU", "PRZYJMIJ_Z_SERWISU", "OZNACZ_DO_PRZEGLADU"]


class ChangeItemLocationRequest(BaseModel):
    egzemplarz_id: int
    magazynier_id: int
    akcja: LocationAction
    warsztat_id: Optional[int] = None
    magazyn_id: Optional[int] = None
    notatka: Optional[str] = None


class AcceptDeliveryRequest(BaseModel):
    # Magazynier accepts new stock of items for a given model
    magazynier_id: int
    model_id: int
    magazyn_id: int
    ilosc_sztuk: int = Field(..., ge=1)


# =========================================================
# OPINIONS (Klient)
# =========================================================

class OpinionCreate(BaseModel):
    model_id: int
    klient_id: int
    ocena: int = Field(..., ge=1, le=5)
    komentarz: Optional[str] = None


# =========================================================
# ANALYTICS & EXPORT
# =========================================================

class DateRangeRequest(BaseModel):
    data_od: date
    data_do: date


class ExportRequest(BaseModel):
    # Minimalistic export control for UI:
    # - table name chosen from a dropdown
    # - filters are optional and can be interpreted per-table
    tabela: str = Field(..., max_length=64)

    # Common simple filters (extend as needed)
    data_od: Optional[date] = None
    data_do: Optional[date] = None

    # Generic filters (e.g., {"status": "WYDANE", "klient_id": 5})
    filtry: Optional[Dict[str, Any]] = None
