#!/usr/bin/python3
""" This module implements the (foundation) GameObject Class """
import sys
from random import randint
from base import Base
from gameaction import GameAction


class GameObject(Base):
    """
    This is the base class for all artifacts, actors, and contexts.
    The abilities of this base class are:
        - own a list of objects (which can be added and retrieved)
        - return a list of GameActions that it enables
        - accept and process non-ATTACK GameActions

    @ivar objects: list of owned/contained GameObjects

    objects can be I{hidden} in which case they might not be returned
    """
    def __init__(self, name="actor", descr=None):
        """
        create a new GameObject
        @param name: display name of this object
        @param descr: for players description of this object
        """
        super(GameObject, self).__init__(name, descr)
        self.objects = []

    def __str__(self):
        """
        return the given name of this object
        """
        return self.name

    def get_objects(self, hidden=False):
        """
        return a list of GameObjects contained in/owned by this GameObject

        if an object is hidden (has a positive RESISTANCE.SEARCH) it may not
        be visible unless
            - it has been successfully found (SEARCH > 0)
            - caller specifies that hidden objects should be returned

        @param hidden: return only hidden objects
        @return: list of discoverd GameOjects
        """
        reported = []
        for thing in self.objects:
            # check object's RESISTANCE.SEARCH and SEARCH attributes
            atr = thing.get("RESISTANCE.SEARCH")
            concealed = atr is not None and atr > 0
            atr = thing.get("SEARCH")
            found = atr is not None and atr > 0

            if hidden:
                # if hidden specified, find all hidden objects
                if concealed and not found:
                    reported.append(thing)
            else:
                # else find only visible objects
                if found or not concealed:
                    reported.append(thing)

        return reported

    def get_object(self, name):
        """
        return a named object from my inventory

        @param name: (string) of the desired object
        @return: first matching object (or None)
        """
        for thing in self.objects:
            if name in thing.name:
                return thing
        return None

    def add_object(self, item):
        """
        add another object to my C{objects} list (if not already there)
        """
        if item not in self.objects:
            self.objects.append(item)

    # pylint: disable=too-many-locals
    def accept_action(self, action, actor, context):
        """
        called by C{GameAction.act()} to receive GameAction, determine effects

        NOTE: this base class cannot process ATTACK actions.
        Those are processed by the C{GameActor} sub-class.
        This base class can only process actions which (if successful),
        increment the property who's name matches the action verb.

        @param action: GameAction being performed
        @param actor: GameActor initiating the action
        @param context: GameContext in which action is occuring

            NOTE: this base class makes no use of the C{actor} or C{context}
            parameters, but they might be useful to a subc-class that could
            process actions before passing them down to us.

        @return: <(boolean) success, (string) description of the effect>
        """
        # get the base verb and sub-type
        if '.' in action.verb:
            base_verb = action.verb.split('.')[0]
            sub_type = action.verb.split('.')[1]
        else:
            base_verb = action.verb
            sub_type = None

        # look up our base resistance
        res = self.get("RESISTANCE")
        resistance = 0 if res is None else int(res)

        # see if we have a RESISTANCE.base-verb
        res = self.get("RESISTANCE." + base_verb)
        if res is not None:
            resistance += int(res)

        # see if we have a RESISTANCE.base-verb.subtype
        if sub_type is not None:
            res = self.get("RESISTANCE." + base_verb + "." + sub_type)
            if res is not None:
                resistance += int(res)

        # if sum of RESISTANCE >= TO_HIT, action has been resisted
        power = int(action.get("TO_HIT")) - resistance
        if power <= 0:
            return (False, "{} resists {} {}"
                    .format(self.name, action.source.name, action.verb))

        # for each STACK instance, roll to see if roll+RESISTANCE > TO_HIT
        incoming = abs(int(action.get("TOTAL")))
        received = 0
        for _ in range(incoming):
            roll = randint(1, 100)
            # accumulate the number that get through
            if roll <= power:
                received += 1

        # add number of successful STACKS to affected attribute
        #   (or if C{GameAction.TOTAL} is negative, subtract)
        sign = 1 if int(action.get("TOTAL")) > 0 else -1
        if received > 0:
            have = self.get(action.verb)
            have = 0 if have is None else int(have)
            # special case: LIFE cannot be raised beyond HP
            if action.verb == "LIFE" and self.get("HP") is not None:
                max_hp = int(self.get("HP"))
                if have + sign * received > max_hp:
                    have = max_hp - received
            self.set(action.verb, have + (sign * received))

        # return <whether or not any succeed, accumulated results>
        return (received > 0,
                "{} resists {}/{} stacks of {} from {} in {}"
                .format(self.name, incoming - received, incoming,
                        ("(negative) " if sign < 0 else "") + action.verb,
                        actor, context))

    # pylint: disable=unused-argument; sub-classes are likely to use them
    # pylint: disable=too-many-branches; there are a lot of cases
    # pylint: disable=too-many-statements; there are a lot of cases
    def possible_actions(self, actor, context):
        """
        return list of C{GameAction}s this object enables

        verbs come from our (comma-separated-verbs) ACTIONS attribute
        for each C{GameAction}, ACCURACY, DAMAGE, POWER, STACKS are the sum of
            - our base ACCURACY, DAMAGE, POWER, STACKS
            - our ACCURACY.verb, DAMAGE.verb, POWER.verb, STACKS.verb,

        @param actor: GameActor initiating the action
        @param context: GameContext in which the action is taken

        NOTE: this base class makes no use of the C{actor} and C{context}
        parameters, but a sub-class might want to determine whether or not
        B{this actor} could perform this action in B{this context}.

        @return: list of possible GameActions
        """
        # get a list of possible actions with this object (e.g. weapon)
        actions = []
        verbs = self.get("ACTIONS")
        if verbs is None:
            return []

        # get our base ACCURACY/DAMAGE/POWER/STACKS attributes
        base_accuracy = self.get("ACCURACY")
        base_damage = self.get("DAMAGE")
        base_power = self.get("POWER")
        base_stacks = self.get("STACKS")

        # instantiate a GameAction for each verb in our ACTIONS list
        for compound_verb in verbs.split(','):
            action = GameAction(self, compound_verb)

            # accumulate base and sub-type attributes
            accuracies = ""
            damages = ""
            powers = ""
            stacks = ""

            # if a verb is compound (+), accumulate each sub-verb separately
            for verb in compound_verb.split('+'):
                if verb.startswith("ATTACK"):
                    # see if we have ATTACK sub-type ACCURACY/DAMAGE
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
                    # see if we have verb sub-type POWER/STACKS
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

                # add accumulated ACCURACY/DAMAGE/POWER/STACKS to C{GameAction}
                if accuracies != "":
                    action.set("ACCURACY", accuracies)
                if damages != "":
                    action.set("DAMAGE", damages)
                if powers != "":
                    action.set("POWER", powers)
                if stacks != "":
                    action.set("STACKS", stacks)

            # append the new C{GameAction} to the list to be returned
            actions.append(action)

        return actions

    def load(self, filename):
        """
        read object definitions from a file
            - blank lines and lines beginning w/# are ignored
            - NAME string ... is the name of an object
            - DESCRIPTION string ... is the description of that object
            - ACTIONS string ... is the list of supported verbs
            - OBJECT ... introduces definition of an object in our inventory
            - anything else is an atribute and value (strings should be quoted)

        NOTE: The object being defined can contain other objects.
        (e.g. guard has a sword, box contains a scroll)
        But contained objects cannot, themselves, contain other objects.

        @param filename: name of file to be read
        """
        cur_object = self

        try:
            infile = open(filename, "r")
            for line in infile:
                # for each non-comment line, read name and value
                (name, value) = _lex(line)
                if name is None:
                    continue

                # check for special names: NAME, DESCRIPTION, OBJECT
                if name == "NAME":
                    cur_object.name = value
                elif name == "DESCRIPTION":
                    cur_object.description = value
                elif name == "OBJECT":
                    cur_object = GameObject()
                    self.add_object(cur_object)
                else:
                    # anything else is just an attribute of latest object
                    cur_object.set(name, value)

            infile.close()
        except IOError:
            sys.stderr.write("Unable to read attributes from {}\n".
                             format(filename))


