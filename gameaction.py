#!/usr/bin/python3
""" This module implements the GameAction class """
from dice import Dice
from base import Base


class GameAction(Base):
    """
    Every GameActor has, at any given time, a list of possible actions
    from which they can choose.  Some of these possibilities may be
    intrinsic in the actor, while others are made possible by GameObjects
    (e.g. a weapon), by other actors (e.g. interaction) or a GameContext
    (e.g. searching a room).

    A GameAction is an action possibility that has been associated with
    a GameActor.  It has attributes that describe and quantify its effects.
    When the GameAction's C{act()} method is called, it computes probabilities
    and strengths (based on attributes of the actor and enabling artifact)
    and calls the target's C{accept_action()} handler, which will determine
    and return the results.

    @ivar attributes: (dict) of <name,value> pairs
    @ivar source: (GameObject) that delivers this action
    @ivar verb: (string) simple or sub-classed name(s)

    verbs may be simple or sub-classed (with subtypes):
        -   SEARCH
        -   VERBAL.INTIMMIDATE
        -   ATTACK.STAB

    attributes to be set by client after instantiation:
        - ATTACK verbs are expected to have ACCURACY (to-hit percentage) and
          DAMAGE (dice formula) attributes.
        - non-ATTACK verbs are expected to have POWER (to-hit percentage) and
          STACKS (dice formulat for instances to attempt/deliver) attributes.

    A verb can also be a plus-separated concatenation of simple and/or
    sub-classed verbs.  If a passed verb contains multiple (plus-separated)
    terms, the ACCURACY, DAMAGE, POWER, and STACKS attributes are each assumed
    to be comma-separated lists with the same number of terms.

    Example:
        - verb="ATTACK.STAB+ATTACK.POISON"
        - ACCURACY=60,40
        - DAMAGE=D6,3D4

    If there are multiple verbs but only a single value, that single value
    should be used for each verb.
    """
    def __init__(self, source, verb):
        """
        create a new C{GameAction}
        @param source: (GameObject) instrument for the action
        @param verb: (string) the name of the action(s)
        """
        super().__init__(verb)
        self.source = source
        self.verb = verb
        self.attributes = {}

        # non-attacks automatically have STACKS=1
        if "ATTACK" not in verb:
            self.set("STACKS", "1")

    def __str__(self):
        """
        return a string representation of our verb and its attributes
        """
        if "ATTACK" in self.verb:
            return (f"{self.verb} (ACCURACY={self.get('ACCURACY')}%"
                    f", DAMAGE={self.get('DAMAGE')})")
        return (f"{self.verb} (POWER={self.get('POWER')}%"
                f", STACKS={self.get('STACKS')})")

    # pylint: disable=too-many-locals; I claim I need them all
    def act(self, initiator, target, context):
        """
        Initiate an action against a target

        If the verb is a concatenation (list of simple/sub-classed verbs),
        split it and process each action separately (stopping if one of
        them fails).

        This (base-class) C{act()} method knows how to process (a list of)
        simple or sub-typed verbs that are simply a matter of looking up
        initiator bonus values, adding them up, and calling the target's
        C{accept_action()} handler, passing:
            - the C{GameAction} (with all of its attributes)
            - the initiating C{GameActor}
            - the C{GameContext} in which this is taking place

        When the target is called, the C{GameAction} attributes will
        include (for ATTACK verbs):
            - C{TO_HIT}: 100 + sum of action's and actor's C{ACCURACY}
            - C{DAMAGE}: sum of rolls against actions's and actor's C{DAMAGE}
        for non-attack verbs:
            - C{TO_HIT}: 100 + the action's and initiator's C{POWER}
            - C{STACKS}: sum of rolls against actions's & initiator's C{STACKS}

        Actions that require more complex processing (before
        calling the target) must be implemented (by additional
        code in a sub-class that extends this method (at least
        for the verbs in question)

        @param initiator: (GameActor) initiating the action
        @param target: (GameObject) target of the action
        @param context: (GameContext) in which this is happening
        @return: (string) description of the results (returned from the target)

        """
        # split verb into a list of individual plus-separated verbs
        verbs = self.verb.split('+') if '+' in self.verb else [self.verb]
        # split the ACCURACY, DAMAGE, POWER and STACKS into corresponding lists
        accuracies = self.__get_list("ACCURACY", len(verbs))
        damages = self.__get_list("DAMAGE", len(verbs))
        powers = self.__get_list("POWER", len(verbs))
        stacks = self.__get_list("STACKS", len(verbs))

        # carry out each of the verbs in the list
        results = ""
        attacks = 0
        conditions = 0
        for verb in verbs:
            # gather the verb and associated base/initiator attributes
            self.verb = verb
            if "ATTACK" in verb:
                self.set("TO_HIT", 100 +
                         compute_accuracy(verb, accuracies[attacks],
                                          initiator))
                self.set("HIT_POINTS",
                         compute_damage(verb, damages[attacks], initiator))
                attacks += 1
            else:
                self.set("TO_HIT", 100 +
                         compute_power(verb, powers[conditions], initiator))
                self.set("TOTAL",
                         compute_stacks(verb, stacks[conditions], initiator))
                conditions += 1
            # pass them on to target, and accumulate results
            (success, result) = target.accept_action(self, initiator, context)
            if results == "":
                results = result
            else:
                results += "\n" + result
            # immediately return false if any action fails
            if not success:
                return (False, results)

        return (True, results)

    def __get_list(self, name, size):
        """
        read specified attribute, lex its (comma-separated) values into a list

        @param name: (string) name of attribute to be looked up and split
        @param size: (int) length of desired list
        @return: (list of strings)
            - if no value is found, a list of Nones will be returned
            - if there is only single value, it will be replicated the
              specified number of times
        """
        atr = self.get(name)
        if atr is None:
            return [None] * size
        if not isinstance(atr, str):
            return [atr] * size
        if ',' not in atr:
            return [atr] * size
        return atr.split(',')


