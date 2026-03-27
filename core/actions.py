from __future__ import annotations

import typing as t 
from dataclasses import dataclass, field 

from core.typesys.types import Type, Doc, List, Comment, Task, Unit, Option
from core.typesys.effects import Type as EffectType
from core.runtime import ExecutionContext, get_runtime, CapabilityDeniedError, EffectViolationError
from fileio.files import parse_comments, CommentValue, TaskValue, load_mixed, load_doc

@dataclass
class Action: 
    name: str 
    input_t: Type
    output_t: Type 
    fn: t.Callable[[t.Any], t.Any]
    meta: dict = field(default_factory=dict)
    
    @property
    def required_effects(self) -> t.Set[str]:
        """Get the set of effects this action requires."""
        return set(self.meta.get("effects", []))
    
    @property
    def is_pure(self) -> bool:
        """Check if this action is pure (no side effects)."""
        return self.meta.get("effect") == "pure" or not self.required_effects

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

def run(name: str, value, context_id: t.Optional[str] = None):
    """
    Execute a registered action by name with runtime enforcement.
    Returns (output_type, output_value)
    """
    act = _REGISTRY.get(name)
    if not act:
        raise KeyError(f"Unknown action '{name}'. Registered: {', '.join(sorted(_REGISTRY)) or '(none)'}")
    
    # If no context provided, create a minimal one for pure actions
    if context_id is None:
        if not act.is_pure:
            raise RuntimeError(f"Action '{name}' requires effects but no execution context provided")
        # Pure actions can run without a context
        result = act.fn(value)
        return act.output_t, result
    
    # Get the execution context and enforce capabilities
    runtime = get_runtime()
    context = runtime.get_context(context_id)
    
    # Declare required effects
    required_effects = act.required_effects
    if required_effects:
        context.declare_effects(required_effects)
    
    # Execute within the context
    with context.execution():
        # Wrap the action function to track effects
        wrapped_fn = _wrap_action_with_effect_tracking(act.fn, context, required_effects)
        result = wrapped_fn(value)
        return act.output_t, result


def _wrap_action_with_effect_tracking(fn: t.Callable, context: ExecutionContext, required_effects: t.Set[str]) -> t.Callable:
    """Wrap an action function to track and enforce effects."""
    def wrapped(value):
        # Record any file I/O effects
        if "IO" in required_effects:
            context.record_effect("IO", "action_execution", {"action": fn.__name__})
        
        # Record any file system effects  
        if "FileSystem" in required_effects:
            context.record_effect("FileSystem", "access", {"action": fn.__name__})
            
        # Execute the original function
        return fn(value)
    
    return wrapped


# ------- Your actions -------

@register_action("extract_comments", Doc, List(Comment), effects=["FileSystem"])
def extract_comments(doc) -> t.List[CommentValue]:
    """Doc -> List[Comment]"""
    if hasattr(doc, "text") and hasattr(doc, "path"):
        return parse_comments(doc)
    path = getattr(doc, "path", str(doc))
    _, dv = load_doc(path)
    return parse_comments(dv)

@register_action("filter_author_me", List(Comment), List(Comment), effect="pure")
def filter_author_me(comments: t.List[CommentValue]) -> t.List[CommentValue]:
    """List[Comment] -> List[Comment]; demo filter"""
    me_aliases = {"me", "joanne", "jungyoon", "jungyoon lim"}
    return [c for c in comments if c.author.strip().lower() in me_aliases]

@register_action("filter_last_10_days", List(Comment), List(Comment), effect="pure")
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

@register_action("delete_all", List(Comment), Unit, effects=["IO", "FileSystem"])
def delete_all(comments: t.List[CommentValue]) -> None:
    """List[Comment] -> Unit; simulate deletion (side-effect)"""
    # In a real editor, you'd rewrite the file without these comment lines.
    # For now, just print what would be deleted.
    src = comments[0].source_path if comments else "—"
    print(f"[delete_all] Would delete {len(comments)} comments from {src}")
    return None

@register_action("head_comment", List(Comment), Option(Comment), effect="pure")
def head_comment(comments: t.List[CommentValue]) -> t.Optional[CommentValue]:
    """List[Comment] -> Option[Comment]; returns first comment or None"""
    return comments[0] if comments else None

@register_action("extract_tasks", Doc, List(Task), effects=["FileSystem"])
def extract_tasks(doc) -> t.List[TaskValue]:
    """Doc -> List[Task]; extract tasks from mixed file"""
    path = getattr(doc, "path", doc)
    vals = load_mixed(path)
    return [v for v in vals if isinstance(v, TaskValue)]