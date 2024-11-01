#!/usr/bin/python3
""" This module implements the GameActor class """
from random import randint
from gameobject import GameObject
from gameaction import GameAction
from gamecontext import GameContext


class GameActor(GameObject):
    """
    A GameActor (typically a PC or NPC) is an agent that has a
    context and is capable of initiating and receiving actions.
    """

    def __init__(self, name="actor", descr=None):
        """
        create a new GameActor
        @param name: display name of this actor
        @param descr: human description of this actor
        """
        super().__init__(name, descr)
        self.context = None
        self.alive = True
        self.incapacitated = False

    def _accept_attack(self, action, actor, context):
        """
        Accept an attack, figure out if it hits, and how bad
        @param action: (GameAction) being performed
        @param actor: (GameActor) initiating the action
        @param context: (GameContext) in which action is being taken
        @return:  (boolean, string) succewss and description of the effect

        """

        # get the victim's base and sub-type EVASION
        evade = self.get("EVASION")
        evasion = 0 if evade is None else int(evade)
        if "ATTACK." in action.verb:
            evade = self.get("EVASION." + action.verb.split(".")[1])
            if evade is not None:
                evasion += int(evade)

        # see if EVASION+D100 can beat the incoming TO_HIT
        to_hit = action.get("TO_HIT") - evasion
        if to_hit < 100 and randint(1, 100) > to_hit:
            return (False,
                    f"{self.name} evades {action.source.name} {action.verb}")

        # get the recipient's base and sub-class PROTECTION
        prot = self.get("PROTECTION")
        protection = 0 if prot is None else int(prot)
        if "ATTACK." in action.verb:
            prot = self.get("PROTECTION." + action.verb.split(".")[1])
            if prot is not None:
                protection += int(prot)

        # see if PROTECTION can absorb all the incoming HIT_POINTS
        delivered = action.get("HIT_POINTS")
        if protection >= delivered:
            return (False,
                    f"{self.name}'s protection absorbs all damage from"
                    f" {action.verb}")

        # subtract received HIT_POINTS from our LIFE
        old_hp = self.get("LIFE")
        if old_hp is None:
            old_hp = 0
        new_hp = old_hp - (delivered - protection)
        self.set("LIFE", new_hp)

        taken = delivered - protection
        result = f"{self.name} hit by {action.verb} from {actor.name}" +\
                 f" using {action.source.name} for {delivered}-{protection}" +\
                 f" life-points in {context.name}" +\
                 f"\n    {self.name} life: {old_hp} - {taken} = {new_hp}"

        # if LIFE<=0 we are incapacitated, and no longer alive
        if new_hp <= 0:
            result += ", and is killed"
            self.alive = False
            self.incapacitated = True
        return (True, result)

    def accept_action(self, action, actor, context):
        """
        receive and process the effects of an ATTACK
        (other actions are passed to our super-class)

        A standard attack comes with at-least two standard attributes:
           - TO_HIT ... the (pre defense) to-hit probability
           - HIT_POINTS ... the (pre-armor) damage being delivered

           1. use D100+EVASION to determine if attack hits
           2. use PROTECTION to see how much damage gets through
           3. update LIFE_POINTS

        @param action: (GameAction) being performed
        @param actor: (GameActor) initiating the action
        @param context: (GameContext) in which action is being taken
        @return:  (boolean, string) description of the effect
        """
        # get the base action verb
        base_verb = action.verb.split('.')[0] \
            if '.' in action.verb else action.verb

        # we handle ATTACK (based on HIT/DAMAGE vs EVASION/PROTECTION)
        if base_verb == "ATTACK":
            return self._accept_attack(action, actor, context)

        # otherwise let our (GameObject) super-class handle it
        return super().accept_action(action, actor, context)

    def interact(self, actor):
        """
        return a list of possible interactions (w/this GameActor)

        @param actor: (GameActor) initiating the interactions
        @return: Interaction object

        GameObjects have a (ACTIONS) list of verbs that can be turned into
        a list of the GameActions that they enable.
        GameActors have a (INTERACTIONS) list of verbs that a requesting
        GameActor can turn into interaction GameActions that can be
        exchanged with that character.

        The interaction object will have an ACTIONS attribute,
        containing a comma-separated list of the supported interaction verbs
        (which can be used to instantiate and deliver GameActions).
        """
        interactions = GameObject("interactions w/" + actor.name)
        verbs = self.get("INTERACTIONS")
        actions = ""
        if verbs is not None:
            for verb in verbs.split(','):
                actions += "VERBAL." if actions == "" else ",VERBAL."
                actions += verb
        interactions.set("ACTIONS", actions)
        return interactions

    def set_context(self, context):
        """
        establish the local context
        """
        self.context = context

    def take_action(self, action, target):
        """
        Initiate an action against a target
        @param action: (GameAction) to be initiated
        @param target: (GameObject) target of the action
        @return: (boolean, string) result of the action
        """
        # call C{action.act()} with me as initiator, in my context
        return action.act(self, target, self.context)

    def take_turn(self):
        """
        called once per round in initiative order
        (must be implemented in sub-classes)
        """
        return self.name + " takes no action"


