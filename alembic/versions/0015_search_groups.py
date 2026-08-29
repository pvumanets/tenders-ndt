"""048: search_groups × platform_settings; drop per-platform searches.

Revision ID: 0015_search_groups
Revises: 0014_shared_search_packages
Create Date: 2026-08-29

"""
from __future__ import annotations

import json
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.worker.search_seeds import (
    group_seed_rows,
    legacy_seed_id_to_group_id,
)

revision: str = "0015_search_groups"
down_revision: Union[str, Sequence[str], None] = "0014_shared_search_packages"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "search_groups",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("queries", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "exclude",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("limit_n", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("in_queue", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "platform_settings",
        sa.Column("platform_id", sa.String(64), primary_key=True, nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
    )

    op.add_column(
        "runs",
        sa.Column("search_group_id", sa.Uuid(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_runs_search_group_id",
        "runs",
        "search_groups",
        ["search_group_id"],
        ["id"],
        ondelete="SET NULL",
    )

    conn = op.get_bind()

    # Seed 5 groups.
    for row in group_seed_rows(in_queue=True):
        conn.execute(
            sa.text(
                "INSERT INTO search_groups "
                "(id, name, queries, exclude, limit_n, in_queue, sort_order) "
                "VALUES (:id, :name, CAST(:queries AS jsonb), CAST(:exclude AS jsonb), "
                ":limit_n, :in_queue, :sort_order)"
            ),
            {
                "id": row["id"],
                "name": row["name"],
                "queries": json.dumps(row["queries"], ensure_ascii=False),
                "exclude": json.dumps(row.get("exclude") or [], ensure_ascii=False),
                "limit_n": row["limit_n"],
                "in_queue": bool(row["in_queue"]),
                "sort_order": row["sort_order"],
            },
        )

    # Platform settings: rostender on; TP/RE off until cookie sync.
    for platform_id, enabled in (
        ("rostender", True),
        ("tender-pro", False),
        ("roseltorg", False),
    ):
        conn.execute(
            sa.text(
                "INSERT INTO platform_settings (platform_id, enabled) "
                "VALUES (:platform_id, :enabled)"
            ),
            {"platform_id": platform_id, "enabled": enabled},
        )

    # Remap runs.search_id → search_group_id for known seed UUIDs.
    id_map = legacy_seed_id_to_group_id()
    for old_id, group_id in id_map.items():
        conn.execute(
            sa.text(
                "UPDATE runs SET search_group_id = :gid "
                "WHERE search_id = :sid AND search_group_id IS NULL"
            ),
            {"gid": group_id, "sid": old_id},
        )

    # Custom non-seed searches → groups by name suffix after " — ".
    existing = conn.execute(
        sa.text(
            "SELECT id, name, platform_id, queries, exclude, limit_n, in_queue, sort_order "
            "FROM searches"
        )
    ).mappings().all()
    seed_ids = set(id_map.keys())
    for row in existing:
        if row["id"] in seed_ids:
            continue
        name = str(row["name"] or "")
        if " — " in name:
            group_name = name.split(" — ", 1)[1].strip()
        else:
            group_name = name.strip()
        if not group_name:
            continue
        found = conn.execute(
            sa.text("SELECT id FROM search_groups WHERE name = :name"),
            {"name": group_name},
        ).first()
        if found is None:
            queries = row["queries"]
            exclude = row["exclude"]
            if not isinstance(queries, str):
                queries = json.dumps(queries or [], ensure_ascii=False)
            if not isinstance(exclude, str):
                exclude = json.dumps(exclude or [], ensure_ascii=False)
            conn.execute(
                sa.text(
                    "INSERT INTO search_groups "
                    "(id, name, queries, exclude, limit_n, in_queue, sort_order) "
                    "VALUES (:id, :name, CAST(:queries AS jsonb), CAST(:exclude AS jsonb), "
                    ":limit_n, :in_queue, :sort_order)"
                ),
                {
                    "id": row["id"],
                    "name": group_name,
                    "queries": queries,
                    "exclude": exclude,
                    "limit_n": int(row["limit_n"] or 0),
                    "in_queue": bool(row["in_queue"]),
                    "sort_order": int(row["sort_order"] or 0),
                },
            )
            group_id = row["id"]
        else:
            group_id = found[0]
        conn.execute(
            sa.text(
                "UPDATE runs SET search_group_id = :gid "
                "WHERE search_id = :sid AND search_group_id IS NULL"
            ),
            {"gid": group_id, "sid": row["id"]},
        )

    # Drop old searches FK + table.
    op.drop_constraint("fk_runs_search_id", "runs", type_="foreignkey")
    op.drop_table("searches")


def downgrade() -> None:
    # Recreate empty searches table shape (no full data restore).
    op.create_table(
        "searches",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("platform_id", sa.String(64), nullable=False),
        sa.Column("queries", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "exclude",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("limit_n", sa.Integer(), nullable=False),
        sa.Column("in_queue", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("name"),
    )
    op.create_foreign_key(
        "fk_runs_search_id",
        "runs",
        "searches",
        ["search_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.drop_constraint("fk_runs_search_group_id", "runs", type_="foreignkey")
    op.drop_column("runs", "search_group_id")
    op.drop_table("platform_settings")
    op.drop_table("search_groups")
