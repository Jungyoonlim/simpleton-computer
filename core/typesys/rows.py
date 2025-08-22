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
    
    def is_closed(self) -> bool:
        """True if this is a closed row (tail is RowEmpty or None)"""
        return self.tail is None or (hasattr(self.tail, 'name') and self.tail.name == "RowEmpty") 

def collect_row(r: Type, return_tail: bool = False) -> CollectedRow: 
    """
    Flatten a row chain into a dictionary of labels and optionally its tail. 

    Supports both closed rows (RowEmpty) and open rows (TVar Row)
    Detects duplicates and fails with ok=False
    """
    if r.kind != K_ROW: 
        return CollectedRow({}, None, False)
    labels: dict[str, Type] = {}
    cur = r 
    tail: Type | None = None 
    seen: set[str] = set()

    while True: 
        if cur.name == "RowEmpty":
            tail = cur if return_tail else None
            return CollectedRow(labels, tail, True)
        if is_tvar(cur):
            tail = cur if return_tail else None 
            return CollectedRow(labels, tail, True)
        if cur.name == "RowExt":
            lbl = cur.metadata["label"]
            if lbl in seen: 
                return CollectedRow({}, None, False)
            seen.add(lbl)
            labels[lbl] = cur.params[0]
            cur = cur.params[1]
            continue 
        return CollectedRow({}, None, False)
    
def get_label_type(r: Type, label: str) -> Type | None: 
    """
    Return the field type if present, else None 
    """
    return collect_row(r).labels.get(label)

def row_subtract(r_big: Type, r_small: Type) -> Type | None: 
    """
    Closed minus closed
    """
    big = collect_row(r_big, return_tail=True)
    small = collect_row(r_small, return_tail=True)
    if not (big.ok and small.ok and big.is_closed() and small.is_closed()):
        return None 
    remain = {k: v for k, v in big.labels.items() if k not in small.labels}
    items = sorted(remain.items(), key=lambda kv: kv[0])
    row = RowEmpty()
    for lbl, ty in reversed(items):
        row = RowExt(lbl, ty, row)
    return row 

def row_union(r1: Type, r2: Type) -> Type | None: 
    """
    Closed union if a label occurs in both, r2 wins
    Returns None for open rows
    """
    c1 = collect_row(r1, return_tail=True)
    c2 = collect_row(r2, return_tail=True)
    if not (c1.ok and c2.ok and c1.is_closed() and c2.is_closed()):
        return None 
    merged = dict(c1.labels); merged.update(c2.labels)
    items = sorted(merged.items(), key=lambda kv: kv[0])
    row = RowEmpty()
    for lbl, ty in reversed(items):
        row = RowExt(lbl, ty, row)
    return row 