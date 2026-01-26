import bcrypt
import hashlib
from passlib.context import CryptContext

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    sha = hashlib.sha256(password.encode("utf-8")).digest()
    return bcrypt.hashpw(sha, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_in_db: str) -> bool:
    if not hashed_in_db: return False
    if hashed_in_db.startswith('$2'):
        try:
            # Próba 1: SHA256 + BCrypt
            sha = hashlib.sha256(plain_password.encode("utf-8")).digest()
            if bcrypt.checkpw(sha, hashed_in_db.encode("utf-8")): return True
            # Próba 2: Standardowy BCrypt
            if bcrypt.checkpw(plain_password.encode("utf-8"), hashed_in_db.encode("utf-8")): return True
        except Exception:
            return False
    return plain_password == hashed_in_db
