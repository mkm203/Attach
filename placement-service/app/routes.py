"""The placement endpoints, all under /v1."""
import math
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import config
from app.database import get_db
from app.errors import ApiError
from app.models import Placement
from app.schemas import (ErrorResponse, FinalEvaluation, PlacementCreate, PlacementOut, PlacementPage,
                         PlacementUpdate)

router = APIRouter(prefix="/v1/placements", tags=["placements"])
DB = Annotated[Session, Depends(get_db)]
ERR = {404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}, 422: {"model": ErrorResponse}}


def find(db: Session, placement_id: str) -> Placement:
    placement = db.get(Placement, placement_id)
    if placement is None:
        raise ApiError(404, "placement_not_found", f"Placement {placement_id} not found")
    return placement


@router.post("", response_model=PlacementOut, status_code=201, responses={422: ERR[422]})
def create_placement(data: PlacementCreate, db: DB):
    """Create a placement (coordinator). The dates must lie inside the term set by TERM_START and TERM_END."""
    if data.end_date <= data.start_date:
        raise ApiError(422, "invalid_dates", "end_date must be after start_date")
    if data.start_date < config.term_start() or data.end_date > config.term_end():
        raise ApiError(422, "outside_term", f"Dates must be inside the term {config.term_start()} to {config.term_end()}")
    weeks = math.ceil(((data.end_date - data.start_date).days + 1) / 7)
    placement = Placement(**data.model_dump(), total_weeks=weeks, status="open")
    db.add(placement)
    db.commit()
    return placement


@router.get("", response_model=PlacementPage)
def list_placements(
    db: DB,
    status: Annotated[str | None, Query(pattern="^(open|closed)$")] = None,
    student_id: str | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
):
    """List placements, filtered by status or student, one page at a time."""
    query = select(Placement)
    if status:
        query = query.where(Placement.status == status)
    if student_id:
        query = query.where(Placement.student_id == student_id)
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    rows = db.scalars(query.order_by(Placement.start_date, Placement.id).offset((page - 1) * page_size).limit(page_size)).all()
    return {"items": rows, "page": page, "page_size": page_size, "total": total}


@router.get("/{placement_id}", response_model=PlacementOut, responses={404: ERR[404]})
def get_placement(placement_id: str, db: DB):
    return find(db, placement_id)


@router.put("/{placement_id}", response_model=PlacementOut, responses={404: ERR[404], 409: ERR[409], 422: ERR[422]})
def update_placement(placement_id: str, data: PlacementUpdate, db: DB):
    """Change the supervisors of an open placement (coordinator)."""
    placement = find(db, placement_id)
    if placement.status == "closed":
        raise ApiError(409, "placement_closed", "A closed placement cannot be changed")
    placement.company_supervisor_id = data.company_supervisor_id
    placement.academic_supervisor_id = data.academic_supervisor_id
    db.commit()
    return placement


@router.post("/{placement_id}/close", response_model=PlacementOut, responses={404: ERR[404], 409: ERR[409], 422: ERR[422]})
def close_placement(placement_id: str, data: FinalEvaluation, db: DB):
    """Close the placement and record the final evaluation (coordinator)."""
    placement = find(db, placement_id)
    if placement.status == "closed":
        raise ApiError(409, "placement_closed", "The placement is already closed")
    placement.status = "closed"
    placement.final_score = data.score
    placement.final_comment = data.comment
    db.commit()
    return placement