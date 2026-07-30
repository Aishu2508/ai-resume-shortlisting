"""
SQLAlchemy engine + session setup.

Defaults to a local SQLite file (candidates.db) so the project runs with
zero external setup. Point DATABASE_URL at Postgres/MySQL/etc. in .env to
switch — nothing else in the app needs to change.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from config import settings

# SQLite needs this connect_arg when used with FastAPI's threaded requests.
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a DB session and closes it afterward."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables. Called once at app startup."""
    from database import models  # noqa: F401  (ensure models are registered)
    Base.metadata.create_all(bind=engine)