def _lex(line):
    """
    helper function to lex a name and (potentially quoted) value from a line
        - treat (single or double) quoted strings as a single token
        - if second token is an integer, return it as such, else a string

    @param line: string to be lexed
    @return: (name, value) ... or (None, None) for blank/comment lines
    """
    # find the start of the first token
    start = 0
    eol = len(line)
    while start < eol and line[start].isspace():
        start += 1

    # if this is a comment or blank line, return (None, None)
    if start >= eol or line[start] == "#":
        return (None, None)

    # lex off first (blank separated) token as a name
    end = start + 1
    while end < eol and not line[end].isspace():
        end += 1
    name = line[start:end]

    # lex off next token as a value
    start = end
    while start < eol and line[start].isspace():
        start += 1

    if start >= eol or line[start] == "#":
        return (name, None)

    # either single or double quotes can surround a value
    if line[start] == '"' or line[start] == "'":
        # scan until the closing quote (or EOL)
        quote = line[start]
        start += 1
        end = start + 1
        while end < eol and line[end] != quote:
            end += 1
        value = line[start:end]
    else:
        end = start + 1
        while end < eol and not line[end].isspace():
            end += 1

        # an un-quoted number should be returned as an int
        try:
            value = int(line[start:end])
        except ValueError:
            value = line[start:end]

    return (name, value)


