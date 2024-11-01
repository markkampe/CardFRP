#!/usr/bin/python3
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
    print(f"In the {local.name} in {village.name} ({village.description})\n")

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
        print(f"\t{person.name} ... {person.description}")
    npcs = local.get_npcs()
    print("\n    NPCs:")
    for person in npcs:
        print(f"\t{person.name} ... {person.description}")
    stuff = local.get_objects(hidden=True)
    print("\n    undiscovered objects:")
    for thing in stuff:
        print(f"\t{thing.name} ... {thing.description}")
    print()

    # TRY CONTEXT AFFORDED ACTIONS, AND SEE WHAT DIFFERNCE THEY MAKE
    actions = local.possible_actions(actor, local)
    for action in actions:
        (_, desc) = actor.take_action(action, local)
        print(f"{actor.name} tries to {action.verb}"
              f"(power={actor.get('POWER.'+action.verb)})"
              f" in {local.name}\n")

    stuff = local.get_objects(hidden=True)
    if not stuff:
        print("after which ... no hidden objects remain")
    else:
        print("\nafter which ... undiscovered objects:")
        for thing in stuff:
            print(f"\t{thing.name} ... {thing.description}")
    print()

    # PERFORM ALL POSSIBLE INTERACTIONS WITH THE GUARD
    interactions = guard.interact(actor)
    actions = interactions.possible_actions(actor, local)
    for interaction in actions:
        (_, desc) = actor.take_action(interaction, guard)
        verb = interaction.verb
        print(f"\n{actor.name} uses {verb} interaction on {guard.name}\n"
              f"    {desc}")
        print(f"    {guard.name}.{verb} = {guard.get(verb)}")

    # TRY PHYSICAL ACTIONS on the guard
    actions = actor.possible_actions(actor, local)
    for action in actions:
        (_, desc) = actor.take_action(action, guard)
        verb = action.verb
        print(f"\n{actor.name} tries to {verb} {guard.name}\n    {desc}")
        print(f"    {guard.name}.{verb} = {guard.get(verb)}")
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
        print(f"\n{actor.name} uses {weapon.name} to {attack.verb}"
              f"{target.name}, delivered={attack.get('HIT_POINTS')}\n"
              f"{desc}")

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
    print(f"    {actor.name} has {actor.get('LIFE')}")

    npcs = local.get_npcs()
    for npc in npcs:
        if npc.alive:
            print(f"    {npc.name} has {npc.get('LIFE')}")
        else:
            print(f"    {npc.name} is dead")

    # TEST A POTION OF CURE LIGHT WOUNDS
    potion = actor.get_object("CLW")

    print("\nHero drinks " + str(potion))
    clw = potion.possible_actions(actor, local)[0]
    (_, desc) = clw.act(actor, actor, local)
    print("    " + desc)
    print(f"    {actor.name} now has {actor.get('LIFE')}")

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
            print(f"    {actor.name} now has {atr} of {value}")

    # TEST A SCROLL OF COURAGE
    scroll = actor.get_object("Courage")

    print()
    print(f"{actor.name} reads {scroll}")
    bold = scroll.possible_actions(actor, local)[0]
    (_, desc) = bold.act(actor, actor, local)
    print("    " + desc)
    print(f"    {actor.name} now has FEAR of {actor.get('MENTAL.FEAR')}")


if __name__ == "__main__":
    main()
