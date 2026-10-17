# The World Engine

The first piece of a computer made of typed things, where the work stays put
and the tools come to it. It lives in `core/world/`. Run the walkthrough with:

```bash
uv run python -m examples.world_demo
```

## The one big flip

In most agent software today, **the conversation is the database.** What the
agent knows lives in a chat log, tools hand back text, and things scroll away.

Here, **the world of things is the database.** Chat, an easel, a text message
from your phone: these are all just windows onto the same world.

## The pieces

| piece | file | what it is |
|---|---|---|
| kinds | `kinds.py` | What kinds of things exist (Event, Recipe, Draft…) and what fields each carries. Content is checked against its kind, including references to other things (`Ref(Place)`). |
| arrows | `arrows.py` | The actions. Each declares its input, output and effects. |
| policy | `policy.py` | The gates: what just happens, what gets previewed, what asks first. |
| store | `store.py` | The world: an append-only log of everything that happened. Current state is what the log adds up to. |
| everyday | `everyday.py` | A small starter vocabulary: events, places, drafts, notes, recipes, tasks, contacts, messages. |

## Two kinds of identity

A thing has both, because a computer needs both:

- **`id` — same thing even as its content changes.** A draft stays the same
  draft through every rewrite. (The Ship of Theseus answer.)
- **`fingerprint` — same content, same fingerprint.** Structural, like the
  type algebra's own equality, or a git blob.

## Two kinds of arrows

This one distinction decides how history, undo, provenance and permissions work.

- **Changing arrows** `τ ⟳ τ` — same thing, new version (`tighten`, `scale`,
  `reschedule`, `send`). Declaring a changing arrow that alters the kind is an
  error, so "the same thing" can never quietly become a different kind of thing.
- **Making arrows** `A → B` — a new thing, linked back to what it came from
  (`outline`, `shopping_list`, `invite`). `A → List(B)` makes several.

## History is never overwritten

Every change is an event with an actor. So you can ask:

- `history(id)` — every version of a thing
- `provenance(id)` / `derived(id)` — where a thing came from, what came from it
- `revert(id, v)` — undo, as one more step forward (history keeps both)
- `log` — who did what, including what the agent did and who approved it

## Parts graduate

You don't decide up front how big a "thing" is. `promote(id, "steps[1]", "Note")`
lifts a part out into a thing of its own, linked back as `part_of`. Identity is
earned by use.

## Gates: you and the agent in one room

People and the agent use exactly the same calls (`put`, `edit`, `apply`,
`run_plan`). The policy decides when the agent must ask:

| situation | what happens |
|---|---|
| the agent **makes** something new, with no outside effect | it just lands, marked as the agent's |
| the agent **changes** something you made | it becomes a proposal, like a suggestion on a doc |
| an effect needs `preview` (Write, Network) or `confirm` (Send, Spend, Delete) | it becomes a proposal |
| an effect nobody wrote a rule for | `confirm` — unknown means careful |

A proposal holds an exact preview of what would happen. Accepting it commits
**exactly that**, and if the thing changed in the meantime, the proposal is
stale and has to be asked again. A whole plan is approved at once, before
anything in it runs.

## Checking before running

- `tools_for(kind)` — the arrows that fit a kind: the tools that gather around a thing
- `check_plan(kind, steps)` — does this chain fit, what does it end as, what are all its effects?
  A bad plan names its bad step: *"step 2: 'send' takes a Message, but it would get a Note."*
- `find_path(A, B)` — a chain of making arrows from one kind to another, shortest and least effectful first

An arrow that returns something other than what it promised raises
`ContractError` and nothing lands. That matters most later, when a model starts
writing arrows: the types are what keep its work honest.

## What this deliberately is not

There is no model anywhere in this engine. Take the AI out and the world still
works: kinds, arrows, history, gates. The AI is meant to join later as one more
actor in the room, writing arrows and proposing plans, held to the same checks.

## Open questions

- **Parts that stay connected.** A promoted part is linked back, but editing it
  doesn't flow back into its parent yet. Should it?
- **Plans that need to look first.** Plans are checked and approved up front.
  Real tasks often need to read something before deciding the next step. How
  rigid should a plan be?
- **Fan-out.** A plan can't continue past a step that makes several things.
  Map over them? Ask?
- **Who decides the kinds?** Today they're declared in code. Later: suggested
  by a model, approved by a person.
- **Effects are simulated.** `send` marks a message sent and the log records
  the effect, but nothing leaves the machine yet. Real effects need handlers.
