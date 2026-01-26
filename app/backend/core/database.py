import os
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine, event, func
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

# DYNAMICZNY URL BAZY
DEFAULT_SQLITE = f"sqlite:///{(Path(__file__).resolve().parents[3] / 'dev.db').as_posix()}"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_SQLITE)

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

print(f"🚀 Łączenie z bazą: {DATABASE_URL}")

# KONFIGURACJA SILNIKA
# connect_args są potrzebne tylko dla SQLite
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

class TimestampMixin:
    data_utworzenia: Mapped[datetime] = mapped_column(default=func.now(), sort_order=999)

# TYLKO DLA SQLITE
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    # SPRAWDZAMY DIALEKT POŁĄCZENIA, A NIE ZMIENNĄ URL
    # To jest "pancerny" sposób - zadziała tylko jeśli baza to faktycznie SQLite
    if dbapi_connection.__class__.__module__.startswith("sqlite3"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
        print("🔧 SQLite: Klucze obce włączone.")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()