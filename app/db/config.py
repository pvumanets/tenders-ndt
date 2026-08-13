"""Env for DB — names only; values from .env / compose (never log secrets)."""
from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv

_REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_REPO_ROOT / ".env")

_HOST_PG_PORT = "5433"


def database_url() -> str | None:
    """Explicit DATABASE_URL, else host DSN from POSTGRES_* (localhost:5433)."""
    url = os.environ.get("DATABASE_URL", "").strip()
    if url:
        return url
    password = os.environ.get("POSTGRES_PASSWORD", "").strip()
    if not password:
        return None
    user = os.environ.get("POSTGRES_USER", "scout").strip() or "scout"
    dbname = os.environ.get("POSTGRES_DB", "scout").strip() or "scout"
    host = os.environ.get("POSTGRES_HOST", "localhost").strip() or "localhost"
    port = os.environ.get("POSTGRES_PORT", _HOST_PG_PORT).strip() or _HOST_PG_PORT
    return (
        f"postgresql+psycopg://{quote_plus(user)}:{quote_plus(password)}"
        f"@{host}:{port}/{dbname}"
    )
