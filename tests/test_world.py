"""Tests for the world engine: things, two kinds of arrows, history, gates."""

import itertools

import pytest

from core.typesys.types import Type, String, Int, Date, List, Option
from core.world import (
    World, Arrow, ArrowKind, Ref, conforms, Gate, Policy, AGENT,
    PlanError, ContractError, StaleProposal, WorldError,
)
from core.world.everyday import vocabulary


@pytest.fixture
def world():
    ticks = itertools.count(1)
    return World(vocabulary(), clock=lambda: f"t{next(ticks)}")


@pytest.fixture
def stuff(world):
    recipe = world.put("Recipe", title="Toast", servings=2,
                       ingredients=["2 slices bread", "1 tbsp butter"], steps=["Toast it", "Butter it"])
    sam = world.put("Contact", name="Sam", email="sam@example.com")
    draft = world.put("Draft", title="Essay", body="This is really very  good.\n\nSecond part. More here.")
    fox = world.put("Place", name="The Fox", address="1807 Telegraph Ave")
    gig = world.put("Event", title="Concert", date="2026-11-14", place=fox.id)
    return dict(recipe=recipe, sam=sam, draft=draft, fox=fox, gig=gig)


def T(name):
    return Type(name)


# ---- kinds and content ---------------------------------------------------------


class TestConforms:
    def test_plain_values(self):
        assert conforms("hi", String) == []
        assert conforms(3, Int) == []
        assert conforms(True, Int)  # a bool is not a number here
        assert conforms("2026-11-14", Date) == []
        assert conforms("next tuesday", Date)

    def test_containers(self):
        assert conforms(None, Option(Int)) == []
        assert conforms(["a", "b"], List(String)) == []
        problems = conforms(["a", 2], List(String), path="xs")
        assert problems and problems[0].startswith("xs[1]")

    def test_refs_follow_the_world(self, world, stuff):
        assert conforms(stuff["fox"].id, Ref(T("Place")), world._lookup) == []
        assert "points to a Contact" in conforms(stuff["sam"].id, Ref(T("Place")), world._lookup)[0]
        assert "no thing" in conforms("place-99", Ref(T("Place")), world._lookup)[0]

    def test_put_rejects_bad_content(self, world):
        with pytest.raises(PlanError, match="servings"):
            world.put("Recipe", title="x", servings="two", ingredients=[], steps=[])
        with pytest.raises(PlanError, match="not a field"):
            world.put("Draft", title="x", body="y", colour="red")


# ---- identity and history -------------------------------------------------------


class TestIdentity:
    def test_change_keeps_identity(self, world, stuff):
        r = stuff["recipe"]
        out = world.apply("scale", r.id, servings=4)
        assert out.done
        now = world.get(r.id)
        assert now.id == r.id and now.version == 2
        assert now.content["ingredients"] == ["4 slices bread", "2 tbsp butter"]
        assert [v.version for v in world.history(r.id)] == [1, 2]
        assert world.history(r.id)[0].content["servings"] == 2  # the old version is still there

    def test_fingerprint_is_structural(self, world):
        a = world.put("Note", title="same", body="words")
        b = world.put("Note", title="same", body="words")
        assert a.id != b.id
        assert a.fingerprint == b.fingerprint

    def test_revert_is_a_step_forward(self, world, stuff):
        d = stuff["draft"]
        world.apply("tighten", d.id)
        back = world.revert(d.id, 1)
        assert back.version == 3
        assert back.content == world.history(d.id)[0].content
        assert back.fingerprint == world.history(d.id)[0].fingerprint
        assert len(world.history(d.id)) == 3

    def test_things_are_immutable(self, world, stuff):
        c = world.get(stuff["recipe"].id).content
        c["title"] = "changed"
        assert world.get(stuff["recipe"].id).content["title"] == "Toast"


# ---- the two kinds of arrows ---------------------------------------------------


