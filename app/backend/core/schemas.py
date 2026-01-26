import re
from pydantic import BaseModel, ConfigDict


class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


def validate_password_strength(v: str) -> str:
    if len(v) < 8:
        raise ValueError("Musi mieć co najmniej 8 znaków")
    if not re.search(r"[A-Z]", v):
        raise ValueError("Musi zawierać co najmniej jedną wielką literę")
    if not re.search(r"\d", v):
        raise ValueError("Musi zawierać co najmniej jedną cyfrę")
    return v
