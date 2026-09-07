"""Scout login: opaque HttpOnly cookie backed by Postgres `sessions`."""
from __future__ import annotations

import hashlib
import logging
import os
import secrets
import threading
import time
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

LOGIN_FAIL_MAX = 5
LOGIN_FAIL_WINDOW_S = 60.0
_login_lock = threading.Lock()
_login_fails: dict[str, list[float]] = {}

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


def reset_login_rate_for_tests() -> None:
    with _login_lock:
        _login_fails.clear()


def client_ip(request: Request) -> str:
    """Last X-Forwarded-For hop behind Caddy, else direct client host."""
    xff = (request.headers.get("x-forwarded-for") or "").strip()
    if xff:
        parts = [p.strip() for p in xff.split(",") if p.strip()]
        if parts:
            return parts[-1]
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def login_allowed(ip: str) -> bool:
    now = time.monotonic()
    with _login_lock:
        stamps = [t for t in _login_fails.get(ip, []) if now - t < LOGIN_FAIL_WINDOW_S]
        _login_fails[ip] = stamps
        return len(stamps) < LOGIN_FAIL_MAX


def note_login_failure(ip: str) -> None:
    now = time.monotonic()
    with _login_lock:
        stamps = [t for t in _login_fails.get(ip, []) if now - t < LOGIN_FAIL_WINDOW_S]
        stamps.append(now)
        _login_fails[ip] = stamps


def clear_login_failures(ip: str) -> None:
    with _login_lock:
        _login_fails.pop(ip, None)
