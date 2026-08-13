"""Smoke: schema, bootstrap_users with qa_smoke_* teardown, password_hash contract."""
from __future__ import annotations

from uuid import uuid4

import bcrypt
import pytest
from sqlalchemy import inspect, select
from sqlalchemy.orm import Session, sessionmaker

from app.db.bootstrap import bootstrap_users
from app.db.models import User
from app.db.session import get_engine
from tests.conftest import SMOKE_PREFIX, _user_count

_CANON_TABLES = frozenset({"users", "sessions", "runs", "lots", "lot_state", "documents"})


def _patch_empty_scout_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in (
        "SCOUT_DIGITAL_USERNAME",
        "SCOUT_DIGITAL_PASSWORD",
        "SCOUT_DIRECTOR_USERNAME",
        "SCOUT_DIRECTOR_PASSWORD",
    ):
        monkeypatch.setenv(key, "")


def _patch_smoke_scout_env(monkeypatch: pytest.MonkeyPatch, suffix: str) -> tuple[str, str, str, str]:
    digital_user = f"{SMOKE_PREFIX}digital_{suffix}"
    director_user = f"{SMOKE_PREFIX}director_{suffix}"
    digital_pass = "qa-smoke-pass-digital"
    director_pass = "qa-smoke-pass-director"
    monkeypatch.setenv("SCOUT_DIGITAL_USERNAME", digital_user)
    monkeypatch.setenv("SCOUT_DIGITAL_PASSWORD", digital_pass)
    monkeypatch.setenv("SCOUT_DIGITAL_DISPLAY", "qa_smoke_digital")
    monkeypatch.setenv("SCOUT_DIRECTOR_USERNAME", director_user)
    monkeypatch.setenv("SCOUT_DIRECTOR_PASSWORD", director_pass)
    monkeypatch.setenv("SCOUT_DIRECTOR_DISPLAY", "qa_smoke_director")
    return digital_user, digital_pass, director_user, director_pass


@pytest.mark.smoke
def test_canon_tables_exist(smoke_db: sessionmaker[Session]) -> None:
    engine = get_engine()
    assert engine is not None
    names = set(inspect(engine).get_table_names())
    assert _CANON_TABLES <= names


@pytest.mark.smoke
def test_smoke_user_hash_not_plaintext(smoke_db: sessionmaker[Session]) -> None:
    username = f"{SMOKE_PREFIX}{uuid4().hex[:12]}"
    password = "qa-smoke-not-owner"
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user_id = None
    try:
        with smoke_db() as session:
            user = User(
                username=username,
                password_hash=hashed,
                display_name="qa_smoke",
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            user_id = user.id
            assert user.password_hash != password
            assert bcrypt.checkpw(
                password.encode("utf-8"),
                user.password_hash.encode("utf-8"),
            )
    finally:
        with smoke_db() as session:
            row = session.get(User, user_id) if user_id is not None else None
            if row is None:
                row = session.scalar(select(User).where(User.username == username))
            if row is not None:
                session.delete(row)
                session.commit()


@pytest.mark.smoke
def test_bootstrap_fail_closed_when_users_empty(
    smoke_db: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if _user_count(smoke_db) != 0:
        pytest.skip("users table not empty")
    _patch_empty_scout_env(monkeypatch)
    with pytest.raises(RuntimeError, match="bootstrap_users_missing_env") as caught:
        bootstrap_users()
    assert "password" not in str(caught.value).lower()
    assert _user_count(smoke_db) == 0


@pytest.mark.smoke
def test_bootstrap_creates_two_hashed_qa_smoke_users(
    smoke_db: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if _user_count(smoke_db) != 0:
        pytest.skip("users table not empty")
    suffix = uuid4().hex[:8]
    digital_user, digital_pass, director_user, director_pass = _patch_smoke_scout_env(
        monkeypatch, suffix
    )
    try:
        bootstrap_users()
        with smoke_db() as session:
            digital = session.scalar(select(User).where(User.username == digital_user))
            director = session.scalar(select(User).where(User.username == director_user))
            assert digital is not None and director is not None
            assert digital.password_hash != digital_pass
            assert director.password_hash != director_pass
            assert bcrypt.checkpw(
                digital_pass.encode("utf-8"),
                digital.password_hash.encode("utf-8"),
            )
            assert bcrypt.checkpw(
                director_pass.encode("utf-8"),
                director.password_hash.encode("utf-8"),
            )
        assert _user_count(smoke_db) == 2
    finally:
        with smoke_db() as session:
            for name in (digital_user, director_user):
                row = session.scalar(select(User).where(User.username == name))
                if row is not None:
                    session.delete(row)
            session.commit()


@pytest.mark.smoke
def test_bootstrap_idempotent_when_users_exist(
    smoke_db: sessionmaker[Session],
) -> None:
    before = _user_count(smoke_db)
    if before == 0:
        pytest.skip("users table empty — empty-bootstrap tests cover insert")
    bootstrap_users()
    assert _user_count(smoke_db) == before