def compute_accuracy(verb, base, initiator):
    """
    helper to compute accuracy of this attack, based on the supplied
    base ACCURACY plus any initiator ACCURACY(.subtype) bonus(es).

    @param verb: (string) attack verb
    @param base: (int) accuracy (from the action)
    @param initiator: (GameActor) who is initiating the attack
    @return: (int) probability of hitting
    """
    # get base accuracy from the action
    if base is None:
        w_accuracy = 0
    else:
        w_accuracy = int(base)

    # get the initiator base accuracy
    acc = initiator.get("ACCURACY")
    if acc is None:
        i_accuracy = 0
    else:
        i_accuracy = int(acc)

    # add any initiator sub-type accuracy
    if 'ATTACK.' in verb:
        sub_type = verb.split('.')[1]
        if sub_type is not None:
            acc = initiator.get("ACCURACY." + sub_type)
            if acc is not None:
                i_accuracy += int(acc)

    return w_accuracy + i_accuracy


def compute_damage(verb, base, initiator):
    """
    helper to compute the damage of this attack, based on the supplied
    base DAMAGE plus any initiator DAMAGE(.subtype) bonus(es).

    @param verb: (string) attack verb
    @param base: (string) dice formula for base damage
    @param initiator: (GameActor) who is initiating the attack
    @return: (int) total damage
    """
    # get the basic action damage formula and roll it
    if base is None:
        w_damage = 0
    else:
        dice = Dice(base)
        w_damage = dice.roll()

    # get initiator base damage formula and roll it
    dmg = initiator.get("DAMAGE")
    if dmg is None:
        i_damage = 0
    else:
        dice = Dice(dmg)
        i_damage = dice.roll()

    # add any initiator sub-type damage
    if 'ATTACK.' in verb:
        sub_type = verb.split('.')[1]
        if sub_type is not None:
            dmg = initiator.get("DAMAGE." + sub_type)
            if dmg is not None:
                dice = Dice(dmg)
                i_damage += dice.roll()

    return w_damage + i_damage


def compute_power(verb, base, initiator):
    """
    helper to compute the power of this action, based on the supplied
    base POWER plus any initiator POWER.verb/POWER.verb.subtype bonuses

    @param verb: (string) action verb
    @param base: (int) base power (from action)
    @param initiator: (GameActor) who is sending the condition
    @return: (int) total probability of hitting
    """
    # figure out the condition type and subtype
    if '.' in verb:
        base_type = verb.split('.')[0]
        sub_type = verb.split('.')[1]
    else:
        base_type = verb
        sub_type = None

    # get base power from the action
    if base is None:
        power = 0
    else:
        power = int(base)

    # add the initiator base power
    pwr = initiator.get("POWER." + base_type)
    if pwr is not None:
        power += int(pwr)

    # add any initiator sub-type power
    if sub_type is not None:
        pwr = initiator.get("POWER." + base_type + '.' + sub_type)
        if pwr is not None:
            power += int(pwr)

    return power


