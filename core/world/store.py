"""
The store: the world of things is the database.

Everything that happens is appended to a log of events, and the current state
is just what the log adds up to. Nothing is overwritten, so every thing keeps
its history, every change says who made it, and undo is one more step forward.

Two kinds of identity live side by side:

    thing.id           same thing even as its content changes (a draft stays
                       the same draft through every rewrite)
    thing.fingerprint  same content, same fingerprint (structural, like the
                       type algebra's equality, or a git blob)

People and the agent use the same calls. The policy decides when the agent has
to ask; when it does, its work becomes a proposal that shows exactly what would
happen, and accepting it commits exactly that.
"""

from __future__ import annotations

import copy
import datetime as dt
import hashlib
import json
import re
import typing as t
from dataclasses import dataclass, field, asdict

from core.typesys.types import Type, String
from .arrows import Arrow, ArrowKind, Vocabulary, is_many
from .kinds import check_content, conforms
from .policy import Policy, Gate

YOU = "you"


class WorldError(Exception):
    pass


class PlanError(WorldError):
    """A plan or arrow does not fit the thing it was pointed at."""


class ContractError(WorldError):
    """An arrow returned something that breaks its own declared type."""


class StaleProposal(WorldError):
    """The thing a proposal was based on has changed since."""


# ---- things -------------------------------------------------------------------


