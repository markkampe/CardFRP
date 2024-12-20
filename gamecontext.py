#!/usr/bin/python3
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
        super().__init__(name, descr)
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
        if self.parent is not None:
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
        actions = super().possible_actions(actor, context)
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
            return (found_stuff, result)

        # if we don't recognize this action, pass it up the chain
        return super().accept_action(action, actor, context)

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

    def remove_member(self, member):
        """
        Remove a player character from this context
        @param member: (GameActor) player to be removed
        """
        if member in self.party:
            self.party.remove(member)

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

    def remove_npc(self, npc):
        """
        Remove a non-player character from this context
        @param npc: (GameActor) NPC to be removed
        """
        if npc in self.npcs:
            self.npcs.remove(npc)


# UNIT TESTING
# pylint: disable=too-many-statements
def member_tests():
    """
    exercise {add,remove}_member and get_party
     - new & empty
     - add one, add a second
     - delete the first, add a third
     - delete the third, delete the second
    """
    a_1 = GameObject("a1")
    a_2 = GameObject("a2")
    a_3 = GameObject("a3")

    tried = 0
    passed = 0

    print("creating a new GameContext and confirming no party")
    cxt = GameContext()
    party = cxt.get_party()
    tried += 1
    assert not party, "new GameContext is not empty"
    passed += 1

    print("adding a first member and confirming party of one")
    cxt.add_member(a_1)
    party = cxt.get_party()
    tried += 2
    assert len(party) == 1, "after adding first party member, len != 1"
    assert a_1 in party, \
        "after adding first party member, he is not in the party"
    passed += 2

    print("adding a second member and confirming party of two")
    cxt.add_member(a_2)
    party = cxt.get_party()
    tried += 3
    assert len(party) == 2, "after adding second party member, len != 2"
    assert a_1 in party, \
        "after adding second party member, first is no longer there"
    assert a_2 in party, \
        "after adding second party member, he is not there"
    passed += 3

    print("removing first member and confirming party of one")
    cxt.remove_member(a_1)
    party = cxt.get_party()
    tried += 3
    assert len(party) == 1, "after removing first party member, len != 1"
    assert a_1 not in party, \
        "after removing first party member, he is still there"
    assert a_2 in party, \
        "after removing first party member, second is no longer there"
    passed += 3

    print("adding a third member and confirming party of two")
    cxt.add_member(a_3)
    party = cxt.get_party()
    tried += 3
    assert len(party) == 2, "after adding another party member, len != 2"
    assert a_2 in party, \
        "after adding another party member, previous is no longer there"
    assert a_3 in party, "after adding another party member, he is not there"
    passed += 3

    print("removing third member and confirming party of one")
    cxt.remove_member(a_3)
    party = cxt.get_party()
    tried += 3
    assert len(party) == 1, "after removing another party member, len != 1"
    assert a_3 not in party, \
        "after removing another party member, he is still there"
    assert a_2 in party, \
        "after removing another party member, second is no longer there"
    passed += 3

    print("removing final member and confirming no party")
    cxt.remove_member(a_2)
    party = cxt.get_party()
    tried += 2
    assert not party, "after removing final party member, len != 0"
    assert a_2 not in party, \
        "after removing final party member, he is still there"
    passed += 2

    print()
    return (tried, passed)


# pylint: disable=too-many-statements
def npc_tests():
    """
    exercise {add,remove}_npc and get_npcs
     - new & empty
     - add one, add a second
     - delete the first, add a third
     - delete the third, delete the second
    """
    a_1 = GameObject("a1")
    a_2 = GameObject("a2")
    a_3 = GameObject("a3")

    tried = 0
    passed = 0

    print("creating a new GameContext and confirming no NPCs")
    cxt = GameContext()
    party = cxt.get_npcs()
    tried += 1
    assert not party, \
        "new GameContext is not empty"
    passed += 1

    print("adding first NPC and confirming one NPC")
    cxt.add_npc(a_1)
    party = cxt.get_npcs()
    tried += 2
    assert len(party) == 1, \
        "after adding first NPC, len != 1"
    assert a_1 in party, \
        "after adding first NPC, he is not in the party"
    passed += 2

    print("adding second NPC and confirming two NPCs")
    cxt.add_npc(a_2)
    party = cxt.get_npcs()
    tried += 3
    assert len(party) == 2, \
        "after adding second NPC, len != 2"
    assert a_1 in party, \
        "after adding second NPC, first is no longer there"
    assert a_2 in party, \
        "after adding second NPC, he is not there"
    passed += 3

    print("removing first NPC and confirming one NPC")
    cxt.remove_npc(a_1)
    party = cxt.get_npcs()
    tried += 3
    assert len(party) == 1, \
        "after removing first NPC, len != 1"
    assert a_1 not in party, \
        "after removing first NPC, he is still there"
    assert a_2 in party, \
        "after removing first NPC, second is no longer there"
    passed += 3

    print("adding third NPC and confirming two NPCs")
    cxt.add_npc(a_3)
    party = cxt.get_npcs()
    tried += 3
    assert len(party) == 2, \
        "after adding another NPC, len != 2"
    assert a_2 in party, \
        "after adding another NPC, previous is no longer there"
    assert a_3 in party, \
        "after adding another NPC, he is not there"
    passed += 3

    print("removing third NPC and confirming one NPC")
    cxt.remove_npc(a_3)
    party = cxt.get_npcs()
    tried += 3
    assert len(party) == 1, \
        "after removing another NPC, len != 1"
    assert a_3 not in party, \
        "after removing another NPC, he is still there"
    assert a_2 in party, \
        "after removing another NPC, second is no longer there"
    passed += 3

    print("removing final NPC and confirming no NPCs")
    cxt.remove_npc(a_2)
    party = cxt.get_npcs()
    tried += 2
    assert not party, \
        "after removing final NPC, len != 0"
    assert a_2 not in party, \
        "after removing final NPC, he is still there"
    passed += 2

    print()
    return (tried, passed)


