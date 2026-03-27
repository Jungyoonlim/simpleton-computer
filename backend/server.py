from __future__ import annotations

import uuid
import typing as t
from pathlib import Path
from dataclasses import dataclass, field

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from core.typesys.types import Type, Doc, List, Comment, Task, Link, Unit, Option
from core.actions import list_actions_for, _REGISTRY
from core.plan import find_chain, list_actions_for as plan_toolspace
from fileio.files import DocValue, CommentValue, TaskValue, LinkValue

import core.actions  # noqa: F401 – triggers @register_action decorators

from core.actions import register_action

if "summarize" not in core.actions._REGISTRY:
    @register_action("summarize", Doc, Doc)
    def summarize(doc):
        return type("X", (object,), {"path": doc.path, "text": doc.text[:100] + "..."})()

if "extract_titles" not in core.actions._REGISTRY:
    @register_action("extract_titles", Doc, List(Doc))
    def extract_titles(doc):
        lines = [line.strip() for line in doc.text.splitlines() if line.strip().startswith("#")]
        return [type("X", (object,), {"path": doc.path, "text": line})() for line in lines]

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="Simpleton Computer")


# ── Session state ──────────────────────────────────────────────────────────────
@dataclass
class Session:
    handle_type: Type
    handle_value: t.Any
    history: list[dict] = field(default_factory=list)

sessions: dict[str, Session] = {}


# ── Helpers ────────────────────────────────────────────────────────────────────
def type_to_str(ty: Type) -> str:
    if ty.params:
        inner = ", ".join(type_to_str(p) for p in ty.params)
        return f"{ty.name}[{inner}]"
    return ty.name

KNOWN_TYPES = {
    "Doc": Doc, "List[Comment]": List(Comment), "List[Task]": List(Task),
    "List[Link]": List(Link), "List[Doc]": List(Doc),
    "Unit": Unit, "Option[Comment]": Option(Comment),
}

def value_preview(ty: Type, val: t.Any) -> t.Any:
    """Serialize a handle value into something JSON-safe."""
    if val is None:
        return None
    if isinstance(val, DocValue):
        return {"path": val.path, "text": val.text[:500], "length": len(val.text)}
    if isinstance(val, list):
        items = []
        for v in val[:50]:
            if isinstance(v, (CommentValue, TaskValue, LinkValue)):
                items.append(str(v))
            elif hasattr(v, "text"):
                items.append(getattr(v, "text", str(v)))
            else:
                items.append(str(v))
        return {"items": items, "total": len(val)}
    return str(val)

def actions_for_type(ty: Type) -> list[dict]:
    acts = list_actions_for(ty)
    return [
        {
            "name": a.name,
            "input_type": type_to_str(a.input_t),
            "output_type": type_to_str(a.output_t),
            "pure": a.is_pure,
        }
        for a in acts.values()
    ]


# ── Request / Response models ─────────────────────────────────────────────────
class ExecuteRequest(BaseModel):
    session_id: str
    action: str

class PlanRequest(BaseModel):
    session_id: str
    goal_type: str


# ── Routes ─────────────────────────────────────────────────────────────────────
@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")

@app.post("/api/load")
async def load_file(file: UploadFile = File(...)):
    raw = await file.read()
    try:
        text = raw.decode("utf-8", errors="replace")
    except Exception as e:
        raise HTTPException(400, detail=str(e))

    ty = Doc
    val = DocValue(path=file.filename, text=text)

    sid = uuid.uuid4().hex[:12]
    sessions[sid] = Session(
        handle_type=ty,
        handle_value=val,
        history=[{"action": "load", "type": type_to_str(ty)}],
    )

    return {
        "session_id": sid,
        "type": type_to_str(ty),
        "value": value_preview(ty, val),
        "actions": actions_for_type(ty),
    }

@app.post("/api/execute")
async def execute(req: ExecuteRequest):
    session = sessions.get(req.session_id)
    if not session:
        raise HTTPException(404, detail="Session not found")

    acts = list_actions_for(session.handle_type)
    if req.action not in acts:
        valid = sorted(acts.keys())
        raise HTTPException(
            400,
            detail=f"Action '{req.action}' not valid for {type_to_str(session.handle_type)}. Valid: {valid}",
        )

    try:
        act = _REGISTRY[req.action]
        out_v = act.fn(session.handle_value)
        out_t = act.output_t
    except Exception as e:
        raise HTTPException(500, detail=str(e))

    session.handle_type = out_t
    session.handle_value = out_v
    session.history.append({"action": req.action, "type": type_to_str(out_t)})

    return {
        "session_id": req.session_id,
        "type": type_to_str(out_t),
        "value": value_preview(out_t, out_v),
        "actions": actions_for_type(out_t),
        "history": session.history,
    }

@app.post("/api/plan")
async def plan(req: PlanRequest):
    session = sessions.get(req.session_id)
    if not session:
        raise HTTPException(404, detail="Session not found")

    goal = KNOWN_TYPES.get(req.goal_type)
    if goal is None:
        raise HTTPException(400, detail=f"Unknown goal type '{req.goal_type}'. Known: {list(KNOWN_TYPES.keys())}")

    chain = find_chain(session.handle_type, goal, plan_toolspace)
    if chain is None:
        raise HTTPException(404, detail=f"No plan found from {type_to_str(session.handle_type)} to {req.goal_type}")

    return {
        "steps": [
            {
                "action": a.name,
                "input_type": type_to_str(a.input_t),
                "output_type": type_to_str(a.output_t),
            }
            for a in chain
        ]
    }

@app.get("/api/actions")
async def all_actions():
    return [
        {
            "name": a.name,
            "input_type": type_to_str(a.input_t),
            "output_type": type_to_str(a.output_t),
            "pure": a.is_pure,
        }
        for a in _REGISTRY.values()
    ]

@app.get("/api/types")
async def all_types():
    return list(KNOWN_TYPES.keys())


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
