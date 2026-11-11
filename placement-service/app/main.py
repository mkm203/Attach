"""Placement service: run with  uvicorn app.main:app --port 8001"""
from fastapi import FastAPI

from app.database import Base, engine
from app.errors import register_handlers
from app.routes import router

Base.metadata.create_all(engine)

app = FastAPI(title="AttachLog Placement Service", version="1.0.0",
              description="Placements managed by the coordinator once per term.")
register_handlers(app)
app.include_router(router)


@app.get("/health", tags=["health"])
def health():
    """Liveness/readiness probe."""
    return {"status": "ok", "service": "placement"}