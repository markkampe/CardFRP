from GameObject import GameObject


class GameActor(GameObject):
    """
    A GameActor (typically a PC or NPC) is an agent that has a
    context and is capable of initiating and receiving actions.
    """

    def __init__(self, name, descr=None):
        """
        create a new GameObject
        @param name(string): display name of this object
        @param descr(string): human description of this object
        """
        super().__init__(name, descr)
        self.context = None

    def accept_action(self, action, actor, context):
        """
        receive and process the effects of an action

        @param action (GameAction): the action being performed
        @param actor (GameActor): the actor initiating the action
        @param context(GameContext): the most local context
        @return (string): description of the effect
        """
        # figure out the action verb and sub-type
        if '.' in action.verb:
            parts = action.verb.split('.')
            base_verb = parts[0]
            sub_type = parts[1]
        else:
            base_verb = action.verb
            sub_type = None

        if base_verb == "ATTACK":
            # see if we are able to evade the attack
            attack = action.get("success")
            evasion = self.get("evasion." + sub_type)
            if evasion is None:
                evasion = self.get("evasion")
            if evasion is not None and attack <= int(evasion):
                return "{} evades {} {} ... evasion={} vs attack={}" \
                       .format(self.name, action.source.name, action.verb,
                               evasion, attack)

            # see how much of the delivered damage we take
            delivered = action.get("delivered_damage")
            protection = self.get("protection." + sub_type)
            if protection is None:
                protection = self.get("protection")
            reduction = 0 if protection is None else int(protection)
            damage = delivered - reduction

            old_hp = self.get("life")
            if delivered > reduction:
                new_hp = old_hp - damage
                self.set("life", new_hp)

                result = "{} hit by {} using {} for {}-{} life-points in {}" \
                         .format(self.name, actor.name, action.source.name,
                                 delivered, reduction, context.name) \
                         + "\n    {} life: {} - {} = {}"\
                           .format(self.name, old_hp, damage, new_hp)
                if new_hp <= 0:
                    result += ", and is killed"
            else:
                result = "{}'s protection absorbs all damage from {}" \
                         .format(self.name, action.verb)
        elif base_verb == "SAVE":
            attack = action.get("success")
            attribute = self.get(sub_type)
            if attack <= attribute:
                result = "{} makes his {} save - {} vs {}" \
                         .format(self.name, sub_type, attribute, attack)
            else:
                result = "{} fails his {} save" \
                         .format(self.name, sub_type)
        else:
            # if we don't recognize this action, pass it up the chain
            result = super().accept_action(action, actor, context)
        return result

    def set_context(self, context):
        """
        establish the local context
        """
        self.context = context

    def take_action(self, action, target):
        """
        Initiate an action against a target
        @param action (GameAction): the action to be initiated
        @param target (GameObject): the target of the action
        @return (string): result of the action
        """
        result = action.act(self, target, self.context)
        return result
