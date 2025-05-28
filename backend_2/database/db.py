from sqlmodel import SQLModel, create_engine, Session
import os

db_path = os.getenv("DB_PATH", "sqlite:///database.db")

engine = create_engine(db_path, echo=True)

def get_session():
    with Session(engine) as session:
        yield session

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
