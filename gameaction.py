""" This module implements the GameAction class """
from dice import Dice
from base import Base


# pylint: disable=no-self-use;   these are still appropriately class-private
class GameAction(Base):
    """
    A GameAction is an action possibility that is available to a GameActor.
    It has attributes that control its effects, and when its act() method
    is called, it delivers that action to the intended target.

    The most interetsting method is act(initiator, target, context)
    which informs the target to process the effects of the action.
    """
    def __init__(self, source, verb):
        """
        create a new GameAction
        @param source: GameObject instrument for the action
        @param verb: the name of the action
        """
        super(GameAction, self).__init__(verb)
        self.source = source
        self.verb = verb
        self.attributes = {}

        # non-attacks automatically have STACKS=1
        if "ATTACK" not in verb:
            self.set("STACKS", "1")

    def __str__(self):
        """
        return a string representation of this action
        """
        if "ATTACK" in self.verb:
            return "{} (ACCURACY={}%, DAMAGE={})".\
                format(self.verb, self.get("ACCURACY"), self.get("DAMAGE"))
        return "{} (POWER={}%, STACKS={})".\
            format(self.verb, self.get("POWER"), self.get("STACKS"))

    def accuracy(self, verb, base, initiator):
        """
        Compute the accuracy of this attack
        @param verb: attack verb
        @param base: accuracy (from the action)
        @param initator: GameActor who is initiating the attack
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

    def damage(self, verb, base, initiator):
        """
        compute the damage from this attack
        @param verb: attack verb
        @param base: base damage (from action)
        @param initator: GameActor who is initiating the attack
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

    def power(self, verb, base, initiator):
        """
        Compute the power with which this condition is being sent
        @param verb: action verb
        @param base: base power (from action)
        @param initator: GameActor who is sending the condition
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

        # add any initiator sub-type accuracy
        if sub_type is not None:
            pwr = initiator.get("POWER." + base_type + '.' + sub_type)
            if pwr is not None:
                power += int(pwr)

        return power

    def stacks(self, verb, base, initiator):
        """
        Compute the number of stacks to be sent
        @param verb: action verb
        @param base: base power (from action)
        @param initator: GameActor who is sending the condition
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
            stacks = 0
        else:
            dice = Dice(base)
            stacks = dice.roll()

        # add the initiator base power
        stx = initiator.get("STACKS." + base_type)
        if stx is not None:
            dice = Dice(stx)
            stacks += dice.roll()

        # add any initiator sub-type accuracy
        if sub_type is not None:
            stx = initiator.get("STACKS." + base_type + '.' + sub_type)
            if stx is not None:
                dice = Dice(stx)
                stacks += dice.roll()

        return stacks

    # pylint: disable=too-many-locals; I claim I need them all
    def act(self, initiator, target, context):
        """
        Initiate an action against a target
        @param initiator: GameActor initiating the action
        @param target: GameObject target of the action
        @param context: GameContext in which this is happening
        @return: (string) result of the action

        This (base-class) act() method knows how to process
        single (or compound) attacks and condition deliveries
        that are simply a matter of looking up initiator bonus
        values, adding them up, and calling the target's
        accept_action handler.

        Actions that require more complex processing (before
        calling the target) must be implemented (by additional
        code in a sub-class that extends this method (at least
        for the verbs in question)
        """
        # pick up the verb(s) and associated attributes
        verbs = self.verb.split(',') if ',' in self.verb else [self.verb]
        accuracies = self.get_list("ACCURACY", len(verbs))
        damages = self.get_list("DAMAGE", len(verbs))
        powers = self.get_list("POWER", len(verbs))
        stacks = self.get_list("STACKS", len(verbs))

        # carry out each of the verbs
        results = ""
        attacks = 0
        conditions = 0
        for verb in verbs:
            # gather the verb and base/initiator attributes
            self.verb = verb
            if "ATTACK" in verb:
                self.set("TO_HIT", 100 +
                         self.accuracy(verb, accuracies[attacks], initiator))
                self.set("HIT_POINTS",
                         self.damage(verb, damages[attacks], initiator))
                attacks += 1
            else:
                self.set("TO_HIT", 100 +
                         self.power(verb, powers[conditions], initiator))
                self.set("TOTAL",
                         self.stacks(verb, stacks[conditions], initiator))
                conditions += 1
            # pass them on to target, and accumulate results
            (success, result) = target.accept_action(self, initiator, context)
            if results == "":
                results = result
            else:
                results += "\n" + result
            if not success:
                return (False, results)

        return (True, results)

    def get_list(self, name, size):
        """
        read specified attribute, parse into a list
        @param name: name of desired attribute
        @param size: number of desired list elements
        @return list of elements
        """
        atr = self.get(name)
        if atr is None:
            return [None] * size
        if not isinstance(atr, str):
            return [atr] * size
        if ',' not in atr:
            return [atr] * size
        return atr.split(',')


