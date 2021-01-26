""" This module implements the GameContext class """
from gameobject import GameObject


class GameContext(GameObject):
    """
    A GameContext corresponds to a geographic location and is a collection
    of GameObjects, GameActors and state attributes.   They exist in
    higherarchical relationships (e.g. kingdom, village, buiding, room).
    """

    def __init__(self, name="context", descr=None, parent=None):
        """
        create a new GameObject
        @param name: display name of this object
        @param descr: human description of this object
        """
        super(GameContext, self).__init__(name, descr)
        self.parent = parent
        self.party = []
        self.npcs = []

    def get(self, attribute):
        """
        return the value of an attribute

        Differs from base class because calls flow up the chain of
        parents if this instance does not have the requested attribute.

        @param attribute: name of attribute to be fetched
        @return: (string) value (or None)
        """
        if attribute in self.attributes:
            return self.attributes[attribute]
        elif self.parent is not None:
            return self.parent.get(attribute)
        return None

    def possible_actions(self, actor, context):
        """
        return a list of possible actions in this context

        This base class merely passes that list up to our parent.

        @param actor: GameActor initiating the action
        @param context: GameContext for this action (should be "self")
        @return: list of possible GameActions
        """
        # default: return our parent's list of possible_actions
        actions = super(GameContext, self).possible_actions(actor, context)
        return actions

    def accept_action(self, action, actor, context):
        """
        receive and process the effects of an action

        The only verb supported by this base class is SEARCH, which it passes
        on to any hidden (RESISTANCE.SEARCH > 0) object in this context.

        @param action: GameAction being performed
        @param actor: GameActor initiating the action
        @param context: GameContext in which the action is happening

        @return: (boolean success, string description of the effect)
        """

        if action.verb == "SEARCH":
            found_stuff = False
            result = ""
            # look for any object with a RESISTANCE.SEARCH
            for thing in self.objects:
                concealment = thing.get("RESISTANCE.SEARCH")
                if concealment is not None and concealment > 0:
                    # pass the SEARCH action on to that object
                    (success, descr) = thing.accept_action(action, actor,
                                                           context)
                    if success:
                        found_stuff = True
                    if result == "":
                        result = descr
                    else:
                        result += "\n    " + descr
            return(found_stuff, result)

        # if we don't recognize this action, pass it up the chain
        return super(GameContext, self).accept_action(action,
                                                      actor, context)

    def get_party(self):
        """
        @return: list of player GameActors in this context
        """
        return self.party

    def add_member(self, member):
        """
        Add an player character to this context
        @param member: (GameActor) player to be added
        """
        if member not in self.party:
            self.party.append(member)

    def get_npcs(self):
        """
        return a list of the NPCs GameActors in this context
        """
        return self.npcs

    def add_npc(self, npc):
        """
        Add an NPC to this context
        @param npc: (GameActor) the NPC to be added
        """
        if npc not in self.npcs:
            self.npcs.append(npc)
