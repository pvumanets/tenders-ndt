"""Compatibility shim: /api/searches* over search_groups × platforms (048 → 049)."""
from __future__ import annotations

from typing import Any
from uuid import UUID, uuid5

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select

from app.api import search_groups as groups_api
from app.db.models import PlatformSetting, SearchGroup
from app.db.session import session_factory
from app.worker.search_seeds import PLATFORM_LABELS, PLATFORM_ORDER

# Stable namespace for synthetic search ids (group × platform).
_SHIM_NS = UUID("aaaaaaaa-bbbb-4ccc-8fff-000000000099")

ALLOWED_PLATFORMS = frozenset(PLATFORM_ORDER)

# Re-export error types under legacy names for main.py handlers.
SearchError = groups_api.SearchGroupError
SearchConflict = groups_api.SearchGroupConflict
SearchNotFound = groups_api.SearchGroupNotFound


class SearchIn(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    platform_id: str = "rostender"
    queries: list[str] = Field(min_length=1)
    exclude: list[str] = Field(default_factory=list)
    limit_n: int = Field(default=0, ge=0)
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

    @field_validator("exclude")
    @classmethod
    def clean_exclude(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def shim_search_id(group_id: UUID, platform_id: str) -> UUID:
    return uuid5(_SHIM_NS, f"{group_id}:{platform_id}")


def _group_display_name(name: str) -> str:
    """Strip legacy 'Площадка — ' prefix if pasted into create."""
    if " — " in name:
        return name.split(" — ", 1)[1].strip() or name.strip()
    return name.strip()


def _resolve_shim(search_id: UUID) -> tuple[UUID, str] | None:
    factory = session_factory()
    with factory() as session:
        groups = session.scalars(select(SearchGroup)).all()
        for group in groups:
            if group.id == search_id:
                return group.id, "rostender"
            for platform_id in PLATFORM_ORDER:
                if shim_search_id(group.id, platform_id) == search_id:
                    return group.id, platform_id
    return None


def list_searches() -> dict[str, Any]:
    factory = session_factory()
    with factory() as session:
        groups = session.scalars(
            select(SearchGroup).order_by(SearchGroup.sort_order, SearchGroup.name)
        ).all()
        settings = {
            row.platform_id: bool(row.enabled)
            for row in session.scalars(select(PlatformSetting)).all()
        }
        items: list[dict[str, Any]] = []
        for group in groups:
            for platform_id in PLATFORM_ORDER:
                label = PLATFORM_LABELS.get(platform_id, platform_id)
                enabled = bool(settings.get(platform_id, False))
                items.append(
                    {
                        "id": str(shim_search_id(group.id, platform_id)),
                        "name": f"{label} — {group.name}",
                        "platform_id": platform_id,
                        "queries": list(group.queries or []),
                        "exclude": list(group.exclude or []),
                        "limit_n": group.limit_n,
                        "in_queue": bool(group.in_queue) and enabled,
                        "sort_order": group.sort_order * 10
                        + list(PLATFORM_ORDER).index(platform_id),
                    }
                )
        return {"items": items}


def get_queued() -> list[Any]:
    """Deprecated for runner — use search_groups.get_queued_steps()."""
    return []  # type: ignore[return-value]


def create_search(body: SearchIn) -> dict[str, Any]:
    group_body = groups_api.SearchGroupIn(
        name=_group_display_name(body.name),
        queries=body.queries,
        exclude=body.exclude,
        limit_n=body.limit_n,
        in_queue=body.in_queue,
        sort_order=body.sort_order,
    )
    created = groups_api.create_group(group_body)
    group_id = UUID(created["id"])
    return {
        "id": str(shim_search_id(group_id, body.platform_id)),
        "name": f"{PLATFORM_LABELS.get(body.platform_id, body.platform_id)} — {created['name']}",
        "platform_id": body.platform_id,
        "queries": created["queries"],
        "exclude": created["exclude"],
        "limit_n": created["limit_n"],
        "in_queue": created["in_queue"],
        "sort_order": created["sort_order"],
    }


def update_search(search_id: UUID, body: SearchIn) -> dict[str, Any]:
    resolved = _resolve_shim(search_id)
    if resolved is None:
        raise SearchNotFound("not_found")
    group_id, _platform = resolved
    factory = session_factory()
    with factory() as session:
        existing = session.get(SearchGroup, group_id)
        if existing is None:
            raise SearchNotFound("not_found")
        # Keep real group sort_order — shim list exposes synthetic per-platform values.
        keep_sort = int(existing.sort_order)
    group_body = groups_api.SearchGroupIn(
        name=_group_display_name(body.name),
        queries=body.queries,
        exclude=body.exclude,
        limit_n=body.limit_n,
        in_queue=body.in_queue,
        sort_order=keep_sort,
    )
    updated = groups_api.update_group(group_id, group_body)
    return {
        "id": str(shim_search_id(group_id, body.platform_id)),
        "name": f"{PLATFORM_LABELS.get(body.platform_id, body.platform_id)} — {updated['name']}",
        "platform_id": body.platform_id,
        "queries": updated["queries"],
        "exclude": updated["exclude"],
        "limit_n": updated["limit_n"],
        "in_queue": updated["in_queue"],
        "sort_order": updated["sort_order"],
    }


def delete_search(search_id: UUID) -> None:
    """Shim DELETE: dequeue the group; do not destroy it.

    Legacy UI deletes one synthetic group×platform row. Hard-deleting the
    shared SearchGroup would wipe queries for every platform. Hard remove
    remains DELETE /api/search-groups/{id}.
    """
    resolved = _resolve_shim(search_id)
    if resolved is None:
        raise SearchNotFound("not_found")
    group_id, _platform = resolved
    factory = session_factory()
    with factory() as session:
        group = session.get(SearchGroup, group_id)
        if group is None:
            raise SearchNotFound("not_found")
        if group.in_queue:
            group.in_queue = False
            session.commit()
