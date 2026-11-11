"""Database engine, session and the base class of the tables."""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import database_url

_url = database_url()
engine = create_engine(_url, connect_args={"check_same_thread": False} if _url.startswith("sqlite") else {})
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    """One database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        