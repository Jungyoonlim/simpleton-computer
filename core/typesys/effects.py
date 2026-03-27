"""
Effect rows are just rows of effect labels.

Computational effects a function may perform e.g. {Console, Network}
represented as EffExt("Console", EffExt("Network", EffEmpty()))

Mathematical Model 
------------------
An effect row ε is a finite set of labels with an optinal tail (row variable)

    ε ::= {ℓ1, …, ℓn} (closed)
    | {ℓ1, …, ℓn | ρ} (open tail ρ)

- Closed rows behave like finite sets of labels.
- Open rows are those same sets + an unknown remainder ρ.

Representation in this module
-----------------------------
We encode rows as a right-linked list using two constructors: 

    EffEmpty ≡ {}
    EffExt(label, tail) ≡ {label} ∪ tail

and reuse TVar(kind=K_EFFROW) for an open tail (ρ). We also use a conservative
unknown placeholder `Type("EffVar", kind=K_EFFROW)` when an operation would
require a union of *distinct* row variables (ρ ⊔ σ) that we do not explicitly
model.

Algebra (informal laws)
-----------------------
- Normalization: Order and duplicates are irrelevant; we canonicalize by sorting labels and deduping. 
- Union: 
    {A,B} ∪ {B,C} = {A,B,C}
    {A | ρ} ∪ {B} = {A,B | ρ}
    {A | ρ} ∪ {B | ρ} = {A,B | ρ}
    {A | ρ} ∪ {B | σ≠ρ} → EffVar (conservative unknown)
• Intersection and difference follow the same spirit; if tails disagree we
return EffVar.
• Equality: two rows are equal iff their label-sets and tails match. Closed vs
open are never equal. Unknown (EffVar) is unequal to everything.
    
Intuition 
---------
Effect rows act as capabilities. `{Network, Files}` means a computation
may use network and filesystem. Open tails let library code be polymorphic in the 
extra capabilities it inherits from its arguments. 
"""

from __future__ import annotations
from typing import Optional, Tuple, Set 

from .kinds import K_EFFROW
from .types import Type, TVar, is_tvar

# Constructors 
def EffEmpty() -> Type: 
    return Type("EffEmpty", kind=K_EFFROW)

def EffExt(effect: str, tail: Type) -> Type: 
    """
    Extend an effect row with a new effect label.
    EffExt("IO", EffExt("Network", EffEmpty())) represents {IO, Network}
    """
    assert tail.kind == K_EFFROW, f"Expected EffRow kind, got {tail.kind}"
    return Type("EffExt", [tail], metadata={"effect": effect}, kind=K_EFFROW)

def EffRowVar(name: str = "ρ") -> Type: 
    return TVar(name, kind=K_EFFROW)

# Internal Helpers 
def _mk_row_from_labels(labels: set[str], tail: Type | None) -> Type:
    row = EffEmpty() if tail is None else tail 
    for lab in sorted(labels):
        row = EffExt(lab, row)
    return row 

def _split_labels_tail(eff_row: Type) -> Optional[Tuple[Set[str], Optional[Type]]]:
    """
    Traverse an effect row and return (labels, tail)
    - If closed, tail is None 
    - If open, tail is a TVar(kind=K_EFFROW)
    """
    if eff_row.kind != K_EFFROW: 
        return None 

    labels = set()
    current = eff_row 

    # Traverse the list 
    while current.name == "EffExt":
        if "effect" not in current.metadata:
            return None
        labels.add(current.metadata["effect"])
        if not current.params:
            return None
        current = current.params[0]

    if current.name == "EffEmpty":
        return (labels, None)
    elif is_tvar(current) or current.name == "EffVar":
        return (labels, current)
    else: 
        return None 

# Basic queries 
def collect_effects(eff_row: Type) -> set[str] | None:
    """
    Flatten an effect row into a set of effect labels. (labels, tail, ok)
    Returns None if malformed.
    """
    if eff_row.kind != K_EFFROW:
        return None
    
    effects: set[str] = set()
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

    - Closed ∪ Closed => Closed with union of labels
    - Open(ρ) ∪ Closed => Open(ρ) with union of labels 
    - Open(ρ) ∪ Open(ρ) => Open(ρ) with union of labels
    - Open(ρ) ∪ Open(σ≠ρ) => returns a conservative unknown row variable `EffVar` 
    """
    r1 = _split_labels_tail(eff1)
    r2 = _split_labels_tail(eff2)

    if r1 is None or r2 is None:
        return Type("EffVar", kind=K_EFFROW)
    
    labels1, tail1 = r1 
    labels2, tail2 = r2 
    
    all_labels = labels1 | labels2 

    if tail1 is None and tail2 is None:
        # Both closed 
        tail = None 
    elif tail1 is None:
        # First closed, second open 
        tail = tail2 
    elif tail2 is None:
        # First open, second closed 
        tail = tail1 
    elif tail1 == tail2: 
        # Same tail variable 
        tail = tail1 
    else: 
        return Type("EffVar", kind=K_EFFROW)

    return _mk_row_from_labels(all_labels, tail)

def effect_eq(a: Type, b: Type) -> bool:
    """Check if two effect rows are equivalent."""
    effects_a = collect_effects(a)
    effects_b = collect_effects(b)
    
    # If both are closed, compare their effect sets
    if effects_a is not None and effects_b is not None:
        return effects_a == effects_b
    
    # If both are open/unknown, check structural equality
    if effects_a is None and effects_b is None:
        return a == b
    
    # One closed, one open - not equal
    return False

def normalize_row(eff_row: Type) -> Type: 
    """
    Normalize to canonical form: sorted, deduplicated labels    
    """
    result = _split_labels_tail(eff_row)
    if result is None: 
        return eff_row
    labels, tail = result 
    return _mk_row_from_labels(labels, tail)
