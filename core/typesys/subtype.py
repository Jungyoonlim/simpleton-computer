from __future__ import annotations 
import typing as t 
from .types import Type
from .kinds import K_EFFROW

def EffEmpty() -> Type: 
    """
    
    """
    return Type("EffEmpty", kind=K_EFFROW)

