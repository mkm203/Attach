import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import config
from app.database import Base, get_db
from app.errors import ApiError
from app.main import app
from app.placement_client import get_placement_client

PLACEMENTS = {
    "P1": {"id": "P1", "student_id": "stu-1", "company_supervisor_id": "cs-1", "academic_supervisor_id": "as-1",
           "total_weeks": 4, "status": "open"},
    "P2": {"id": "P2", "student_id": "stu-2", "company_supervisor_id": "cs-2", "academic_supervisor_id": "as-1",
           "total_weeks": 4, "status": "open"},
    "P3": {"id": "P3", "student_id": "stu-1", "company_supervisor_id": "cs-1", "academic_supervisor_id": "as-1",
           "total_weeks": 4, "status": "closed"},
}


class FakePlacements:
    """Stands in for the placement service, so these tests need no second server."""
    def get(self, placement_id, token):
        if placement_id not in PLACEMENTS:
            raise ApiError(404, "placement_not_found", f"Placement {placement_id} not found")
        return PLACEMENTS[placement_id]


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
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override
    app.dependency_overrides[get_placement_client] = lambda: FakePlacements()
    yield TestClient(app)
    app.dependency_overrides.clear()


def submit(client, week=1, placement="P1", headers=STUDENT, **extra):
    return client.post(f"/v1/placements/{placement}/entries",
                       json={"week": week, "tasks": "Fixed bugs", "hours": 35, **extra}, headers=headers)