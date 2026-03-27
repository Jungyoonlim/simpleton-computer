from __future__ import annotations

from dataclasses import dataclass, field
import typing as t  
from .kinds import K_TYPE

@dataclass(frozen=True)
class Type:
    """
    the Type dataclass

    Algebraic Type Term:
    - Name: Head Symbol in Σ 
    - Params: Subterms (τ1,...,τk)
    - Metadata: Extra Annotations 
    - Kind: Implementation Tag 
    """
    name: str
    params: t.List['Type'] = field(default_factory=list)     
    metadata: t.Dict[str, t.Any] = field(default_factory=dict) 
    kind: str = K_TYPE

    @property
    def carrier(self):
        return self.metadata.get("py")

    def __str__(self):
        if not self.params:
            return self.name
        param_str = ", ".join(str(p) for p in self.params)
        return f"{self.name}[{param_str}]"

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        if not isinstance(other, Type):
            return False
        return (self.name == other.name and
                self.params == other.params)

    def __hash__(self):
        return hash((self.name, tuple(self.params)))

# Base Types
Unit = Type("Unit")
Bool = Type("Bool")
Int = Type("Int")
String = Type("String")
Float = Type("Float")
Bytes = Type("Bytes")
Top = Type("Top") 
Doc = Type("Doc")
Comment = Type("Comment")
Task = Type("Task")
Link = Type("Link")
Date = Type("Date")
Path = Type("Path")

# Container Types
def List(t_: Type) -> Type:
    return Type("List", [t_])

def Option(t_: Type) -> Type:
    return Type("Option", [t_])

def Tuple(*types: Type) -> Type:
    return Type("Tuple", list(types))

def Function(input_t: Type, output_t: Type) -> Type:
    return Type("Function", [input_t, output_t])

def Map(key_t: Type, value_t: Type) -> Type:   # <-- rename from Dict to avoid shadowing typing.Dict
    return Type("Map", [key_t, value_t])

def Set(t_: Type) -> Type:
    return Type("Set", [t_])

def Record(row: Type) -> Type:
    """Record type built from a row: Record(RowExt(...))"""
    return Type("Record", [row])

def Variant(row: Type) -> Type:
    """Variant type built from a row: Variant(RowExt(...))"""
    return Type("Variant", [row])

def Range(start_t: Type | None = None, end_t: Type | None = None) -> Type:
    start_t = start_t or Int
    end_t = end_t or Int
    return Type("Range", [start_t, end_t], metadata={"description": "A range of positions"})

# Context wrapper
def Context(t_: Type, **metadata) -> Type:
    return Type("Context", [t_], metadata)

# Effect types
Effect = Type("Effect")

def IO(t_: Type | None = None) -> Type:
    return Type("IO", [t_ or Top])

def Network(t_: Type | None = None) -> Type:
    return Type("Network", [t_ or Top])

def UI(t_: Type | None = None) -> Type:
    return Type("UI", [t_ or Top])

# Patterns
def Maybe(t_: Type) -> Type:
    return Option(t_)

def Either(left_t: Type, right_t: Type) -> Type:
    return Type("Either", [left_t, right_t])

def Stream(t_: Type) -> Type:
    return Type("Stream", [t_])

def Promise(t_: Type) -> Type:
    return Type("Promise", [t_])

class TVar(Type):
    def __init__(self, varname: str, kind: str = K_TYPE):
        super().__init__(name=f"TVar({varname})", params=[], metadata={"tvar": varname}, kind=kind)

def is_tvar(t_: Type) -> bool:
    return isinstance(t_, TVar)

def occurs(var: str, t: Type, subst: dict) -> bool:
    """Does TVar(var) appear inside type t under current substitution subst?"""
    if is_tvar(t):
        v = t.metadata["tvar"]
        if v == var: 
            return True
        return v in subst and occurs(var, subst[v], subst)
    return any(occurs(var, p, subst) for p in t.params)

# Unification
def unify(a: Type, b: Type, subst: t.Optional[dict]=None) -> t.Optional[dict]:
    subst = {} if subst is None else dict(subst)

    # Top matches anything
    if a.name == "Top" or b.name == "Top":
        return subst

    # Context unwrap (keep your versions)
    if a.name == "Context" and a.params:
        return unify(a.params[0], b, subst)
    if b.name == "Context" and b.params:
        return unify(a, b.params[0], subst)

    # --- Type variables ---
    if is_tvar(a):
        key = a.metadata["tvar"]
        if key in subst:
            return unify(subst[key], b, subst)
        if occurs(key, b, subst):
            return None
        subst[key] = b
        return subst

    if is_tvar(b):
        key = b.metadata["tvar"]
        if key in subst:
            return unify(a, subst[key], subst)
        if occurs(key, a, subst):
            return None
        subst[key] = a
        return subst

    # Names/arity must match
    if a.name != b.name or len(a.params) != len(b.params):
        return None

    # Recurse
    for ap, bp in zip(a.params, b.params):
        subst = unify(ap, bp, subst)
        if subst is None:
            return None
    return subst