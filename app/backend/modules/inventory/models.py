from datetime import datetime
from typing import List, Optional
from decimal import Decimal
from sqlalchemy import String, ForeignKey, Text, Numeric, CheckConstraint, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.backend.core.database import Base, TimestampMixin


class Magazyn(Base):
    __tablename__ = "magazyny"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nazwa: Mapped[str] = mapped_column(String(100))
    adres: Mapped[Optional[str]] = mapped_column(String(255))
    pojemnosc: Mapped[Optional[int]]
    egzemplarze: Mapped[List["EgzemplarzNarzedzia"]] = relationship(back_populates="magazyn")


class Warsztat(Base):
    __tablename__ = "warsztaty"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nazwa: Mapped[str] = mapped_column(String(100))
    adres: Mapped[Optional[str]] = mapped_column(String(255))
    egzemplarze: Mapped[List["EgzemplarzNarzedzia"]] = relationship(back_populates="warsztat")


class ModelNarzedzia(Base, TimestampMixin):
    __tablename__ = "modele_narzedzi"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nazwa_modelu: Mapped[str] = mapped_column(String(100))
    producent: Mapped[Optional[str]] = mapped_column(String(50))
    kategoria: Mapped[Optional[str]] = mapped_column(String(50))
    opis: Mapped[Optional[str]] = mapped_column(Text)
    cena_za_dobe: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    kaucja: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    wycofany: Mapped[bool] = mapped_column(Boolean, default=False)

    egzemplarze: Mapped[List["EgzemplarzNarzedzia"]] = relationship(back_populates="model")
    opinie: Mapped[List["Opinia"]] = relationship(back_populates="model", cascade="all, delete-orphan")


class EgzemplarzNarzedzia(Base):
    __tablename__ = "egzemplarze_narzedzi"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    model_id: Mapped[int] = mapped_column(ForeignKey("modele_narzedzi.id"))
    numer_seryjny: Mapped[str] = mapped_column(String(50), unique=True)
    status: Mapped[str] = mapped_column(String(50), default="W_MAGAZYNIE")
    stan_techniczny: Mapped[str] = mapped_column(String(50), default="SPRAWNY")
    data_zakupu: Mapped[Optional[datetime]]
    licznik_wypozyczen: Mapped[int] = mapped_column(default=0)
    magazyn_id: Mapped[Optional[int]] = mapped_column(ForeignKey("magazyny.id"))
    warsztat_id: Mapped[Optional[int]] = mapped_column(ForeignKey("warsztaty.id"))

    __table_args__ = (
        CheckConstraint("NOT (magazyn_id IS NOT NULL AND warsztat_id IS NOT NULL)",
                        name="ck_egzemplarz_magazyn_xor_warsztat"),
    )

    model: Mapped["ModelNarzedzia"] = relationship(back_populates="egzemplarze")
    magazyn: Mapped["Magazyn"] = relationship(back_populates="egzemplarze")
    warsztat: Mapped["Warsztat"] = relationship(back_populates="egzemplarze")
    pozycje_wypozyczenia: Mapped[List["PozycjaWypozyczenia"]] = relationship(back_populates="egzemplarz")
    historia_serwisowa: Mapped[List["CzynnoscSerwisowa"]] = relationship(back_populates="egzemplarz",
                                                                         cascade="all, delete-orphan")
