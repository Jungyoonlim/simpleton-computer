"""
Row-polymorphic structures (records and variants)

A row is represented as a linked list:
    RowExt(label, type, tail)
    RowEmpty

This module provides: 
- RowEmpty / RowExt constructors
- Surface sugar for records (Rec) and variants (Case)
- Collectors that flatten row chains into dictionaries and tail 
"""
from __future__ import annotations
from dataclasses import dataclass
import typing as t 
from .kinds import K_ROW 
from .types import Type, TVar, is_tvar, Record, Variant 

def _assert_row_kind(t: Type) -> None: 
    assert t.kind == K_ROW, f"expected Row kind, got {t.kind} for {t}"

def RowEmpty() -> Type: 
    return Type("RowEmpty", kind=K_ROW)

def RowExt(label: str, ty: Type, tail: Type) -> Type: 
    _assert_row_kind(tail)
    return Type("RowExt", [ty, tail], metadata={"label": label}, kind=K_ROW)

def Rec(**fields: Type) -> Type: 
    """
    Build a record type {field1: T1, field2: T2, ...}
    Under the hood: Record(RowExt(...))
    """
    row = RowEmpty()
    for lbl, ty in reversed(list(fields.items())):
        row = RowExt(lbl, ty, row)
    return Record(row)

def Case(labels: dict[str, Type]) -> Type: 
    """
    Build a variant type <Lbl1: T1 | Lbl2: T2 | ...>
    Under the hood: Variant(RowExt(...))
    """
    row = RowEmpty()
    for lbl, ty in reversed(list(labels.items())):
        row = RowExt(lbl, ty, row)
    return Variant(row)

@dataclass(frozen=True)
class CollectedRow: 
    labels: dict[str, Type]
    tail: Type | None 
    ok: bool 

def collect_row(r: Type, return_tail: bool = False) -> CollectedRow: 
    """
    Flatten a row chain into a dictionary of labels and optionally its tail. 

    
    """