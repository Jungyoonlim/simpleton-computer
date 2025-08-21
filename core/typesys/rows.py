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

