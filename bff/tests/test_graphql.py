from unittest.mock import AsyncMock

from app import schema as schema_module
from app.clients import RestError
from tests.conftest import ACADEMIC, STUDENT, SUPERVISOR

PLACEMENT = {
    "id": "P1", "student_id": "stu-1", "student_name": "Clarisse Ngo",
    "company_name": "Douala Tech SARL", "company_city": "Douala",
    "company_supervisor_id": "cs-1", "academic_supervisor_id": "as-1",
    "start_date": "2026-09-07", "end_date": "2026-11-29",
    "total_weeks": 12, "status": "open", "final_score": None, "final_comment": None,
}

ENTRY = {
    "id": "E1", "placement_id": "P1", "student_id": "stu-1", "week": 1,
    "tasks": "Fixed bugs", "hours": 35, "status": "pending",
    "created_at": "2026-09-14T10:00:00Z", "updated_at": "2026-09-14T10:00:00Z",
}

PLACEMENT_QUERY = """
query Placement($id: ID!) {
  placement(id: $id) {
    student { name }
    company { name city }
    completionPercent
    entries(status: PENDING) { week hours status }
  }
}
"""

MY_ENTRIES_QUERY = """
query MyEntries($status: EntryStatus) {
  myEntries(status: $status) { total page pageSize items { week hours status } }
}
"""

REVIEW_MUTATION = """
mutation Review($input: ReviewInput!) {
  reviewLogEntry(input: $input) {
    entry { status }
    errors { code message }
  }
}
"""


def _token(headers):
    return headers["Authorization"].split(" ", 1)[1]


def test_placement_query_composes_both_rest_services(client, monkeypatch):
    get_placement = AsyncMock(return_value=PLACEMENT)
    get_progress = AsyncMock(return_value={"completion_percent": 25.0})
    list_entries = AsyncMock(return_value={"items": [ENTRY], "page": 1, "page_size": 100, "total": 1})
    monkeypatch.setattr(schema_module.placements, "get", get_placement)
    monkeypatch.setattr(schema_module.logbook, "progress", get_progress)
    monkeypatch.setattr(schema_module.logbook, "list_entries", list_entries)

    response = client.post("/graphql", json={"query": PLACEMENT_QUERY, "variables": {"id": "P1"}},
                           headers=ACADEMIC)
    assert response.status_code == 200
    body = response.json()
    assert "errors" not in body or body["errors"] == []
    placement = body["data"]["placement"]
    assert placement["student"] == {"name": "Clarisse Ngo"}
    assert placement["company"] == {"name": "Douala Tech SARL", "city": "Douala"}
    assert placement["completionPercent"] == 25.0
    assert placement["entries"] == [{"week": 1, "hours": 35, "status": "PENDING"}]

    get_placement.assert_awaited_once_with("P1", _token(ACADEMIC))
    get_progress.assert_awaited_once_with("P1", _token(ACADEMIC))
    list_entries.assert_awaited_once_with(_token(ACADEMIC), placement_id="P1", status="pending", page_size=100)


def test_my_entries_query(client, monkeypatch):
    list_entries = AsyncMock(return_value={"items": [ENTRY], "page": 1, "page_size": 10, "total": 1})
    monkeypatch.setattr(schema_module.logbook, "list_entries", list_entries)

    response = client.post("/graphql", json={"query": MY_ENTRIES_QUERY, "variables": {"status": "PENDING"}},
                           headers=STUDENT)
    assert response.status_code == 200
    page = response.json()["data"]["myEntries"]
    assert page["total"] == 1 and page["pageSize"] == 10
    assert page["items"] == [{"week": 1, "hours": 35, "status": "PENDING"}]
    list_entries.assert_awaited_once_with(_token(STUDENT), status="pending", page=1, page_size=10)


def test_review_mutation_success(client, monkeypatch):
    review = AsyncMock(return_value={"id": "R1"})
    get_entry = AsyncMock(return_value={**ENTRY, "status": "approved"})
    monkeypatch.setattr(schema_module.logbook, "review", review)
    monkeypatch.setattr(schema_module.logbook, "get_entry", get_entry)

    response = client.post("/graphql", json={
        "query": REVIEW_MUTATION,
        "variables": {"input": {"entryId": "E1", "decision": "APPROVED"}},
    }, headers=SUPERVISOR)
    assert response.status_code == 200
    result = response.json()["data"]["reviewLogEntry"]
    assert result == {"entry": {"status": "APPROVED"}, "errors": []}
    review.assert_awaited_once_with("E1", "approved", None, _token(SUPERVISOR))
    get_entry.assert_awaited_once_with("E1", _token(SUPERVISOR))


def test_review_mutation_returns_business_error(client, monkeypatch):
    review = AsyncMock(side_effect=RestError(409, "entry_not_pending", "Only a pending entry can be reviewed"))
    monkeypatch.setattr(schema_module.logbook, "review", review)

    response = client.post("/graphql", json={
        "query": REVIEW_MUTATION,
        "variables": {"input": {"entryId": "E1", "decision": "APPROVED"}},
    }, headers=SUPERVISOR)
    assert response.status_code == 200
    result = response.json()["data"]["reviewLogEntry"]
    assert result["entry"] is None
    assert result["errors"] == [{"code": "entry_not_pending", "message": "Only a pending entry can be reviewed"}]


def test_review_mutation_unassigned_supervisor_is_403(client, monkeypatch):
    review = AsyncMock(side_effect=RestError(403, "not_assigned_supervisor",
                                             "You are not the supervisor assigned to this placement"))
    monkeypatch.setattr(schema_module.logbook, "review", review)

    response = client.post("/graphql", json={
        "query": REVIEW_MUTATION,
        "variables": {"input": {"entryId": "E1", "decision": "APPROVED"}},
    }, headers=SUPERVISOR)
    assert response.status_code == 403
    result = response.json()["data"]["reviewLogEntry"]
    assert result["errors"][0]["code"] == "not_assigned_supervisor"
