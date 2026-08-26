"""Named searches + run queue columns.

Revision ID: 0003_searches
Revises: 0002_sessions
Create Date: 2026-08-26

"""
from typing import Sequence, Union
from uuid import UUID

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_searches"
down_revision: Union[str, Sequence[str], None] = "0002_sessions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_ROSTENDER_ID = UUID("aaaaaaaa-bbbb-4ccc-8ddd-000000000001")
_TENDER_PRO_ID = UUID("aaaaaaaa-bbbb-4ccc-8ddd-000000000002")


def upgrade() -> None:
    op.create_table(
        "searches",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("platform_id", sa.String(length=64), nullable=False),
        sa.Column("queries", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("limit_n", sa.Integer(), nullable=False),
        sa.Column("in_queue", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.add_column("runs", sa.Column("source_platform_id", sa.String(length=64), nullable=True))
    op.add_column("runs", sa.Column("search_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_runs_search_id",
        "runs",
        "searches",
        ["search_id"],
        ["id"],
        ondelete="SET NULL",
    )
    searches = sa.table(
        "searches",
        sa.column("id", sa.Uuid()),
        sa.column("name", sa.String()),
        sa.column("platform_id", sa.String()),
        sa.column("queries", postgresql.JSONB()),
        sa.column("limit_n", sa.Integer()),
        sa.column("in_queue", sa.Boolean()),
        sa.column("sort_order", sa.Integer()),
    )
    op.bulk_insert(
        searches,
        [
            {
                "id": _ROSTENDER_ID,
                "name": "РосТендер НК",
                "platform_id": "rostender",
                "queries": ["неразрушающий"],
                "limit_n": 1000,
                "in_queue": True,
                "sort_order": 0,
            },
            {
                "id": _TENDER_PRO_ID,
                "name": "Tender.Pro НК",
                "platform_id": "tender-pro",
                "queries": ["ВИК", "ПВК", "УЗК", "РК"],
                "limit_n": 1000,
                "in_queue": False,
                "sort_order": 1,
            },
        ],
    )


def downgrade() -> None:
    op.drop_constraint("fk_runs_search_id", "runs", type_="foreignkey")
    op.drop_column("runs", "search_id")
    op.drop_column("runs", "source_platform_id")
    op.drop_table("searches")
