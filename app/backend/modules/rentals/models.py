from typing import List, Optional
from decimal import Decimal
from datetime import datetime
from sqlalchemy import String, ForeignKey, Text, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.backend.core.database import Base


class Wypozyczenie(Base):
    __tablename__ = "wypozyczenia"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    klient_id: Mapped[int] = mapped_column(ForeignKey("klienci.id"))
    magazynier_wydaj_id: Mapped[Optional[int]] = mapped_column(ForeignKey("magazynierzy.pracownik_id"))
    magazynier_przyjmij_id: Mapped[Optional[int]] = mapped_column(ForeignKey("magazynierzy.pracownik_id"))

    data_rezerwacji: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    data_plan_wydania: Mapped[Optional[datetime]]
    data_plan_zwrotu: Mapped[Optional[datetime]]
    data_faktyczna_wydania: Mapped[Optional[datetime]]
    data_faktyczna_zwrotu: Mapped[Optional[datetime]]

    status: Mapped[str] = mapped_column(String(20), default="REZERWACJA")
    koszt_calkowity: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.00)

    klient: Mapped["Klient"] = relationship(back_populates="wypozyczenia")
    pozycje: Mapped[List["PozycjaWypozyczenia"]] = relationship(back_populates="wypozyczenie",
                                                                cascade="all, delete-orphan")


class PozycjaWypozyczenia(Base):
    __tablename__ = "pozycje_wypozyczenia"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    wypozyczenie_id: Mapped[int] = mapped_column(ForeignKey("wypozyczenia.id", ondelete="CASCADE"))
    egzemplarz_id: Mapped[int] = mapped_column(ForeignKey("egzemplarze_narzedzi.id"))
    czy_zgloszono_usterke: Mapped[bool] = mapped_column(default=False)
    opis_usterki: Mapped[Optional[str]] = mapped_column(Text)

    __table_args__ = (UniqueConstraint("wypozyczenie_id", "egzemplarz_id", name="uq_pozycja_wyp_egz"),)
    wypozyczenie: Mapped["Wypozyczenie"] = relationship(back_populates="pozycje")
    egzemplarz: Mapped["EgzemplarzNarzedzia"] = relationship(back_populates="pozycje_wypozyczenia")


class CzynnoscSerwisowa(Base):
    __tablename__ = "czynnosci_serwisowe"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    egzemplarz_id: Mapped[int] = mapped_column(ForeignKey("egzemplarze_narzedzi.id"))
    serwisant_id: Mapped[int] = mapped_column(ForeignKey("serwisanci.pracownik_id"))
    rodzaj: Mapped[str] = mapped_column(String(50))
    data_rozpoczecia: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    data_zakonczenia: Mapped[Optional[datetime]]
    notatka_opis: Mapped[Optional[str]] = mapped_column(Text)

    egzemplarz: Mapped["EgzemplarzNarzedzia"] = relationship(back_populates="historia_serwisowa")
    serwisant: Mapped["Serwisant"] = relationship(back_populates="czynnosci_serwisowe")


class Opinia(Base):
    __tablename__ = "opinie"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    model_id: Mapped[int] = mapped_column(ForeignKey("modele_narzedzi.id"))
    klient_id: Mapped[int] = mapped_column(ForeignKey("klienci.id"))
    ocena: Mapped[int]
    komentarz: Mapped[Optional[str]] = mapped_column(Text)
    data_wystawienia: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    model: Mapped["ModelNarzedzia"] = relationship(back_populates="opinie")
    klient: Mapped["Klient"] = relationship(back_populates="opinie")
