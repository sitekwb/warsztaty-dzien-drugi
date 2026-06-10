"""SQLAlchemy engine and session factory.

Reads DATABASE_URL from minibank.config.Settings. SQLite for dev, Postgres for prod.
"""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from minibank.config import get_settings


def _make_engine() -> Engine:
    url = get_settings().database_url
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=connect_args, future=True)


def _make_session_local(bound_engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=bound_engine, autoflush=False, autocommit=False, expire_on_commit=False)


engine = _make_engine()
SessionLocal = _make_session_local(engine)


def get_db() -> Iterator[Session]:
    """FastAPI dependency: yield a session, close on exit."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
