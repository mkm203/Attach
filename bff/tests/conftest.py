import jwt
import pytest
from fastapi.testclient import TestClient

from app import config
from app.main import app


def make_token(sub: str, role: str) -> dict:
    return {"Authorization": "Bearer " + jwt.encode({"sub": sub, "role": role}, config.jwt_secret(), algorithm="HS256")}


STUDENT = make_token("stu-1", "student")
OTHER_STUDENT = make_token("stu-2", "student")
SUPERVISOR = make_token("cs-1", "company_supervisor")
OTHER_SUPERVISOR = make_token("cs-2", "company_supervisor")
ACADEMIC = make_token("as-1", "academic_supervisor")
COORDINATOR = make_token("co-1", "coordinator")


@pytest.fixture()
def client():
    return TestClient(app)
