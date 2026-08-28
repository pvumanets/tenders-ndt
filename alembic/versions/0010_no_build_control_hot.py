"""035: drop строительный контроль from seeds; scoring force L3.

Revision ID: 0010_no_build_control_hot
Revises: 0009_full_keywords_vik_only
Create Date: 2026-08-28

"""
from __future__ import annotations

import json
from typing import Sequence, Union
from uuid import UUID

import sqlalchemy as sa
from alembic import op

revision: str = "0010_no_build_control_hot"
down_revision: Union[str, Sequence[str], None] = "0009_full_keywords_vik_only"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_RT_D = UUID("aaaaaaaa-bbbb-4ccc-8ddd-0000000000a4")
_TP_CTRL = UUID("aaaaaaaa-bbbb-4ccc-8ddd-0000000000b3")
_QUERIES = [
    "принимающий контроль",
    "приёмочный контроль",
    "входной контроль",
]


def upgrade() -> None:
    conn = op.get_bind()
    q = json.dumps(_QUERIES, ensure_ascii=False)
    for sid in (_RT_D, _TP_CTRL):
        conn.execute(
            sa.text("UPDATE searches SET queries = CAST(:q AS jsonb) WHERE id = :id"),
            {"id": sid, "q": q},
        )


def downgrade() -> None:
    conn = op.get_bind()
    prev = [
        "принимающий контроль",
        "приёмочный контроль",
        "входной контроль",
        "строительный контроль",
    ]
    q = json.dumps(prev, ensure_ascii=False)
    for sid in (_RT_D, _TP_CTRL):
        conn.execute(
            sa.text("UPDATE searches SET queries = CAST(:q AS jsonb) WHERE id = :id"),
            {"id": sid, "q": q},
        )
