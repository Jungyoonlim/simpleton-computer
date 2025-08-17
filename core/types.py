from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class Type:
    name: str
    param: Optional['Type'] = None

Doc = Type("Doc")

def List(t: Type) -> Type: 
    return Type("List", t)

def unify(a: Type, b: Type) -> bool: 
    """Return True if type structures match"""
    if a.name != b.name: 
        return False
    if a.param and b.param:
        return unify(a.param, b.param)
    return (a.param is None) and (b.param is None)