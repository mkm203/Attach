"""Settings read from environment variables (ConfigMap/Secret in Kubernetes)."""
import os


def placement_service_url() -> str:
    return os.getenv("PLACEMENT_SERVICE_URL", "http://localhost:8001")


def logbook_service_url() -> str:
    return os.getenv("LOGBOOK_SERVICE_URL", "http://localhost:8002")


def jwt_secret() -> str:
    return os.getenv("JWT_SECRET", "dev-secret-change-me-use-32-chars-min")