class TestRecipient(Base):
    """
    a minimal object that can receive, and report on actions
    """

    def accept_action(self, action, actor, context):
        """
        report on the action we received
        @param action: GameAction being sent
        @param actor: GameActor who set it
        @param context: GameContext in which this happened
        """
        if "ATTACK" in action.verb:
            return (True,
                    "{} receives {} (TO_HIT={}, DAMAGE={}) from {} in {}".
                    format(self, action.verb,
                           action.get("TO_HIT"), action.get("HIT_POINTS"),
                           actor, context))
        result = "resists" if action.verb == "FAIL" else "receives"
        return (action.verb != "FAIL",
                "{} {} {} (TO_HIT={}, STACKS={}) from {} in {}".
                format(self, result, action.verb,
                       action.get("TO_HIT"), action.get("TOTAL"),
                       actor, context))


def base_attacks():
    """
    GameAction test cases:
      TO_HIT and DAMAGE computations for base ATTACKs
    """

    # create a victim and context
    victim = TestRecipient("victim")
    context = Base("unit-test")

    # create an artifact with actions
    artifact = Base("test-case")

    # test attacks from an un-skilled attacker (base values)
    lame = Base("lame attacker")        # attacker w/no skills
    # pylint: disable=bad-whitespace
    lame_attacks = [
        # verb,       accuracy, damage, exp hit, exp dmg
        ("ATTACK",        None,    "1",     100,       1),
        ("ATTACK.ten",      10,   "10",     110,      10),
        ("ATTACK.twenty",   20,   "20",     120,      20),
        ("ATTACK.thirty",   30,   "30",     130,      30)]

    for (verb, accuracy, damage, exp_hit, exp_dmg) in lame_attacks:
        action = GameAction(artifact, verb)
        if accuracy is not None:
            action.set("ACCURACY", accuracy)
        action.set("DAMAGE", damage)
        (_, result) = action.act(lame, victim, context)

        # see if the action contained the expected values
        to_hit = action.get("TO_HIT")
        hit_points = action.get("HIT_POINTS")
        if action.verb == verb and to_hit == exp_hit and hit_points == exp_dmg:
            print(result + " ... CORRECT")
        else:
            print(result)
            assert action.verb == verb, \
                "incorrect action verb: expected " + verb
            assert action.get("TO_HIT") == exp_hit, \
                "incorrect base accuracy: expected " + str(exp_hit)
            assert action.get("HIT_POINTS") == exp_dmg, \
                "incorrect base damage: expected " + str(exp_dmg)

    print()


