"""Request and response models, with the examples shown in /docs."""
from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PlacementCreate(BaseModel):
    student_id: str = Field(min_length=1, max_length=50)
    student_name: str = Field(min_length=1, max_length=120)
    company_name: str = Field(min_length=1, max_length=120)
    company_city: str = Field(min_length=1, max_length=80)
    company_supervisor_id: str = Field(min_length=1, max_length=50)
    academic_supervisor_id: str = Field(min_length=1, max_length=50)
    start_date: date
    end_date: date

    model_config = ConfigDict(json_schema_extra={"examples": [{
        "student_id": "stu-1", "student_name": "Clarisse Ngo", "company_name": "Douala Tech SARL",
        "company_city": "Douala", "company_supervisor_id": "cs-1", "academic_supervisor_id": "as-1",
        "start_date": "2026-09-07", "end_date": "2026-11-29"}]})


class PlacementUpdate(BaseModel):
    """Only the supervisors can be changed after creation."""
    company_supervisor_id: str = Field(min_length=1, max_length=50)
    academic_supervisor_id: str = Field(min_length=1, max_length=50)


class FinalEvaluation(BaseModel):
    score: int = Field(ge=0, le=20)
    comment: str = Field(min_length=1, max_length=1000)

    model_config = ConfigDict(json_schema_extra={"examples": [{"score": 16, "comment": "Reliable and curious."}]})


class PlacementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    student_id: str
    student_name: str
    company_name: str
    company_city: str
    company_supervisor_id: str
    academic_supervisor_id: str
    start_date: date
    end_date: date
    total_weeks: int
    status: Literal["open", "closed"]
    final_score: int | None = None
    final_comment: str | None = None


class PlacementPage(BaseModel):
    items: list[PlacementOut]
    page: int
    page_size: int
    total: int


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list | None = None


class ErrorResponse(BaseModel):
    """The one error format of every service: {"error": {"code", "message", "details"}}."""
    error: ErrorBody