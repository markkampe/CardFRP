"""
This module contains:

    1. pytest test cases for key functionlity that extends beyond a
       single class (GameObject.load(), SEARCHing, and character interactions

    2. sample code that runs through exploring a context, verbal interactions,
       physical interactions, combat, and use of spells and potions.
"""
import argparse
from random import randint
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


# pylint: disable=too-many-branches
# pylint: disable=too-many-statements
# pylint: disable=too-many-locals
def main():
    """
    This is more intended as sample code than as test cases
    """
    # figure out what we have been asked to do
    parser = argparse.ArgumentParser(description='general test cases')
    parser.add_argument("--nocombat",
                        dest="no_combat", action="store_true", default=False)
    args = parser.parse_args()

    # create a town square within a village
    village = GameContext("Snaefelness", "village on north end of island")
    local = GameContext(parent=village)
    local.load(CONTEXT_DESCR)
    print("In the {} in {} ({})\n".
          format(local.name, village.name, village.description))

    # create hero and the guard
    actor = GameActor()
    actor.load(HERO_DESCR)
    actor.context = local
    local.add_member(actor)

    guard = NPC_guard()
    guard.load(GUARD_DESCR)
    guard.context = local
    local.add_npc(guard)

    # ASK THE LOCAL CONTEXT ABOUT PARTY, NPCS AND (OBVIOUS) OBJECTS
    party = local.get_party()
    print("    party:")
    for person in party:
        print("\t{} ... {}".format(person.name, person.description))
    npcs = local.get_npcs()
    print("\n    NPCs:")
    for person in npcs:
        print("\t{} ... {}".format(person.name, person.description))
    stuff = local.get_objects(hidden=True)
    print("\n    undiscovered objects:")
    for thing in stuff:
        print("\t{} ... {}".format(thing.name, thing.description))
    print()

    # TRY CONTEXT AFFORDED ACTIONS, AND SEE WHAT DIFFERNCE THEY MAKE
    actions = local.possible_actions(actor, local)
    for action in actions:
        (_, desc) = actor.take_action(action, local)
        print("{} tries to {}(power={}) in {}\n"
              .format(actor.name,
                      action.verb, actor.get("POWER."+action.verb),
                      local.name))

    stuff = local.get_objects(hidden=True)
    if not stuff:
        print("after which ... no hidden objects remain")
    else:
        print("\nafter which ... undiscovered objects:")
        for thing in stuff:
            print("\t{} ... {}".format(thing.name, thing.description))
    print()

    # PERFORM ALL POSSIBLE INTERACTIONS WITH THE GUARD
    interactions = guard.interact(actor)
    actions = interactions.possible_actions(actor, local)
    for interaction in actions:
        (_, desc) = actor.take_action(interaction, guard)
        verb = interaction.verb
        print("\n{} uses {} interaction on {}\n    {}"
              .format(actor.name, verb, guard.name, desc))
        print("    {}.{} = {}".format(guard.name, verb, guard.get(verb)))

    # TRY PHYSICAL ACTIONS on the guard
    actions = actor.possible_actions(actor, local)
    for action in actions:
        (_, desc) = actor.take_action(action, guard)
        verb = action.verb
        print("\n{} tries to {} {}\n    {}"
              .format(actor.name, verb, guard.name, desc))
        print("    {}.{} = {}".format(guard.name, verb, guard.get(verb)))
    print()

    if args.no_combat:
        return

    # HERO TAKES UP HIS SWORD AND THEY FIGHT TO THE DEATH
    weapon = actor.get_object("sword")

    target = npcs[0]
    actions = weapon.possible_actions(actor, local)
    while target is not None and actor.get("LIFE") > 0:
        # choose a random attack
        attack = actions[randint(0, len(actions)-1)]
        (_, desc) = actor.take_action(attack, target)
        print("\n{} uses {} to {} {}, delivered={}\n    {}"
              .format(actor.name, weapon.name, attack.verb, target.name,
                      attack.get("HIT_POINTS"), desc))

        # give each NPC an action and choose a target for nextg round
        target = None
        npcs = local.get_npcs()
        for npc in npcs:
            if not npc.incapacitated:
                (_, desc) = npc.take_turn()
                print(desc)
                if target is None:
                    target = npc

    # PRINT OUT THE DEATH TOLL
    print("\nAfter the combat:")
    print("    {} has {} LIFE".format(actor.name, actor.get("LIFE")))

    npcs = local.get_npcs()
    for npc in npcs:
        if npc.alive:
            print("    {} has {} LIFE".format(npc.name, npc.get("LIFE")))
        else:
            print("    {} is dead".format(npc.name))

    # TEST A SCROLL OF CURE LIGHT WOUNDS
    scroll = actor.get_object("CLW")

    print("\nHero reads " + str(scroll))
    clw = scroll.possible_actions(actor, local)[0]
    (_, desc) = clw.act(actor, actor, local)
    print("    " + desc)
    print("    {} now has {} LIFE".format(actor.name, actor.get("LIFE")))

    # USE A WEAPON WITH A COMPOUND ATTACK
    dagger = actor.get_object("Dagger")

    print("\nHero attacked by " + str(dagger))
    success = False
    while not success:
        stab = dagger.possible_actions(guard, local)[0]
        (success, desc) = stab.act(guard, actor, local)
        lines = desc.split("\n")
        for line in lines:
            print("    " + line)
        for atr in ["PHYSICAL.POISON", "MENTAL.FEAR"]:
            value = actor.get(atr)
            if value is None:
                continue
            print("    {} now has {} of {}".format(actor.name, atr, value))

    # TEST A SCROLL OF COURAGE
    scroll = actor.get_object("Courage")

    print()
    print("{} reads {}".format(actor.name, scroll))
    bold = scroll.possible_actions(actor, local)[0]
    (_, desc) = bold.act(actor, actor, local)
    print("    " + desc)
    print("    {} now has FEAR of {}".format(actor.name,
                                             actor.get("MENTAL.FEAR")))


if __name__ == "__main__":
    main()
