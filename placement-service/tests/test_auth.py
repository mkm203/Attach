import jwt

from app import config


def test_issue_token_and_use_it(client):
    r = client.post("/v1/auth/token", json={"sub": "stu-9", "role": "student"})
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer" and body["sub"] == "stu-9" and body["role"] == "student"
    assert body["expires_in"] == config.jwt_ttl_minutes() * 60

    claims = jwt.decode(body["access_token"], config.jwt_secret(), algorithms=["HS256"])
    assert claims["sub"] == "stu-9" and claims["role"] == "student"
    assert claims["exp"] > claims["iat"]

    auth = {"Authorization": f"Bearer {body['access_token']}"}
    assert client.get("/v1/placements", headers=auth).status_code == 200


def test_unknown_role_is_422(client):
    r = client.post("/v1/auth/token", json={"sub": "x", "role": "admin"})
    assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error"


def test_missing_or_empty_fields_are_422(client):
    assert client.post("/v1/auth/token", json={"role": "student"}).status_code == 422
    assert client.post("/v1/auth/token", json={"sub": "", "role": "student"}).status_code == 422
