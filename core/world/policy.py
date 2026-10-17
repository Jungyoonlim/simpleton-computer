"""
Gates: who may do what without asking.

Each effect label maps to a gate:

    AUTO     just happens               (pure work, reading)
    PREVIEW  show the result first      (writing outside, network)
    CONFIRM  ask before doing it        (sending, spending)

An effect nobody has written a rule for gets CONFIRM. Unknown means careful.

People and the agent are treated differently, on purpose:

- A person's own click is the approval. A person never waits on a proposal.
- The agent may make new things freely, because making only adds to the
  world: nothing of yours is touched, and the new thing lands on the easel
  marked as the agent's.
- The agent may not change a thing someone else made without asking. That
  edit becomes a proposal, like a suggestion on a doc.
- The agent may not cross a PREVIEW or CONFIRM gate without asking either.
"""

from __future__ import annotations

import enum
import typing as t
from dataclasses import dataclass, field

from .arrows import Arrow, ArrowKind


class Gate(enum.IntEnum):
    AUTO = 0
    PREVIEW = 1
    CONFIRM = 2

    def __str__(self) -> str:
        return self.name.lower()


DEFAULT_RULES: dict[str, Gate] = {
    "Read": Gate.AUTO,
    "Write": Gate.PREVIEW,
    "Network": Gate.PREVIEW,
    "Send": Gate.CONFIRM,
    "Spend": Gate.CONFIRM,
    "Delete": Gate.CONFIRM,
}

AGENT = "agent"


@dataclass
class Policy:
    rules: dict[str, Gate] = field(default_factory=lambda: dict(DEFAULT_RULES))
    agents: frozenset[str] = frozenset({AGENT})

    def gate_for(self, effects: t.Iterable[str]) -> Gate:
        """The strictest gate any of these effects needs."""
        return max((self.rules.get(e, Gate.CONFIRM) for e in effects), default=Gate.AUTO)

    def is_agent(self, actor: str) -> bool:
        return actor in self.agents

    def needs_approval(self, actor: str, arrows: t.Sequence[Arrow], owners: t.Sequence[str]) -> list[str]:
        """
        Reasons this actor must ask before running these arrows on things
        made by `owners`. An empty list means go ahead.
        """
        if not self.is_agent(actor):
            return []
        reasons: list[str] = []
        effects = frozenset().union(*(a.effects for a in arrows)) if arrows else frozenset()
        gate = self.gate_for(effects)
        if gate > Gate.AUTO:
            labels = ", ".join(sorted(effects))
            reasons.append(f"it would {labels}, which needs {gate}")
        for arrow, owner in zip(arrows, owners):
            if arrow.kind is ArrowKind.CHANGE and owner != actor:
                reasons.append(f"'{arrow.name}' changes something {owner} made")
        return reasons
