"""CRUD for search groups (048)."""
from __future__ import annotations

from typing import Any
from uuid import UUID, uuid5

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.models import PlatformSetting, SearchGroup
from app.db.session import session_factory
from app.worker.search_seeds import PLATFORM_ORDER, group_seed_rows

# Must match app.api.searches._SHIM_NS — unique queue step ids for group×platform.
_SHIM_NS = UUID("aaaaaaaa-bbbb-4ccc-8fff-000000000099")


def step_id_for(group_id: UUID, platform_id: str) -> str:
    return str(uuid5(_SHIM_NS, f"{group_id}:{platform_id}"))


class SearchGroupError(ValueError):
    """400-class validation."""


class SearchGroupConflict(RuntimeError):
    """409 unique name."""


class SearchGroupNotFound(LookupError):
    pass


class SearchGroupIn(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    queries: list[str] = Field(min_length=1)
    exclude: list[str] = Field(default_factory=list)
    limit_n: int = Field(default=0, ge=0, description="0 = без потолка; иначе soft stop")
    in_queue: bool = False
    sort_order: int = Field(default=0, ge=0, le=10_000)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("empty_name")
        return text

    @field_validator("queries")
    @classmethod
    def clean_queries(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if isinstance(item, str) and item.strip()]
        if not cleaned:
            raise ValueError("empty_queries")
        return cleaned

    @field_validator("exclude")
    @classmethod
    def clean_exclude(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _dump(row: SearchGroup) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "name": row.name,
        "queries": list(row.queries or []),
        "exclude": list(row.exclude or []),
        "limit_n": row.limit_n,
        "in_queue": bool(row.in_queue),
        "sort_order": row.sort_order,
    }


def list_groups() -> dict[str, Any]:
    factory = session_factory()
    with factory() as session:
        rows = session.scalars(
            select(SearchGroup).order_by(SearchGroup.sort_order, SearchGroup.name)
        ).all()
        return {"items": [_dump(row) for row in rows]}


def get_queued_steps() -> list[dict[str, Any]]:
    """Cartesian: in_queue groups × enabled platforms (registry order)."""
    factory = session_factory()
    with factory() as session:
        groups = session.scalars(
            select(SearchGroup)
            .where(SearchGroup.in_queue.is_(True))
            .order_by(SearchGroup.sort_order, SearchGroup.name)
        ).all()
        settings = {
            row.platform_id: bool(row.enabled)
            for row in session.scalars(select(PlatformSetting)).all()
        }
        enabled = [pid for pid in PLATFORM_ORDER if settings.get(pid, False)]
        steps: list[dict[str, Any]] = []
        for group in groups:
            for platform_id in enabled:
                steps.append(
                    {
                        "id": step_id_for(group.id, platform_id),
                        "group_id": str(group.id),
                        "group_name": group.name,
                        "name": group.name,
                        "platform_id": platform_id,
                        "queries": list(group.queries or []),
                        "exclude": list(group.exclude or []),
                        "limit_n": group.limit_n,
                        "status": "pending",
                    }
                )
        return steps


def create_group(body: SearchGroupIn) -> dict[str, Any]:
    factory = session_factory()
    row = SearchGroup(
        name=body.name,
        queries=body.queries,
        exclude=body.exclude,
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
            raise SearchGroupConflict("duplicate_name") from exc
        session.refresh(row)
        return _dump(row)


def update_group(group_id: UUID, body: SearchGroupIn) -> dict[str, Any]:
    factory = session_factory()
    with factory() as session:
        row = session.get(SearchGroup, group_id)
        if row is None:
            raise SearchGroupNotFound("not_found")
        row.name = body.name
        row.queries = body.queries
        row.exclude = body.exclude
        row.limit_n = body.limit_n
        row.in_queue = body.in_queue
        row.sort_order = body.sort_order
        try:
            session.commit()
        except IntegrityError as exc:
            session.rollback()
            raise SearchGroupConflict("duplicate_name") from exc
        session.refresh(row)
        return _dump(row)


def delete_group(group_id: UUID) -> None:
    factory = session_factory()
    with factory() as session:
        row = session.get(SearchGroup, group_id)
        if row is None:
            raise SearchGroupNotFound("not_found")
        session.delete(row)
        session.commit()


def ensure_group_seeds() -> None:
    """Idempotent insert of missing A–E groups and platform_settings rows.

    Does **not** overwrite existing group lexicon (operator edits survive restart).
    Does **not** force platform enabled flags (except insert defaults).
    """
    from app.db.config import database_url

    if not database_url():
        return
    factory = session_factory()
    with factory() as session:
        for row in group_seed_rows(in_queue=True):
            existing = session.get(SearchGroup, row["id"])
            if existing is None:
                by_name = session.scalar(
                    select(SearchGroup).where(SearchGroup.name == row["name"])
                )
                if by_name is not None:
                    existing = by_name
            if existing is None:
                session.add(
                    SearchGroup(
                        id=row["id"],
                        name=row["name"],
                        queries=row["queries"],
                        exclude=row["exclude"],
                        limit_n=row["limit_n"],
                        in_queue=row["in_queue"],
                        sort_order=row["sort_order"],
                    )
                )
        for platform_id in PLATFORM_ORDER:
            if session.get(PlatformSetting, platform_id) is None:
                session.add(
                    PlatformSetting(
                        platform_id=platform_id,
                        enabled=(platform_id == "rostender"),
                    )
                )
        session.commit()
