#!/usr/bin/python3
# pylint: disable=invalid-name; "Npc_guard" would be an abomination
""" This module implements the NPC_guard class """
from random import randint
from gameobject import GameObject
from gameactor import GameActor
from gamecontext import GameContext


class NPC_guard(GameActor):
    """
    A guard is a low-level NPC fighter who will quickly
    engage and can call for reinforcements.
    """
    def __init__(self, name="guard", descr=None):
        """
        create a new GameObject
        @param name: display name of this object
        @param descr: human description of this object
        """
        super(NPC_guard, self).__init__(name, descr)
        self.context = None

        # default attributes ... easily changed after instantiation
        self.set("HP", 16)
        self.set("LIFE", 16)
        self.set("ACCURACY", 10)
        self.set("EVASION", 40)
        self.set("EVASION.slash", 20)   # slashes are harder to dodge
        self.set("PROTECTION", 2)       # by default, cheap armor
        self.set("reinforcements", 0)   # by default, alone

        self.weapon = GameObject("sword")
        self.weapon.set("ACTIONS", "ATTACK.slash")
        self.weapon.set("DAMAGE.slash", "D6")

        # sub-class combat attributes
        self.help_arrived = False
        self.target = None

    def accept_action(self, action, actor, context):
        """
        receive and process the effects of an action

        @param action: GameAction being performed
        @param actor: GameActor) initiating the action
        @param context: GameContext in which action is being taken
        @return: (boolean success, string description of the effect)

        The only special things about a guard ar that, if attacked
        (1) he counter-attacks
        (2) he can call for reinforcements.

        """
        # remember where this is happening
        self.context = context

        # start with standard GameActor responses
        (hit, desc) = super(NPC_guard, self).accept_action(action,
                                                           actor, context)

        # figure out the action verb and sub-type
        if '.' in action.verb:
            base_verb = action.verb.split('.')[0]
        else:
            base_verb = action.verb

        # if I have been attacked, and am not dead
        if base_verb == "ATTACK" and \
           self.get("LIFE") > 0:
            # counter attack when our turn comes
            self.target = actor

            # see if we can call for help
            if self.get("reinforcements") > 0 and not self.help_arrived:
                desc += "\n    " + self.name + " calls for help"
                roll = randint(1, 100)
                if roll <= self.get("reinforcements"):
                    helper = NPC_guard("Guard #2", "test reinforcement")
                    helper.target = actor
                    desc += ", and " + helper.name + " arrives"
                    context.add_npc(helper)
                    helper.set_context(context)
                    self.help_arrived = True

        # and return our (perhaps updated) result
        return (hit, desc)

    def take_turn(self):
        """
        Take action when your turn comes.
        The only actions this test Guard can take are fighting back
        """
        if self.target is not None:
            weapon = self.weapon
            actions = weapon.possible_actions(self.target, self.context)
            attack = actions[randint(0, len(actions)-1)]
            (success, desc) = self.take_action(actions[0], self.target)
            return (success,
                    "\n{} uses {} to {} {}, delivered={}\n    {}"
                    .format(self.name, weapon.name, attack.verb,
                            self.target.name, attack.get("HIT_POINTS"),
                            desc))
        return super(NPC_guard, self).take_turn()


# UNIT TESTING
class NoGoodNick(GameActor):
    """
    A NoGoodNick is an actor who will attack a guard and report when
    he is (counter-) attacked, and by whom
    """
    def __init__(self, name):
        """
        @param name: (string) name of this actor
        """

        # create a bad-guy brawler
        super(NoGoodNick, self).__init__(name, "test aggressor")
        self.set("HP", 16)
        self.set("LIFE", 16)
        self.set("ACCURACY", 10)
        self.set("EVASION", 40)
        self.set("DAMAGE", "D6")
        self.set("ACTIONS", "ATTACK.BRAWL")

    def accept_action(self, action, actor, context):
        """
        receive an attack and report who made it

        @param action: GameAction being performed
        @param actor: GameActor) initiating the action
        @param context: GameContext in which action is being taken
        @return: (boolean success, string description of the effect)
        """
        return (True, "{} counter-attacks {}".format(actor.name, self.name))


def test_target():
    """
    create a GameActor who attacks me, and confirm that I return the attack
    """
    # create a guard and a thug in an arena
    cxt = GameContext("the arena")
    good_guy = NPC_guard("guard #1")
    bad_guy = NoGoodNick("thug #1")
    assault = bad_guy.possible_actions(good_guy, cxt)[0]

    tried = 0
    passed = 0

    # thug attacks the guard
    tried += 1
    print("{} {}s {} in {}".
          format(bad_guy.name, assault.verb, good_guy.name, cxt.name))
    (_, desc) = assault.act(bad_guy, good_guy, cxt)
    print(desc)

    # confirm guard knows who attacked him
    assert good_guy.target is bad_guy, \
        "after being attacked, {} does not target {}"\
        .format(good_guy.name, bad_guy.name)
    passed += 1

    # confirm guard's next turn counter-attacks his attacker
    tried += 1
    (_, desc) = good_guy.take_turn()
    print(desc)
    assert "guard #1 counter-attacks thug #1" in desc,\
        "after being attacked, guard's turn is not counter-attack"
    passed += 1

    print()
    return (tried, passed)


def test_reinforcements():
    """
    create a GameActor who attacks me, and confirm that I call for
    reinforcements, who will attack my attacker
    """
    # create a guard (who likes help) and a thug in an arena
    cxt = GameContext("the arena")
    good_guy = NPC_guard("guard #1")
    cxt.add_npc(good_guy)
    good_guy.set("reinforcements", 100)

    bad_guy = NoGoodNick("thug #1")
    assault = bad_guy.possible_actions(good_guy, cxt)[0]

    tried = 0
    passed = 0

    # thug attacks the guard
    print("{} {}s {} in {}".
          format(bad_guy.name, assault.verb, good_guy.name, cxt.name))
    (_, desc) = assault.act(bad_guy, good_guy, cxt)
    print(desc)

    # confirm there is now (another) NPC in the context
    tried += 1
    npcs = cxt.get_npcs()
    assert len(npcs) == 2, "Reinforcement not added to context"
    passed += 1

    # confirm there is someone other than me in the context
    tried += 1
    helper = None
    for npc in npcs:
        if npc.name != good_guy.name:
            helper = npc

    assert helper is not None, \
        "Nobody but {} in context".format(good_guy.name)
    passed += 1

    # confirm helper knows who the enemy is
    tried += 1
    assert helper.target is bad_guy, \
        "after coming to assist, {} does not target {}"\
        .format(helper.name, bad_guy.name)
    passed += 1

    # confirm helper attacks the thug on his next turn
    tried += 1
    (_, desc) = helper.take_turn()
    print(desc)
    assert "{} counter-attacks thug #1".format(helper.name) in desc,\
        "after being attacked, guard's turn is not counter-attack"
    passed += 1

    print()
    return (tried, passed)


def main():
    """
    Run all unit-test cases and print out summary of results
    """
    (t_1, p_1) = test_target()
    (t_2, p_2) = test_reinforcements()
    tried = t_1 + t_2
    passed = p_1 + p_2
    if tried == passed:
        print("Passed all {} NPC_guard tests".format(passed))
    else:
        print("FAILED {}/{} GameNPC_guard tests".format(tried-passed, tried))


if __name__ == "__main__":
    main()
