"""Create two Scout users from env when `users` is empty; rotate hashes when env password changes."""
from __future__ import annotations

import logging
import os

import bcrypt
from sqlalchemy import delete, func, select

from app.db.config import database_url
from app.db.models import ScoutSession, User
from app.db.session import get_engine, session_factory

log = logging.getLogger("uvicorn.error")


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _required_pair(user_key: str, pass_key: str) -> tuple[str, str]:
    username = os.environ.get(user_key, "").strip()
    password = os.environ.get(pass_key, "")
    if not username or not password:
        raise RuntimeError("bootstrap_users_missing_env")
    return username, password


def _optional_pair(user_key: str, pass_key: str) -> tuple[str, str] | None:
    username = os.environ.get(user_key, "").strip()
    password = os.environ.get(pass_key, "")
    if not username or not password:
        return None
    return username, password


def _password_matches(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def _rotate_if_changed(session, username: str, password: str) -> None:
    user = session.scalar(select(User).where(User.username == username))
    if user is None:
        return
    if _password_matches(password, user.password_hash):
        return
    user.password_hash = _hash_password(password)
    session.execute(delete(ScoutSession).where(ScoutSession.user_id == user.id))
    log.info("password_hash_rotated")


def bootstrap_users() -> None:
    if not database_url():
        return
    try:
        if get_engine() is None:
            raise RuntimeError("database_unconfigured")

        factory = session_factory()
        with factory() as session:
            count = session.scalar(select(func.count()).select_from(User)) or 0
            if count:
                for pair in (
                    _optional_pair("SCOUT_DIGITAL_USERNAME", "SCOUT_DIGITAL_PASSWORD"),
                    _optional_pair("SCOUT_DIRECTOR_USERNAME", "SCOUT_DIRECTOR_PASSWORD"),
                ):
                    if pair:
                        _rotate_if_changed(session, pair[0], pair[1])
                session.commit()
                return

            digital_user, digital_pass = _required_pair(
                "SCOUT_DIGITAL_USERNAME", "SCOUT_DIGITAL_PASSWORD"
            )
            director_user, director_pass = _required_pair(
                "SCOUT_DIRECTOR_USERNAME", "SCOUT_DIRECTOR_PASSWORD"
            )
            if digital_user == director_user:
                raise RuntimeError("bootstrap_users_duplicate_username")

            digital_display = os.environ.get("SCOUT_DIGITAL_DISPLAY", "").strip() or "Digital"
            director_display = os.environ.get("SCOUT_DIRECTOR_DISPLAY", "").strip() or "Директор"

            session.add(
                User(
                    username=digital_user,
                    password_hash=_hash_password(digital_pass),
                    display_name=digital_display,
                )
            )
            session.add(
                User(
                    username=director_user,
                    password_hash=_hash_password(director_pass),
                    display_name=director_display,
                )
            )
            session.commit()
            log.info("bootstrapped users count=2")
    except RuntimeError:
        raise
    except Exception:
        raise RuntimeError("database_unavailable") from None
