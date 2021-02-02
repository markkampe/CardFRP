#!/usr/bin/python3
""" This module implements the base class for almost everything"""


class Base(object):
    """
    This is the base class for all other classes

    @ivar name:         name of this object
    @ivar description:  one line this description
    @ivar attributes:   dict of <name,value> pairs"
    """

    def __init__(self, name, descr=None):
        """
        create a new object
        @param name: display name of this object
        @param descr: human description of this object
        """
        self.name = name
        self.description = descr
        self.attributes = {}

    def __str__(self):
        """
        return a descriptive string for this object
        """
        if self.description is None:
            return self.name
        return "{}({})".format(self.name, self.description)

    def get(self, attribute):
        """
        return: value of an attribute

        @param attribute: name of attribute to be fetched
        @return: (string) value (or none)
        """
        if attribute in self.attributes:
            return self.attributes[attribute]
        return None

    def set(self, attribute, value):
        """
        set the value of an attribute

        @param attribute: name of attribute to be fetched
        @param value: value to be stored for that attribute
        """
        self.attributes[attribute] = value


# UNIT TESTING
def main():
    """
    basic test cases for name, description, and attributes
    """

    describe = "simple get/set test object"
    go1 = Base("Base Object 1", describe)
    go2 = Base("Base Object 2")

    tried = 0
    passed = 0

    # new object has name, description, and nothing else
    print("Created 'Base 1', descr={}\n    got '{}'"
          .format(describe, str(go1)))
    tried += 2
    assert (go1.name == "Base Object 1"), \
        "New object does not have assigned name"
    assert (go1.description == describe), \
        "New object does not have assigned description"
    passed += 2

    # a new set correctly adds a value
    print("    before set(): get('attribute#1') -> {}"
          .format(go1.get("attribute#1")))
    tried += 2
    assert (go1.get("attribute#1") is None), \
        "New object has attribute values before set"
    go1.set("attribute#1", "value1")
    print("    after set('attribute#1', 'value1'): get('attribute#1') -> '{}'"
          .format(go1.get("attribute#1")))
    assert (go1.get("attribute#1") == "value1"), \
        "set does not correctly set new value"
    passed += 2

    # a second set correctly changes a value
    go1.set("attribute#1", "value2")
    print("    after set('attribute#1', 'value2'): get('attribute#1') -> '{}'"
          .format(go1.get("attribute#1")))
    tried += 1
    assert (go1.get("attribute#1") == "value2"), \
        "set does not correctly change value"
    passed += 1

    # description defaults to None
    print("Created 'Base Object 2, descr=None\n    got '{}'"
          .format(str(go2)))
    tried += 2
    assert (go2.name == "Base Object 2"), \
        "New object does not have assigned name"
    assert (go2.description is None), \
        "New description does not default to None"
    passed += 2

    print()
    if tried == passed:
        print("Passed all {} Base tests".format(passed))
    else:
        print("FAILED {}/{} Base tests".format(tried-passed, tried))


if __name__ == "__main__":
    main()
