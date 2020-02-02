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
        default_foil = CircularFoil()
        zero_distance = CircularFoil(diameter=1.0, distance=0.0)
        zero_diameter = CircularFoil(diameter=0.0, distance=1.0)
        unit_foil = CircularFoil(diameter=1.0, distance=1.0)

        self.assertRaises(ZeroDivisionError,
                          lambda: default_foil.get_solid_angle())
        self.assertRaises(ZeroDivisionError,
                          lambda: zero_distance.get_solid_angle())

        self.assertEqual(0, zero_diameter.get_solid_angle())

        self.assertAlmostEqual(785.4,
                               unit_foil.get_solid_angle(),
                               places=2)

        # Testing unit conversions:
        self.check_solid_angle_unit_conversion(unit_foil, 785.4, 785398.16,
                                               0.79, places=2)

        # Radians are not a valid unit
        self.assertRaises(ValueError,
                          lambda: unit_foil.get_solid_angle("rad"))

    def test_rec_foil_solid_angle(self):
        default_foil = RectangularFoil()
        zero_distance = RectangularFoil(size_x=1.0, size_y=1.0, distance=0.0)
        zero_x = RectangularFoil(size_x=0.0, size_y=1.0, distance=1.0)
        zero_y = RectangularFoil(size_x=1.0, size_y=0.0, distance=1.0)
        unit_foil = RectangularFoil(size_x=1.0, size_y=1.0, distance=1.0)

        self.assertRaises(ZeroDivisionError,
                          lambda: default_foil.get_solid_angle())

        self.assertRaises(ZeroDivisionError,
                          lambda: zero_distance.get_solid_angle())

        self.assertEqual(0, zero_x.get_solid_angle())
        self.assertEqual(0, zero_y.get_solid_angle())
        self.assertEqual(1000, unit_foil.get_solid_angle())

        self.check_solid_angle_unit_conversion(unit_foil,
                                               1000,
                                               1000000,
                                               1,
                                               places=2)

    def check_solid_angle_unit_conversion(self, foil, *expected, places=2):
        """Tests unit conversion by comparing the results of get_solid_angle
        function to each expected value.
        """
        msr, usr, sr = expected
        self.assertAlmostEqual(msr,
                               foil.get_solid_angle(units="msr"),
                               places=places)

        self.assertAlmostEqual(usr,
                               foil.get_solid_angle(units="usr"),
                               places=places)

        self.assertAlmostEqual(sr,
                               foil.get_solid_angle(units="sr"),
                               places=places)

    def test_slots(self):
        """Tests that __slots__ work properly for Foils"""
        rec = RectangularFoil()
        cir = CircularFoil()

        def assignment_attempt(obj):
            obj.x = 10

        self.assertRaises(AttributeError, lambda: assignment_attempt(rec))
        self.assertRaises(AttributeError, lambda: assignment_attempt(cir))
        self.assertRaises(AttributeError, lambda: rec.__dict__)
        self.assertRaises(AttributeError, lambda: cir.__dict__)


if __name__ == "__main__":
    unittest.main()
