"""
The world engine: a computer made of typed things.

    kinds     what kinds of things exist, and what fields they carry
    arrows    changing arrows (same thing, new version) and making arrows
              (a new thing, linked back), each with its effects
    policy    gates: what happens freely, what is previewed, what asks first
    store     the world itself: an append-only log of everything that happened
    everyday  a small starter vocabulary (events, drafts, recipes, ...)

See docs/WORLD.md for the ideas behind it.
"""

from .kinds import Kind, Ref, conforms, check_content
from .arrows import Arrow, ArrowKind, Vocabulary, PlanCheck
from .policy import Gate, Policy, AGENT
from .store import (
    World, Thing, Proposal, Outcome, Tool, Event, YOU,
    WorldError, PlanError, ContractError, StaleProposal,
)

__all__ = [
    "Kind", "Ref", "conforms", "check_content",
    "Arrow", "ArrowKind", "Vocabulary", "PlanCheck",
    "Gate", "Policy", "AGENT",
    "World", "Thing", "Proposal", "Outcome", "Tool", "Event", "YOU",
    "WorldError", "PlanError", "ContractError", "StaleProposal",
]
