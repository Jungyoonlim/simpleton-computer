"""
Kinds of things, and checking that a thing's content fits its kind.

A kind is a nominal type (Event, Recipe, Draft) plus the fields a thing of
that kind carries. The type is what arrows unify against; the fields are what
content is checked against.

Field types reuse the type algebra:

    String, Int, Float, Bool, Date     plain values
    List(τ), Option(τ)                 containers
    Ref(K)                             a pointer to another thing of kind K
    Top                                anything
"""

from __future__ import annotations

import datetime as dt
import typing as t
from dataclasses import dataclass

from core.typesys.types import Type, String, Int, Float, Bool, Date, Top


def Ref(kind: Type) -> Type:
    """A reference to another thing of the given kind, stored as its id."""
    return Type("Ref", [kind])


@dataclass(eq=False)
class Kind:
    type: Type
    fields: dict[str, Type]
    title_field: str | None = None
    doc: str = ""

    @property
    def name(self) -> str:
        return self.type.name

    def title_of(self, content: t.Mapping[str, t.Any]) -> str:
        if self.title_field and content.get(self.title_field):
            return str(content[self.title_field])
        return self.name


# A lookup the checker uses to follow Ref fields: id -> kind name, or None
RefLookup = t.Callable[[str], t.Optional[str]]


def conforms(value: t.Any, ty: Type, lookup: RefLookup | None = None, path: str = "") -> list[str]:
    """
    Check a plain Python value against a field type.
    Returns a list of problems ("where: what"); an empty list means it fits.
    """
    where = path or "value"
    name = ty.name

    if name == "Top":
        return []
    if name == "Option":
        return [] if value is None else conforms(value, ty.params[0], lookup, path)
    if value is None:
        return [f"{where}: missing (expected {ty})"]

    if name == "String":
        return [] if isinstance(value, str) else [f"{where}: expected text, got {type(value).__name__}"]
    if name == "Int":
        ok = isinstance(value, int) and not isinstance(value, bool)
        return [] if ok else [f"{where}: expected a whole number, got {value!r}"]
    if name == "Float":
        ok = isinstance(value, (int, float)) and not isinstance(value, bool)
        return [] if ok else [f"{where}: expected a number, got {value!r}"]
    if name == "Bool":
        return [] if isinstance(value, bool) else [f"{where}: expected true/false, got {value!r}"]
    if name == "Date":
        if isinstance(value, str):
            try:
                dt.date.fromisoformat(value[:10])
                return []
            except ValueError:
                pass
        return [f"{where}: expected a date like 2026-11-14, got {value!r}"]
    if name == "List":
        if not isinstance(value, list):
            return [f"{where}: expected a list, got {type(value).__name__}"]
        out: list[str] = []
        for i, item in enumerate(value):
            out += conforms(item, ty.params[0], lookup, f"{where}[{i}]")
        return out
    if name == "Ref":
        want = ty.params[0].name
        if not isinstance(value, str):
            return [f"{where}: expected a reference to a {want}, got {value!r}"]
        if lookup is None:
            return []
        got = lookup(value)
        if got is None:
            return [f"{where}: no thing with id {value!r}"]
        if got != want:
            return [f"{where}: points to a {got}, expected a {want}"]
        return []

    return [f"{where}: no checker for type {ty}"]


def check_content(kind: Kind, content: t.Mapping[str, t.Any], lookup: RefLookup | None = None) -> list[str]:
    """Check a whole content record against its kind: known fields, right shapes."""
    if not isinstance(content, t.Mapping):
        return [f"{kind.name}: content must be a record of fields"]
    problems: list[str] = []
    for fname in content:
        if fname not in kind.fields:
            problems.append(f"{fname}: not a field of {kind.name}")
    for fname, fty in kind.fields.items():
        problems += conforms(content.get(fname), fty, lookup, fname)
    return problems


__all__ = ["Kind", "Ref", "conforms", "check_content", "String", "Int", "Float", "Bool", "Date", "Top"]
