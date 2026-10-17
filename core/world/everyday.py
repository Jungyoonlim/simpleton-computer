"""
A small everyday world: events, places, drafts, notes, recipes, tasks,
contacts and messages, with a handful of arrows between them.

The arrows are plain deterministic code on purpose. Nothing here needs a
model; the point is that the structure stands on its own. Later, a model can
write new arrows, and they get checked by the same types.

Effects are simulated: `send` marks a message as sent and the event log
records the Send effect, but nothing leaves the machine.
"""

from __future__ import annotations

import re

from core.typesys.types import String, Int, Bool, Date, List, Option
from .arrows import Vocabulary
from .kinds import Ref

FILLER = ("very ", "really ", "just ", "basically ", "actually ")


def vocabulary() -> Vocabulary:
    v = Vocabulary()

    Place = v.add_kind("Place", {"name": String, "address": Option(String)}, title="name")
    Contact = v.add_kind("Contact", {"name": String, "email": String}, title="name")
    Event = v.add_kind("Event", {"title": String, "date": Date, "place": Option(Ref(Place)),
                                 "notes": Option(String)}, title="title")
    Draft = v.add_kind("Draft", {"title": String, "body": String}, title="title")
    Note = v.add_kind("Note", {"title": String, "body": String}, title="title")
    Recipe = v.add_kind("Recipe", {"title": String, "servings": Int, "ingredients": List(String),
                                   "steps": List(String)}, title="title")
    Task = v.add_kind("Task", {"title": String, "done": Bool, "due": Option(Date)}, title="title")
    Message = v.add_kind("Message", {"to": Ref(Contact), "subject": String, "body": String,
                                     "status": String}, title="subject")

    # ---- changing arrows: same thing, new version -------------------------

    @v.change("tighten", Draft)
    def tighten(c):
        """Remove filler words and doubled spaces."""
        body = c["body"]
        for word in FILLER:
            body = re.sub(word, "", body, flags=re.IGNORECASE)
        c["body"] = re.sub(r"[ \t]{2,}", " ", body).strip()
        return c

    @v.change("retitle", Draft, params={"title": String})
    def retitle(c, title):
        """Give the draft a new title."""
        c["title"] = title
        return c

    @v.change("scale", Recipe, params={"servings": Int})
    def scale(c, servings):
        """Scale the leading quantity of each ingredient to a new number of servings."""
        factor = servings / c["servings"]

        def rescale(line: str) -> str:
            m = re.match(r"^(\d+(?:\.\d+)?)(.*)$", line)
            if not m:
                return line
            n = float(m.group(1)) * factor
            return f"{int(n) if n == int(n) else round(n, 2)}{m.group(2)}"

        c["ingredients"] = [rescale(x) for x in c["ingredients"]]
        c["servings"] = servings
        return c

    @v.change("reschedule", Event, params={"date": Date})
    def reschedule(c, date):
        """Move the event to another day."""
        c["date"] = date
        return c

    @v.change("complete", Task)
    def complete(c):
        """Mark the task done."""
        c["done"] = True
        return c

    @v.change("send", Message, effects={"Send"})
    def send(c):
        """Send the message (simulated)."""
        c["status"] = "sent"
        return c

    # ---- making arrows: a new thing, linked back ---------------------------

    @v.make("outline", Draft, Note)
    def outline(c):
        """The first sentence of each paragraph, as a note."""
        paras = [p.strip() for p in c["body"].split("\n\n") if p.strip()]
        firsts = [re.split(r"(?<=[.!?])\s", p, maxsplit=1)[0] for p in paras]
        return {"title": f"Outline: {c['title']}", "body": "\n".join(f"- {s}" for s in firsts)}

    @v.make("expand", Note, Draft)
    def expand(c):
        """Start a draft from a note."""
        return {"title": c["title"], "body": c["body"]}

    @v.make("shopping_list", Recipe, List(Task))
    def shopping_list(c):
        """One task per ingredient."""
        return [{"title": f"Buy {x}", "done": False, "due": None} for x in c["ingredients"]]

    @v.make("reminder", Event, Task)
    def reminder(c):
        """A task due on the day of the event."""
        return {"title": f"Get ready: {c['title']}", "done": False, "due": c["date"]}

    @v.make("invite", Event, Message, params={"to": Ref(Contact)})
    def invite(c, to):
        """A draft invitation to the event."""
        return {"to": to, "subject": f"Join me: {c['title']}",
                "body": f"Would you like to come to {c['title']} on {c['date']}?", "status": "draft"}

    @v.make("share", Recipe, Message, params={"to": Ref(Contact)})
    def share(c, to):
        """A draft message carrying the recipe."""
        lines = "\n".join(f"- {x}" for x in c["ingredients"])
        return {"to": to, "subject": c["title"], "body": f"Serves {c['servings']}.\n{lines}", "status": "draft"}

    @v.make("directions", Place, Note, effects={"Network"})
    def directions(c):
        """Directions to the place (simulated lookup)."""
        where = c.get("address") or c["name"]
        return {"title": f"Directions to {c['name']}", "body": f"Route to {where}."}

    return v
