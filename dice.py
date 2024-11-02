#!/usr/bin/python3
"""
This module provides the Dice class (formula based random numbers)
"""
import sys
from random import randint


# pylint: disable=too-few-public-methods
class Dice():
    """
    This class supports formula based dice rolls.
    The formulae can be described in a few (fairly standard) formats:
        - DnD style ... D100, 3D6, 3D6+4
        - ranges ... 4-12
        - simple numbers ... 50

    @ivar num_dice: (int) number of dice to be rolled, None if a range
    @ivar dice_type: (int) number of faces on each die, None if a range
    @ivar plus: (int) number to be added to the roll
    @ivar min_value: (int) lowest legal value in range, None if a formula
    @ivar max_value: (int) highest legal value range, None if a formula
    """

    # pylint: disable=too-many-branches
    def __init__(self, formula):
        """
        instantiate a roller for a specified formula

        @param formula: (string) description of roll
        @raise ValueError: illegal formula expression
        """
        self.num_dice = None
        self.dice_type = None
        self.min_value = None
        self.max_value = None
        self.plus = 0

        # formula must be a string (or integer)
        if isinstance(formula, int):
            self.plus = formula
            return
        if not isinstance(formula, str):
            raise ValueError("non-string dice expression")

        # if it is just a number, this is simple
        if formula.isnumeric():
            self.plus = int(formula)
            return
        if formula[0] == '-' and formula[1:].isnumeric():
            self.plus = int(formula)
            return

        # figure out what kind of expression this is
        delimiter = None
        if 'D' in formula:
            delimiter = 'D'
            values = formula.split(delimiter)
        elif 'd' in formula:
            delimiter = 'd'
            values = formula.split(delimiter)
        elif '-' in formula:
            delimiter = '-'
            values = formula.split(delimiter)

        # see if it has known form and 2 values
        if delimiter is None or len(values) != 2:
            raise ValueError("unrecognized dice expression")

        # process the values
        if delimiter in ('D', 'd'):
            try:
                self.num_dice = 1 if values[0] == '' else int(values[0])

                # there might be a plus after the dice type
                if '+' in values[1]:
                    parts = values[1].split('+')
                    values[1] = parts[0]
                    values.append(parts[1])
                else:
                    values.append('0')

                self.dice_type = 100 if values[1] == '%' else int(values[1])
                self.plus = int(values[2])
            except ValueError:
                raise ValueError("non-numeric value in dice expression")
        else:
            try:
                self.min_value = int(values[0])
                self.max_value = int(values[1])
                if self.min_value >= self.max_value:
                    self.min_value = None
                    self.max_value = None
                    raise ValueError("illegal range in dice expression")
            except ValueError:
                raise ValueError("non-numeric value in dice expression")

    def str(self):
        """
        return string representation of these dice"
        """
        if self.num_dice is not None and self.dice_type is not None:
            descr = f"{self.num_dice}D{self.dice_type}"
            if self.plus > 0:
                descr += f"+{self.plus}"
        elif self.min_value is not None and self.max_value is not None:
            descr = f"{self.min_value}-{self.max_value}"
        elif self.plus != 0:
            descr = str(self.plus)
        else:
            descr = ""

        return descr

    def roll(self):
        """
        roll this set of dice and return result
        @return: (int) resulting value
        """
        total = 0

        if self.num_dice is not None and self.dice_type is not None:
            for _ in range(self.num_dice):
                total += randint(1, self.dice_type)
        elif self.min_value is not None and self.max_value is not None:
            total = randint(self.min_value, self.max_value)

        return total + self.plus


# UNIT TESTING
def test(formula, min_expected, max_expected, rolls=20):
    """
    test that a formula generates rolls w/expected values
    @param formula: (string) for the DIce
    @param min_expected: minimum expected value
    @param max_expected: maximum expecetd value
    @param rolls: number of test rolls
    """
    dice = Dice(formula)
    min_rolled = 666666
    max_rolled = -666666
    for _ in range(rolls):
        rolled = dice.roll()
        if rolled < min_rolled:
            min_rolled = rolled
        if rolled > max_rolled:
            max_rolled = rolled

    result = "    legal formula "
    if isinstance(formula, str):
        result += '"' + formula + '"'
    else:
        result += str(formula)
    result += f" ({dice.str()}): returns"
    result += f" {rolls} values between {min_rolled} and {max_rolled}"
    print(result)

    assert min_rolled >= min_expected, "roll returns below-minimum values"
    assert max_rolled <= max_expected, "roll returns above-maximum values"

    return min_rolled >= min_expected and max_rolled <= max_expected


def main():
    """
    test cases:
    """

    # test valid dice expressions
    tests_run = 0
    tests_passed = 0

    tests_run += 1
    if test("3D4", 3, 12, 40):
        tests_passed += 1

    tests_run += 1
    if test("d20", 1, 20, 80):
        tests_passed += 1

    tests_run += 1
    if test("D%", 1, 100, 300):
        tests_passed += 1

    tests_run += 1
    if test("2D2+3", 5, 7):
        tests_passed += 1

    tests_run += 1
    if test("3-9", 3, 9):
        tests_passed += 1

    tests_run += 1
    if test("47", 47, 47, 10):
        tests_passed += 1

    tests_run += 1
    if test(47, 47, 47, 10):
        tests_passed += 1

    tests_run += 1
    if test("-3", -3, -3, 10):
        tests_passed += 1

    # test detection of invalid expressions
    for formula in ["2D", "D", "xDy",
                    "4-2", "-", "3-", "x-y",
                    "7to9"]:
        tests_run += 1
        try:
            _dice = Dice(formula)
            sys.stderr.write("    ERROR: illegal formula")
            sys.stderr.write(f"{formula} accepted as {_dice.str()}\n")
        except ValueError:
            print(f"  illegal formula {formula}: {sys.exc_info()[1]}")
            tests_passed += 1

    print()
    if tests_run == tests_passed:
        print(f"Passed all {tests_passed} Dice tests")
    else:
        missed = tests_run - tests_passed
        print(f"FAILED {missed}/{tests_run} Dice tests")


if __name__ == "__main__":
    main()
