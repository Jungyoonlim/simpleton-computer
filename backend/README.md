# Simpleton Computer — Backend

FastAPI server that exposes the type-directed core as a web application.
Upload a document, see only the actions that make sense for its type, execute them,
and plan multi-step chains toward a goal type — all through a lightweight JSON API
and a bundled single-page UI.

## Quick start

```bash
# from the project root
uv sync                           # install all deps
uvicorn backend.server:app --reload   # http://localhost:8000
```

## Architecture

```
backend/
├── server.py          # FastAPI app, routes, in-memory sessions
└── static/
    ├── index.html     # SPA shell (drop zone, workspace panels)
    ├── app.js         # fetch-based client that talks to /api/*
    └── style.css      # full-page styling
```

The server is intentionally thin.
All type logic, action registration, and planning live in `core/`;
the backend's job is to wire HTTP to those primitives and manage sessions.

### Request flow

```
Browser ──POST /api/load──▶ server.py ──▶ core types (Doc)
                                          ├─ creates Session
                                          └─ returns type + matching actions

Browser ──POST /api/execute──▶ server.py ──▶ core.actions.run()
                                             ├─ updates Session (new type/value)
                                             └─ returns new state + valid actions

Browser ──POST /api/plan──▶ server.py ──▶ core.plan.find_chain()
                                          └─ A*-style search over the action graph
```

## API reference

### `POST /api/load`

Upload a file. Creates a session and returns the initial typed handle.

| Field | Type | Description |
|-------|------|-------------|
| `file` | multipart | The file to load (read as UTF-8) |

**Response**

```json
{
  "session_id": "a1b2c3d4e5f6",
  "type": "Doc",
  "value": { "path": "notes.md", "text": "...", "length": 1842 },
  "actions": [
    { "name": "summarize", "input_type": "Doc", "output_type": "Doc", "pure": true },
    { "name": "extract_titles", "input_type": "Doc", "output_type": "List[Doc]", "pure": true }
  ]
}
```

### `POST /api/execute`

Run a type-checked action on the current handle.

```json
{ "session_id": "a1b2c3d4e5f6", "action": "summarize" }
```

Returns the same shape as `/api/load` plus a `history` array tracking
every `action -> type` transition.

### `POST /api/plan`

Find an action chain from the current type to a goal type (A\*-style search).

```json
{ "session_id": "a1b2c3d4e5f6", "goal_type": "List[Comment]" }
```

**Response**

```json
{
  "steps": [
    { "action": "extract_comments", "input_type": "Doc", "output_type": "List[Comment]" }
  ]
}
```

### `GET /api/actions`

List every registered action (all types).

### `GET /api/types`

List known goal-type labels available for planning.

## Sessions

State is held **in-memory** in a `dict[str, Session]`.
Each session tracks:

| Field | Type | Description |
|-------|------|-------------|
| `handle_type` | `Type` | Current type of the handle |
| `handle_value` | `Any` | Current value |
| `history` | `list[dict]` | Ordered log of `{action, type}` transitions |

Sessions are created on `/api/load` and mutated on `/api/execute`.
They do **not** persist across server restarts.

## Frontend

The static SPA (`static/`) communicates exclusively through the JSON API above.

- **Drop zone** — drag-and-drop or click-to-upload a file.
- **Handle panel** — shows the current type badge and a preview of the value.
- **Actions grid** — cards for each valid action with type signatures; click to execute.
- **Plan panel** — pick a goal type and see the computed chain.
- **History trail** — breadcrumb-style trace of every transformation applied.

## Dependencies

Pulled in from the root `pyproject.toml`:

| Package | Role |
|---------|------|
| `fastapi` | HTTP framework |
| `uvicorn` | ASGI server |
| `python-multipart` | File uploads |
| `pydantic` | Request validation |

Plus everything in `core/` and `fileio/` (imported at startup).

## Development

```bash
# run with auto-reload
uvicorn backend.server:app --reload

# run tests from the project root
python -m pytest

# lint
ruff check backend/
```
