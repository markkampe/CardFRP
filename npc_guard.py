#!/usr/bin/python3
# pylint: disable=invalid-name; "Npc_guard" would be an abomination
""" This module implements the NPC_guard class """
from random import randint
from gameobject import GameObject
from gameactor import GameActor


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
#   targeting attacker
#   calling for reinforcements
