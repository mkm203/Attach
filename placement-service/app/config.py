"""Settings read from environment variables (a ConfigMap in Kubernetes)."""
import os
from datetime import date


def term_start() -> date:
    return date.fromisoformat(os.getenv("TERM_START", "2026-09-01"))


def term_end() -> date:
    return date.fromisoformat(os.getenv("TERM_END", "2027-02-28"))


def database_url() -> str:
    return os.getenv("DATABASE_URL", "sqlite:///./placement.db")