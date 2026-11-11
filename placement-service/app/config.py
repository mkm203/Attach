"""Settings read from environment variables (a ConfigMap in Kubernetes)."""
import os
from datetime import date


def term_start() -> date:
    return date.fromisoformat(os.getenv("TERM_START", "2026-09-01"))


def term_end() -> date:
    return date.fromisoformat(os.getenv("TERM_END", "2027-02-28"))


def database_url() -> str:
    return os.getenv("DATABASE_URL", "sqlite:///./placement.db")


def jwt_secret() -> str:
    return os.getenv("JWT_SECRET", "dev-secret-change-me-use-32-chars-min")


def jwt_ttl_minutes() -> int:
    return int(os.getenv("JWT_TTL_MINUTES", "480"))