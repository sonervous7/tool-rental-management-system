from app.backend.database import engine
from app.backend.models import Base

from sqlalchemy import inspect

if __name__ == "__main__":
    Base.metadata.drop_all(bind=engine)   # na dev — pewne wyczyszczenie
    Base.metadata.create_all(bind=engine)

    print("DB initialized")
    print(inspect(engine).get_table_names())
