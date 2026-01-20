# app/backend/models.py

import datetime as dt

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .database import Base


# =========================================================
# UZYTKOWNICY I ROLE (zgodne z ERD: Pracownik + tabele rol)
# =========================================================

class Pracownik(Base):
    __tablename__ = "pracownicy"

    id = Column(Integer, primary_key=True, index=True)

    imie = Column(String(50), nullable=False)
    nazwisko = Column(String(50), nullable=False)
    pesel = Column(String(11), unique=True, nullable=False)

    adres = Column(String(255), nullable=True)
    telefon = Column(String(15), nullable=True)
    email = Column(String(100), unique=True, nullable=True)

    login = Column(String(30), unique=True, nullable=False)
    haslo = Column(String(255), nullable=False)

    data_utworzenia = Column(DateTime, default=dt.datetime.utcnow, nullable=False)

    # 1:1 role (podtypy) – pełna symetria back_populates
    kierownik = relationship(
        "Kierownik",
        back_populates="pracownik",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    magazynier = relationship(
        "Magazynier",
        back_populates="pracownik",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    serwisant = relationship(
        "Serwisant",
        back_populates="pracownik",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Kierownik(Base):
    __tablename__ = "kierownicy"

    pracownik_id = Column(
        Integer,
        ForeignKey("pracownicy.id", ondelete="CASCADE"),
        primary_key=True,
    )
    data_zatrudnienia = Column(DateTime, default=dt.datetime.utcnow, nullable=False)
    data_zwolnienia = Column(DateTime, nullable=True)
    # 1:1 back to Pracownik
    pracownik = relationship("Pracownik", back_populates="kierownik", uselist=False)


class Magazynier(Base):
    __tablename__ = "magazynierzy"

    pracownik_id = Column(
        Integer,
        ForeignKey("pracownicy.id", ondelete="CASCADE"),
        primary_key=True,
    )
    data_zatrudnienia = Column(DateTime, default=dt.datetime.utcnow, nullable=False)
    data_zwolnienia = Column(DateTime, nullable=True)
    pracownik = relationship("Pracownik", back_populates="magazynier", uselist=False)


class Serwisant(Base):
    __tablename__ = "serwisanci"

    pracownik_id = Column(
        Integer,
        ForeignKey("pracownicy.id", ondelete="CASCADE"),
        primary_key=True,
    )
    data_zatrudnienia = Column(DateTime, default=dt.datetime.utcnow, nullable=False)
    data_zwolnienia = Column(DateTime, nullable=True)
    pracownik = relationship("Pracownik", back_populates="serwisant", uselist=False)

    czynnosci_serwisowe = relationship(
        "CzynnoscSerwisowa",
        back_populates="serwisant",
        cascade="all, delete-orphan",
    )



class Klient(Base):
    __tablename__ = "klienci"

    id = Column(Integer, primary_key=True, index=True)

    imie = Column(String(50), nullable=False)
    nazwisko = Column(String(50), nullable=False)

    email = Column(String(100), unique=True, nullable=False)
    telefon = Column(String(15), nullable=True)

    haslo = Column(String(255), nullable=False)
    data_rejestracji = Column(DateTime, default=dt.datetime.utcnow, nullable=False)

    pytanie_pomocnicze = Column(String(255), nullable=True)
    odp_na_pytanie_pom = Column(String(255), nullable=True)

    wypozyczenia = relationship("Wypozyczenie", back_populates="klient")
    opinie = relationship("Opinia", back_populates="klient", cascade="all, delete-orphan")


# =========================================================
# LOKALIZACJE
# =========================================================

class Magazyn(Base):
    __tablename__ = "magazyny"

    id = Column(Integer, primary_key=True, index=True)
    nazwa = Column(String(100), nullable=False)
    adres = Column(String(255), nullable=True)
    pojemnosc = Column(Integer, nullable=True)

    egzemplarze = relationship("EgzemplarzNarzedzia", back_populates="magazyn")


class Warsztat(Base):
    __tablename__ = "warsztaty"

    id = Column(Integer, primary_key=True, index=True)
    nazwa = Column(String(100), nullable=False)
    adres = Column(String(255), nullable=True)

    egzemplarze = relationship("EgzemplarzNarzedzia", back_populates="warsztat")


# =========================================================
# ZASOBY (3NF: Model vs Egzemplarz)
# =========================================================

class ModelNarzedzia(Base):
    __tablename__ = "modele_narzedzi"

    id = Column(Integer, primary_key=True, index=True)

    nazwa_modelu = Column(String(100), nullable=False)
    producent = Column(String(50), nullable=True)
    kategoria = Column(String(50), nullable=True)
    opis = Column(Text, nullable=True)

    cena_za_dobe = Column(Numeric(10, 2), nullable=False)
    kaucja = Column(Numeric(10, 2), nullable=True)

    data_utworzenia = Column(DateTime, default=dt.datetime.utcnow, nullable=False)

    egzemplarze = relationship("EgzemplarzNarzedzia", back_populates="model")
    opinie = relationship("Opinia", back_populates="model", cascade="all, delete-orphan")
    wycofany = Column(Boolean, default=False, nullable=False)

class EgzemplarzNarzedzia(Base):
    __tablename__ = "egzemplarze_narzedzi"

    id = Column(Integer, primary_key=True, index=True)

    model_id = Column(Integer, ForeignKey("modele_narzedzi.id"), nullable=False)

    numer_seryjny = Column(String(50), unique=True, nullable=False)

    # status = "gdzie jest / czyj jest" (lokalizacja/posiadanie)
    status = Column(String(50), nullable=False, default="W_MAGAZYNIE")
    # stan_techniczny = "czy jest sprawny"
    stan_techniczny = Column(String(50), nullable=False, default="SPRAWNY")

    data_zakupu = Column(DateTime, nullable=True)
    licznik_wypozyczen = Column(Integer, default=0, nullable=False)

    # Lokalizacje (mogą być NULL: u klienta lub wycofany)
    magazyn_id = Column(Integer, ForeignKey("magazyny.id"), nullable=True)
    warsztat_id = Column(Integer, ForeignKey("warsztaty.id"), nullable=True)

    __table_args__ = (
        # Nie może być jednocześnie w magazynie i w warsztacie
        CheckConstraint(
            "NOT (magazyn_id IS NOT NULL AND warsztat_id IS NOT NULL)",
            name="ck_egzemplarz_magazyn_xor_warsztat",
        ),
    )

    model = relationship("ModelNarzedzia", back_populates="egzemplarze")
    magazyn = relationship("Magazyn", back_populates="egzemplarze")
    warsztat = relationship("Warsztat", back_populates="egzemplarze")

    pozycje_wypozyczenia = relationship("PozycjaWypozyczenia", back_populates="egzemplarz")
    historia_serwisowa = relationship(
        "CzynnoscSerwisowa",
        back_populates="egzemplarz",
        cascade="all, delete-orphan",
    )


# =========================================================
# PROCES WYPOZYCZENIA
# =========================================================

class Wypozyczenie(Base):
    __tablename__ = "wypozyczenia"

    id = Column(Integer, primary_key=True, index=True)

    klient_id = Column(Integer, ForeignKey("klienci.id"), nullable=False)

    # zgodnie z ERD: wydaje/przyjmuje magazynier
    magazynier_wydaj_id = Column(
        Integer,
        ForeignKey("magazynierzy.pracownik_id"),
        nullable=True,
    )
    magazynier_przyjmij_id = Column(
        Integer,
        ForeignKey("magazynierzy.pracownik_id"),
        nullable=True,
    )

    data_rezerwacji = Column(DateTime, default=dt.datetime.utcnow, nullable=False)

    data_plan_wydania = Column(DateTime, nullable=True)
    data_plan_zwrotu = Column(DateTime, nullable=True)

    data_faktyczna_wydania = Column(DateTime, nullable=True)
    data_faktyczna_zwrotu = Column(DateTime, nullable=True)

    status = Column(String(20), nullable=False, default="REZERWACJA")
    koszt_calkowity = Column(Numeric(10, 2), default=0.00, nullable=False)

    klient = relationship("Klient", back_populates="wypozyczenia")

    magazynier_wydaj = relationship(
        "Magazynier",
        foreign_keys=[magazynier_wydaj_id],
        uselist=False,
    )
    magazynier_przyjmij = relationship(
        "Magazynier",
        foreign_keys=[magazynier_przyjmij_id],
        uselist=False,
    )

    pozycje = relationship(
        "PozycjaWypozyczenia",
        back_populates="wypozyczenie",
        cascade="all, delete-orphan",
    )



class PozycjaWypozyczenia(Base):
    __tablename__ = "pozycje_wypozyczenia"

    id = Column(Integer, primary_key=True, index=True)

    wypozyczenie_id = Column(Integer, ForeignKey("wypozyczenia.id", ondelete="CASCADE"), nullable=False)
    egzemplarz_id = Column(Integer, ForeignKey("egzemplarze_narzedzi.id"), nullable=False)

    czy_zgloszono_usterke = Column(Boolean, default=False, nullable=False)
    opis_usterki = Column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "wypozyczenie_id",
            "egzemplarz_id",
            name="uq_pozycja_wypozyczenia_egzemplarz_wypozyczenie",
        ),
    )

    wypozyczenie = relationship("Wypozyczenie", back_populates="pozycje")
    egzemplarz = relationship("EgzemplarzNarzedzia", back_populates="pozycje_wypozyczenia")


# =========================================================
# SERWIS I OPINIE
# =========================================================

class CzynnoscSerwisowa(Base):
    __tablename__ = "czynnosci_serwisowe"

    id = Column(Integer, primary_key=True, index=True)

    egzemplarz_id = Column(Integer, ForeignKey("egzemplarze_narzedzi.id"), nullable=False)
    serwisant_id = Column(Integer, ForeignKey("serwisanci.pracownik_id"), nullable=False)

    rodzaj = Column(String(50), nullable=False)  # np. NAPRAWA/PRZEGLAD/KONSERWACJA
    data_rozpoczecia = Column(DateTime, default=dt.datetime.utcnow, nullable=False)
    data_zakonczenia = Column(DateTime, nullable=True)

    notatka_opis = Column(Text, nullable=True)

    egzemplarz = relationship("EgzemplarzNarzedzia", back_populates="historia_serwisowa")
    serwisant = relationship("Serwisant", back_populates="czynnosci_serwisowe")


class Opinia(Base):
    __tablename__ = "opinie"

    id = Column(Integer, primary_key=True, index=True)

    model_id = Column(Integer, ForeignKey("modele_narzedzi.id"), nullable=False)
    klient_id = Column(Integer, ForeignKey("klienci.id"), nullable=False)

    ocena = Column(Integer, nullable=False)  # waliduj w API (np. 1..5)
    komentarz = Column(Text, nullable=True)
    data_wystawienia = Column(DateTime, default=dt.datetime.utcnow, nullable=False)

    model = relationship("ModelNarzedzia", back_populates="opinie")
    klient = relationship("Klient", back_populates="opinie")