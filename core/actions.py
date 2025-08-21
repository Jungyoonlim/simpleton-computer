from __future__ import annotations

import typing as t 
from dataclasses import dataclass, field 

from core.types import Type, Doc, List, Comment, Unit
from fileio.files import parse_comments, CommentValue

@dataclass
class Action: 
    name: str 
    input_t: Type
    output_t: Type 
    fn: t.Callable[[t.Any], t.Any]
    meta: dict = field(default_factory=dict)

_registry: t.Dict[str, t.Tuple[Type, Type, t.Callable]] = {}

def register_action(name: str, input_t: Type, output_t: Type):
    """
    Decorator: Register a typed action 
    Usage: 
        @register_action("foo", InType, OutType, effect="IO")
        def foo(v):
    """
    def deco(fn: t.Callable):
        _registry[name] = (input_t, output_t, fn)
        return fn 
    return deco

def list_actions_for(t_: Type):
    from core.types import unify
    return {name: (inp, out) for name, (inp, out, _) in _registry.items() if unify(inp, t_)}

def run(name: str, value):
    inp_t, out_t, fn = _registry[name]
    return out_t, fn(value)


# ------- Your actions -------

@register_action("extract_comments", Doc, List(Comment))
def extract_comments(doc):
    """Doc -> List[Comment]"""
    return parse_comments(doc)

@register_action("filter_author_me", List(Comment), List(Comment))
def filter_author_me(comments: t.List[CommentValue]):
    """List[Comment] -> List[Comment]; demo filter"""
    me_aliases = {"me", "joanne", "jungyoon", "jungyoon lim"}
    return [c for c in comments if c.author.strip().lower() in me_aliases]

@register_action("filter_last_10_days", List(Comment), List(Comment))
def filter_last_10_days(comments: t.List[CommentValue]):
    """List[Comment] -> List[Comment]; keeps comments with date within last 10 days (naive ISO compare)"""
    # quick-and-dirty: compare strings; good enough if month boundaries are sane
    import datetime as dt
    cutoff = (dt.date.today() - dt.timedelta(days=10)).isoformat()
    return [c for c in comments if c.date >= cutoff]

@register_action("delete_all", List(Comment), Unit)
def delete_all(comments: t.List[CommentValue]):
    """List[Comment] -> Unit; simulate deletion (side-effect)"""
    # In a real editor, you'd rewrite the file without these comment lines.
    # For now, just print what would be deleted.
    print(f"[delete_all] Would delete {len(comments)} comments from {comments[0].source_path if comments else '—'}")
    return None