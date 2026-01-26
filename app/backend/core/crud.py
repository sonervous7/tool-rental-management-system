import csv
import io
from datetime import date, datetime, timedelta

from sqlalchemy import Date, cast, func
from sqlalchemy.orm import Session

from app.backend.modules.inventory import models as inv_models
from app.backend.modules.rentals import models as rental_models
from app.backend.modules.users import models as user_models


_EXPORT_MAP = {
    "pracownicy": user_models.Pracownik,
    "klienci": user_models.Klient,
    "modele_narzedzi": inv_models.ModelNarzedzia,
    "egzemplarze_narzedzi": inv_models.EgzemplarzNarzedzia,
    "wypozyczenia": rental_models.Wypozyczenie,
    "opinie": rental_models.Opinia,
}


def get_dashboard_summary(db: Session, date_from: date, date_to: date):
    start_dt = datetime.combine(date_from, datetime.min.time())
    end_dt = datetime.combine(date_to, datetime.max.time())

    total_rentals = (
        db.query(func.count(rental_models.Wypozyczenie.id))
        .filter(rental_models.Wypozyczenie.data_rezerwacji.between(start_dt, end_dt))
        .scalar()
        or 0
    )

    total_revenue = (
        db.query(func.sum(rental_models.Wypozyczenie.koszt_calkowity))
        .filter(rental_models.Wypozyczenie.data_rezerwacji.between(start_dt, end_dt))
        .scalar()
        or 0
    )

    daily_stats_raw = (
        db.query(
            func.date(rental_models.Wypozyczenie.data_rezerwacji).label("date"),
            func.sum(rental_models.Wypozyczenie.koszt_calkowity).label("revenue"),
            func.count(rental_models.Wypozyczenie.id).label("count"),
        )
        .filter(rental_models.Wypozyczenie.data_rezerwacji.between(start_dt, end_dt))
        .group_by(func.date(rental_models.Wypozyczenie.data_rezerwacji))
        .order_by("date")
        .all()
    )

    daily_stats = [
        {"date": str(row.date), "revenue": float(row.revenue or 0), "count": int(row.count or 0)}
        for row in daily_stats_raw
    ]

    return {
        "total_rentals": int(total_rentals),
        "total_revenue": float(total_revenue),
        "daily_stats": daily_stats,
    }


def get_top_performing_models(db: Session, limit: int = 5):
    results = (
        db.query(
            inv_models.ModelNarzedzia.nazwa_modelu,
            func.count(rental_models.PozycjaWypozyczenia.id).label("rent_count"),
        )
        .select_from(inv_models.ModelNarzedzia)
        .join(
            inv_models.EgzemplarzNarzedzia,
            inv_models.ModelNarzedzia.id == inv_models.EgzemplarzNarzedzia.model_id,
        )
        .join(
            rental_models.PozycjaWypozyczenia,
            inv_models.EgzemplarzNarzedzia.id == rental_models.PozycjaWypozyczenia.egzemplarz_id,
        )
        .group_by(inv_models.ModelNarzedzia.id, inv_models.ModelNarzedzia.nazwa_modelu)
        .order_by(func.count(rental_models.PozycjaWypozyczenia.id).desc())
        .limit(limit)
        .all()
    )

    return [{"model_name": row.nazwa_modelu, "rent_count": row.rent_count} for row in results]


def get_category_distribution(db: Session):
    results = (
        db.query(
            inv_models.ModelNarzedzia.kategoria,
            func.count(rental_models.PozycjaWypozyczenia.id).label("count"),
        )
        .select_from(inv_models.ModelNarzedzia)
        .join(
            inv_models.EgzemplarzNarzedzia,
            inv_models.ModelNarzedzia.id == inv_models.EgzemplarzNarzedzia.model_id,
        )
        .join(
            rental_models.PozycjaWypozyczenia,
            inv_models.EgzemplarzNarzedzia.id == rental_models.PozycjaWypozyczenia.egzemplarz_id,
        )
        .group_by(inv_models.ModelNarzedzia.kategoria)
        .all()
    )

    return [{"kategoria": row.kategoria, "count": row.count} for row in results]


def export_to_csv(db: Session, table_name: str) -> str:
    model = _EXPORT_MAP.get(table_name)
    if not model:
        raise ValueError(f"Tabela {table_name} nie jest dostępna do eksportu.")

    rows = db.query(model).all()
    columns = [c.name for c in model.__table__.columns]

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(columns)
    for r in rows:
        writer.writerow([getattr(r, col) for col in columns])

    return output.getvalue()
