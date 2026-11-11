"""Strawberry schema composing the placement and logbook REST services."""
from enum import Enum
from typing import Any

import strawberry
from graphql import GraphQLError
from strawberry.types import Info

from app.clients import LogbookClient, PlacementClient, RestError
from app.security import require_role, require_user

placements = PlacementClient()
logbook = LogbookClient()


@strawberry.enum(name="EntryStatus")
class EntryStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


@strawberry.enum(name="ReviewDecision")
class ReviewDecision(Enum):
    APPROVED = "approved"
    REJECTED = "rejected"


@strawberry.type
class Student:
    name: str


@strawberry.type
class Company:
    name: str
    city: str


@strawberry.type
class Entry:
    id: strawberry.ID
    placement_id: str
    student_id: str
    week: int
    tasks: str
    hours: int
    status: EntryStatus


def _entry(row: dict) -> Entry:
    return Entry(id=row["id"], placement_id=row["placement_id"], student_id=row["student_id"],
                 week=row["week"], tasks=row["tasks"], hours=row["hours"],
                 status=EntryStatus(row["status"]))


@strawberry.type
class EntryPage:
    items: list[Entry]
    page: int
    page_size: int
    total: int


@strawberry.type
class Placement:
    id: strawberry.ID
    student: Student
    company: Company
    total_weeks: int
    status: str
    completion_percent: float

    @strawberry.field
    async def entries(self, info: Info, status: EntryStatus | None = None) -> list[Entry]:
        user = require_user(info)
        data = await logbook.list_entries(
            user.token, placement_id=str(self.id),
            status=status.value if status else None, page_size=100)
        return [_entry(row) for row in data["items"]]


@strawberry.type
class UserError:
    code: str
    message: str


@strawberry.type
class ReviewResult:
    entry: Entry | None
    errors: list[UserError]


@strawberry.input
class ReviewInput:
    entry_id: strawberry.ID
    decision: ReviewDecision
    comment: str | None = None


def _raise_rest_error(info: Info, exc: RestError) -> None:
    info.context["response"].status_code = exc.status_code
    raise GraphQLError(exc.message, extensions={"code": exc.code})


@strawberry.type
class Query:
    @strawberry.field
    async def placement(self, info: Info, id: strawberry.ID) -> Placement | None:
        """Placement details + progress + entries, composed from both REST services."""
        user = require_user(info)
        try:
            placement = await placements.get(str(id), user.token)
            progress = await logbook.progress(str(id), user.token)
        except RestError as exc:
            _raise_rest_error(info, exc)
        return Placement(
            id=placement["id"],
            student=Student(name=placement["student_name"]),
            company=Company(name=placement["company_name"], city=placement["company_city"]),
            total_weeks=placement["total_weeks"],
            status=placement["status"],
            completion_percent=progress["completion_percent"],
        )

    @strawberry.field
    async def my_entries(self, info: Info, status: EntryStatus | None = None,
                         page: int = 1, page_size: int = 10) -> EntryPage:
        """Entries visible to the caller (a student only sees their own)."""
        user = require_user(info)
        try:
            data = await logbook.list_entries(
                user.token, status=status.value if status else None, page=page, page_size=page_size)
        except RestError as exc:
            _raise_rest_error(info, exc)
        return EntryPage(items=[_entry(row) for row in data["items"]], page=data["page"],
                         page_size=data["page_size"], total=data["total"])


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def review_log_entry(self, info: Info, input: ReviewInput) -> ReviewResult:
        """Approve/reject an entry. Only the assigned company supervisor may do it."""
        user = require_role(info, "company_supervisor")
        try:
            await logbook.review(str(input.entry_id), input.decision.value, input.comment, user.token)
            entry = await logbook.get_entry(str(input.entry_id), user.token)
        except RestError as exc:
            if exc.status_code in (401, 403):
                info.context["response"].status_code = exc.status_code
            return ReviewResult(entry=None, errors=[UserError(code=exc.code, message=exc.message)])
        return ReviewResult(entry=_entry(entry), errors=[])


schema = strawberry.Schema(query=Query, mutation=Mutation)