# UNIT TESTING
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
    return (3, 3)


# pylint: disable=too-many-locals,too-many-statements
def weapon_test():
    """
    test for weapon actions and damage
    """
    tried = 0
    passed = 0

    # by default a weapon has no actions or attributes
    w_0 = GameObject("Null Weapon")
    tried += 4
    assert w_0.name == "Null Weapon", \
        "Incorrect name: expected w_0"
    assert w_0.get("DAMAGE") is None, \
        "Incorrect default damage: expected None"
    assert w_0.get("ACCURACY") is None, \
        "Incorrect default accuracy, expected None"
    actions = w_0.possible_actions(None, None)
    assert not actions, \
        "incorrect default actions, expected None"
    passed += 4
    print("test #1: " + str(w_0) +
          " ... NO ATTACKS, ACCURACY or DAMAGE - CORRECT")

    # if a weapon is created with damage, it has ATTACK
    w_1 = GameObject("Simple Weapon")
    w_1.set("ACTIONS", "ATTACK")
    w_1.set("ACCURACY", 66)
    w_1.set("DAMAGE", "666")
    tried += 6
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
    passed += 6
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
    tried += 1
    assert len(actions) == 3, \
        "incorrect actions list, expected 3, got " + str(actions)
    passed += 1

    # pylint: disable=consider-using-enumerate; two parallel lists
    for index in range(len(actions)):
        (verb, accuracy, damage, exp_acc, exp_dmg) = attacks[index]
        action = actions[index]
        tried += 3
        assert action.verb == verb, \
            "action {}, verb={}, expected {}".format(index, action.verb, verb)
        assert action.get("ACCURACY") == exp_acc, \
            "action {}, expected ACCURACY={}, got {}". \
            format(action.verb, exp_acc, action.get("ACCURACY"))
        assert action.get("DAMAGE") == exp_dmg, \
            "action {}, expected DAMAGE={}, got {}". \
            format(action.verb, exp_dmg, action.get("DAMAGE"))
        passed += 3
        print("test #3: {} {} ... ACCURACY({}) and DAMAGE({}) - CORRECT".
              format(w_2.name, action.verb,
                     "base plus sub-type" if "." in verb else "base only",
                     "sub-type only" if "." in verb else "base only"))
    return (tried, passed)


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

    tried = 0
    passed = 0

    actions = obj.possible_actions(None, None)
    for action in actions:
        if action.verb == first:
            tried += 8
            # attack accuracy = [base+sub, base-only]
            accuracies = action.get("ACCURACY").split(',')
            assert accuracies[0] == "15", "ACCURACY.one not added"
            assert accuracies[1] == "10", "base ACCURACY not used"
            passed += 2

            # attack damage = [sub, base-only]
            damages = action.get("DAMAGE").split(',')
            assert damages[0] == "666", "DAMAGE.one not used"
            assert damages[1] == "60", "base DAMAGE not used"
            passed += 2
            print("test #4a: {} {} ...\n\t  ACCURACY(S), DAMAGE(S) - CORRECT".
                  format(obj.name, action.verb))

            # condition power = [base+sub, base=only]
            powers = action.get("POWER").split(',')
            assert powers[0] == "30", "POWER.two not added in"
            assert powers[1] == "20", "base POWER not used"
            passed += 2

            # condition stacks = [sub, base=only]
            stacks = action.get("STACKS").split(',')
            assert stacks[0] == "6", "STACKS.two not used"
            assert stacks[1] == "3", "base STACKS not used"
            passed += 2
            print("test #4b: {} {} ...\n\t  POWER(S), STACKS(S) - CORRECT".
                  format(obj.name, action.verb))
        elif action.verb == second:
            tried += 4
            accuracies = action.get("ACCURACY").split(',')
            assert accuracies[0] == "25", "ACCURACY.five not added"
            damages = action.get("DAMAGE").split(',')
            assert damages[0] == "55", "DAMAGE.five not used"
            passed += 2

            powers = action.get("POWER").split(',')
            assert powers[0] == "26", "POWER.six not added in"
            stacks = action.get("STACKS").split(',')
            assert stacks[0] == "66", "STACKS.six not used"
            passed += 2
            print("test #4c: {} {} ... \n\tPOWER, STACKS - CORRECT".
                  format(obj.name, action.verb))
        else:
            tried += 1
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

    return (tried, passed)


