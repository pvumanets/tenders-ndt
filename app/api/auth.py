"""Scout login: opaque HttpOnly cookie backed by Postgres `sessions`."""
from __future__ import annotations

import hashlib
import logging
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

import bcrypt
from fastapi import Request, Response
from sqlalchemy import select

from app.db.models import ScoutSession, User
from app.db.session import session_factory

log = logging.getLogger("uvicorn.error")

COOKIE_NAME = "scout_session"
SESSION_TTL = timedelta(days=7)
_DUMMY_HASH = bcrypt.hashpw(b"invalid-placeholder", bcrypt.gensalt()).decode("utf-8")

PUBLIC_API = frozenset(
    {
        ("GET", "/api/health"),
        ("POST", "/api/auth/login"),
        ("POST", "/api/auth/logout"),
    }
)


@dataclass(frozen=True)
class ScoutPrincipal:
    id: UUID
    username: str
    display_name: str


def cookie_secure() -> bool:
    return os.environ.get("SCOUT_COOKIE_SECURE", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }


def is_public_api(method: str, path: str) -> bool:
    if (method.upper(), path) in PUBLIC_API:
        return True
    return not path.startswith("/api/")


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        COOKIE_NAME,
        token,
        httponly=True,
        samesite="lax",
        secure=cookie_secure(),
        path="/",
        max_age=int(SESSION_TTL.total_seconds()),
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        COOKIE_NAME,
        path="/",
        httponly=True,
        samesite="lax",
        secure=cookie_secure(),
    )


def authenticate(username: str, password: str) -> User | None:
    factory = session_factory()
    with factory() as session:
        user = session.scalar(select(User).where(User.username == username))
        if user is None:
            _verify_password(password, _DUMMY_HASH)
            return None
        if not _verify_password(password, user.password_hash):
            return None
        session.expunge(user)
        return user


def create_session(user_id: UUID) -> str:
    token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    factory = session_factory()
    with factory() as session:
        session.add(
            ScoutSession(
                user_id=user_id,
                token_hash=hash_token(token),
                expires_at=now + SESSION_TTL,
            )
        )
        session.commit()
    return token


def resolve_principal(request: Request) -> ScoutPrincipal | None:
    token = request.cookies.get(COOKIE_NAME, "").strip()
    if not token:
        return None
    now = datetime.now(timezone.utc)
    factory = session_factory()
    with factory() as session:
        row = session.scalar(
            select(ScoutSession).where(ScoutSession.token_hash == hash_token(token))
        )
        if row is None or row.expires_at <= now:
            return None
        user = session.get(User, row.user_id)
        if user is None:
            return None
        return ScoutPrincipal(id=user.id, username=user.username, display_name=user.display_name)


def destroy_session(request: Request) -> None:
    token = request.cookies.get(COOKIE_NAME, "").strip()
    if not token:
        return
    factory = session_factory()
    with factory() as session:
        row = session.scalar(
            select(ScoutSession).where(ScoutSession.token_hash == hash_token(token))
        )
        if row is not None:
            session.delete(row)
            session.commit()


def login_ok_log() -> None:
    log.info("login_ok")


def login_failed_log() -> None:
    log.info("login_failed")