# UNIT TESTING
# pylint: disable=too-many-statements
def simple_attack_tests():
    """
    Base attacks with assured outcomes
    """
    attacker = GameActor("attacker")
    target = GameActor("target")
    context = GameContext("unit-test")

    tried = 0
    passed = 0

    # attack guarnteed to fail
    target.set("LIFE", 10)
    source = GameObject("weak-attack")
    action = GameAction(source, "ATTACK")
    action.set("ACCURACY", -100)
    action.set("DAMAGE", "1")
    print("{attacker} tries to {action} {target} with {source}")
    (_, desc) = action.act(attacker, target, context)
    tried += 1
    assert target.get("LIFE") == 10, \
        f"{target} took damage, LIFE: {10} -> {target.get('LIFE')}"
    passed += 1
    print("    " + desc)
    print()

    # attack guaranteed to succeed
    source = GameObject("strong-attack")
    action = GameAction(source, "ATTACK")
    action.set("ACCURACY", 100)
    action.set("DAMAGE", "1")
    print(f"{attacker} tries to {action} {target} with {source}")
    tried += 1
    (_, desc) = action.act(attacker, target, context)
    assert target.get("LIFE") == 9, \
        f"{target} took incorrect damage, LIFE: {10} -> {target.get('LIFE')}"
    passed += 1
    print("    " + desc)
    print()

    # attack that will be evaded
    source = GameObject("evadable-attack")
    action = GameAction(source, "ATTACK")
    action.set("ACCURACY", 0)
    action.set("DAMAGE", "1")
    target.set("EVASION", 100)
    target.set("LIFE", 10)
    print(f"{attacker} tries to {action} {target} with {source}")
    tried += 1
    (_, desc) = action.act(attacker, target, context)
    assert target.get("LIFE") == 10, \
        f"{target} took incorrect damage, LIFE: {10} -> {target.get('LIFE')}"
    passed += 1
    print("    " + desc)
    print()

    # attack that will be absorbabed
    source = GameObject("absorbable-attack")
    action = GameAction(source, "ATTACK")
    action.set("ACCURACY", 100)
    action.set("DAMAGE", "1")
    target.set("EVASION", 0)
    target.set("LIFE", 10)
    target.set("PROTECTION", 1)
    print(f"{attacker} tries to {action} {target} with {source}")
    tried += 1
    (_, desc) = action.act(attacker, target, context)
    assert target.get("LIFE") == 10, \
        f"{target} took incorrect damage, LIFE: {10} -> {target.get('LIFE')}"
    passed += 1
    print("    " + desc)
    print()
    return (tried, passed)


def sub_attack_tests():
    """
    Attacks that draw on sub-type EVASION and PROTECTION
    """
    attacker = GameActor("attacker")
    target = GameActor("target")
    context = GameContext("unit-test")

    tried = 0
    passed = 0

    # evasion succeeds because base and sub-type add
    source = GameObject("evadable")
    action = GameAction(source, "ATTACK.subtype")
    action.set("ACCURACY", 0)
    action.set("DAMAGE", "1")

    target.set("LIFE", 10)
    target.set("EVASION", 50)
    target.set("EVASION.subtype", 50)

    print(f"{attacker} tries to {action} {target} with {source}")
    (_, desc) = action.act(attacker, target, context)
    tried += 1
    assert target.get("LIFE") == 10, \
        f"{target} took incorrect damage, LIFE: {10} -> {target.get('LIFE')}"
    passed += 1
    print("    " + desc)

    # protection is sum of base and sub-type
    source = GameObject("absorbable")
    action = GameAction(source, "ATTACK.subtype")
    action.set("ACCURACY", 0)
    action.set("DAMAGE", "4")

    target.set("LIFE", 10)
    target.set("EVASION", 0)
    target.set("EVASION.subtype", 0)
    target.set("PROTECTION", 1)
    target.set("PROTECTION.subtype", 1)

    print(f"{attacker} tries to {action} {target} with {source}")
    (_, desc) = action.act(attacker, target, context)
    tried += 1
    assert target.get("LIFE") == 8, \
        f"{target} took incorrect damage, LIFE: {8} -> {target.get('LIFE')}"
    passed += 1
    print("    " + desc)
    print()
    return (tried, passed)


def random_attack_tests():
    """
    attacks that depend on dice-rolls
    """
    attacker = GameActor("attacker")
    target = GameActor("target")
    context = GameContext("unit-test")

    target.set("LIFE", 10)
    source = GameObject("fair-fight")
    action = GameAction(source, "ATTACK")
    action.set("ACCURACY", 0)
    action.set("DAMAGE", "1")
    target.set("EVASION", 50)
    target.set("LIFE", 10)
    target.set("PROTECTION", 0)
    rounds = 10
    for _ in range(rounds):
        print(f"{attacker} tries to {action} {target} with {source}")
        (_, desc) = action.act(attacker, target, context)
        print("    " + desc)

    life = target.get("LIFE")
    assert life < 10, "{target} took no damage in {roudns} rounds"
    assert life > 10 - rounds, "{target} took damage every round"
    remain = 10 - life
    print(f"{target} was hit {remain} times in {rounds} rounds")
    print()
    return (2, 2)