def get_tests():
    """
    exercise hierarchical gets

    set distinct and overlapping properties at various levels of nested
    GameContexts, and see which values are returned from gets in
    different levels:
     - each level has a different value
     - different levels define different properties
     - a property in no level will return None

    """
    tried = 0
    passed = 0

    c_1 = GameContext("C1")
    c_2 = GameContext("C2", parent=c_1)
    c_3 = GameContext("C3", parent=c_2)

    print("gets are satisfied from nearest context")
    c_1.set("CAME_FROM", 1)
    c_2.set("CAME_FROM", 2)
    c_3.set("CAME_FROM", 3)

    ret = c_1.get("CAME_FROM")
    tried += 1
    assert ret == 1, \
        "grand-parent.get() returns " + str(ret) + "!=1"
    passed += 1
    ret = c_2.get("CAME_FROM")
    tried += 1
    assert ret == 2, \
        "parent.get() returns " + str(ret) + "!=2"
    passed += 1
    ret = c_3.get("CAME_FROM")
    tried += 1
    assert ret == 3, \
        "child.get() returns " + str(ret) + "!=1"
    passed += 1

    print("gets follow parents if necessary")
    c_3.set("IN_THREE", 3)
    ret = c_3.get("IN_THREE")
    tried += 1
    assert ret == 3, \
        "child.get() does not return its own value"
    passed += 1
    c_2.set("IN_TWO", 2)
    ret = c_3.get("IN_TWO")
    tried += 1
    assert ret == 2, \
        "child.get() does not return parent's value"
    passed += 1
    c_1.set("IN_ONE", 1)
    ret = c_3.get("IN_ONE")
    tried += 1
    assert ret == 1, \
        "child.get() does not return grand-parents value"
    passed += 1

    print("absent values reported as None")
    ret = c_3.get("NOWHERE")
    tried += 1
    assert ret is None, \
        "get() of non-existent value returns " + str(ret)
    passed += 1

    print()
    return (tried, passed)


class TestObject(GameObject):
    """
    A TestObject is a hidden object that will be found after a
    specified number of searches.
    """
    def __init__(self, name, searches):
        """
        a TestObject will be hidden for a specified number of searches,
        after which it will be found

        @param name: (string) name of the object
        @param searches: (int) number of searches to find it
        """
        super().__init__(name, "findable object")
        self.set("RESISTANCE.SEARCH", searches)
        self.set("SEARCHES", 0)

    def accept_action(self, action, actor, context):
        """
        receive and process the effects of an action

        The only verb supported by this test class is SEARCH,
        which will succeed after a specified number of tries

        @param action: GameAction being performed
        @param actor: GameActor initiating the action
        @param context: GameContext in which the action is happening

        @return: (boolean success, string description of the effect)
        """
        if action.verb != "SEARCH":
            return (False, "Unsupported action")

        resistance = self.get("RESISTANCE.SEARCH")
        searches = self.get("SEARCHES") + 1
        self.set("SEARCHES", searches)

        if searches >= resistance:
            return (True, self.name)
        return (False, "!" + self.name)


def search_tests():
    """
    exercise search for hidden objects
     - create a context with one non-hidden and three hidden test objects
     - the test objects will be discovered after 1, 2, and 3 searches
     - do three searches and confirm the right objects found by each
    """
    cxt = GameContext("searchable")

    # create three test objects w/different degrees of hiddenness
    o_1 = TestObject("one", 1)
    o_1.set("RESISTANCE.SEARCH", 1)
    cxt.add_object(o_1)
    o_2 = TestObject("two", 2)
    o_2.set("RESISTANCE.SEARCH", 2)
    cxt.add_object(o_2)
    o_3 = TestObject("three", 3)
    o_3.set("RESISTANCE.SEARCH", 3)
    cxt.add_object(o_3)

    # create a (verb only) search action
    search = GameObject("SEARCH OPERATION")
    search.verb = "SEARCH"

    tried = 0
    passed = 0

    print("first search for (singly hidden object) " + o_1.name)
    (success, descr) = cxt.accept_action(search, None, cxt)
    tried += 2
    assert success, "first SEARCH failed"
    found = descr.replace('\n', ' ').split()
    assert found == ['one', '!two', '!three'], \
        "first search returned " + descr
    passed += 2

    print("second search for (doubly hidden object) " + o_2.name)
    (success, descr) = cxt.accept_action(search, None, cxt)
    tried += 2
    assert success, "second SEARCH failed"
    found = descr.replace('\n', ' ').split()
    assert found == ['one', 'two', '!three'], \
        "first search returned " + descr
    passed += 2

    print("third search for (tripply hidden object) " + o_3.name)
    (success, descr) = cxt.accept_action(search, None, cxt)
    tried += 2
    assert success, "third SEARCH failed"
    found = descr.replace('\n', ' ').split()
    assert found == ['one', 'two', 'three'], \
        "third search returned " + descr
    passed += 2

    print()

    return (tried, passed)


def main():
    """
    Run all unit-test cases and print out summary of results
    """
    (t_1, p_1) = member_tests()
    (t_2, p_2) = npc_tests()
    (t_3, p_3) = get_tests()
    (t_4, p_4) = search_tests()
    tried = t_1 + t_2 + t_3 + t_4
    passed = p_1 + p_2 + p_3 + p_4
    if tried == passed:
        print(f"Passed all {passed} GameContext tests")
    else:
        print(f"FAILED {tried-passed}/{tried} GameContext tests")


if __name__ == "__main__":
    main()
