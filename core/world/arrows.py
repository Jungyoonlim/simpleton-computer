"""
Arrows: the actions that move things around.

There are two kinds of arrow, and the difference decides how identity and
history work:

    CHANGE  τ → τ   same thing, new version     (edit, scale, reschedule)
    MAKE    A → B   a new thing, linked back    (outline, shopping list, invite)

A CHANGE arrow must keep the kind; that is enforced when it is declared, so
"same thing" can never quietly become a different kind of thing.

Every arrow also declares its effects, a set of labels such as {Send} or
{Network}. Pure arrows declare none. Effects are what the gates look at.

A Vocabulary holds the kinds and arrows of one world. It answers three
questions without running anything:

    tools_for(kind)        which arrows fit this kind of thing?
    check_plan(kind, ...)  does this chain of arrows fit together, and what
                           does it do to the world?
    find_path(A, B)        what chain of arrows gets from A to B?
"""

from __future__ import annotations

import enum
import heapq
import typing as t
from dataclasses import dataclass, field

from core.typesys.types import Type, unify, is_tvar
from core.typesys.effects import _mk_row_from_labels
from .kinds import Kind


class ArrowKind(enum.Enum):
    CHANGE = "change"
    MAKE = "make"


ArrowFn = t.Callable[..., t.Any]


def substitute(ty: Type, subst: dict) -> Type:
    """Apply a unifier to a type term."""
    if is_tvar(ty):
        key = ty.metadata["tvar"]
        return substitute(subst[key], subst) if key in subst else ty
    if not ty.params:
        return ty
    return Type(ty.name, [substitute(p, subst) for p in ty.params], dict(ty.metadata), ty.kind)


def is_many(ty: Type) -> bool:
    return ty.name == "List" and len(ty.params) == 1


@dataclass(eq=False)
class Arrow:
    name: str
    kind: ArrowKind
    input: Type
    output: Type
    fn: ArrowFn
    effects: frozenset[str] = frozenset()
    params: dict[str, Type] = field(default_factory=dict)
    doc: str = ""

    def __post_init__(self) -> None:
        self.effects = frozenset(self.effects)
        if self.kind is ArrowKind.CHANGE:
            if is_many(self.output) or unify(self.input, self.output) is None:
                raise TypeError(
                    f"'{self.name}' is a changing arrow, so it must keep the kind: "
                    f"{self.input} → {self.output} does not. Declare it as a making arrow instead."
                )

    @property
    def effect_row(self) -> Type:
        """The effects as a closed effect row term, e.g. {Network, Send}."""
        return _mk_row_from_labels(set(self.effects), None)

    @property
    def is_pure(self) -> bool:
        return not self.effects

    def output_for(self, input_t: Type) -> Type | None:
        """The output type when applied to input_t, or None if it does not fit."""
        subst = unify(self.input, input_t)
        if subst is None:
            return None
        return substitute(self.output, subst)

    def signature(self) -> str:
        eff = "{" + ", ".join(sorted(self.effects)) + "}" if self.effects else "pure"
        arrow = "⟳" if self.kind is ArrowKind.CHANGE else "→"
        return f"{self.name}: {self.input} {arrow} {self.output}  {eff}"


@dataclass(frozen=True)
class PlanCheck:
    ok: bool
    start: Type
    final: Type | None
    effects: frozenset[str]
    problem: str | None = None
    at: int | None = None  # index of the step that failed

    def __bool__(self) -> bool:
        return self.ok


