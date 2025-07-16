import os
from dotenv import load_dotenv
from contextlib import contextmanager
from sqlmodel import SQLModel, create_engine, Session

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "")

engine = create_engine(DATABASE_URL, echo=True)


# For FastAPI Depends
def get_session():
    with Session(engine) as session:
        yield session


# For scripts/ETL
@contextmanager
def get_context_session():
    with Session(engine) as session:
        yield session
