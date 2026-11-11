# AttachLog

Three services in one repo:

- `placement-service` (port 8001): owns placements, `placement.db`. Verifies HS256 JWTs; writes require the `coordinator` role, reads accept any authenticated role. Also exposes `POST /v1/auth/token` (dev-only: no user store, it signs whatever `sub`/`role` you send).
- `logbook-service` (port 8002): owns entries/reviews, `logbook.db`. Verifies the same JWTs (`sub`, `role`) and calls the placement service over HTTP via `app/placement_client.py`, forwarding the caller's bearer token. The logbook tests fake this client, so they need no second server. Both services must share `JWT_SECRET` (same dev default).
- `bff` (port 8003): Strawberry GraphQL facade over both REST services. No database. Exposes `placement`, `myEntries`, and the `reviewLogEntry` mutation, plus `/health` and GraphiQL at `/graphql`.

`client/` is a demo script (GraphQL query + mutation with variables, then one direct REST call). `integration-tests/` starts all three services for real. `k8s/` holds the deployment manifests; `docker-compose.yml` runs the stack locally.

## Commands

The only environment is `.venv/` at the repo root (Python 3.14). Each service has a `requirements.txt`; `requirements-dev.txt` includes all three plus pytest. Key deps: fastapi, uvicorn, sqlalchemy, pydantic, PyJWT, httpx, pytest, strawberry-graphql.

**Always use `python -m pytest` and run from inside the service directory.** Code imports `app.*`, and cwd must be the service root. Bare `pytest.exe` and running pytest from the repo root both fail with `ModuleNotFoundError: No module named 'app'`. The exception is `integration-tests/`, which is run from the repo root and starts its own servers.

```powershell
cd placement-service; ..\.venv\Scripts\python.exe -m pytest          # 22 tests
cd logbook-service;   ..\.venv\Scripts\python.exe -m pytest          # 37 tests
cd bff;               ..\.venv\Scripts\python.exe -m pytest          # 12 tests
.\.venv\Scripts\python.exe -m pytest integration-tests               # 1 end-to-end test

# single test
cd logbook-service; ..\.venv\Scripts\python.exe -m pytest tests/test_reviews.py::test_progress_for_the_academic_supervisor
```

Run a service from its own directory (SQLite paths are relative to cwd):

```powershell
cd placement-service; ..\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8001
cd logbook-service;   ..\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8002
cd bff;               ..\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8003
```

With all three running:

```powershell
.\.venv\Scripts\python.exe client\client.py
```

The integration test uses free ports and temporary SQLite files, and needs no already-running servers. Set `ATTACHLOG_KEEP_E2E=1` to keep the service logs after a run.

## Auth and OpenAPI

Get a dev token (or run `POST /v1/auth/token` from http://localhost:8001/docs):

```powershell
Invoke-RestMethod -Method Post http://localhost:8001/v1/auth/token -ContentType application/json -Body '{"sub":"co-1","role":"coordinator"}'
```

Paste `access_token` into the Authorize box on both `/docs` pages, or into the GraphiQL headers panel as `{"Authorization": "Bearer <token>"}`. Roles: `student`, `company_supervisor`, `academic_supervisor`, `coordinator`. Tokens expire after `JWT_TTL_MINUTES` (default 480). The token endpoint has no password/user store — it is for local demos only.

The BFF decodes the same token in `app/security.py`. Auth failures set HTTP 401/403 on the response and return a GraphQL error with `extensions.code` (`not_authenticated`/`forbidden`). REST business errors surface in `ReviewResult.errors` for the mutation.

`openapi.json` in each service is a generated snapshot; regenerate after changing routes or auth (run the same command in `logbook-service`):

```powershell
cd placement-service; ..\.venv\Scripts\python.exe -c "import json; from app.main import app; open('openapi.json','w',encoding='utf-8').write(json.dumps(app.openapi(), indent=2)+'\n')"
```

No linter, formatter, typecheck, CI, or migration tool is configured.

## Architecture and conventions

- Tables are created by `Base.metadata.create_all(engine)` at import in each `app/main.py`. There are no migrations: after changing a model, delete the local `.db` file to recreate the schema.
- All API routes live under `/v1`; each service also exposes `/health`.
- Raise `ApiError(status, code, message)` (see `app/errors.py`). Responses use the shared shape `{"error": {"code", "message", "details"}}`; tests assert exact codes, so preserve them.
- Put domain routes in `app/routes.py` (auth in `app/auth.py`), Pydantic models in `app/schemas.py`, and SQLAlchemy models in `app/models.py`, keeping `response_model`/`responses` declarations.
- Query params are snake_case except the logbook list endpoint's `placementId` alias.
- Note the misspelled filename `logbook-service/tests/test_enteries.py`.
- Tests use per-service `tests/conftest.py`: in-memory SQLite + `StaticPool` + `app.dependency_overrides`. Logbook tests build tokens with `make_token()` and substitute `FakePlacements`; follow that pattern instead of starting real servers.
- BFF tests use FastAPI `TestClient` and `monkeypatch` the async client methods (`schema_module.placements`/`schema_module.logbook`) with `AsyncMock`; no REST server is needed.
- `client/client.py` seeds its own placement/entry through REST when `--placement-id`/`--entry-id` are omitted.
- Shared config in the BFF lives in `bff/app/config.py`; the two REST services keep their own `app/config.py`.

## Containers and Kubernetes

Each service has a `Dockerfile` and `.dockerignore`. Images are `attachlog/<service>:1.0.0`.

```powershell
docker compose up --build -d      # placement 8001, logbook 8002, bff 8003
docker compose ps
docker compose down -v
```

`k8s/` contains `namespace.yaml`, `configmap.yaml`, `secret.yaml`, and one file per service (PVC + Deployment + Service). Placement/logbook use `strategy: Recreate` with ReadWriteOnce PVCs because SQLite cannot be shared; the BFF runs 2 stateless replicas. All containers have `/health` liveness and readiness probes, run as UID 10001, and drop all capabilities.

```powershell
kind create cluster --name attachlog
kind load docker-image attachlog/placement-service:1.0.0 attachlog/logbook-service:1.0.0 attachlog/bff:1.0.0 --name attachlog
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml -f k8s/secret.yaml
kubectl apply -f k8s/placement-service.yaml -f k8s/logbook-service.yaml -f k8s/bff.yaml
kubectl -n attachlog get pods
```

Validate Compose with `docker compose config` (works without a daemon). `kubectl --dry-run=client` still needs API discovery, so validate the YAML with PyYAML when no cluster is available.

## Environment variables

| Variable | Service | Default |
| --- | --- | --- |
| `JWT_SECRET` | all | `dev-secret-change-me-use-32-chars-min` |
| `JWT_TTL_MINUTES` | placement | `480` |
| `DATABASE_URL` | placement/logbook | `sqlite:///./<service>.db` |
| `TERM_START`, `TERM_END` | placement | `2026-09-01`, `2027-02-28` |
| `PLACEMENT_SERVICE_URL` | logbook/bff | `http://localhost:8001` |
| `LOGBOOK_SERVICE_URL` | bff | `http://localhost:8002` |
