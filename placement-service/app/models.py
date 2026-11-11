"""The placements table (owned by this service only)."""
import uuid
from datetime import date

from sqlalchemy import Date, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Placement(Base):
    __tablename__ = "placements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id: Mapped[str] = mapped_column(String(50), index=True)
    student_name: Mapped[str] = mapped_column(String(120))
    company_name: Mapped[str] = mapped_column(String(120))
    company_city: Mapped[str] = mapped_column(String(80))
    company_supervisor_id: Mapped[str] = mapped_column(String(50), index=True)
    academic_supervisor_id: Mapped[str] = mapped_column(String(50), index=True)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    total_weeks: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(10), default="open")
    final_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    final_comment: Mapped[str | None] = mapped_column(Text, nullable=True)