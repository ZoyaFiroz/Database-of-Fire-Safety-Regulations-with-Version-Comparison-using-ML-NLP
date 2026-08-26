"""Shared SQLAlchemy engine/session setup, used by app/api/main.py and the
auth/user-data route modules alike so there's a single source of truth for
the database connection."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base
from app.db import general_models  # noqa: F401 - registers its tables on Base.metadata

DATABASE_URL = "sqlite:///./fire_regs.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base.metadata.create_all(engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
