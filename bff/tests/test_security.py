import jwt

from app import config
from tests.conftest import ACADEMIC, COORDINATOR, STUDENT

PLACEMENT_QUERY = """
query Placement($id: ID!) { placement(id: $id) { id } }
"""

MY_ENTRIES_QUERY = """
query MyEntries { myEntries { total } }
"""

REVIEW_MUTATION = """
mutation Review($input: ReviewInput!) {
  reviewLogEntry(input: $input) { entry { status } errors { code message } }
}
"""


def _code(response):
    return response.json()["errors"][0]["extensions"]["code"]


def test_placement_query_needs_a_token(client):
    response = client.post("/graphql", json={"query": PLACEMENT_QUERY, "variables": {"id": "P1"}})
    assert response.status_code == 401
    assert _code(response) == "not_authenticated"


def test_my_entries_query_needs_a_token(client):
    response = client.post("/graphql", json={"query": MY_ENTRIES_QUERY})
    assert response.status_code == 401
    assert _code(response) == "not_authenticated"


def test_review_mutation_needs_a_token(client):
    response = client.post("/graphql", json={
        "query": REVIEW_MUTATION,
        "variables": {"input": {"entryId": "E1", "decision": "APPROVED"}},
    })
    assert response.status_code == 401
    assert _code(response) == "not_authenticated"


def test_review_mutation_wrong_role_is_403(client):
    response = client.post("/graphql", json={
        "query": REVIEW_MUTATION,
        "variables": {"input": {"entryId": "E1", "decision": "APPROVED"}},
    }, headers=STUDENT)
    assert response.status_code == 403
    assert _code(response) == "forbidden"


def test_review_mutation_coordinator_is_403(client):
    response = client.post("/graphql", json={
        "query": REVIEW_MUTATION,
        "variables": {"input": {"entryId": "E1", "decision": "APPROVED"}},
    }, headers=COORDINATOR)
    assert response.status_code == 403
    assert _code(response) == "forbidden"


def test_invalid_and_forged_tokens_are_401(client):
    forged = {"Authorization": "Bearer " + jwt.encode(
        {"sub": "stu-1", "role": "student"}, "wrong-secret-wrong-secret-wrong-secret", algorithm="HS256")}
    for headers in ({"Authorization": "Bearer garbage"}, forged,
                    {"Authorization": "Bearer " + jwt.encode({"sub": "stu-1"}, config.jwt_secret(),
                                                             algorithm="HS256")}):
        response = client.post("/graphql", json={"query": MY_ENTRIES_QUERY}, headers=headers)
        assert response.status_code == 401
        assert _code(response) == "not_authenticated"


def test_academic_supervisor_can_read(client, monkeypatch):
    from unittest.mock import AsyncMock
    from app import schema as schema_module
    monkeypatch.setattr(schema_module.logbook, "list_entries",
                        AsyncMock(return_value={"items": [], "page": 1, "page_size": 10, "total": 0}))
    response = client.post("/graphql", json={"query": MY_ENTRIES_QUERY}, headers=ACADEMIC)
    assert response.status_code == 200
