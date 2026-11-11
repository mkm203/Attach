import jwt
import pytest

from app import config
from tests.conftest import ACADEMIC, COORDINATOR, STUDENT, SUPERVISOR, submit

BODY = {"week": 1, "tasks": "t", "hours": 5}

# every protected operation: (method, url, json, a token with the WRONG role)
OPERATIONS = [
    ("post", "/v1/placements/P1/entries", BODY, SUPERVISOR),
    ("put", "/v1/entries/x", {"tasks": "t", "hours": 5}, SUPERVISOR),
    ("post", "/v1/entries/x/reviews", {"decision": "approved"}, STUDENT),
    ("post", "/v1/entries/x/reviews", {"decision": "approved"}, COORDINATOR),
    ("get", "/v1/entries", None, None),
    ("get", "/v1/entries/x", None, None),
    ("get", "/v1/entries/x/reviews", None, None),
    ("get", "/v1/placements/P1/progress", None, None),
]


@pytest.mark.parametrize("method,url,body,_wrong", OPERATIONS)
def test_no_token_is_401(client, method, url, body, _wrong):
    r = getattr(client, method)(url, **({"json": body} if body else {}))
    assert r.status_code == 401 and r.json()["error"]["code"] == "not_authenticated"


@pytest.mark.parametrize("method,url,body,wrong", [o for o in OPERATIONS if o[3]])
def test_wrong_role_is_403(client, method, url, body, wrong):
    r = getattr(client, method)(url, headers=wrong, **({"json": body} if body else {}))
    assert r.status_code == 403 and r.json()["error"]["code"] == "forbidden"


def test_forged_and_malformed_tokens_are_401(client):
    forged = {"Authorization": "Bearer " + jwt.encode({"sub": "stu-1", "role": "student"}, "wrong-secret-wrong-secret-wrong-secret", algorithm="HS256")}
    assert submit(client, headers=forged).status_code == 401
    assert submit(client, headers={"Authorization": "Bearer garbage"}).status_code == 401
    no_role = {"Authorization": "Bearer " + jwt.encode({"sub": "x"}, config.jwt_secret(), algorithm="HS256")}
    assert submit(client, headers=no_role).status_code == 401


def test_academic_supervisor_cannot_write(client):
    assert submit(client, headers=ACADEMIC).status_code == 403