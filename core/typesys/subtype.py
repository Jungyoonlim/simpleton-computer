from __future__ import annotations 
from .types import Type
from .kinds import K_EFFROW

def EffEmpty() -> Type: 
    """
    Closed empty effect row 
    """
    return Type("EffEmpty", kind=K_EFFROW)

def EffExt(effect: str, tail: Type) -> Type: 
    """
    
    """
    assert getattr(tail, "kind", None) == K_EFFROW, ""
    return Type("EffExt", [tail], metadata={"effect": effect}, kind=K_EFFROW)

def _flatten_effect_row(): 
    return 

def _effect_row_subtype() -> bool: 
    return False

def _nominal_leq():
    return 

def is_subtype():
    return 

def type_equiv():
    return 