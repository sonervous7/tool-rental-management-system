from typing import List, Optional
from datetime import datetime
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.backend.core.database import Base, TimestampMixin


class Pracownik(Base, TimestampMixin):
    __tablename__ = "pracownicy"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    imie: Mapped[str] = mapped_column(String(50))
    nazwisko: Mapped[str] = mapped_column(String(50))
    pesel: Mapped[str] = mapped_column(String(11), unique=True)
    adres: Mapped[Optional[str]] = mapped_column(String(255))
    telefon: Mapped[Optional[str]] = mapped_column(String(15))
    email: Mapped[Optional[str]] = mapped_column(String(100), unique=True)
    login: Mapped[str] = mapped_column(String(30), unique=True)
    haslo: Mapped[str] = mapped_column(String(255))

    kierownik: Mapped["Kierownik"] = relationship(back_populates="pracownik", uselist=False,
                                                  cascade="all, delete-orphan")
    magazynier: Mapped["Magazynier"] = relationship(back_populates="pracownik", uselist=False,
                                                    cascade="all, delete-orphan")
    serwisant: Mapped["Serwisant"] = relationship(back_populates="pracownik", uselist=False,
                                                  cascade="all, delete-orphan")


class Kierownik(Base):
    __tablename__ = "kierownicy"
    pracownik_id: Mapped[int] = mapped_column(ForeignKey("pracownicy.id", ondelete="CASCADE"), primary_key=True)
    data_zatrudnienia: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    data_zwolnienia: Mapped[Optional[datetime]]
    pracownik: Mapped["Pracownik"] = relationship(back_populates="kierownik")


class Magazynier(Base):
    __tablename__ = "magazynierzy"
    pracownik_id: Mapped[int] = mapped_column(ForeignKey("pracownicy.id", ondelete="CASCADE"), primary_key=True)
    data_zatrudnienia: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    data_zwolnienia: Mapped[Optional[datetime]]
    pracownik: Mapped["Pracownik"] = relationship(back_populates="magazynier")


class Serwisant(Base):
    __tablename__ = "serwisanci"
    pracownik_id: Mapped[int] = mapped_column(ForeignKey("pracownicy.id", ondelete="CASCADE"), primary_key=True)
    data_zatrudnienia: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    data_zwolnienia: Mapped[Optional[datetime]]
    pracownik: Mapped["Pracownik"] = relationship(back_populates="serwisant")
    czynnosci_serwisowe: Mapped[List["CzynnoscSerwisowa"]] = relationship(back_populates="serwisant")


class Klient(Base, TimestampMixin):
    __tablename__ = "klienci"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    imie: Mapped[str] = mapped_column(String(50))
    nazwisko: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(100), unique=True)
    telefon: Mapped[Optional[str]] = mapped_column(String(15))
    haslo: Mapped[str] = mapped_column(String(255))
    pytanie_pomocnicze: Mapped[Optional[str]] = mapped_column(String(255))
    odp_na_pytanie_pom: Mapped[Optional[str]] = mapped_column(String(255))

    wypozyczenia: Mapped[List["Wypozyczenie"]] = relationship(back_populates="klient")
    opinie: Mapped[List["Opinia"]] = relationship(back_populates="klient", cascade="all, delete-orphan")