class TestArrows:
    def test_changing_arrow_must_keep_kind(self):
        with pytest.raises(TypeError, match="must keep the kind"):
            Arrow("bad", ArrowKind.CHANGE, T("Draft"), T("Note"), lambda c: c)

    def test_make_links_back(self, world, stuff):
        out = world.apply("outline", stuff["draft"].id)
        note = out.things[0]
        assert note.kind == "Note" and note.made_by == "outline"
        assert note.derived_from == (stuff["draft"].id,)
        assert [t.id for t in world.derived(stuff["draft"].id)] == [note.id]
        assert note.content["body"] == "- This is really very  good.\n- Second part."

    def test_make_many(self, world, stuff):
        out = world.apply("shopping_list", stuff["recipe"].id)
        assert [t.content["title"] for t in out.things] == ["Buy 2 slices bread", "Buy 1 tbsp butter"]
        assert all(t.derived_from == (stuff["recipe"].id,) for t in out.things)

    def test_provenance_walks_back(self, world, stuff):
        note = world.apply("outline", stuff["draft"].id).things[0]
        draft2 = world.apply("expand", note.id).things[0]
        assert [t.id for t in world.provenance(draft2.id)] == [note.id, stuff["draft"].id]

    def test_tools_gather_by_kind(self, world, stuff):
        names = {t.arrow.name for t in world.tools(stuff["recipe"].id)}
        assert names == {"scale", "shopping_list", "share"}
        names = {t.arrow.name for t in world.tools(stuff["fox"].id)}
        assert names == {"directions"}

    def test_args_are_checked(self, world, stuff):
        with pytest.raises(PlanError, match="needs servings"):
            world.apply("scale", stuff["recipe"].id)
        with pytest.raises(PlanError, match="whole number"):
            world.apply("scale", stuff["recipe"].id, servings="four")
        with pytest.raises(PlanError, match="points to a Place"):
            world.apply("invite", stuff["gig"].id, to=stuff["fox"].id)

    def test_arrow_that_breaks_its_promise(self):
        v = vocabulary()

        @v.make("broken", T("Draft"), T("Note"))
        def broken(c):
            return {"title": "no body"}

        w = World(v)
        d = w.put("Draft", title="x", body="y")
        with pytest.raises(ContractError, match="promised a Note"):
            w.apply("broken", d.id)
        assert len(w.things()) == 1  # nothing landed

    def test_polymorphic_arrow(self):
        from core.typesys.types import TVar
        v = vocabulary()
        a = TVar("a")
        v.add_arrow(Arrow("touch", ArrowKind.CHANGE, a, a, lambda c: c))
        w = World(v)
        r = w.put("Note", title="n", body="b")
        assert "touch" in {t.arrow.name for t in w.tools(r.id)}
        assert w.apply("touch", r.id).things[0].version == 2


# ---- plans ----------------------------------------------------------------------


class TestPlans:
    def test_check_plan_names_the_bad_step(self, world):
        check = world.vocab.check_plan(T("Draft"), ["outline", "send"])
        assert not check.ok and check.at == 1
        assert "takes a Message, but it would get a Note" in check.problem

    def test_check_plan_collects_effects(self, world):
        check = world.vocab.check_plan(T("Recipe"), ["share", "send"])
        assert check.ok and check.final == T("Message") and check.effects == {"Send"}

    def test_cannot_continue_past_many(self, world):
        check = world.vocab.check_plan(T("Recipe"), ["shopping_list", "complete"])
        assert not check.ok and "several things" in check.problem

    def test_find_path(self, world):
        assert world.vocab.find_path(T("Note"), T("Note")) == []
        assert world.vocab.find_path(T("Event"), T("Message")) == ["invite"]
        assert world.vocab.find_path(T("Note"), T("Draft")) == ["expand"]
        assert world.vocab.find_path(T("Place"), T("Recipe")) is None

    def test_run_plan(self, world, stuff):
        out = world.run_plan(stuff["recipe"].id, [("share", {"to": stuff["sam"].id}), "send"])
        assert out.done
        msg = out.things[-1]
        assert msg.content["status"] == "sent" and msg.version == 2
        assert [e.op for e in world.outbox()] == ["change"]

    def test_bad_plan_runs_nothing(self, world, stuff):
        before = len(world.log)
        with pytest.raises(PlanError):
            world.run_plan(stuff["draft"].id, ["outline", "send"])
        assert len(world.log) == before


# ---- gates and the agent --------------------------------------------------------


