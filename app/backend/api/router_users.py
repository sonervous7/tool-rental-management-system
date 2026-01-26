from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.backend.core.database import get_db
from app.backend.modules.users import crud as user_crud
from app.backend.modules.users import models as user_models
from app.backend.modules.users import schemas as user_schemas

router = APIRouter(prefix="/users", tags=["Users & Auth"])


def _user_public_payload(user) -> dict:
    return {
        "id": user.id,
        "imie": user.imie,
        "nazwisko": user.nazwisko,
        "email": user.email,
    }


def _get_user_by_id(db: Session, user_id: int):
    user = db.query(user_models.Pracownik).filter(user_models.Pracownik.id == user_id).first()
    if user:
        return user
    return db.query(user_models.Klient).filter(user_models.Klient.id == user_id).first()


@router.post("/login")
def login(payload: user_schemas.LoginRequest, db: Session = Depends(get_db)):
    user, role = user_crud.authenticate_user(db, payload.login, payload.haslo)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Błędny login lub hasło",
        )

    return {**_user_public_payload(user), "role": role}


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_customer(payload: user_schemas.CustomerCreate, db: Session = Depends(get_db)):
    try:
        return user_crud.create_customer(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/employees", response_model=List[dict])
def list_employees(db: Session = Depends(get_db)):
    return user_crud.list_employees(db)


@router.post("/employees", status_code=status.HTTP_201_CREATED)
def create_employee(payload: user_schemas.EmployeeCreate, db: Session = Depends(get_db)):
    try:
        return user_crud.create_employee(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/employees/{emp_id}")
def delete_employee(emp_id: int, db: Session = Depends(get_db)):
    try:
        user_crud.delete_employee(db, emp_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"message": "Pracownik został pomyślnie usunięty"}


@router.get("/security-question")
def get_security_question(email: str, db: Session = Depends(get_db)):
    question = user_crud.get_security_question_by_email(db, email)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nie znaleziono użytkownika o podanym adresie e-mail.",
        )
    return {"question": question}


@router.post("/verify-security-answer")
def verify_security_answer(email: str, answer: str, db: Session = Depends(get_db)):
    is_correct = user_crud.verify_security_answer(db, email, answer)
    if not is_correct:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Błędna odpowiedź na pytanie pomocnicze.",
        )
    return {"status": "success", "message": "Odpowiedź poprawna. Instrukcja została wysłana."}


@router.patch("/change-password")
def change_password(
    user_id: int,
    payload: user_schemas.PasswordChange,
    db: Session = Depends(get_db),
):
    user = _get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Użytkownik nie istnieje")

    try:
        updated_user = user_crud.update_user_password(db, user, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "status": "success",
        "message": "Hasło zostało zmienione",
        "user": _user_public_payload(updated_user),
    }


@router.patch("/employees/{emp_id}")
def update_employee_full(
    emp_id: int,
    payload: user_schemas.EmployeeUpdate,
    db: Session = Depends(get_db),
):
    try:
        employee = user_crud.update_employee(db, emp_id, payload)

        if payload.rola:
            user_crud.change_employee_role(
                db,
                employee_id=emp_id,
                new_role=payload.rola,
            )

        return {"status": "success", "message": "Dane i rola zaktualizowane"}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Błąd krytyczny: {str(exc)}") from exc
