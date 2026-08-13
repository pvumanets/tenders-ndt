"""initial schema: users, runs, lots, lot_state, documents

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-13

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
    )
    op.create_table(
        "runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("limit_n", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "lots",
        sa.Column("tender_id", sa.String(length=64), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("tier", sa.String(length=16), nullable=False),
        sa.Column("location", sa.Text(), nullable=True),
        sa.Column("customer_name", sa.Text(), nullable=True),
        sa.Column("customer_inn", sa.String(length=32), nullable=True),
        sa.Column("deadline_msk", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=True),
        sa.Column("price_rub", sa.Numeric(14, 2), nullable=True),
        sa.Column("fit_reason", sa.Text(), nullable=True),
        sa.Column("source_platform_id", sa.String(length=64), nullable=True),
        sa.Column("contact_name", sa.Text(), nullable=True),
        sa.Column("contact_phone", sa.Text(), nullable=True),
        sa.Column("contact_email", sa.Text(), nullable=True),
        sa.Column("raw", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "ingested_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["run_id"], ["runs.id"]),
        sa.PrimaryKeyConstraint("tender_id"),
    )
    op.create_index("ix_lots_score", "lots", ["score"])
    op.create_index("ix_lots_ingested_at", "lots", ["ingested_at"])
    op.create_table(
        "lot_state",
        sa.Column("tender_id", sa.String(length=64), nullable=False),
        sa.Column("viewed", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("viewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("manual_tier", sa.String(length=8), nullable=True),
        sa.Column("manual_tier_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tender_id"], ["lots.tender_id"]),
        sa.PrimaryKeyConstraint("tender_id"),
    )
    op.create_table(
        "documents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tender_id", sa.String(length=64), nullable=False),
        sa.Column("filename", sa.String(length=512), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("volume_path", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["tender_id"], ["lots.tender_id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tender_id", "filename", name="uq_documents_lot_file"),
    )


def downgrade() -> None:
    op.drop_table("documents")
    op.drop_table("lot_state")
    op.drop_index("ix_lots_ingested_at", table_name="lots")
    op.drop_index("ix_lots_score", table_name="lots")
    op.drop_table("lots")
    op.drop_table("runs")
    op.drop_table("users")
