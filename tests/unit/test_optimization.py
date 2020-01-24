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

from modules import general_functions as gf


class TestOptimization(unittest.TestCase):
    def test_dominates(self):
        """Testing dominates function."""
        # Testing identical solutions
        self.assertFalse(gf.dominates([0, 0, 0], [0, 0, 0]))
        self.assertFalse(gf.dominates([1, 0, 0], [1, 0, 0]))
        self.assertFalse(gf.dominates([0, 1, 0], [0, 1, 0]))
        self.assertFalse(gf.dominates([0, 0, 1], [0, 0, 1]))
        self.assertFalse(gf.dominates([1, 1, 1], [1, 1, 1]))
        self.assertFalse(gf.dominates([1, 0, 1], [1, 0, 1]))

        # Testing to see that correct value is returned when
        # order of the parameters is switched
        self.assertFalse(gf.dominates([1, 0, 0], [0, 0, 0]))
        self.assertFalse(gf.dominates([0, 1, 0], [0, 0, 0]))
        self.assertFalse(gf.dominates([0, 0, 1], [0, 0, 0]))
        self.assertTrue(gf.dominates([0, 0, 0], [1, 0, 0]))
        self.assertTrue(gf.dominates([0, 0, 0], [0, 1, 0]))
        self.assertTrue(gf.dominates([0, 0, 0], [0, 0, 1]))

        self.assertFalse(gf.dominates([1, 0, 0], [0, 1, 0]))
        self.assertFalse(gf.dominates([0, 1, 0], [1, 0, 0]))

        self.assertTrue(gf.dominates([0, 0, 0], [1, 1, 1]))
        self.assertFalse(gf.dominates([1, 1, 1], [0, 0, 0]))

        self.assertFalse(gf.dominates([1, 2, 0], [1, 1, 1]))
        self.assertFalse(gf.dominates([1, 1, 1], [1, 2, 0]))

        # Testing empty lists
        self.assertFalse(gf.dominates([], []))

        # Different size lists.
        self.assertRaises(
            IndexError, lambda: gf.dominates([1, 1, 1, 1], [1, 1, 1]))
        self.assertFalse(gf.dominates([1, 1, 1], [1, 1, 1, 1]))