def simple_condition_tests():
    """
    conditions that are guaranteed to happen or not
    """
    sender = GameActor("sender")
    target = GameActor("target")
    context = GameContext("unit-test")

    tried = 0
    passed = 0

    # impossibly weak condition will not happen
    source = GameObject("weak-condition")
    action = GameAction(source, "MENTAL.CONDITION-1")
    action.set("POWER", -100)
    action.set("STACKS", "10")
    print(f"{sender} tries to {action} {target} with {context}")
    (success, desc) = action.act(sender, target, context)
    assert not success, \
        f"{action.verb} was successful against {target}"
    assert target.get(action.verb) is None, \
        f"{target} RECEIVED {action.verb}={target.get(action.verb)}"
    print("    " + desc)
    tried += 2
    passed += 2

    # un-resisted condition will always happen
    source = GameObject("strong-condition")
    action = GameAction(source, "MENTAL.CONDITION-2")
    action.set("POWER", 0)
    action.set("STACKS", "10")
    print(f"{sender} tries to {action} {target} with {source}")
    (success, desc) = action.act(sender, target, context)
    assert success, \
        f"{action.verb} was unsuccessful against {target}"
    assert target.get(action.verb) == 10, \
        f"{target} RECEIVED {action.verb}={target.get(action.verb)}"
    print("    " + desc)
    tried += 2
    passed += 2

    # fully resisted condition will never happen
    source = GameObject("base-class-resisted-condition")
    action = GameAction(source, "MENTAL.CONDITION-3")
    action.set("POWER", 0)
    action.set("STACKS", "10")
    target.set("RESISTANCE.MENTAL", 100)
    print(f"{sender} tries to {action} {target} with {source}")
    (success, desc) = action.act(sender, target, context)
    assert not success, \
        f"{action.verb} was successful against {target}"
    assert target.get(action.verb) is None, \
        f"{target} RECEIVED {action.verb}={target.get(action.verb)}"
    print("    " + desc)
    tried += 2
    passed += 2

    print()
    return (tried, passed)


def sub_condition_tests():
    """
    conditions that draw on sub-type RESISTANCE
    """
    sender = GameActor("sender")
    target = GameActor("target")
    context = GameContext("unit-test")

    # MENTAL + sub-type are sufficient to resist it
    source = GameObject("sub-type-resisted-condition")
    action = GameAction(source, "MENTAL.CONDITION-4")
    action.set("POWER", 0)
    action.set("STACKS", "10")
    target.set("RESISTANCE.MENTAL", 50)
    target.set("RESISTANCE.MENTAL.CONDITION-4", 50)
    print(f"{sender} tries to {action} {target} with {source}")
    (success, desc) = action.act(sender, target, context)
    assert not success, \
        "{action.verb} was successful against {target}"
    assert target.get(action.verb) is None, \
        f"{target} RECEIVED {action.verb}={target.get(action.verb)}"
    print("    " + desc)

    print()
    return (2, 2)


def random_condition_tests():
    """
    conditions that depend on dice rolls
    """
    sender = GameActor("sender")
    target = GameActor("target")
    context = GameContext("unit-test")

    source = GameObject("partially-resisted-condition")
    action = GameAction(source, "MENTAL.CONDITION-5")
    action.set("POWER", 0)
    action.set("STACKS", "10")
    target.set("RESISTANCE.MENTAL", 25)
    target.set("RESISTANCE.MENTAL.CONDITION-5", 25)

    rounds = 5
    for _ in range(rounds):
        print(f"{sender} tries to {action} {target} with {source}")
        (success, desc) = action.act(sender, target, context)
        assert success, \
            f"none of 10 stacks of {action.verb} got through"
        print("    " + desc)

    delivered = rounds * 10
    expected = delivered / 2    # TO_HIT=100, RESISTANCE=50
    received = target.get(action.verb)
    assert received > 0.7 * expected, \
        "{target} took {recived}/{delivered} stacks"
    assert received < 1.3 * expected, \
        "{target} took {recived}/{delivered} stacks"
    print(f"{target} took {received}/{delivered} stacks"
          f" (vs {int(expected)} expected)")

    print()
    return (2, 2)


def main():
    """
    Run all unit-test cases and print out summary of results
    """
    (t_1, p_1) = simple_attack_tests()
    (t_2, p_2) = sub_attack_tests()
    (t_3, p_3) = random_attack_tests()
    (t_4, p_4) = simple_condition_tests()
    (t_5, p_5) = sub_condition_tests()
    (t_6, p_6) = random_condition_tests()
    tried = t_1 + t_2 + t_3 + t_4 + t_5 + t_6
    passed = p_1 + p_2 + p_3 + p_4 + p_5 + p_6
    if tried == passed:
        print(f"Passed all {passed} GameActor tests")
    else:
        missed = tried - passed
        print(f"FAILED {missed}/{tried} GameActor tests")


if __name__ == "__main__":
    main()
