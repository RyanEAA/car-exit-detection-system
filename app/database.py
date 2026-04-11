from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import inspect, text
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:///./car_exit.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    if "detections" in inspector.get_table_names():
        columns = {column["name"] for column in inspector.get_columns("detections")}
        if "media_type" not in columns:
            with engine.begin() as connection:
                connection.execute(
                    text("ALTER TABLE detections ADD COLUMN media_type VARCHAR(16) NOT NULL DEFAULT 'image'")
                )