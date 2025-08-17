from typing import Callable, Dict, Tuple, List as PyList
from core.types import Type, Doc, List, Comment, Unit
from fileio.files import parse_comments, CommentValue

_registry: Dict[str, Tuple[Type, Type, Callable]] = {}

def register_action(name: str, input_t: Type, output_t: Type):
    def deco(fn: Callable):
        _registry[name] = (input_t, output_t, fn)
        return fn 
    return deco

def list_actions_for(t: Type):
    from core.types import unify  # if you have a unify; else do simple name match
    def _unify(a: Type, b: Type) -> bool:
        # minimal structural match
        if a.name != b.name: return False
        if a.param and b.param: return _unify(a.param, b.param)
        return (a.param is None) and (b.param is None)
    return {name: (inp, out) for name, (inp, out, _) in _registry.items() if _unify(inp, t)}

def run(name: str, value):
    inp_t, out_t, fn = _registry[name]
    return out_t, fn(value)

@register_action("extract_comments", Doc, List(Comment))
def extract_comments(doc):
    """Doc -> List[Comment]"""
    return parse_comments(doc)

@register_action("filter_author_me", List(Comment), List(Comment))
def filter_author_me(comments: PyList[CommentValue]):
    """List[Comment] -> List[Comment]; demo filter"""
    me_aliases = {"me", "joanne", "jungyoon", "jungyoon lim"}
    return [c for c in comments if c.author.strip().lower() in me_aliases]

@register_action("filter_last_10_days", List(Comment), List(Comment))
def filter_last_10_days(comments: PyList[CommentValue]):
    """List[Comment] -> List[Comment]; keeps comments with date within last 10 days (naive ISO compare)"""
    # quick-and-dirty: compare strings; good enough if month boundaries are sane
    import datetime as dt
    cutoff = (dt.date.today() - dt.timedelta(days=10)).isoformat()
    return [c for c in comments if c.date >= cutoff]

@register_action("delete_all", List(Comment), Unit)
def delete_all(comments: PyList[CommentValue]):
    """List[Comment] -> Unit; simulate deletion (side-effect)"""
    # In a real editor, you'd rewrite the file without these comment lines.
    # For now, just print what would be deleted.
    print(f"[delete_all] Would delete {len(comments)} comments from {comments[0].source_path if comments else '—'}")
    return None