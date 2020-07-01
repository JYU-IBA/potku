# coding=utf-8
"""
Created on 26.1.2020

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2020 Juhani Sundell

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
__version__ = "2.0"

import unittest

import tests.utils as utils

from modules.foil import Foil
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
        self.assertRaises(AttributeError,
                          lambda: utils.slots_test(RectangularFoil()))
        self.assertRaises(AttributeError,
                          lambda: utils.slots_test(CircularFoil()))

    def test_get_mcerd_params(self):
        unit_rec = RectangularFoil(size_x=1.0, size_y=1.0, distance=1.0)
        self.assertEqual([
            "Foil type: rectangular",
            "Foil size: 1.0 1.0",
            "Foil distance: 1.0"
        ], unit_rec.get_mcerd_params())

        unit_rec = CircularFoil(diameter=1.0, distance=1.0)
        self.assertEqual([
            "Foil type: circular",
            "Foil diameter: 1.0",
            "Foil distance: 1.0"
        ], unit_rec.get_mcerd_params())

    def test_to_dict(self):
        self.assertEqual({
            "type": "circular",
            "distance": 0,
            "transmission": 1.0,
            "diameter": 0,
            "layers": [],
            "name": "Default"
        }, CircularFoil().to_dict())
        self.assertEqual("rectangular", RectangularFoil().to_dict()["type"])

    def test_foil_factory_default_args(self):
        self.assertIsInstance(Foil.generate_foil("circular"),
                              CircularFoil)
        self.assertIsInstance(Foil.generate_foil("rectangular"),
                              RectangularFoil)

    def test_foil_factory_kwargs(self):
        kwargs = {
            "type": "circular",
            "transmission": 1,
            "diameter": 5.5,
            "distance": 0.2
        }
        f = Foil.generate_foil(**kwargs)
        self.assertEqual(1, f.transmission)
        self.assertEqual(5.5, f.diameter)
        self.assertEqual(0.2, f.distance)

        kwargs = {
            "type": "rectangular",
            "transmission": 0.5,
            "size_x": 2,
            "size_y": 3,
            "distance": 4
        }
        f = Foil.generate_foil(**kwargs)
        self.assertEqual(0.5, f.transmission)
        self.assertEqual((2, 3), f.size)
        self.assertEqual(4, f.distance)

    def test_bad_foil_factory_args(self):
        self.assertRaises(TypeError, lambda: Foil.generate_foil())
        self.assertRaises(ValueError, lambda: Foil.generate_foil(None))
        self.assertRaises(TypeError, lambda: Foil.generate_foil(
            type="rectangular", diameter=3))
        self.assertRaises(TypeError, lambda: Foil.generate_foil(
            type="circular", size_x=3))


if __name__ == "__main__":
    unittest.main()
