"""036: searches.exclude JSONB + RT D plus/minus seeds.

Revision ID: 0011_search_exclude
Revises: 0010_no_build_control_hot
Create Date: 2026-08-28

"""
from __future__ import annotations

import json
from typing import Sequence, Union
from uuid import UUID

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0011_search_exclude"
down_revision: Union[str, Sequence[str], None] = "0010_no_build_control_hot"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_RT_D = UUID("aaaaaaaa-bbbb-4ccc-8ddd-0000000000a4")
_D_QUERIES = [
    "принимающий контроль",
    "приёмочный контроль",
    "входной контроль",
    "строительный контроль",
]
_D_EXCLUDE = [
    "жилой",
    "жилых",
    "ЖК",
    "кровля",
    "крыша",
    "ЗАГС",
    "школа",
    "детсад",
    "поликлиника",
    "фасад",
    "благоустройство",
    "дороги",
]


def upgrade() -> None:
    op.add_column(
        "searches",
        sa.Column(
            "exclude",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "UPDATE searches SET queries = CAST(:q AS jsonb), exclude = CAST(:e AS jsonb) WHERE id = :id"
        ),
        {
            "id": _RT_D,
            "q": json.dumps(_D_QUERIES, ensure_ascii=False),
            "e": json.dumps(_D_EXCLUDE, ensure_ascii=False),
        },
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "UPDATE searches SET queries = CAST(:q AS jsonb) WHERE id = :id"
        ),
        {
            "id": _RT_D,
            "q": json.dumps(
                [
                    "принимающий контроль",
                    "приёмочный контроль",
                    "входной контроль",
                ],
                ensure_ascii=False,
            ),
        },
    )
    op.drop_column("searches", "exclude")
