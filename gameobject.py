""" This module implements the (foundation) GameObject Class """
import sys
from random import randint
from base import Base
from gameaction import GameAction


class GameObject(Base):
    """
    This is the base class for all objects and actors.
    Its only abilities are
        - to own objects
        - to offer and accept actions.
    """
    def __init__(self, name="actor", descr=None):
        """
        create a new GameObject
        @param name: display name of this object
        @param descr: human description of this object
        """
        super(GameObject, self).__init__(name, descr)
        self.objects = []

    def __str__(self):
        """
        return string description of this weapon
        """
        return self.name

    def get_objects(self, hidden=False):
        """
        @param hidden: hidden (rather than obvious) objects
        @return: list of GameOjects in this context
        """
        reported = []
        for thing in self.objects:
            atr = thing.get("RESISTANCE.SEARCH")
            concealed = atr is not None and atr > 0
            atr = thing.get("SEARCH")
            found = atr is not None and atr > 0

            if hidden:
                if concealed and not found:
                    reported.append(thing)
            else:
                if found or not concealed:
                    reported.append(thing)

        return reported

    def get_object(self, name):
        """
        return a named object from my inventory
        @param name: string to match against object name
        @return: first matching object (or None)
        """
        for thing in self.objects:
            if name in thing.name:
                return thing
        return None

    def add_object(self, item):
        """
        add another object to this context
        """
        if item not in self.objects:
            self.objects.append(item)

    # pylint: disable=too-many-locals
    def accept_action(self, action, actor, context):
        """
        receive and process the effects of an action

        @param action: GameAction being performed
        @param actor: GameActor initiating the action
        @param context: GameContext in which action is occuring
        @return: (boolean success, string description of the effect)
        """
        # get the base verb and sub-type
        if '.' in action.verb:
            base_verb = action.verb.split('.')[0]
            sub_type = action.verb.split('.')[1]
        else:
            base_verb = action.verb
            sub_type = None

        # check our base resistance
        res = self.get("RESISTANCE")
        resistance = 0 if res is None else int(res)

        # see if we have a base-type resistance
        res = self.get("RESISTANCE." + base_verb)
        if res is not None:
            resistance += int(res)

        # see if we have a sube-type resistance
        if sub_type is not None:
            res = self.get("RESISTANCE." + base_verb + "." + sub_type)
            if res is not None:
                resistance += int(res)

        # see if we can resist it entirely
        power = int(action.get("TO_HIT")) - resistance
        if power <= 0:
            return (False, "{} resists {} {}"
                    .format(self.name, action.source.name, action.verb))

        # see how many stacks we can resist
        incoming = abs(int(action.get("TOTAL")))
        received = 0
        for _ in range(incoming):
            roll = randint(1, 100)
            if roll <= power:
                received += 1

        # deliver the updated condition
        sign = 1 if int(action.get("TOTAL")) > 0 else -1
        if received > 0:
            have = self.get(action.verb)
            have = 0 if have is None else int(have)
            # special case: LIFE cannot be raised beyond HP
            if action.verb == "LIFE" and self.get("HP") is not None:
                max_hp = int(self.get("HP"))
                if have + sign * received > max_hp:
                    have = max_hp - received
            self.set(action.verb, have + sign * received)

        return (received > 0,
                "{} resists {}/{} stacks of {} from {} in {}"
                .format(self.name, incoming - received, incoming,
                        action.verb if sign > 0
                        else "(negative) " + action.verb,
                        actor, context))

    # pylint: disable=unused-argument; sub-classes are likely to use them
    # pylint: disable=too-many-branches; there are a lot of cases
    # pylint: disable=too-many-statements; there are a lot of cases
    def possible_actions(self, actor, context):
        """
        receive and process the effects of an action

        @param actor: GameActor initiating the action
        @param context: GameContext in which the action is taken
        @return: list of possible GameActions

        PROBLEM:
        Base and sub-type ACCURACY values add, as they should.
        This is harder to do with DAMAGE because those are not
        (easily added) values, but dice formulae.  For now,
        we simply use the sub-type value if present, else the
        base value.
        """
        # get a list of possible actions with this weapon
        actions = []
        verbs = self.get("ACTIONS")
        if verbs is None:
            return []

        # get our base accuracy/damage/power/stacks
        base_accuracy = self.get("ACCURACY")
        base_damage = self.get("DAMAGE")
        base_power = self.get("POWER")
        base_stacks = self.get("STACKS")

        # instantiate a GameAction for each verb in our ACTIONS list
        for compound_verb in verbs.split(','):
            action = GameAction(self, compound_verb)

            # verbs may be compound, each sub-verb having sub-type attributes
            accuracies = ""
            damages = ""
            powers = ""
            stacks = ""
            for verb in compound_verb.split('+'):
                if verb.startswith("ATTACK"):
                    # see if we have sub-type accuracy/damage
                    sub_accuracy = None
                    sub_damage = None
                    if verb.startswith('ATTACK.'):
                        sub_type = verb.split('.')[1]
                        sub_accuracy = self.get("ACCURACY." + sub_type)
                        sub_damage = self.get("DAMAGE." + sub_type)

                    # combine the base and sub-type values
                    accuracy = 0 if base_accuracy is None \
                        else int(base_accuracy)
                    accuracy += 0 if sub_accuracy is None \
                        else int(sub_accuracy)
                    if accuracies == "":
                        accuracies = str(accuracy)
                    else:
                        accuracies += "," + str(accuracy)

                    # FIX GameAction.DAMAGE could be a (non-addable) D-formula
                    if sub_damage is not None:
                        damage = sub_damage
                    elif base_damage is not None:
                        damage = base_damage
                    else:
                        damage = 0
                    if damages == "":
                        damages = str(damage)
                    else:
                        damages += "," + str(damage)
                else:
                    # see if we have sub-type power/stacks
                    sub_power = self.get("POWER." + verb)
                    power = 0 if base_power is None else int(base_power)
                    power += 0 if sub_power is None else int(sub_power)
                    if powers == "":
                        powers = str(power)
                    else:
                        powers += "," + str(power)

                    # FIX GameAction.STACKS could be a (non-addable) D-formula
                    sub_stacks = self.get("STACKS." + verb)
                    if sub_stacks is not None:
                        stack = sub_stacks
                    elif base_stacks is not None:
                        stack = base_stacks
                    else:
                        stack = 1
                    if stacks == "":
                        stacks = str(stack)
                    else:
                        stacks += "," + str(stack)

                # add the accumulated attributes to the action
                if accuracies != "":
                    action.set("ACCURACY", accuracies)
                if damages != "":
                    action.set("DAMAGE", damages)
                if powers != "":
                    action.set("POWER", powers)
                if stacks != "":
                    action.set("STACKS", stacks)

            actions.append(action)

        return actions

    def load(self, filename):
        """
        read attributes from a file
        @param filename: name of file to be read
        """
        cur_object = self

        try:
            infile = open(filename, "r")
            for line in infile:
                # see if we can lex it into two white-space separated fields
                (name, value) = __lex(line)
                if name is None:
                    continue

                # check for a few special names
                if name == "NAME":
                    cur_object.name = value
                elif name == "DESCRIPTION":
                    cur_object.description = value
                elif name == "OBJECT":
                    cur_object = GameObject()
                    self.add_object(cur_object)
                else:
                    cur_object.set(name, value)

            infile.close()
        except IOError:
            sys.stderr.write("Unable to read attributes from {}\n".
                             format(filename))