class TestGates:
    def test_policy_strictest_wins_and_unknown_asks(self):
        p = Policy()
        assert p.gate_for([]) is Gate.AUTO
        assert p.gate_for(["Read", "Send"]) is Gate.CONFIRM
        assert p.gate_for(["Teleport"]) is Gate.CONFIRM

    def test_agent_makes_freely(self, world, stuff):
        out = world.apply("shopping_list", stuff["recipe"].id, actor=AGENT)
        assert out.done and all(t.actor == AGENT for t in out.things)

    def test_agent_change_to_your_thing_is_a_proposal(self, world, stuff):
        d = stuff["draft"]
        out = world.apply("tighten", d.id, actor=AGENT)
        assert out.status == "proposed"
        assert world.get(d.id).version == 1  # nothing changed yet
        p = out.proposal
        assert p.reasons == ["'tighten' changes something you made"]
        assert p.preview[0]["contents"][0]["body"] == "This is good.\n\nSecond part. More here."
        assert world.accept(p.id).done
        th = world.get(d.id)
        assert th.version == 2 and th.actor == AGENT
        assert th.content == p.preview[0]["contents"][0]  # what you saw is what landed
        assert world.log[-1].approved_by == "you"

    def test_agent_hand_edit_is_gated_too(self, world, stuff):
        out = world.edit(stuff["draft"].id, actor=AGENT, title="Better title")
        assert out.status == "proposed"
        assert world.edit(stuff["draft"].id, title="My title").done

    def test_agent_may_change_its_own_things(self, world, stuff):
        note = world.apply("outline", stuff["draft"].id, actor=AGENT).things[0]
        draft = world.apply("expand", note.id, actor=AGENT).things[0]
        assert world.apply("tighten", draft.id, actor=AGENT).done

    def test_send_needs_confirmation_as_one_plan(self, world, stuff):
        out = world.run_plan(stuff["recipe"].id, [("share", {"to": stuff["sam"].id}), "send"], actor=AGENT)
        assert out.status == "proposed" and out.proposal.gate == "confirm"
        assert world.things("Message") == []  # not even the draft lands before approval
        world.reject(out.proposal.id, note="not now")
        assert world.proposals() == []
        assert world.proposals("rejected")[0].note == "not now"
        assert world.outbox() == []

    def test_network_needs_preview(self, world, stuff):
        out = world.apply("directions", stuff["fox"].id, actor=AGENT)
        assert out.status == "proposed" and out.proposal.gate == "preview"

    def test_stale_proposal(self, world, stuff):
        d = stuff["draft"]
        p = world.apply("tighten", d.id, actor=AGENT).proposal
        world.edit(d.id, body="I rewrote it myself.")
        with pytest.raises(StaleProposal):
            world.accept(p.id)

    def test_agent_cannot_approve(self, world, stuff):
        p = world.apply("tighten", stuff["draft"].id, actor=AGENT).proposal
        with pytest.raises(WorldError):
            world.accept(p.id, actor=AGENT)

    def test_menu_shows_who_must_ask(self, world, stuff):
        menu = {t.arrow.name: t for t in world.tools(stuff["recipe"].id, actor=AGENT)}
        assert menu["scale"].asks and not menu["shopping_list"].asks
        assert all(not t.asks for t in world.tools(stuff["recipe"].id))


# ---- parts graduate ---------------------------------------------------------------


class TestPromote:
    def test_part_becomes_a_thing(self, world, stuff):
        r = stuff["recipe"]
        note = world.promote(r.id, "steps[1]", "Note", title="Buttering")
        assert note.content == {"title": "Buttering", "body": "Butter it"}
        assert note.part_of == r.id and note.part_path == "steps[1]"
        assert [p.id for p in world.parts(r.id)] == [note.id]
        assert world.get(r.id).version == 1  # the recipe itself is untouched

    def test_bad_path(self, world, stuff):
        with pytest.raises(WorldError, match="no part"):
            world.promote(stuff["recipe"].id, "steps[9]", "Note", title="x")


# ---- the log is the truth ------------------------------------------------------------


class TestPersistence:
    def test_save_and_load_replays_everything(self, world, stuff, tmp_path):
        world.apply("scale", stuff["recipe"].id, servings=4)
        world.apply("shopping_list", stuff["recipe"].id, actor=AGENT)
        pending = world.apply("tighten", stuff["draft"].id, actor=AGENT).proposal
        path = tmp_path / "world.jsonl"
        world.save(str(path))

        again = World.load(str(path), vocabulary())
        assert {t.id: t.fingerprint for t in again.things()} == {t.id: t.fingerprint for t in world.things()}
        assert len(again.history(stuff["recipe"].id)) == 2
        assert [p.id for p in again.proposals()] == [pending.id]
        again.accept(pending.id)  # a proposal survives a restart
        fresh = again.put("Note", title="n", body="b")
        assert fresh.id not in {t.id for t in world.things()}  # ids keep counting