def compute_stacks(verb, base, initiator):
    """
    helper to compute the stacks of this action, based on the supplied
    base STACKS plus any initiator STACKS.verb/STACKS.verb.subtype bonuses

    @param verb: (string) action verb
    @param base: (string) dice formula for base stacks
    @param initiator: (GameActor) who is sending the condition
    @return: (int) total number of stacks
    """
    # figure out the condition type and subtype
    if '.' in verb:
        base_type = verb.split('.')[0]
        sub_type = verb.split('.')[1]
    else:
        base_type = verb
        sub_type = None

    # get base stacks from the action
    if base is None:
        stacks = 1
    else:
        dice = Dice(base)
        stacks = dice.roll()

    # add the initiator base stacks
    stx = initiator.get("STACKS." + base_type)
    if stx is not None:
        dice = Dice(stx)
        stacks += dice.roll()

    # add any initiator sub-type stacks
    if sub_type is not None:
        stx = initiator.get("STACKS." + base_type + '.' + sub_type)
        if stx is not None:
            dice = Dice(stx)
            stacks += dice.roll()

    return stacks


# UNIT TESTING
class TestRecipient(Base):
    """
    a minimal object that can receive, and report on actions

    The returned result string will include the passed TO_HIT and POWER/STACKS
    attributes so that the test case can confirm that they were properly
    computed and passed.
    """

    def accept_action(self, action, actor, context):
        """
        report on the action we received

        @param action: GameAction being sent
        @param actor: GameActor who set it
        @param context: GameContext in which this happened
        @return (boolean success, string results)
        """
        if "ATTACK" in action.verb:
            return (True,
                    f"{self} receives {action.verb}"
                    f" (TO_HIT={action.get('TO_HIT')}"
                    f", DAMAGE={action.get('HIT_POINTS')})"
                    f"from {actor} in {context}")
        result = "resists" if action.verb == "FAIL" else "receives"
        return (action.verb != "FAIL",
                f"{self} {result} {action.verb}"
                f" (TO_HIT={action.get('TO_HIT')},"
                f" STACKS={action.get('TOTAL')})"
                f" from {actor} in {context}")


# pylint: disable=too-many-locals; I claim I need them all
def base_attacks():
    """
    GameAction base ability ATTACK test cases:
        - test correctness of TO_HIT and DAMAGE computations
          for base and sub-type attacks
          but with no sub-type or initiator bonuses
    """

    # create a victim and context
    victim = TestRecipient("victim")
    context = Base("unit-test")

    # create an artifact with actions
    artifact = Base("test-case")

    # test attacks from an un-skilled attacker (base values)
    lame = Base("lame attacker")        # attacker w/no skills
    lame_attacks = [
        # verb,       accuracy, damage, exp hit, exp dmg
        ("ATTACK",        None,    "1",     100,       1),
        ("ATTACK.ten",      10,   "10",     110,      10),
        ("ATTACK.twenty",   20,   "20",     120,      20),
        ("ATTACK.thirty",   30,   "30",     130,      30)]

    tried = 0
    passed = 0
    for (verb, accuracy, damage, exp_hit, exp_dmg) in lame_attacks:
        action = GameAction(artifact, verb)
        if accuracy is not None:
            action.set("ACCURACY", accuracy)
        action.set("DAMAGE", damage)
        (_, result) = action.act(lame, victim, context)

        # see if the action contained the expected values
        to_hit = action.get("TO_HIT")
        hit_points = action.get("HIT_POINTS")
        tried += 3
        if action.verb == verb and to_hit == exp_hit and hit_points == exp_dmg:
            print(result + " ... CORRECT")
            passed += 3
        else:
            print(result)
            assert action.verb == verb, \
                "incorrect action verb: expected " + verb
            passed += 1
            assert action.get("TO_HIT") == exp_hit, \
                "incorrect base accuracy: expected " + str(exp_hit)
            passed += 1
            assert action.get("HIT_POINTS") == exp_dmg, \
                "incorrect base damage: expected " + str(exp_dmg)
            passed += 1

    print()
    return (tried, passed)


