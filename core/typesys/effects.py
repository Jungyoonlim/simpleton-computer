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
    Extend an effect row with a new effect label.
    EffExt("IO", EffExt("Network", EffEmpty())) represents {IO, Network}
    """
    assert tail.kind == K_EFFROW, f"Expected EffRow kind, got {tail.kind}"
    return Type("EffExt", [tail], metadata={"effect": effect}, kind=K_EFFROW)

def collect_effects(eff_row: Type) -> set[str] | None:
    """
    Flatten an effect row into a set of effect labels.
    Returns None if malformed.
    """
    if eff_row.kind != K_EFFROW:
        return None
    
    effects = set()
    current = eff_row
    
    while True:
        if current.name == "EffEmpty":
            return effects
        elif current.name == "EffExt":
            effect = current.metadata.get("effect")
            if effect is None:
                return None
            effects.add(effect)
            current = current.params[0]
        elif is_tvar(current):
            # Open effect row - can't fully collect
            return None
        else:
            return None

def has_effect(eff_row: Type, effect: str) -> bool:
    """Check if an effect row contains a specific effect."""
    effects = collect_effects(eff_row)
    return effects is not None and effect in effects

def effect_union(eff1: Type, eff2: Type) -> Type:
    """
    Union of two closed effect rows.
    Returns EffEmpty for empty union.
    """
    effects1 = collect_effects(eff1)
    effects2 = collect_effects(eff2)
    
    if effects1 is None or effects2 is None:
        # Can't union open effect rows
        return Type("EffVar", kind=K_EFFROW)  # Return unknown effect variable
    
    all_effects = effects1 | effects2
    
    # Build effect row from sorted effects for deterministic ordering
    result = EffEmpty()
    for effect in sorted(all_effects):
        result = EffExt(effect, result)
    
    return result 