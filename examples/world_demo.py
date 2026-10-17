"""
A walk through the world engine.

    uv run python -m examples.world_demo

You and an agent share one world of typed things. Tools gather around each
thing by its kind. Changing arrows make new versions; making arrows make new
things that remember where they came from. The agent works freely when it
only adds, and asks when it would touch your things or reach outside.
"""

from __future__ import annotations

import os
import tempfile

from rich.console import Console
from rich.table import Table

from core.typesys.types import Type
from core.world import World, AGENT
from core.world.everyday import vocabulary

con = Console()


def say(title: str) -> None:
    con.rule(f"[bold]{title}")


def menu(world: World, thing_id: str, actor: str) -> None:
    th = world.get(thing_id)
    tab = Table(title=f"tools around {world.title(th)} ({th.kind}) — for {actor}")
    tab.add_column("arrow")
    tab.add_column("signature")
    tab.add_column("gate")
    tab.add_column("asks first because")
    for tool in world.tools(thing_id, actor):
        tab.add_row(tool.arrow.name, tool.arrow.signature(), str(tool.gate), "; ".join(tool.asks) or "—")
    con.print(tab)


def main() -> None:
    world = World(vocabulary())

    say("1. You put a few things down")
    sam = world.put("Contact", name="Sam", email="sam@example.com")
    recipe = world.put("Recipe", title="Miso toast", servings=2,
                       ingredients=["2 slices sourdough", "1 tbsp white miso", "2 tbsp butter"],
                       steps=["Toast the bread", "Mash miso into soft butter", "Spread while warm"])
    draft = world.put("Draft", title="Why apps aren't the final form",
                      body="Apps are really just a unit of selling.\n\nThe work should stay put and the tools should come to it.")
    for th in world.things():
        con.print(f"  {th.id:<10} {th.kind:<8} {world.title(th)}")

    say("2. Tools gather around a thing by its kind")
    menu(world, recipe.id, "you")
    menu(world, recipe.id, AGENT)

    say("3. A changing arrow: same thing, new version")
    world.apply("scale", recipe.id, servings=4)
    for v in world.history(recipe.id):
        con.print(f"  {v.id} v{v.version}  fingerprint {v.fingerprint}  {v.content['ingredients']}")

    say("4. The agent makes things freely — it only adds")
    out = world.apply("shopping_list", recipe.id, actor=AGENT)
    for th in out.things:
        con.print(f"  [green]{out.status}[/]  {th.id}  {world.title(th)}  (made by {th.actor} via {th.made_by}, from {th.derived_from[0]})")

    say("5. The agent wants to change your draft — that becomes a proposal")
    out = world.apply("tighten", draft.id, actor=AGENT)
    p = out.proposal
    con.print(f"  [yellow]{out.status}[/]  {p.id}: {'; '.join(p.reasons)}")
    con.print(f"  preview → {p.preview[0]['contents'][0]['body']!r}")
    world.accept(p.id)
    con.print(f"  you accepted → {draft.id} is now v{world.get(draft.id).version}, changed by {world.get(draft.id).actor}")

    say("6. The agent wants to share and send — one plan, one confirmation")
    out = world.run_plan(recipe.id, [("share", {"to": sam.id}), "send"], actor=AGENT)
    p = out.proposal
    con.print(f"  [yellow]{out.status}[/]  gate={p.gate}: {'; '.join(p.reasons)}")
    con.print(f"  messages in the world before you decide: {len(world.things('Message'))}")
    world.reject(p.id, note="not yet")
    con.print(f"  you said no → sent: {len(world.outbox())}")

    say("7. The checker names the bad step before anything runs")
    check = world.vocab.check_plan(Type("Draft"), ["outline", "send"])
    con.print(f"  outline → send: [red]{check.problem}[/]")
    check = world.vocab.check_plan(Type("Recipe"), ["share", "send"])
    con.print(f"  share → send:   [green]fits[/], ends as {check.final}, effects {set(check.effects)}")
    con.print(f"  a path from Note to Draft: {world.vocab.find_path(Type('Note'), Type('Draft'))}")

    say("8. A part graduates into a thing of its own")
    tip = world.promote(recipe.id, "steps[1]", "Note", title="The miso butter trick")
    con.print(f"  {tip.id}: {tip.content}  (part {tip.part_path} of {tip.part_of})")

    say("9. Undo is one more step forward")
    back = world.revert(recipe.id, 1)
    con.print(f"  {recipe.id} v{back.version} has v1's content again: {back.fingerprint == world.history(recipe.id)[0].fingerprint}")

    say("10. The log is the truth — save it, load it, same world")
    path = os.path.join(tempfile.mkdtemp(), "world.jsonl")
    world.save(path)
    again = World.load(path, vocabulary())
    same = {t.id: t.fingerprint for t in again.things()} == {t.id: t.fingerprint for t in world.things()}
    con.print(f"  {len(world.log)} events → reloaded, identical: {same}")
    con.print()
    for e in world.log[-6:]:
        what = (e.thing or {}).get("id") or (e.proposal or {}).get("id")
        extra = f" via {e.arrow}" if e.arrow else ""
        extra += f", approved by {e.approved_by}" if e.approved_by else ""
        con.print(f"  #{e.seq:<3} {e.actor:<6} {e.op:<8} {what}{extra}")


if __name__ == "__main__":
    main()
