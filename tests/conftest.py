"""Pytest hooks — prefer SCOUT_TEST_DATABASE_URL; always sweep qa_smoke_ users/lots."""
from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(_ROOT / ".env")

_test_url = os.environ.get("SCOUT_TEST_DATABASE_URL", "").strip()
if _test_url:
    os.environ["DATABASE_URL"] = _test_url

SMOKE_PREFIX = "qa_smoke_"


def _db_reachable() -> bool:
    from app.db.config import database_url
    from app.db.session import ping_db

    return bool(database_url()) and ping_db()


def _sweep_smoke_users() -> None:
    from sqlalchemy import delete, select

    from app.db.models import ScoutSession, User
    from app.db.session import session_factory

    factory = session_factory()
    with factory() as session:
        rows = session.scalars(
            select(User).where(User.username.startswith(SMOKE_PREFIX))
        ).all()
        ids = [row.id for row in rows]
        if ids:
            session.execute(delete(ScoutSession).where(ScoutSession.user_id.in_(ids)))
        for row in rows:
            session.delete(row)
        session.commit()


def _sweep_smoke_lots() -> None:
    from sqlalchemy import delete, select
    from sqlalchemy.exc import ProgrammingError

    from app.db.models import Document, Lot, LotState, NamedSearch, Run
    from app.db.session import session_factory

    factory = session_factory()
    with factory() as session:
        try:
            lot_ids = list(
                session.scalars(
                    select(Lot.tender_id).where(
                        (Lot.tender_id.startswith(SMOKE_PREFIX))
                        | (Lot.tender_id.like(f"%:{SMOKE_PREFIX}%"))
                    )
                )
            )
            if lot_ids:
                session.execute(delete(Document).where(Document.tender_id.in_(lot_ids)))
                session.execute(delete(LotState).where(LotState.tender_id.in_(lot_ids)))
                session.execute(delete(Lot).where(Lot.tender_id.in_(lot_ids)))
            session.execute(delete(Run).where(Run.query.startswith(SMOKE_PREFIX)))
            search_ids = list(
                session.scalars(select(NamedSearch.id).where(NamedSearch.name.startswith(SMOKE_PREFIX)))
            )
            if search_ids:
                session.execute(delete(Run).where(Run.search_id.in_(search_ids)))
                session.execute(delete(NamedSearch).where(NamedSearch.id.in_(search_ids)))
            session.commit()
        except ProgrammingError:
            session.rollback()


def _user_count(factory: sessionmaker[Session]) -> int:
    from sqlalchemy import func, select

    from app.db.models import User

    with factory() as session:
        return int(session.scalar(select(func.count()).select_from(User)) or 0)


@pytest.fixture
def api_client() -> Iterator[TestClient]:
    from app.api.main import app

    try:
        client = TestClient(app, lifespan="off")
    except TypeError:
        client = TestClient(app)
    with client as opened:
        yield opened


@pytest.fixture(scope="session")
def smoke_db() -> Iterator[sessionmaker[Session]]:
    if not _db_reachable():
        pytest.skip("dev stand down — run scripts/dev-up.ps1")
    _sweep_smoke_users()
    _sweep_smoke_lots()
    from app.db.session import session_factory

    yield session_factory()
    _sweep_smoke_users()
    _sweep_smoke_lots()
