"""
This module contains sample code that runs through exploring a context,
verbal interactions, physical interactions, combat, and use of spells and
potions.
"""
import argparse
from random import randint
from gameactor import GameActor
from npc_guard import NPC_guard
from gamecontext import GameContext

# configuration file names
CONTEXT_DESCR = "TEST_context.dat"
GUARD_DESCR = "TEST_guard.dat"
HERO_DESCR = "TEST_hero.dat"


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
