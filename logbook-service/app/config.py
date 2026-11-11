"""Settings read from environment variables (ConfigMap and Secret in Kubernetes)."""
import os


def database_url() -> str:
    return os.getenv("DATABASE_URL", "sqlite:///./logbook.db")


def placement_service_url() -> str:
    return os.getenv("PLACEMENT_SERVICE_URL", "http://localhost:8001")


def jwt_secret() -> str:
    return os.getenv("JWT_SECRET", "dev-secret-change-me-use-32-chars-min")