# AttachLog demo client

Requires `httpx` (already in the repo's `.venv`).

With both REST services and the BFF running:

```powershell
.\.venv\Scripts\python.exe client\client.py
```

The script seeds a fresh placement and week-1 entry through REST, then:

1. runs the `placement` GraphQL query with `$id` variables,
2. runs the `reviewLogEntry` GraphQL mutation with `$input` variables,
3. makes one direct REST call to `GET /v1/placements/{id}`.

To use existing records:

```powershell
.\.venv\Scripts\python.exe client\client.py --placement-id <id> --entry-id <id>
```

Options: `--decision rejected --comment "..."`, `--placement-url`, `--logbook-url`, `--graphql-url`.
GraphQL and REST errors are printed and the process exits non-zero.