def _canon(content: t.Mapping[str, t.Any]) -> str:
    return json.dumps(content, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


@dataclass(frozen=True)
class Thing:
    """One version of one thing. Content is stored as canonical JSON, so a Thing is immutable."""
    id: str
    kind: str
    version: int
    content_json: str
    actor: str
    made_by: str = "hand"                 # arrow name, or "hand"
    derived_from: tuple[str, ...] = ()    # provenance: what it was made from
    part_of: str | None = None            # a part that graduated from a bigger thing
    part_path: str | None = None
    at: str = ""

    @property
    def content(self) -> dict[str, t.Any]:
        return json.loads(self.content_json)

    @property
    def fingerprint(self) -> str:
        return hashlib.sha256(f"{self.kind}\n{self.content_json}".encode()).hexdigest()[:12]

    def to_dict(self) -> dict:
        d = asdict(self)
        d["derived_from"] = list(self.derived_from)
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Thing":
        d = dict(d)
        d["derived_from"] = tuple(d.get("derived_from", ()))
        return cls(**d)


# ---- proposals and outcomes -------------------------------------------------


@dataclass
class Proposal:
    id: str
    actor: str
    start: str
    base_version: int
    steps: list[tuple[str, dict]]
    reasons: list[str]
    effects: list[str]
    gate: str
    preview: list[dict]                   # exactly what accepting will commit
    status: str = "pending"               # pending | accepted | rejected
    decided_by: str | None = None
    note: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["steps"] = [[n, a] for n, a in self.steps]
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Proposal":
        d = dict(d)
        d["steps"] = [(n, a) for n, a in d["steps"]]
        return cls(**d)


@dataclass
class Outcome:
    status: str                                   # done | proposed
    things: list[Thing] = field(default_factory=list)
    proposal: Proposal | None = None
    effects: frozenset[str] = frozenset()

    @property
    def done(self) -> bool:
        return self.status == "done"


@dataclass(frozen=True)
class Tool:
    """One entry in the menu that gathers around a thing."""
    arrow: Arrow
    gate: Gate
    asks: tuple[str, ...]                  # why this actor would have to ask; empty = it just happens


@dataclass(frozen=True)
class Event:
    seq: int
    at: str
    actor: str
    op: str          # put | change | make | promote | revert | propose | accept | reject
    thing: dict | None = None
    proposal: dict | None = None
    arrow: str | None = None
    args: dict | None = None
    effects: tuple[str, ...] = ()
    approved_by: str | None = None
    note: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["effects"] = list(self.effects)
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Event":
        d = dict(d)
        d["effects"] = tuple(d.get("effects", ()))
        return cls(**d)


# ---- the world ----------------------------------------------------------------


def _now() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


_PATH = re.compile(r"^([A-Za-z_]\w*)((?:\[\d+\])*)$")


class World:
    def __init__(self, vocab: Vocabulary, policy: Policy | None = None,
                 clock: t.Callable[[], str] | None = None) -> None:
        self.vocab = vocab
        self.policy = policy or Policy()
        self.clock = clock or _now
        self._log: list[Event] = []
        self._versions: dict[str, list[Thing]] = {}
        self._proposals: dict[str, Proposal] = {}
        self._counters: dict[str, int] = {}

    # ---- reading ------------------------------------------------------------

    @property
    def log(self) -> tuple[Event, ...]:
        return tuple(self._log)

    def get(self, thing_id: str) -> Thing:
        if thing_id not in self._versions:
            raise KeyError(f"no thing with id '{thing_id}'")
        return self._versions[thing_id][-1]

    def history(self, thing_id: str) -> list[Thing]:
        self.get(thing_id)
        return list(self._versions[thing_id])

    def things(self, kind: str | None = None) -> list[Thing]:
        latest = [vs[-1] for vs in self._versions.values()]
        return [th for th in latest if kind is None or th.kind == kind]

    def owner(self, thing_id: str) -> str:
        return self.history(thing_id)[0].actor

    def title(self, thing: Thing) -> str:
        return self.vocab.kind_of(thing.kind).title_of(thing.content)

    def provenance(self, thing_id: str) -> list[Thing]:
        """Walk back through what a thing was made from, nearest first."""
        out: list[Thing] = []
        seen: set[str] = set()
        frontier = list(self.get(thing_id).derived_from)
        while frontier:
            src = frontier.pop(0)
            if src in seen or src not in self._versions:
                continue
            seen.add(src)
            th = self.get(src)
            out.append(th)
            frontier += list(th.derived_from)
        return out

    def derived(self, thing_id: str) -> list[Thing]:
        """Things that were made from this one."""
        return [th for th in self.things() if thing_id in self.history(th.id)[0].derived_from]

    def parts(self, thing_id: str) -> list[Thing]:
        return [th for th in self.things() if th.part_of == thing_id]

    def proposals(self, status: str | None = "pending") -> list[Proposal]:
        return [p for p in self._proposals.values() if status is None or p.status == status]

    def outbox(self, effect: str = "Send") -> list[Event]:
        """Events that reached outside the world with a given effect."""
        return [e for e in self._log if effect in e.effects]

    def tools(self, thing_id: str, actor: str = YOU) -> list[Tool]:
        """The menu for a thing: arrows that fit its kind, with the gate each one meets for this actor."""
        th = self.get(thing_id)
        out = []
        for arrow in self.vocab.tools_for(Type(th.kind)):
            asks = self.policy.needs_approval(actor, [arrow], [self.owner(thing_id)])
            out.append(Tool(arrow, self.policy.gate_for(arrow.effects), tuple(asks)))
        return out

    # ---- writing by hand -----------------------------------------------------

    def put(self, kind: str, content: t.Mapping[str, t.Any] | None = None, *, actor: str = YOU,
            **fields: t.Any) -> Thing:
        """Put a new thing into the world."""
        body = dict(content or {}, **fields)
        self._validate(kind, body)
        th = Thing(self._new_id(kind), kind, 1, _canon(body), actor, at=self.clock())
        self._emit("put", actor, thing=th.to_dict())
        return th

    def edit(self, thing_id: str, *, actor: str = YOU, **fields: t.Any) -> Outcome:
        """Change fields by hand. It is a changing arrow like any other, so the same gates apply."""
        th = self.get(thing_id)
        kind_t = Type(th.kind)
        hand = Arrow("edit", ArrowKind.CHANGE, kind_t, kind_t, lambda c, **kw: {**c, **kw},
                     params={k: self.vocab.kind_of(th.kind).fields.get(k, String) for k in fields})
        return self._run(th, [(hand, dict(fields))], actor)

    def revert(self, thing_id: str, to_version: int, *, actor: str = YOU) -> Thing:
        """Undo, as one more step: a new version whose content equals an older one."""
        hist = self.history(thing_id)
        if not 1 <= to_version <= len(hist):
            raise WorldError(f"{thing_id} has versions 1..{len(hist)}, not {to_version}")
        old, cur = hist[to_version - 1], hist[-1]
        th = Thing(cur.id, cur.kind, cur.version + 1, old.content_json, actor, made_by=f"revert to v{to_version}",
                   derived_from=cur.derived_from, part_of=cur.part_of, part_path=cur.part_path, at=self.clock())
        self._emit("revert", actor, thing=th.to_dict(), note=f"back to v{to_version}")
        return th

    def promote(self, thing_id: str, path: str, kind: str, *, actor: str = YOU,
                into: str | None = None, **fields: t.Any) -> Thing:
        """
        A part graduates into a thing of its own. The value at `path`
        (e.g. "steps[2]") becomes field `into` of a new thing of `kind`,
        linked back to where it came from.
        """
        src = self.get(thing_id)
        value = self._value_at(src.content, path)
        k = self.vocab.kind_of(kind)
        if isinstance(value, dict) and into is None:
            body = {**value, **fields}
        else:
            target = into or next((f for f, ty in k.fields.items() if ty == String and f not in fields), None)
            if target is None:
                raise WorldError(f"say which field of {kind} the part goes into (into=...)")
            body = {**fields, target: value}
        self._validate(kind, body)
        th = Thing(self._new_id(kind), kind, 1, _canon(body), actor, made_by="promote",
                   derived_from=(thing_id,), part_of=thing_id, part_path=path, at=self.clock())
        self._emit("promote", actor, thing=th.to_dict(), note=f"{path} of {thing_id}")
        return th

    # ---- arrows and plans ---------------------------------------------------

    def apply(self, arrow: str, thing_id: str, *, actor: str = YOU, **args: t.Any) -> Outcome:
        """Use one arrow on one thing."""
        return self.run_plan(thing_id, [(arrow, args)], actor=actor)

    def run_plan(self, thing_id: str, steps: t.Sequence[str | tuple[str, dict]], *, actor: str = YOU) -> Outcome:
        """
        Run a chain of arrows starting from a thing. The whole chain is checked
        before anything runs, and the whole chain is approved (or not) at once.
        """
        resolved = [(self.vocab.arrow(s), {}) if isinstance(s, str) else (self.vocab.arrow(s[0]), dict(s[1]))
                    for s in steps]
        return self._run(self.get(thing_id), resolved, actor)

    def accept(self, proposal_id: str, *, actor: str = YOU) -> Outcome:
        p = self._pending(proposal_id)
        if self.policy.is_agent(actor):
            raise WorldError("an agent can't approve proposals")
        if self.get(p.start).version != p.base_version:
            raise StaleProposal(f"{p.start} changed since this was proposed (v{p.base_version} → "
                                f"v{self.get(p.start).version}); ask again")
        self._emit("accept", actor, proposal={"id": p.id})
        things = self._commit(p.preview, p.actor, approved_by=actor)
        return Outcome("done", things, p, frozenset(p.effects))

    def reject(self, proposal_id: str, *, actor: str = YOU, note: str = "") -> Proposal:
        p = self._pending(proposal_id)
        self._emit("reject", actor, proposal={"id": p.id}, note=note)
        return p

    # ---- persistence ----------------------------------------------------------

    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            for e in self._log:
                f.write(json.dumps(e.to_dict(), ensure_ascii=False) + "\n")

    @classmethod
    def load(cls, path: str, vocab: Vocabulary, policy: Policy | None = None,
             clock: t.Callable[[], str] | None = None) -> "World":
        w = cls(vocab, policy, clock)
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    w._replay(Event.from_dict(json.loads(line)))
        return w

    # ---- internals ----------------------------------------------------------

    def _lookup(self, thing_id: str) -> str | None:
        return self._versions[thing_id][-1].kind if thing_id in self._versions else None

    def _validate(self, kind: str, content: t.Mapping[str, t.Any], who: str | None = None) -> None:
        problems = check_content(self.vocab.kind_of(kind), content, self._lookup)
        if problems:
            if who:
                raise ContractError(f"'{who}' promised a {kind} but returned something else: " + "; ".join(problems))
            raise PlanError(f"not a valid {kind}: " + "; ".join(problems))

    def _check_args(self, arrow: Arrow, args: dict) -> None:
        missing = [p for p, ty in arrow.params.items() if p not in args and ty.name != "Option"]
        extra = [a for a in args if a not in arrow.params]
        if missing or extra:
            bits = ([f"needs {', '.join(missing)}"] if missing else []) + ([f"doesn't take {', '.join(extra)}"] if extra else [])
            raise PlanError(f"'{arrow.name}' " + " and ".join(bits))
        problems = [p for name, val in args.items() for p in conforms(val, arrow.params[name], self._lookup, name)]
        if problems:
            raise PlanError(f"'{arrow.name}': " + "; ".join(problems))

    def _run(self, start: Thing, steps: list[tuple[Arrow, dict]], actor: str) -> Outcome:
        check = self.vocab.check_plan(Type(start.kind), [a.name for a, _ in steps]) \
            if all(a.name in self.vocab.arrows for a, _ in steps) else None
        if check is not None and not check.ok:
            raise PlanError(check.problem)

        preview, owners = self._simulate(start, steps, actor)
        effects = frozenset().union(*(a.effects for a, _ in steps))
        reasons = self.policy.needs_approval(actor, [a for a, _ in steps], owners)
        if not reasons:
            return Outcome("done", self._commit(preview, actor), None, effects)

        p = Proposal(self._new_id("proposal"), actor, start.id, start.version,
                     [(a.name, args) for a, args in steps], reasons, sorted(effects),
                     str(self.policy.gate_for(effects)), preview)
        self._emit("propose", actor, proposal=p.to_dict())
        return Outcome("proposed", [], self._proposals[p.id], effects)

    def _simulate(self, start: Thing, steps: list[tuple[Arrow, dict]], actor: str) -> tuple[list[dict], list[str]]:
        """Work out exactly what a plan would do, without touching the world."""
        ops: list[dict] = []
        owners: list[str] = []
        cur_id, cur_kind, cur_content = start.id, start.kind, start.content
        cur_owner = self.owner(start.id)
        placeholder = 0
        for i, (arrow, args) in enumerate(steps):
            out_t = arrow.output_for(Type(cur_kind))
            if out_t is None:
                raise PlanError(f"step {i + 1}: '{arrow.name}' takes a {arrow.input}, but it would get a {cur_kind}")
            self._check_args(arrow, args)
            owners.append(cur_owner)
            result = arrow.fn(copy.deepcopy(cur_content), **copy.deepcopy(args))
            base = {"arrow": arrow.name, "args": args, "effects": sorted(arrow.effects)}
            if arrow.kind is ArrowKind.CHANGE:
                self._validate(cur_kind, result, who=arrow.name)
                ops.append({**base, "op": "change", "target": cur_id, "kind": cur_kind, "contents": [result]})
                cur_content = result
                continue
            many = is_many(out_t)
            kind = out_t.params[0].name if many else out_t.name
            results = result if many else [result]
            if many and not isinstance(result, list):
                raise ContractError(f"'{arrow.name}' promised several {kind}s but returned {type(result).__name__}")
            for r in results:
                self._validate(kind, r, who=arrow.name)
            ids = []
            for _ in results:
                placeholder += 1
                ids.append(f"@{placeholder}")
            ops.append({**base, "op": "make", "source": cur_id, "kind": kind, "contents": results, "ids": ids})
            if many:
                break
            cur_id, cur_kind, cur_content, cur_owner = ids[0], kind, results[0], actor
        return ops, owners

    def _commit(self, ops: list[dict], actor: str, approved_by: str | None = None) -> list[Thing]:
        real: dict[str, str] = {}
        out: list[Thing] = []
        for op in ops:
            if op["op"] == "change":
                target = real.get(op["target"], op["target"])
                cur = self.get(target)
                th = Thing(cur.id, cur.kind, cur.version + 1, _canon(op["contents"][0]), actor, op["arrow"],
                           cur.derived_from, cur.part_of, cur.part_path, self.clock())
                self._emit("change", actor, thing=th.to_dict(), arrow=op["arrow"], args=op["args"],
                           effects=tuple(op["effects"]), approved_by=approved_by)
                out = [o for o in out if o.id != th.id] + [th]
            else:
                source = real.get(op["source"], op["source"])
                for ph, content in zip(op["ids"], op["contents"]):
                    th = Thing(self._new_id(op["kind"]), op["kind"], 1, _canon(content), actor, op["arrow"],
                               (source,), at=self.clock())
                    real[ph] = th.id
                    self._emit("make", actor, thing=th.to_dict(), arrow=op["arrow"], args=op["args"],
                               effects=tuple(op["effects"]), approved_by=approved_by)
                    out.append(th)
        return out

    def _pending(self, proposal_id: str) -> Proposal:
        if proposal_id not in self._proposals:
            raise KeyError(f"no proposal '{proposal_id}'")
        p = self._proposals[proposal_id]
        if p.status != "pending":
            raise WorldError(f"{proposal_id} was already {p.status}")
        return p

    def _value_at(self, content: dict, path: str) -> t.Any:
        m = _PATH.match(path)
        if not m or m.group(1) not in content:
            raise WorldError(f"no part '{path}'")
        value = content[m.group(1)]
        for idx in re.findall(r"\[(\d+)\]", m.group(2)):
            if not isinstance(value, list) or int(idx) >= len(value):
                raise WorldError(f"no part '{path}'")
            value = value[int(idx)]
        return value

    def _new_id(self, kind: str) -> str:
        key = kind.lower()
        self._counters[key] = self._counters.get(key, 0) + 1
        return f"{key}-{self._counters[key]}"

    def _emit(self, op: str, actor: str, **kw: t.Any) -> Event:
        e = Event(len(self._log) + 1, self.clock(), actor, op, **kw)
        self._replay(e)
        return e

    def _replay(self, e: Event) -> None:
        self._log.append(e)
        if e.thing is not None:
            th = Thing.from_dict(e.thing)
            self._versions.setdefault(th.id, []).append(th)
            self._bump(th.id)
        if e.op == "propose" and e.proposal:
            p = Proposal.from_dict(e.proposal)
            self._proposals[p.id] = p
            self._bump(p.id)
        elif e.op in ("accept", "reject") and e.proposal:
            p = self._proposals[e.proposal["id"]]
            p.status = "accepted" if e.op == "accept" else "rejected"
            p.decided_by = e.actor
            p.note = e.note

    def _bump(self, ident: str) -> None:
        key, _, n = ident.rpartition("-")
        if n.isdigit():
            self._counters[key] = max(self._counters.get(key, 0), int(n))