# pylint: disable=too-many-locals; I claim I need them all
def subtype_attacks():
    """
    GameAction sub-type ability ATTACK test cases:
        - test correctness of TO_HIT and DAMAGE computations
          for base and sub-type attacks
          both action and initiator have both base and sub-type bonuses
    """

    # create a victim and context
    victim = TestRecipient("victim")
    context = Base("unit-test")

    # create an artifact with actions
    artifact = Base("test-case")

    # test attacks from a skilled attacker, w/bonus values
    skilled = Base("skilled attacker")  # attacker w/many skills
    skilled.set("ACCURACY", 10)
    skilled.set("DAMAGE", "10")
    skilled.set("ACCURACY.twenty", 20)
    skilled.set("DAMAGE.twenty", "20")
    skilled.set("ACCURACY.thirty", 30)
    skilled.set("DAMAGE.thirty", "30")

    skilled_attacks = [
        # verb,       accuracy, damage, exp hit, exp dmg
        ("ATTACK",        None,    "1",     110,      11),
        ("ATTACK.ten",      10,   "10",     120,      20),
        ("ATTACK.twenty",   20,   "20",     150,      50),
        ("ATTACK.thirty",   30,   "30",     170,      70)]

    tried = 0
    passed = 0
    for (verb, accuracy, damage, exp_hit, exp_dmg) in skilled_attacks:
        action = GameAction(artifact, verb)
        if accuracy is not None:
            action.set("ACCURACY", accuracy)
        action.set("DAMAGE", damage)
        (_, result) = action.act(skilled, victim, context)

        # see if the action contained the expected values
        tried += 3
        to_hit = action.get("TO_HIT")
        hit_points = action.get("HIT_POINTS")
        if action.verb == verb and to_hit == exp_hit and hit_points == exp_dmg:
            print(result + " ... CORRECT")
            passed += 3
        else:
            print(result)
            assert action.verb == verb, \
                "incorrect action verb: expected " + verb
            passed += 1
            assert action.get("TO_HIT") == exp_hit, \
                "incorrect base accuracy: expected " + str(exp_hit)
            passed += 1
            assert action.get("HIT_POINTS") == exp_dmg, \
                "incorrect base damage: expected " + str(exp_dmg)
            passed += 1
    print()
    return (tried, passed)


# pylint: disable=too-many-locals; I claim I need them all
def base_conditions():
    """
    GameAction base ability condition test cases:
        - test correctness of TO_HIT and STACKS computations
          for base and sub-type verbs
          but with no sub-type or initiator bonuses
    """

    # create a victim and context
    victim = TestRecipient("victim")
    context = Base("unit-test")

    # create an artifact with actions
    artifact = Base("test-case")

    # test attacks from an un-skilled attacker (base values)
    lame = Base("unskilled sender")      # sender w/no skills
    lame_attacks = [
        # verb,       power, stacks, exp hit, exp stx
        ("MENTAL",     None,    "1",     100,       1),
        ("MENTAL.X",     10,   "10",     110,      10),
        ("MENTAL.Y",     20,   "20",     120,      20),
        ("MENTAL.Z",     30,   "30",     130,      30)]

    tried = 0
    passed = 0
    for (verb, power, stacks, exp_hit, exp_stx) in lame_attacks:
        action = GameAction(artifact, verb)
        if power is not None:
            action.set("POWER", power)
        action.set("STACKS", stacks)
        (_, result) = action.act(lame, victim, context)

        # see if the action contained the expected values
        tried += 3
        to_hit = action.get("TO_HIT")
        stacks = action.get("TOTAL")
        if action.verb == verb and to_hit == exp_hit and stacks == exp_stx:
            print(result + " ... CORRECT")
            passed += 3
        else:
            print(result)
            assert action.verb == verb, \
                "incorrect action verb: expected " + verb
            passed += 1
            assert action.get("TO_HIT") == exp_hit, \
                "incorrect base accuracy: expected " + str(exp_hit)
            passed += 1
            assert action.get("TOTAL") == exp_stx, \
                "incorrect base stacks: expected " + str(exp_stx)
            passed += 1
    print()
    return (tried, passed)


