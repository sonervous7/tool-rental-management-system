from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from pathlib import Path
from sqlalchemy.engine import Engine
# DATABASE_URL = "postgresql://admin:secret_password@localhost:5432/rental_system"

BASE_DIR = Path(__file__).resolve().parents[2]  # repo root (tool-rental-management-system)
DB_PATH = BASE_DIR / "dev.db"

DATABASE_URL = f"sqlite:///{DB_PATH.as_posix()}"


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # ważne dla Streamlit
)

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()