def subtype_attacks():
    """
    GameAction test cases:
      TO_HIT and DAMAGE computations for sub-type attacks
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

    # pylint: disable=bad-whitespace
    skilled_attacks = [
        # verb,       accuracy, damage, exp hit, exp dmg
        ("ATTACK",        None,    "1",     110,      11),
        ("ATTACK.ten",      10,   "10",     120,      20),
        ("ATTACK.twenty",   20,   "20",     150,      50),
        ("ATTACK.thirty",   30,   "30",     170,      70)]

    for (verb, accuracy, damage, exp_hit, exp_dmg) in skilled_attacks:
        action = GameAction(artifact, verb)
        if accuracy is not None:
            action.set("ACCURACY", accuracy)
        action.set("DAMAGE", damage)
        (_, result) = action.act(skilled, victim, context)

        # see if the action contained the expected values
        to_hit = action.get("TO_HIT")
        hit_points = action.get("HIT_POINTS")
        if action.verb == verb and to_hit == exp_hit and hit_points == exp_dmg:
            print(result + " ... CORRECT")
        else:
            print(result)
            assert action.verb == verb, \
                "incorrect action verb: expected " + verb
            assert action.get("TO_HIT") == exp_hit, \
                "incorrect base accuracy: expected " + str(exp_hit)
            assert action.get("HIT_POINTS") == exp_dmg, \
                "incorrect base damage: expected " + str(exp_dmg)
    print()


def base_conditions():
    """
    GameAction test cases:
      TO_HIT and STACKS computations for base CONDITIONS
    """

    # create a victim and context
    victim = TestRecipient("victim")
    context = Base("unit-test")

    # create an artifact with actions
    artifact = Base("test-case")

    # test attacks from an un-skilled attacker (base values)
    lame = Base("unskilled sender")      # sender w/no skills
    # pylint: disable=bad-whitespace
    lame_attacks = [
        # verb,       power, stacks, exp hit, exp stx
        ("MENTAL",     None,    "1",     100,       1),
        ("MENTAL.X",     10,   "10",     110,      10),
        ("MENTAL.Y",     20,   "20",     120,      20),
        ("MENTAL.Z",     30,   "30",     130,      30)]

    for (verb, power, stacks, exp_hit, exp_stx) in lame_attacks:
        action = GameAction(artifact, verb)
        if power is not None:
            action.set("POWER", power)
        action.set("STACKS", stacks)
        (_, result) = action.act(lame, victim, context)

        # see if the action contained the expected values
        to_hit = action.get("TO_HIT")
        stacks = action.get("TOTAL")
        if action.verb == verb and to_hit == exp_hit and stacks == exp_stx:
            print(result + " ... CORRECT")
        else:
            print(result)
            assert action.verb == verb, \
                "incorrect action verb: expected " + verb
            assert action.get("TO_HIT") == exp_hit, \
                "incorrect base accuracy: expected " + str(exp_hit)
            assert action.get("TOTAL") == exp_stx, \
                "incorrect base stacks: expected " + str(exp_stx)
    print()


def subtype_conditions():
    """
    GameAction test cases:
      TO_HIT and TOTAL computations for sub-type attacks
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

    # pylint: disable=bad-whitespace
    skilled_attacks = [
        # verb,       power, stacks, exp hit, exp stx
        ("MENTAL",     None,    "1",     110,      11),
        ("MENTAL.X",     10,   "10",     120,      20),
        ("MENTAL.Y",     20,   "20",     150,      50),
        ("MENTAL.Z",     30,   "30",     170,      70)]

    for (verb, power, stacks, exp_hit, exp_stx) in skilled_attacks:
        action = GameAction(artifact, verb)
        if power is not None:
            action.set("POWER", power)
        action.set("STACKS", stacks)
        (_, result) = action.act(skilled, victim, context)

        # see if the action contained the expected values
        to_hit = action.get("TO_HIT")
        stacks = action.get("TOTAL")
        if action.verb == verb and to_hit == exp_hit and stacks == exp_stx:
            print(result + " ... CORRECT")
        else:
            print(result)
            assert action.verb == verb, \
                "incorrect action verb: expected " + verb
            assert action.get("TO_HIT") == exp_hit, \
                "incorrect base accuracy: expected " + str(exp_hit)
            assert action.get("TOTAL") == exp_stx, \
                "incorrect base stacks: expected " + str(exp_stx)
    print()


def compound_verbs():
    """
    GameAction test cases:
      recognition of compound verbs
      and correct matching of list attributes to each
    """
    context = Base("unit-test")
    artifact = Base("test-case")
    victim = TestRecipient("victim")
    lame = Base("unskilled sender")      # sender w/no skills

    verbs = "ATTACK.one,MENTAL.two,ATTACK.three,PHYSICAL.four,VERBAL.five" + \
            ",FAIL,WONT-HAPPEN"
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


if __name__ == "__main__":
    base_attacks()
    subtype_attacks()
    base_conditions()
    subtype_conditions()
    compound_verbs()
    print("All GameAction test cases passed")