def __lex(line):
    """
    try to lex a name and (potentially quoted) value from a line
    @param line: string to be lexed
    @return: (name, value)
    """
    # find the start of the first token
    start = 0
    eol = len(line)
    while start < eol and line[start].isspace():
        start += 1

    # see if this is a comment or blank line
    if start >= eol or line[start] == "#":
        return (None, None)

    # find the end of this token
    end = start + 1
    while end < eol and not line[end].isspace():
        end += 1
    name = line[start:end]

    # find the start of the next token
    start = end
    while start < eol and line[start].isspace():
        start += 1

    # see if there is no next token
    if start >= eol or line[start] == "#":
        return (name, None)

    # does the next token start with a quote
    if line[start] == '"' or line[start] == "'":
        # scan until the closing quote (or EOL)
        quote = line[start]
        start += 1
        end = start + 1
        while end < eol and line[end] != quote:
            end += 1
        value = line[start:end]
    else:
        # scan until a terminating blank (or EOL)
        end = start + 1
        while end < eol and not line[end].isspace():
            end += 1

        # if it is an un-quoted number, convert it
        try:
            value = int(line[start:end])
        except ValueError:
            value = line[start:end]

    return (name, value)


def action_test():
    """
    basic test GameObject test cases
    """

    describe = "simple get/set test object"
    go1 = GameObject("GameObject 1", describe)

    # defaults to no actions
    actions = go1.possible_actions(None, None)
    assert (not actions), \
        "New object returns non-empty action list"

    # added actions are returned
    test_actions = "ACTION,SECOND ACTION"
    go1.set("ACTIONS", test_actions)
    print("Set actions='{}', possible_actions returns:".format(test_actions))
    actions = go1.possible_actions(None, None)
    for action in actions:
        print("    {}".format(action.verb))
    assert (len(actions) == 2), \
        "possible_actions returns wrong number of actions"
    assert (actions[0].verb == "ACTION"), \
        "first action not correctly returned"
    assert (actions[1].verb == "SECOND ACTION"), \
        "second action not correctly returned"


