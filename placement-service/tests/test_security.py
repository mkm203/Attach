import jwt
import pytest

from app import config
from tests.conftest import COORDINATOR, STUDENT

BODY = {"student_id": "stu-1", "student_name": "Clarisse Ngo", "company_name": "Douala Tech SARL",
        "company_city": "Douala", "company_supervisor_id": "cs-1", "academic_supervisor_id": "as-1",
        "start_date": "2026-09-07", "end_date": "2026-11-29"}

# (method, url, json) for every protected placement operation
PROTECTED = [
    ("post", "/v1/placements", BODY),
    ("put", "/v1/placements/x", {"company_supervisor_id": "cs-9", "academic_supervisor_id": "as-9"}),
    ("post", "/v1/placements/x/close", {"score": 10, "comment": "ok"}),
    ("get", "/v1/placements", None),
    ("get", "/v1/placements/x", None),
]

WRITES = PROTECTED[:3]


@pytest.mark.parametrize("method,url,body", PROTECTED)
def test_no_token_is_401(client, method, url, body):
    r = getattr(client, method)(url, **({"json": body} if body else {}))
    assert r.status_code == 401 and r.json()["error"]["code"] == "not_authenticated"


@pytest.mark.parametrize("method,url,body", WRITES)
def test_wrong_role_is_403(client, method, url, body):
    r = getattr(client, method)(url, json=body, headers=STUDENT)
    assert r.status_code == 403 and r.json()["error"]["code"] == "forbidden"


def test_forged_and_malformed_tokens_are_401(client):
    forged = {"Authorization": "Bearer " + jwt.encode(
        {"sub": "co-1", "role": "coordinator"}, "wrong-secret-wrong-secret-wrong-secret", algorithm="HS256")}
    assert client.get("/v1/placements", headers=forged).status_code == 401
    assert client.get("/v1/placements", headers={"Authorization": "Bearer garbage"}).status_code == 401
    no_role = {"Authorization": "Bearer " + jwt.encode({"sub": "co-1"}, config.jwt_secret(), algorithm="HS256")}
    assert client.get("/v1/placements", headers=no_role).status_code == 401
    expired = {"Authorization": "Bearer " + jwt.encode(
        {"sub": "co-1", "role": "coordinator", "exp": 1}, config.jwt_secret(), algorithm="HS256")}
    assert client.get("/v1/placements", headers=expired).status_code == 401


def test_any_authenticated_role_can_read(client):
    pid = client.post("/v1/placements", json=BODY, headers=COORDINATOR).json()["id"]
    assert client.get("/v1/placements", headers=STUDENT).status_code == 200
    assert client.get(f"/v1/placements/{pid}", headers=STUDENT).status_code == 200
