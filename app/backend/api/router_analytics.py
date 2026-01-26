from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.backend.core import crud as analytic_crud
from app.backend.core.database import get_db


router = APIRouter(prefix="/analytics", tags=["Analytics & Reports"])


@router.get("/summary")
def get_summary(date_from: date, date_to: date, db: Session = Depends(get_db)):
    return analytic_crud.get_dashboard_summary(db, date_from, date_to)


@router.get("/top-models")
def get_top_models(limit: int = 5, db: Session = Depends(get_db)):
    return analytic_crud.get_top_performing_models(db, limit)


@router.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    return analytic_crud.get_category_distribution(db)


@router.get("/export/{table_name}")
def export_data(table_name: str, db: Session = Depends(get_db)):
    try:
        csv_content = analytic_crud.export_to_csv(db, table_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={table_name}.csv"},
    )
