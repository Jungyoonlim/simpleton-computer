"""
Effect rows are just rows of effect labels.

Computational effects a function may perform e.g. {Console, Network}
represented as EffExt("Console", EffExt("Network", EffEmpty()))
"""

from __future__ import annotations
from .kinds import K_EFFROW
from .types import Type, TVar, is_tvar

def EffEmpty() -> Type: 
    return Type("EffEmpty", kind=K_EFFROW)

def EffExt(effect: str, tail: Type) -> Type: 
    """
    
    """
    return 