from sqlmodel import SQLModel, create_engine, Session
import os

os.makedirs('./db', exist_ok=True)

engine = create_engine(
    'sqlite:///./db/reviewer.db',
    echo=False,
    connect_args={"check_same_thread": False}
)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session