#!/usr/bin/pytest-3
"""
This module contains pytest test cases for key functionlity that extends
beyond a single class (GameObject.load(), SEARCHing, and character interactions
"""
import pytest
from gameactor import GameActor
from npc_guard import NPC_guard
from gamecontext import GameContext

# configuration file names
CONTEXT_DESCR = "TEST_context.dat"
GUARD_DESCR = "TEST_guard.dat"
HERO_DESCR = "TEST_hero.dat"


@pytest.mark.parametrize("filename", [(CONTEXT_DESCR)])
def test_load_context(filename):
    """
    Create a new GameContext, use its load() method to read in its attributes
    and contained objects, and then check that it has correctly read the name,
    description, and contained objects from that file.

    @param filename: name of the context description to be loaded
    """
    # create a town square within a village
    village = GameContext("Snaefelness", "village on north end of island")
    local = GameContext(parent=village)
    local.load(filename)

    # test name and description
    assert local.name == "town square", \
        "Name improperly read from " + filename
    assert local.description == "center of village", \
        "Description improperly read from " + filename

    # test obvious objects (in TEST_contxt.dat)
    obvious = local.get_objects()
    expected = ['bench']
    assert len(obvious) == len(expected), \
        "did not find expected number of obvious items in " + filename
    found = False
    for desired in expected:
        for item in obvious:
            if item.name == desired:
                found = True
        assert found, \
            "did not find obvious item " + desired + " in " + filename

    # test hidden objects (in TEST_contxt.dat)
    hidden = local.get_objects(True)
    expected = ['trap-door', 'coin']
    assert len(hidden) == len(expected), \
        "did not find expected number of hidden items in " + filename
    found = False
    for desired in expected:
        for item in hidden:
            if item.name == desired:
                found = True
        assert found, \
            "did not find hidden item " + desired + " in " + filename


@pytest.mark.parametrize("filename,npc",
                         [(GUARD_DESCR, True), (HERO_DESCR, False)])
def test_load_actor(filename, npc):
    """
    Create a new GameActor (or NPC), use its load() method to read in  its
    attributes and owned objects, and then check that it has correctly
    read the name, attributes, and owned objects from that file.

    @param filename: (string) name of the GameActor description to be loaded
    @param npc: (boolean) which description is being read (values to expect)
    """
    # create the GameActor and load the description
    actor = NPC_guard() if npc else GameActor()
    actor.load(filename)

    # check the name and description
    expected = "Guard #1" if npc else "Hero"
    assert actor.name == expected, \
        "name attribute improperly read from " + filename

    expected = "test target" if npc else "test actor"
    assert actor.description == expected, \
        "description attribute improperly read from " + filename

    # check a few attributes against expected values
    if npc:
        # in TEST_guard.dat
        assert actor.get("RESISTANCE.PHYSICAL") == 75, \
            "RESISTANCE.PHYSICAL improperly read from " + filename
        assert actor.get("PROTECTION") == 4, \
            "PROTECTION improperly read from " + filename
    else:
        # in TEST_hero.dat
        assert actor.get("POWER.SEARCH") == 25, \
            "POWER.SEARCH improperly read from " + filename
        assert actor.get("DAMAGE") == "D4", \
            "DAMAGE improperly read from " + filename

        # the Hero also has several items
        for (obj, atr, exp) in [
                ('long sword', 'DAMAGE.slash', 'D6+2'),
                ('Scroll of CLW', 'POWER', 100),
                ('Poison Dagger', 'STACKS.PHYSICAL.POISON', 'D4')]:
            assert actor.get_object(obj).get(atr) == exp, \
                obj + " " + atr + " improperly read from " + filename


@pytest.mark.parametrize("context,actor", [(CONTEXT_DESCR, HERO_DESCR)])
def test_search(context, actor):
    """
    search a context for hidden objects

    @param context: (string) context description file name
    @param actor: (string) searching actor description file name
    """
    # instantiate the context and actor
    local = GameContext()
    local.load(context)
    hero = GameActor()
    hero.load(actor)
    hero.context = local

    # confirm that the context affords a SEARCH operation
    actions = local.possible_actions(hero, local)
    assert len(actions) == 1 and actions[0].verb == "SEARCH", \
        context + " offered actions other than [SEARCH]"

    # see what is obvious before we search
    before = local.get_objects()
    assert len(before) == 1, \
        "expected only one visible object prior to search"

    # do a search
    hero.take_action(actions[0], local)
    after = local.get_objects()
    assert len(after) > 1, \
        "SEARCH did not find anything"

    # if we didn't find everything, do a more thorough search
    if len(after) == 2:
        actions[0].set("STACKS", 10)
        hero.take_action(actions[0], local)
        final = local.get_objects()
        assert len(final) == 3, \
            "thorough SEARCH did not find everything"


@pytest.mark.parametrize("context,actor,target,verb,expect", [
    (CONTEXT_DESCR, HERO_DESCR, GUARD_DESCR, 'VERBAL.FLATTER', True),
    (CONTEXT_DESCR, HERO_DESCR, GUARD_DESCR, 'VERBAL.OUTRANK', False),
    ])
# pylint: disable=too-many-locals
def test_interaction(context, actor, target, verb, expect):
    """
    @param context: (string) context description file name
    @param actor: (string) initiating actor description file name
    @param target: (string) receiving actor description file name
    @param verb: (string) action to take
    @param expect: (boolean) do we expect it to succeed
    """
    # instantiate the context and actors
    local = GameContext()
    local.load(context)

    hero = GameActor()
    hero.load(actor)
    hero.context = local

    guard = NPC_guard()
    guard.load(target)
    guard.context = local

    # find the desired interaction
    interactions = guard.interact(hero)
    actions = interactions.possible_actions(hero, local)
    found = None
    for action in actions:
        if action.verb == verb:
            found = action
            break
    assert found is not None, \
        "Unable to find interaction " + verb + " in " + target

    # get the property to be affected
    pre = guard.get(verb)

    # perform that interaction
    if expect:
        found.set("STACKS", 10)      # lay it on thick
    (result, _) = hero.take_action(found, guard)

    # get the affected property after the fact
    post = guard.get(verb)

    # did it succeed/fail as expected, and result in expected attribute change
    if expect:
        assert result, \
            verb + " on " + guard.name + " " + "failed"
        if pre:
            assert post > pre, \
                "successful " + verb + " vs " + guard.name + \
                " did not increase " + verb
        else:
            assert post >= 1, \
                "successful " + verb + " vs " + guard.name + \
                " did not result in positive " + verb
    else:
        assert not result, \
            verb + " on " + guard.name + " " + "failed"
        assert post == pre, \
            "failed " + verb + " vs " + guard.name + " changed " + verb
