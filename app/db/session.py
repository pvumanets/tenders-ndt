"""Sync SQLAlchemy engine. No DSN in logs or API responses."""
from __future__ import annotations

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.config import database_url

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def get_engine() -> Engine | None:
    global _engine, _SessionLocal
    url = database_url()
    if not url:
        return None
    if _engine is None:
        _engine = create_engine(url, pool_pre_ping=True)
        _SessionLocal = sessionmaker(bind=_engine, expire_on_commit=False)
    return _engine


def session_factory() -> sessionmaker[Session]:
    get_engine()
    if _SessionLocal is None:
        raise RuntimeError("database_unconfigured")
    return _SessionLocal


def ping_db() -> bool:
    engine = get_engine()
    if engine is None:
        return False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
