import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import config
from app.database import Base, get_db
from app.main import app


def make_token(sub: str, role: str) -> dict:
    return {"Authorization": "Bearer " + jwt.encode({"sub": sub, "role": role}, config.jwt_secret(), algorithm="HS256")}


STUDENT = make_token("stu-1", "student")
OTHER_STUDENT = make_token("stu-2", "student")
SUPERVISOR = make_token("cs-1", "company_supervisor")
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
    yield TestClient(app)
    app.dependency_overrides.clear()