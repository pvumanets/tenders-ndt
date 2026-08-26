"""CRUD for named searches (023)."""
from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.models import NamedSearch
from app.db.session import session_factory

ALLOWED_PLATFORMS = frozenset({"rostender", "tender-pro"})


class SearchError(ValueError):
    """400-class search validation."""


class SearchConflict(RuntimeError):
    """409 unique name."""


class SearchNotFound(LookupError):
    pass


class SearchIn(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    platform_id: str
    queries: list[str] = Field(min_length=1)
    limit_n: int = Field(default=1000, ge=1, le=1000)
    in_queue: bool = False
    sort_order: int = Field(default=0, ge=0, le=10_000)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("empty_name")
        return text

    @field_validator("platform_id")
    @classmethod
    def platform(cls, value: str) -> str:
        slug = value.strip()
        if slug not in ALLOWED_PLATFORMS:
            raise ValueError("invalid_platform")
        return slug

    @field_validator("queries")
    @classmethod
    def clean_queries(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if isinstance(item, str) and item.strip()]
        if not cleaned:
            raise ValueError("empty_queries")
        return cleaned


def _dump(row: NamedSearch) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "name": row.name,
        "platform_id": row.platform_id,
        "queries": list(row.queries or []),
        "limit_n": row.limit_n,
        "in_queue": bool(row.in_queue),
        "sort_order": row.sort_order,
    }


def list_searches() -> dict[str, Any]:
    factory = session_factory()
    with factory() as session:
        rows = session.scalars(
            select(NamedSearch).order_by(NamedSearch.sort_order, NamedSearch.name)
        ).all()
        return {"items": [_dump(row) for row in rows]}


def get_queued() -> list[NamedSearch]:
    factory = session_factory()
    with factory() as session:
        rows = session.scalars(
            select(NamedSearch)
            .where(NamedSearch.in_queue.is_(True))
            .order_by(NamedSearch.sort_order, NamedSearch.name)
        ).all()
        session.expunge_all()
        return list(rows)


def create_search(body: SearchIn) -> dict[str, Any]:
    factory = session_factory()
    row = NamedSearch(
        name=body.name,
        platform_id=body.platform_id,
        queries=body.queries,
        limit_n=body.limit_n,
        in_queue=body.in_queue,
        sort_order=body.sort_order,
    )
    with factory() as session:
        session.add(row)
        try:
            session.commit()
        except IntegrityError as exc:
            session.rollback()
            raise SearchConflict("duplicate_name") from exc
        session.refresh(row)
        return _dump(row)


def update_search(search_id: UUID, body: SearchIn) -> dict[str, Any]:
    factory = session_factory()
    with factory() as session:
        row = session.get(NamedSearch, search_id)
        if row is None:
            raise SearchNotFound("not_found")
        row.name = body.name
        row.platform_id = body.platform_id
        row.queries = body.queries
        row.limit_n = body.limit_n
        row.in_queue = body.in_queue
        row.sort_order = body.sort_order
        try:
            session.commit()
        except IntegrityError as exc:
            session.rollback()
            raise SearchConflict("duplicate_name") from exc
        session.refresh(row)
        return _dump(row)


def delete_search(search_id: UUID) -> None:
    factory = session_factory()
    with factory() as session:
        row = session.get(NamedSearch, search_id)
        if row is None:
            raise SearchNotFound("not_found")
        session.delete(row)
        session.commit()
