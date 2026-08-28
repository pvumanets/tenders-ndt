"""SQLAlchemy models — canon tables from platform-phases P5.1–P5.2."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    sessions: Mapped[list["ScoutSession"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class ScoutSession(Base):
    __tablename__ = "sessions"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user: Mapped[User] = relationship(back_populates="sessions")


class NamedSearch(Base):
    __tablename__ = "searches"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    platform_id: Mapped[str] = mapped_column(String(64), nullable=False)
    queries: Mapped[list] = mapped_column(JSONB, nullable=False)
    exclude: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=list, server_default="[]"
    )
    limit_n: Mapped[int] = mapped_column(Integer, nullable=False)
    in_queue: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    runs: Mapped[list["Run"]] = relationship(back_populates="search")


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    limit_n: Mapped[int] = mapped_column(Integer, nullable=False)
    source_platform_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    search_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("searches.id", ondelete="SET NULL"), nullable=True
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    search: Mapped[NamedSearch | None] = relationship(back_populates="runs")
    lots: Mapped[list[Lot]] = relationship(back_populates="run")


class Lot(Base):
    __tablename__ = "lots"

    tender_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    run_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("runs.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    tier: Mapped[str] = mapped_column(String(16), nullable=False)
    location: Mapped[str | None] = mapped_column(Text, nullable=True)
    customer_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    customer_inn: Mapped[str | None] = mapped_column(String(32), nullable=True)
    deadline_msk: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str | None] = mapped_column(Text, nullable=True)
    price_rub: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    fit_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_platform_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    contact_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(Text, nullable=True)
    contact_email: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    run: Mapped[Run | None] = relationship(back_populates="lots")
    documents: Mapped[list[Document]] = relationship(back_populates="lot")


class LotState(Base):
    __tablename__ = "lot_state"

    tender_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("lots.tender_id"), primary_key=True
    )
    viewed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    viewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    manual_tier: Mapped[str | None] = mapped_column(String(8), nullable=True)
    manual_tier_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    board_hidden: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    board_hidden_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    rules_tier: Mapped[str | None] = mapped_column(String(8), nullable=True)
    ai_reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ai_tier: Mapped[str | None] = mapped_column(String(8), nullable=True)
    ai_reason_ru: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_wrong_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ai_wrong_note: Mapped[str | None] = mapped_column(Text, nullable=True)


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (UniqueConstraint("tender_id", "filename", name="uq_documents_lot_file"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tender_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("lots.tender_id"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    volume_path: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    lot: Mapped[Lot] = relationship(back_populates="documents")