def accept_test():
    """
    tests for (non-ATTACK) accept_action()
    """
    tried = 0
    passed = 0

    # create the initiator, recipient, and context
    initiator = GameObject("tester")    # won't need any GameActor functions
    target = GameObject("target")
    arena = GameObject("arena")         # won't need any GameCOntext functions

    # STACKS get through in proportion to TO_HIT - RESISTANCE
    action = GameAction(initiator, "50/50")
    action.set("STACKS", 100)
    target.set("RESISTANCE", 50)    # half should get through
    (success, desc) = action.act(initiator, target, arena)
    tried += 5
    assert success, \
        "None of 100 50/50 STACKs got through"
    passed += 1

    # decode and check the returned status string
    resisted = int(desc.split()[2].split('/')[0])
    expect = "{} resists {}/100 stacks of {} from {} in {}".\
        format(target.name, resisted, action.verb, initiator.name, arena.name)
    assert desc == expect, \
        "Successful 50/50 did not return expected result string"
    passed += 1

    # confirm a reasonable number of stacks got through
    assert resisted >= 35, \
        "too few 50/50 STACKS got through"
    assert resisted <= 64, \
        "too many 50/50 STACKS got through"
    attribute = target.get(action.verb)
    assert attribute == (100 - resisted), \
        "target's {} does not reflect correct 100-{}". \
        format(action.verb, resisted)
    passed += 3

    print("test #5a: {} resists {}/100 STACKS of {} ... \n\t{}.{} 100 -> {}".
          format(target.name, resisted, action.verb, target.name,
                 action.verb, attribute))

    # confirm that negative stacks also get through
    action = GameAction(initiator, "SURE-THING")
    action.set("STACKS", -50)
    target.set("RESISTANCE", 0)     # no resistance
    target.set(action.verb, 100)    # initial value
    (success, desc) = action.act(initiator, target, arena)
    tried += 4
    assert success, \
        "{} action failed".format(action.verb)

    resisted = int(desc.split()[2].split('/')[0])
    expect = "{} resists {}/50 stacks of (negative) {} from {} in {}".\
        format(target.name, resisted, action.verb, initiator.name, arena.name)
    assert desc == expect, \
        "Successful SURE-THING did not return expected result string"
    assert resisted == 0, \
        "{} resists {} STACKS of {}".format(target.name, resisted, action.verb)

    attribute = target.get(action.verb)
    assert attribute == (100 - 50), \
        "100 - 50 STACKS of {} -> {}".format(action.verb, attribute)
    passed += 4

    print("test #5b: {} delivers -50 STACKS of {} ... \n\t{}.{} 100 -> {}".
          format(initiator.name, action.verb, target.name, action.verb,
                 attribute))

    # adequate RESISTANCE is total protection
    target.set("RESISTANCE", 100)
    action = GameAction(initiator, "BASE-RESISTED-ACTION")
    action.set("STACKS", 100)
    (success, desc) = action.act(initiator, target, arena)
    tried += 3
    assert not success, \
        "{} action succeeded".format(action.verb)
    assert desc == "{} resists {} {}". \
        format(target.name, initiator.name, action.verb), \
        "{} action does not return correct failure message".format(action.verb)
    assert target.get(action.verb) is None, \
        "target property was set by failed {} action".format(action.verb)
    passed += 3

    print("test #5c: {} delivers 100 STACKS of {} ... \n\t{}".
          format(initiator.name, action.verb, desc))

    # adequate RESISTANCE.verb is total protection
    target.set("RESISTANCE", None)
    target.set("RESISTANCE.VERB-RESISTED-ACTION", 100)
    action = GameAction(initiator, "VERB-RESISTED-ACTION")
    action.set("STACKS", 100)
    (success, desc) = action.act(initiator, target, arena)
    tried += 3
    assert not success, \
        "{} action succeeded".format(action.verb)
    assert desc == "{} resists {} {}". \
        format(target.name, initiator.name, action.verb), \
        "{} action does not return correct failure message".format(action.verb)
    assert target.get(action.verb) is None, \
        "target property was set by failed {} action".format(action.verb)
    passed += 3

    print("test #5d: {} delivers 100 STACKS of {} ... \n\t{}".
          format(initiator.name, action.verb, desc))

    # adequate RESISTANCE.verb.subtype is total protection
    target.set("RESISTANCE.VERB-RESISTED-ACTION", None)
    target.set("RESISTANCE.RESISTED-ACTION.SUBTYPE", 100)
    action = GameAction(initiator, "RESISTED-ACTION.SUBTYPE")
    action.set("STACKS", 100)
    (success, desc) = action.act(initiator, target, arena)
    tried += 3
    assert not success, \
        "{} action succeeded".format(action.verb)
    assert desc == "{} resists {} {}". \
        format(target.name, initiator.name, action.verb), \
        "{} action does not return correct failure message".format(action.verb)
    assert target.get(action.verb) is None, \
        "target property was set by failed {} action".format(action.verb)
    passed += 3

    print("test #5e: {} delivers 100 STACKS of {} ... \n\t{}".
          format(initiator.name, action.verb, desc))

    target.set("RESISTANCE.RESISTED-ACTION.SUBTYPE", None)

    # LIFE cannot be increased beyond HP
    target.set("RESISTANCE.RESISTED-ACTION.SUBTYPE", None)
    target.set("LIFE", 25)
    target.set("HP", 50)
    action = GameAction(initiator, "LIFE")
    action.set("STACKS", 100)
    (success, desc) = action.act(initiator, target, arena)
    tried += 3
    assert success, \
        "sure thing {} did not succeed".format(action.verb)
    life = target.get(action.verb)
    assert life <= target.get("HP"), \
        "{} raised above HP {}".format(action.verb, target.get("HP"))
    assert life == target.get("HP"), \
        "25/50 + 100 STACKS of {} -> {}".format(action.verb, life)
    passed += 3

    print("test #5f: 25/50 + 100 STACKS of {} ... \n\t{}.{} 25 -> {}".
          format(action.verb, target.name, action.verb, life))

    print()
    return (tried, passed)


def main():
    """
    Run all unit-test cases and print out summary of results
    """
    (t_1, p_1) = action_test()
    (t_2, p_2) = weapon_test()
    (t_3, p_3) = compound_test()
    (t_4, p_4) = accept_test()
    tried = t_1 + t_2 + t_3 + t_4
    passed = p_1 + p_2 + p_3 + p_4
    if tried == passed:
        print("Passed all {} GameObject tests".format(passed))
    else:
        print("FAILED {}/{} GameObject tests".format(tried-passed, tried))


if __name__ == "__main__":
    main()