def weapon_test():
    """
    test for weapon actions and damage
    """
    # by default a weapon has no actions or attributes
    w_0 = GameObject("Null Weapon")
    assert w_0.name == "Null Weapon", \
        "Incorrect name: expected w_0"
    assert w_0.get("DAMAGE") is None, \
        "Incorrect default damage: expected None"
    assert w_0.get("ACCURACY") is None, \
        "Incorrect default accuracy, expected None"
    actions = w_0.possible_actions(None, None)
    assert not actions, \
        "incorrect default actions, expected None"
    print("test #1: " + str(w_0) +
          " ... NO ATTACKS, ACCURACY or DAMAGE - CORRECT")

    # if a weapon is created with damage, it has ATTACK
    w_1 = GameObject("Simple Weapon")
    w_1.set("ACTIONS", "ATTACK")
    w_1.set("ACCURACY", 66)
    w_1.set("DAMAGE", "666")
    assert w_1.get("DAMAGE") == "666", \
        "Incorrect default damage: expected '666'"
    assert w_1.get("ACCURACY") == 66, \
        "Incorrect default accuracy, expected 66"
    actions = w_1.possible_actions(None, None)
    assert len(actions) == 1, \
        "incorrect default actions, expected ['ATTACK'], got " + str(actions)
    assert actions[0].verb == "ATTACK", \
        "incorrect default action, expected 'ATTACK', got " + str(actions[0])
    assert actions[0].get("DAMAGE") == "666", \
        "incorrect base damage, expected '666', got " + str(actions[0])
    assert actions[0].get("ACCURACY") == "66", \
        "incorrect base accuracy, expected 66, got " + str(actions[0])
    print("test #2: " + str(w_1) +
          " ... BASE ATTACK, ACCURACY and DAMAGE - CORRECT")

    # multi-attack weapons have (addative) damage and accuracy for each attack
    # pylint: disable=bad-whitespace
    w_2 = GameObject("multi-attack weapon")

    attacks = [
        # verb,    accuracy, damage, exp acc, exp dmg
        ("ATTACK",       50,   "D5",    "50",    "D5"),
        ("ATTACK.60",    10,   "D6",    "60",    "D6"),
        ("ATTACK.70",    20,   "D7",    "70",    "D7")]
    verbs = None
    for (verb, accuracy, damage, exp_acc, exp_dmg) in attacks:
        if verbs is None:
            verbs = verb
        else:
            verbs += "," + verb
        if "." in verb:
            sub_verb = verb.split(".")[1]
            w_2.set("ACCURACY." + sub_verb, accuracy)
            w_2.set("DAMAGE." + sub_verb, damage)
        else:
            w_2.set("ACCURACY", accuracy)
            w_2.set("DAMAGE", damage)

    w_2.set("ACTIONS", verbs)
    actions = w_2.possible_actions(None, None)
    assert len(actions) == 3, \
        "incorrect actions list, expected 3, got " + str(actions)

    # pylint: disable=consider-using-enumerate; two parallel lists
    for index in range(len(actions)):
        (verb, accuracy, damage, exp_acc, exp_dmg) = attacks[index]
        action = actions[index]
        assert action.verb == verb, \
            "action {}, verb={}, expected {}".format(index, action.verb, verb)
        assert action.get("ACCURACY") == exp_acc, \
            "action {}, expected ACCURACY={}, got {}". \
            format(action.verb, exp_acc, action.get("ACCURACY"))
        assert action.get("DAMAGE") == exp_dmg, \
            "action {}, expected DAMAGE={}, got {}". \
            format(action.verb, exp_dmg, action.get("DAMAGE"))
        print("test #3: {} {} ... ACCURACY({}) and DAMAGE({}) - CORRECT".
              format(w_2.name, action.verb,
                     "base plus sub-type" if "." in verb else "base only",
                     "sub-type only" if "." in verb else "base only"))