# pylint: disable=too-many-locals; I claim I need them all
def subtype_conditions():
    """
    GameAction sub-type ability condition test cases:
        - test correctness of TO_HIT and STACKS computations
          for base and sub-type verbs
          both action and initiator have both base and sub-type bonuses
    """

    # create a victim and context
    victim = TestRecipient("victim")
    context = Base("unit-test")

    # create an artifact with actions
    artifact = Base("test-case")

    # test attacks from a skilled attacker, w/bonus values
    skilled = Base("skilled sender")  # sender w/many skills
    skilled.set("POWER.MENTAL", 10)
    skilled.set("STACKS.MENTAL", "10")
    skilled.set("POWER.MENTAL.Y", 20)
    skilled.set("STACKS.MENTAL.Y", "20")
    skilled.set("POWER.MENTAL.Z", 30)
    skilled.set("STACKS.MENTAL.Z", "30")

    skilled_attacks = [
        # verb,       power, stacks, exp hit, exp stx
        ("MENTAL",     None,    "1",     110,      11),
        ("MENTAL.X",     10,   "10",     120,      20),
        ("MENTAL.Y",     20,   "20",     150,      50),
        ("MENTAL.Z",     30,   "30",     170,      70)]

    tried = 0
    passed = 0
    for (verb, power, stacks, exp_hit, exp_stx) in skilled_attacks:
        action = GameAction(artifact, verb)
        if power is not None:
            action.set("POWER", power)
        action.set("STACKS", stacks)
        (_, result) = action.act(skilled, victim, context)

        # see if the action contained the expected values
        tried += 3
        to_hit = action.get("TO_HIT")
        stacks = action.get("TOTAL")
        if action.verb == verb and to_hit == exp_hit and stacks == exp_stx:
            print(result + " ... CORRECT")
            passed += 3
        else:
            print(result)
            assert action.verb == verb, \
                "incorrect action verb: expected " + verb
            passed += 1
            assert action.get("TO_HIT") == exp_hit, \
                "incorrect base accuracy: expected " + str(exp_hit)
            passed += 1
            assert action.get("TOTAL") == exp_stx, \
                "incorrect base stacks: expected " + str(exp_stx)
            passed += 1
    print()
    return (tried, passed)


def compound_verbs():
    """
    GameAction compound-verb test cases:
      - recognition and handling of compound verbs
      - correct association with ACCURACY, DAMAGE, POWER and STACKS lists
      - stopping list processing on first action that fails
    """
    context = Base("unit-test")
    artifact = Base("test-case")
    victim = TestRecipient("victim")
    lame = Base("unskilled sender")      # sender w/no skills

    verbs = "ATTACK.one+MENTAL.two+ATTACK.three+PHYSICAL.four+VERBAL.five" + \
            "+FAIL+WONT-HAPPEN"
    action = GameAction(artifact, verbs)
    action.set("ACCURACY", "1,3")
    action.set("DAMAGE", "10,30")
    action.set("POWER", "2,4,5,0")
    action.set("STACKS", "2,4,5,0")

    print("Compound verb: " + verbs)
    for attr in ["ACCURACY", "DAMAGE", "POWER", "STACKS"]:
        print("    " + attr + ":\t" + action.get(attr))

    (success, results) = action.act(lame, victim, context)
    print(results)
    assert "ATTACK.one (TO_HIT=101, DAMAGE=10)" in results, \
        "ATTACK.one was not correctly passed"
    assert "two (TO_HIT=102, STACKS=2)" in results, \
        "MENTAL.two was not correctly passed"
    assert "ATTACK.three (TO_HIT=103, DAMAGE=30)" in results, \
        "ATTACK.three was not correctly passed"
    assert "four (TO_HIT=104, STACKS=4)" in results, \
        "PHYSICAL.four was not correctly passed"
    assert "five (TO_HIT=105, STACKS=5)" in results, \
        "VERBAL.five was not correctly passed"
    assert "resists FAIL" in results, \
        "sixth (FAIL) condition was not correctly passed"
    assert not success, \
        "sixth (FAIL) condition did not cause action to fail"
    assert "WONT-HAPPEN" not in results, \
        "seventh (WONT-HAPPEN) action should not have been sent"

    print()
    return (8, 8)


def main():
    """
    Run all unit-test cases and print out summary of results
    """
    (t_1, p_1) = base_attacks()
    (t_2, p_2) = subtype_attacks()
    (t_3, p_3) = base_conditions()
    (t_4, p_4) = subtype_conditions()
    (t_5, p_5) = compound_verbs()
    tried = t_1 + t_2 + t_3 + t_4 + t_5
    passed = p_1 + p_2 + p_3 + p_4 + p_5
    if tried == passed:
        print(f"Passed all {passed} GameAction tests")
    else:
        missed = tried - passed
        print(f"FAILED {missed}/{tried} GameAction tests")


if __name__ == "__main__":
    main()
