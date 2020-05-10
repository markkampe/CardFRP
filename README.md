This is an prototype execution engine for a card-based FRPG.

**Elements of such a game:**
   - party members and equipment they possess
   - NPCs and equipment they possess
   - (hierarchy of) local context(s) which contain NPCs and objects

**Basic Game Mechanics:**
   1. based on provisioned equipment and context, players get "action-cards"
   2. those cards are played (vs a target) when it is a player's turn to act
   3. those actions cause changes in party members, NPCs and context(s)

Christopher Kampe wanted to explore such games, and started working on
tools for creating characters and artifacts.  I decided to prototype
an engine to implement the most basic mechanics:

   - characters that have a wide range of attributes
   - objects that return sets of possible (interaction, skill, combat) actions
   - the ability to apply an action to a particular target, resulting in
     changes to the target's (or other characters/objects) attributes
  
My key design goals were:
   - to be able to implement most of the interactions found in most such games.
   - to enable as much as possible of this behavior to be implemented 
     on the basis of character/object attributes.  It should only very
     seldom be necessary to write code in order to achieve most interactions.
   - to implement the game engine in an easily extended (object oriented,
     open-source, interpreted language) form (e.g. Python classes).

The engine is implemented with a few Python classes.  A key goal has
been that almost all behavior should be controlled by attributes, so
that it would seldom
This repo contains that prototype.

**Key classes:**
   - *Base* ... a named object with attributes
   - *GameObject* ... offers and can receive actions, can possess other objects
   - *GameAction* ... implements simple attacks and other attribute-changing actions
     (including character and artifact bonuses)
   - *GameActor* ... can receive and process the (attribute changing) consequences
     of an action (after considering character and artifact bonuses)
   - *GameContext* ... a location that includes characters, objects, and 
     (local condition) attributes.
   - *Dice* ... an engine that understands typical formulae (e.g. "3D6+2" or D%")
     and can roll against them.

   *GameObjects* (including *GameActors* and *GameContexts*) support a 
   *load* method, which can be used to read a complete set of attributes
   (including those of nested *GameObjects*) from a file.

   Most of these classes, if run as a *main*, include a unit-test suite
   for the basic functionality of that class.

   Sample code to instantiate objects, load their parameters, and obtain
   their possible actions, and perform those (interaction, skill, and
   combat) actions can be found in *test.py*.  The attributes of the
   actor, target NPC, and local context are *load*ed from three files:
   *TEST_hero.dat*, *TEST_guard.dat*, and *TEST_context.dat*.

**Makefile targets:**
   - *default*: run the basic *test.py* program
   - *all*: run all of the unit-test cases as well as *test.py*
   - *doc*: use *epydoc* to generate a class diagram and API documentation.
   - *lint*: use *pylint* and *pep8* to check the code for standards compliance