# pylint: disable=too-many-statements
def compound_test():
    """
    Test for attribute collection for compound actions
    """
    obj = GameObject("Compound Actions w/base attributes")
    first = "ATTACK.one+CONDITION.two+ATTACK.three+CONDITION.four"
    second = "ATTACK.five+CONDITION.six"
    obj.set("ACTIONS", first + "," + second)
    obj.set("ACCURACY", 10)
    obj.set("ACCURACY.one", 5)
    obj.set("DAMAGE", "60")
    obj.set("DAMAGE.one", 666)

    obj.set("POWER", "20")
    obj.set("POWER.CONDITION.two", 10)
    obj.set("STACKS", 3)
    obj.set("STACKS.CONDITION.two", 6)

    obj.set("ACCURACY.five", 15)
    obj.set("DAMAGE.five", 55)
    obj.set("POWER.CONDITION.six", 6)
    obj.set("STACKS.CONDITION.six", 66)

    actions = obj.possible_actions(None, None)
    for action in actions:
        if action.verb == first:
            # attack accuracy = [base+sub, base-only]
            accuracies = action.get("ACCURACY").split(',')
            assert accuracies[0] == "15", "ACCURACY.one not added"
            assert accuracies[1] == "10", "base ACCURACY not used"

            # attack damage = [sub, base-only]
            damages = action.get("DAMAGE").split(',')
            assert damages[0] == "666", "DAMAGE.one not used"
            assert damages[1] == "60", "base DAMAGE not used"
            print("test #4a: {} {} ...\n\t  ACCURACY(S), DAMAGE(S) - CORRECT".
                  format(obj.name, action.verb))

            # condition power = [base+sub, base=only]
            powers = action.get("POWER").split(',')
            assert powers[0] == "30", "POWER.two not added in"
            assert powers[1] == "20", "base POWER not used"

            # condition stacks = [sub, base=only]
            stacks = action.get("STACKS").split(',')
            assert stacks[0] == "6", "STACKS.two not used"
            assert stacks[1] == "3", "base STACKS not used"
            print("test #4b: {} {} ...\n\t  POWER(S), STACKS(S) - CORRECT".
                  format(obj.name, action.verb))
        elif action.verb == second:
            accuracies = action.get("ACCURACY").split(',')
            assert accuracies[0] == "25", "ACCURACY.five not added"
            damages = action.get("DAMAGE").split(',')
            assert damages[0] == "55", "DAMAGE.five not used"

            powers = action.get("POWER").split(',')
            assert powers[0] == "26", "POWER.six not added in"
            stacks = action.get("STACKS").split(',')
            assert stacks[0] == "66", "STACKS.six not used"
            print("test #4c: {} {} ... \n\tPOWER, STACKS - CORRECT".
                  format(obj.name, action.verb))
        else:
            assert False, "Incorrect verb: " + action.verb

    # next set of tests are combinations w/no base attributes
    obj = GameObject("Compound Actions w/o base attributes")
    first = "ATTACK.seven+CONDITION.eight+ATTACK.nine+CONDITION.ten"
    obj.set("ACTIONS", first)
    obj.set("ACCURACY.seven", 7)
    obj.set("DAMAGE.seven", "777")

    obj.set("POWER.CONDITION.eight", 8)
    obj.set("STACKS.CONDITION.eight", "88")

    actions = obj.possible_actions(None, None)
    assert len(actions) == 1, \
        "Incorrect actions: expected 1, got {}".format(len(actions))
    action = actions[0]
    assert action.verb == first, \
        "Incorrect action: expected {}, got {}".format(first, action.verb)

    # attack accuracy = [sub, None]
    accuracies = action.get("ACCURACY").split(',')
    assert accuracies[0] == "7", "ACCURACY.seven not used"
    assert accuracies[1] == "0", \
        "expected ACCURACY=0, got {}".format(accuracies[1])

    # attack damage = [sub, None]
    damages = action.get("DAMAGE").split(',')
    assert damages[0] == "777", "DAMAGE.seven not used"
    assert damages[1] == "0", \
        "expected DAMAGE=0, got {}".format(damages[1])

    print("test #4d: {} {} ... \n\tACCURACY, DAMAGE - CORRECT".
          format(obj.name, action.verb))

    # condition power = [base+sub, base=only]
    powers = action.get("POWER").split(',')
    assert powers[0] == "8", "POWER.eight not used"
    assert powers[1] == "0", \
        "expected POWER=0, got {}".format(powers[1])

    # condition stacks = [sub, base=only]
    stacks = action.get("STACKS").split(',')
    assert stacks[0] == "88", "STACKS.eight not used"
    assert stacks[1] == "1", "default STACKS=1 not used"

    print("test #4e: {} {} ... \n\tPOWER, STACKS - CORRECT".
          format(obj.name, action.verb))


if __name__ == "__main__":
    action_test()
    weapon_test()
    compound_test()
    print("All GameObject test cases passed")
