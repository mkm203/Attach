"""Request and response models, with the examples shown in /docs."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class EntryCreate(BaseModel):
    week: int = Field(ge=1, le=60)
    tasks: str = Field(min_length=1, max_length=2000)
    hours: int = Field(ge=1, le=60)

    model_config = ConfigDict(json_schema_extra={"examples": [
        {"week": 1, "tasks": "Installed the dev environment and fixed two bugs.", "hours": 38}]})


class EntryUpdate(BaseModel):
    tasks: str = Field(min_length=1, max_length=2000)
    hours: int = Field(ge=1, le=60)

    model_config = ConfigDict(json_schema_extra={"examples": [
        {"tasks": "Added tests and reviewed the deployment notes.", "hours": 40}]})


class ReviewCreate(BaseModel):
    decision: Literal["approved", "rejected"]
    comment: str | None = Field(default=None, max_length=1000)

    model_config = ConfigDict(json_schema_extra={"examples": [
        {"decision": "approved"}, {"decision": "rejected", "comment": "Please detail the tasks."}]})


class EntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, json_schema_extra={"examples": [{
        "id": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
        "placement_id": "5c1e6f2a-9b7d-4c3e-8a1f-2d6b9e4c7a10",
        "student_id": "stu-1", "week": 1, "tasks": "Installed the dev environment and fixed two bugs.",
        "hours": 38, "status": "pending",
        "created_at": "2026-09-14T10:00:00Z", "updated_at": "2026-09-14T10:00:00Z"}]})

    id: str
    placement_id: str
    student_id: str
    week: int
    tasks: str
    hours: int
    status: Literal["pending", "approved", "rejected"]
    created_at: datetime
    updated_at: datetime


class EntryPage(BaseModel):
    items: list[EntryOut]
    page: int
    page_size: int
    total: int

    model_config = ConfigDict(json_schema_extra={"examples": [{
        "items": [{
            "id": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
            "placement_id": "5c1e6f2a-9b7d-4c3e-8a1f-2d6b9e4c7a10",
            "student_id": "stu-1", "week": 1, "tasks": "Fixed two bugs.",
            "hours": 38, "status": "pending",
            "created_at": "2026-09-14T10:00:00Z", "updated_at": "2026-09-14T10:00:00Z"}],
        "page": 1, "page_size": 10, "total": 1}]})


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, json_schema_extra={"examples": [{
        "id": "b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e",
        "entry_id": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
        "reviewer_id": "cs-1", "decision": "approved",
        "comment": None, "created_at": "2026-09-15T09:30:00Z"}]})

    id: str
    entry_id: str
    reviewer_id: str
    decision: Literal["approved", "rejected"]
    comment: str | None = None
    created_at: datetime


class ProgressComment(BaseModel):
    week: int
    decision: str
    comment: str
    reviewer_id: str

    model_config = ConfigDict(json_schema_extra={"examples": [{
        "week": 2, "decision": "rejected", "comment": "Please detail the tasks.",
        "reviewer_id": "cs-1"}]})


class Progress(BaseModel):
    placement_id: str
    total_weeks: int
    submitted: int
    approved: int
    pending: int
    rejected: int
    completion_percent: float
    comments: list[ProgressComment]

    model_config = ConfigDict(json_schema_extra={"examples": [{
        "placement_id": "5c1e6f2a-9b7d-4c3e-8a1f-2d6b9e4c7a10",
        "total_weeks": 12, "submitted": 3, "approved": 1, "pending": 1, "rejected": 1,
        "completion_percent": 8.3,
        "comments": [{"week": 2, "decision": "rejected",
                      "comment": "Please detail the tasks.", "reviewer_id": "cs-1"}]}]})


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list | None = None


class ErrorResponse(BaseModel):
    """The one error format of every service: {"error": {"code", "message", "details"}}."""
    error: ErrorBody

    model_config = ConfigDict(json_schema_extra={"examples": [{
        "error": {"code": "entry_exists", "message": "An entry already exists for week 2",
                  "details": None}}]})