import os
from sqlmodel import SQLModel, create_engine, Session

DB_URL = os.getenv("DATABASE_URL", "sqlite:///./autoforge.db")
connect_args = {"check_same_thread": False} if DB_URL.startswith("sqlite") else {}

engine = create_engine(DB_URL, echo=False, connect_args=connect_args)

def init_db() -> None:
    SQLModel.metadata.create_all(engine)

def get_session() -> Session:
    return Session(engine)
