from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, EmailStr, Field, field_validator
from app.backend.core.schemas import ORMBase, validate_password_strength


class LoginRequest(BaseModel):
    login: str = Field(..., max_length=30)
    haslo: str = Field(..., max_length=255)


class EmployeeCreate(BaseModel):
    imie: str = Field(..., min_length=1, max_length=50)
    nazwisko: str = Field(..., min_length=1, max_length=50)
    pesel: str = Field(..., min_length=11, max_length=11)
    adres: str = Field(..., min_length=1, max_length=255)
    email: EmailStr = Field(...)
    telefon: str = Field(..., min_length=7, max_length=15)
    login: str = Field(..., min_length=3, max_length=30)
    haslo: str
    rola: Literal["KIEROWNIK", "MAGAZYNIER", "SERWISANT"]
    data_zatrudnienia: Optional[datetime] = None

    @field_validator("haslo")
    @classmethod
    def check_password(cls, v):
        return validate_password_strength(v)


class EmployeeUpdate(BaseModel):
    imie: Optional[str] = Field(None, max_length=50)
    nazwisko: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    telefon: Optional[str] = None
    adres: Optional[str] = None
    rola: Optional[Literal["KIEROWNIK", "MAGAZYNIER", "SERWISANT"]] = None
    data_zatrudnienia: Optional[datetime] = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str

    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v, info):
        if 'new_password' in info.data and v != info.data['new_password']:
            raise ValueError('Hasła nie są identyczne')
        return v


class CustomerCreate(BaseModel):
    imie: str = Field(..., max_length=50)
    nazwisko: str = Field(..., max_length=50)
    email: EmailStr = Field(..., max_length=100)
    telefon: Optional[str] = Field(None, max_length=15)
    pytanie_pomocnicze: str = Field(..., max_length=255)
    # Mapujemy nazwę z frontendu na tę, którą wyślemy do bazy
    odpowiedz_pomocnicza: str = Field(..., max_length=255)
    haslo: str = Field(..., min_length=8)
    haslo_powtorz: str

    @field_validator("haslo")
    @classmethod
    def check_password_strength(cls, v):
        return validate_password_strength(v)

    @field_validator("haslo_powtorz")
    @classmethod
    def passwords_match(cls, v, info):
        if 'haslo' in info.data and v != info.data['haslo']:
            raise ValueError('Hasła nie są identyczne')
        return v


class ClientRead(ORMBase):
    id: int
    imie: str
    nazwisko: str
    email: EmailStr