class Vocabulary:
    """The kinds and arrows of one world."""

    def __init__(self) -> None:
        self.kinds: dict[str, Kind] = {}
        self.arrows: dict[str, Arrow] = {}

    # ---- declaring ---------------------------------------------------------

    def add_kind(self, name: str, fields: dict[str, Type], *, title: str | None = None, doc: str = "") -> Type:
        if name in self.kinds:
            raise ValueError(f"kind '{name}' already declared")
        ty = Type(name)
        self.kinds[name] = Kind(ty, dict(fields), title, doc)
        return ty

    def kind_of(self, ty_or_name: Type | str) -> Kind:
        name = ty_or_name if isinstance(ty_or_name, str) else ty_or_name.name
        if name not in self.kinds:
            raise KeyError(f"unknown kind '{name}'. Known: {', '.join(sorted(self.kinds))}")
        return self.kinds[name]

    def add_arrow(self, arrow: Arrow) -> Arrow:
        if arrow.name in self.arrows:
            raise ValueError(f"arrow '{arrow.name}' already declared")
        for ty in (arrow.input, arrow.output):
            inner = ty.params[0] if is_many(ty) else ty
            if not is_tvar(inner) and inner.name not in self.kinds:
                raise KeyError(f"arrow '{arrow.name}' mentions unknown kind '{inner.name}'")
        self.arrows[arrow.name] = arrow
        return arrow

    def change(self, name: str, kind: Type, *, effects: t.Iterable[str] = (), params: dict[str, Type] | None = None):
        """Decorator for a changing arrow: fn(content, **args) -> new content."""
        def deco(fn: ArrowFn) -> ArrowFn:
            self.add_arrow(Arrow(name, ArrowKind.CHANGE, kind, kind, fn, frozenset(effects),
                                 dict(params or {}), (fn.__doc__ or "").strip()))
            return fn
        return deco

    def make(self, name: str, input: Type, output: Type, *, effects: t.Iterable[str] = (),
             params: dict[str, Type] | None = None):
        """Decorator for a making arrow: fn(content, **args) -> content, or a list of contents for List(K)."""
        def deco(fn: ArrowFn) -> ArrowFn:
            self.add_arrow(Arrow(name, ArrowKind.MAKE, input, output, fn, frozenset(effects),
                                 dict(params or {}), (fn.__doc__ or "").strip()))
            return fn
        return deco

    def arrow(self, name: str) -> Arrow:
        if name not in self.arrows:
            raise KeyError(f"unknown arrow '{name}'. Known: {', '.join(sorted(self.arrows))}")
        return self.arrows[name]

    # ---- asking ------------------------------------------------------------

    def tools_for(self, ty: Type) -> list[Arrow]:
        """Arrows whose input fits this kind: the tools that gather around a thing."""
        return [a for a in self.arrows.values() if unify(a.input, ty) is not None]

    def check_plan(self, start: Type, steps: t.Sequence[str]) -> PlanCheck:
        """
        Check that a chain of arrows fits together, without running it.
        Returns the final kind and every effect the chain would have.
        """
        cur = start
        effects: set[str] = set()
        for i, name in enumerate(steps):
            if name not in self.arrows:
                return PlanCheck(False, start, None, frozenset(effects), f"step {i + 1}: no arrow called '{name}'", i)
            if is_many(cur):
                return PlanCheck(False, start, None, frozenset(effects),
                                 f"step {i + 1}: the step before makes several things ({cur}); "
                                 f"a plan can't continue past that yet", i)
            arrow = self.arrows[name]
            out = arrow.output_for(cur)
            if out is None:
                return PlanCheck(False, start, None, frozenset(effects),
                                 f"step {i + 1}: '{name}' takes a {arrow.input}, but it would get a {cur}", i)
            effects |= arrow.effects
            cur = out
        return PlanCheck(True, start, cur, frozenset(effects))

    def find_path(self, start: Type, goal: Type, *, max_depth: int = 4) -> list[str] | None:
        """
        Find a chain of making arrows from one kind to another.
        Shorter chains win; among equal lengths, chains with fewer effects win.
        """
        if unify(start, goal) is not None:
            return []
        counter = 0
        frontier: list[tuple[float, int, Type, list[str]]] = [(0.0, counter, start, [])]
        best: dict[Type, float] = {start: 0.0}
        while frontier:
            cost, _, cur, path = heapq.heappop(frontier)
            if unify(cur, goal) is not None:
                return path
            if len(path) >= max_depth or is_many(cur):
                continue
            for arrow in self.tools_for(cur):
                if arrow.kind is not ArrowKind.MAKE:
                    continue
                out = arrow.output_for(cur)
                if out is None:
                    continue
                c = cost + 1.0 + 0.25 * len(arrow.effects)
                if best.get(out, float("inf")) <= c:
                    continue
                best[out] = c
                counter += 1
                heapq.heappush(frontier, (c, counter, out, path + [arrow.name]))
        return None
