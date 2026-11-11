"""The two tables of the logbook service: entries and reviews."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def now() -> datetime:
    return datetime.now(timezone.utc)


def new_id() -> str:
    return str(uuid.uuid4())


class Entry(Base):
    __tablename__ = "entries"
    # Rule 1: one entry per placement (so per student) per week, enforced by the database too
    __table_args__ = (UniqueConstraint("placement_id", "week", name="uq_entry_placement_week"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    placement_id: Mapped[str] = mapped_column(String(36), index=True)
    student_id: Mapped[str] = mapped_column(String(50), index=True)
    week: Mapped[int] = mapped_column(Integer)
    tasks: Mapped[str] = mapped_column(Text)
    hours: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(10), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    entry_id: Mapped[str] = mapped_column(ForeignKey("entries.id"), index=True)
    reviewer_id: Mapped[str] = mapped_column(String(50))
    decision: Mapped[str] = mapped_column(String(10))
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)