# coding=utf-8
"""
Created on 23.1.2020

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2020 TODO

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program (file named 'LICENCE').
"""

__author__ = "Juhani Sundell"
__version__ = ""  # TODO

import unittest
import itertools

from modules import general_functions as gf


class TestOptimization(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Sets up ideal and nadir solutions and a couple of fronts
        in between."""
        # Ideal solution dominates all other solutions while
        # nadir is dominated by all
        cls.ideal = [0, 0, 0]
        cls.nadir = [10, 10, 10]

        # Pareto front 1 dominates the second front
        cls.front1 = [
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1],
            [0.5, 0.5, 0.5]
        ]

        cls.front2 = [
            [2, 1, 1],
            [1, 2, 1],
            [1, 1, 2],
            [1.5, 1.5, 1.5]
        ]

    def test_domination(self):
        """Testing that all solutions that should dominate
        other solutions, do so."""
        # Assert that ideal solution dominates all fronts
        self.assert_dominates([self.ideal], self.front1)
        self.assert_dominates([self.ideal], self.front2)
        self.assert_dominates([self.ideal], [self.nadir])

        # Assert that front1 dominates front2 and nadir
        self.assert_dominates(self.front1, self.front2)
        self.assert_dominates(self.front1, [self.nadir])

        # Assert that front2 dominates nadir
        self.assert_dominates(self.front2, [self.nadir])

    def test_nondomination(self):
        """Testing that solutions that do not dominate other
        solutions, do not indeed do so."""
        # Assert that no front dominates ideal (including ideal
        # itself)
        self.assert_not_dominates([self.ideal], [self.ideal])
        self.assert_not_dominates(self.front1, [self.ideal])
        self.assert_not_dominates(self.front2, [self.ideal])
        self.assert_not_dominates([self.nadir], [self.ideal])

        # Assert that front1, front2 and nadir do not dominate
        # front1
        self.assert_not_dominates(self.front1, self.front1)
        self.assert_not_dominates(self.front2, self.front1)
        self.assert_not_dominates([self.nadir], self.front1)

        # Assert that front2 and nadir do not dominate front2
        self.assert_not_dominates(self.front2, self.front2)
        self.assert_not_dominates([self.nadir], self.front2)

        # Assert that nadir does not dominate itself
        self.assert_not_dominates([self.nadir], [self.nadir])

    def test_misc_inputs(self):
        """Tests how the dominates function works when the solutions
        do not have the same number of objective values."""
        self.assertFalse(gf.dominates([], []))
        self.assertFalse(gf.dominates([-1], []))
        self.assertFalse(gf.dominates([], [1]))
        self.assertTrue(gf.dominates([0, 1], [1]))
        self.assertFalse(gf.dominates([0], [0, 1]))
        self.assertFalse(gf.dominates([1], [0, 1]))
        self.assertRaises(TypeError, lambda: gf.dominates("s", [0]))

    def assert_dominates(self, nondominated, dominated):
        """Helper function that checks if the solutions in the nondominated
        set dominate all solutions in the dominated set."""
        for nd, d in itertools.product(nondominated, dominated):
            self.assertTrue(gf.dominates(nd, d))

    def assert_not_dominates(self, set1, set2):
        """Helper function that checks if the solutions in the first
        set do not dominate all solutions in the second set."""
        for sol1, sol2 in itertools.product(set1, set2):
            self.assertFalse(gf.dominates(sol1, sol2))

