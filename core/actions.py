from __future__ import annotations

import typing as t 
from dataclasses import dataclass, field 

from core.typesys.types import Type, Doc, List, Comment, Task, Unit, Option
from fileio.files import parse_comments, CommentValue, TaskValue, load_mixed

@dataclass
class Action: 
    name: str 
    input_t: Type
    output_t: Type 
    fn: t.Callable[[t.Any], t.Any]
    meta: dict = field(default_factory=dict)

_REGISTRY: dict[str, Action] = {}

def register_action(name: str, input_t: Type, output_t: Type, **meta):
    """
    Decorator: Register a typed action 
    Usage: 
        @register_action("foo", InType, OutType, effect="IO")
        def foo(v):
    """
    def deco(fn: t.Callable[[t.Any], t.Any]):
        if name in _REGISTRY: 
            raise ValueError(f"Action '{name}' already registered")
        _REGISTRY[name] = Action(name, input_t, output_t, fn, meta)
        return fn 
    return deco

def list_actions_for(t_: Type) -> dict[str, Action]:
    """
    Return actions whose input type unifies with t_. 
    """
    from core.typesys.types import unify
    out: dict[str, Action] = {}
    for name, act in _REGISTRY.items():
        ok = unify(act.input_t, t_)
        if ok is not False:
            out[name] = act
    return out 

def run(name: str, value):
    """
    Execute a registered action by name 
    Returns (output_type, output_value)
    """
    act = _REGISTRY.get(name)
    if not act:
        raise KeyError(f"Unknown action '{name}'. Registered: {', '.join(sorted(_REGISTRY)) or '(none)'}")
    result = act.fn(value)
    return act.output_t, result


# ------- Your actions -------

@register_action("extract_comments", Doc, List(Comment), effect="pure")
def extract_comments(doc) -> t.List[CommentValue]:
    """Doc -> List[Comment]"""
    path = getattr(doc, "path", doc)
    try: 
        return parse_comments(path)
    except TypeError:
        return parse_comments(doc)

@register_action("filter_author_me", List(Comment), List(Comment))
def filter_author_me(comments: t.List[CommentValue]) -> t.List[CommentValue]:
    """List[Comment] -> List[Comment]; demo filter"""
    me_aliases = {"me", "joanne", "jungyoon", "jungyoon lim"}
    return [c for c in comments if c.author.strip().lower() in me_aliases]

@register_action("filter_last_10_days", List(Comment), List(Comment))
def filter_last_10_days(comments: t.List[CommentValue]) -> t.List[CommentValue]:
    """List[Comment] -> List[Comment]; keeps comments with date within last 10 days (naive ISO compare)"""
    # quick-and-dirty: compare strings; good enough if month boundaries are sane
    import datetime as dt
    cutoff = (dt.date.today() - dt.timedelta(days=10))
    out: list[CommentValue] = []

    for c in comments: 
        s = str(getattr(c, "date", ""))[:10]
        try: 
            d = dt.date.fromisoformat(s)
        except Exception:
            continue 
        if d >= cutoff: 
            out.append(c)
    return out 

@register_action("delete_all", List(Comment), Unit)
def delete_all(comments: t.List[CommentValue]) -> None:
    """List[Comment] -> Unit; simulate deletion (side-effect)"""
    # In a real editor, you'd rewrite the file without these comment lines.
    # For now, just print what would be deleted.
    src = comments[0].source_path if comments else "—"
    print(f"[delete_all] Would delete {len(comments)} comments from {src}")
    return None

@register_action("head_comment", List(Comment), Option(Comment))
def head_comment(comments: t.List[CommentValue]) -> t.Optional[CommentValue]:
    """List[Comment] -> Option[Comment]; returns first comment or None"""
    return comments[0] if comments else None

@register_action("extract_tasks", Doc, List(Task), effect="pure")
def extract_tasks(doc) -> t.List[TaskValue]:
    """Doc -> List[Task]; extract tasks from mixed file"""
    path = getattr(doc, "path", doc)
    vals = load_mixed(path)
    return [v for v in vals if isinstance(v, TaskValue)]