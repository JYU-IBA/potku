# coding=utf-8
"""
Created on 26.1.2020

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
from modules.foil import CircularFoil
from modules.foil import RectangularFoil


class TestFoil(unittest.TestCase):
    def test_circular_solid_angle(self):
        """Tests solid angle calculation for circular foil"""
        circular = CircularFoil()
        self.assertRaises(ZeroDivisionError,
                          lambda: circular.get_solid_angle())

        # TODO more realistic numbers
        circular.diameter = 2

        self.assertRaises(ZeroDivisionError,
                          lambda: circular.get_solid_angle())

        circular.distance = 3

        self.assertAlmostEqual(349,
                               circular.get_solid_angle(),
                               delta=0.1)

        self.assertEqual(circular.get_solid_angle(),
                         circular.get_solid_angle(units="msr"))
        self.assertEqual(0.001 * circular.get_solid_angle(),
                         circular.get_solid_angle(units="sr"))

        self.assertEqual(1000 * circular.get_solid_angle(),
                         circular.get_solid_angle(units="usr"))
        circular.diameter = 0
        self.assertEqual(0, circular.get_solid_angle())

        self.assertRaises(ValueError,
                          lambda: circular.get_solid_angle("rad"))


if __name__ == "__main__":
    unittest.main()
