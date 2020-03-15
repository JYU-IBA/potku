# coding=utf-8
"""
Created on 8.2.2020

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
import tempfile
import os

from modules.detector import Detector
from modules.foil import CircularFoil
from modules.foil import RectangularFoil


class TestBeam(unittest.TestCase):
    def setUp(self):
        path = os.path.join(tempfile.gettempdir(), ".detector")
        mesu = os.path.join(tempfile.gettempdir(), "mesu")
        self.det = Detector(path, mesu, save_in_creation=False)
        self.unit_foil = CircularFoil(diameter=1, distance=1, transmission=1)
        self.rect_foil = RectangularFoil(size_x=2, size_y=2, distance=2,
                                         transmission=2)

    def test_get_mcerd_params(self):
        self.assertEqual(
            ["Detector type: TOF",
             "Detector angle: 41",
             "Virtual detector size: 2.0 5.0",
             "Timing detector numbers: 1 2"],
            self.det.get_mcerd_params()
        )

    def test_default_init(self):
        # If no foils are given, detector is initialized with 4 default foils
        self.assertEqual(4, len(self.det.foils))
        self.assertEqual([1, 2], self.det.tof_foils)

    def test_calculate_smallest_solid_angle(self):
        self.assertAlmostEqual(0.1805,
                               self.det.calculate_smallest_solid_angle(),
                               places=3)

        self.det.foils.clear()
        self.assertEqual(0, self.det.calculate_smallest_solid_angle())

        self.det.foils.append(self.unit_foil)
        self.assertAlmostEqual(785.398,
                               self.det.calculate_smallest_solid_angle(),
                               places=3)

    def test_calculate_solid(self):
        self.assertAlmostEqual(0.1805,
                               self.det.calculate_solid(),
                               places=3)

        self.det.foils.clear()
        self.assertEqual(0, self.det.calculate_solid())

        self.det.foils.append(self.unit_foil)
        self.assertAlmostEqual(785.398,
                               self.det.calculate_solid(),
                               places=3)

        self.det.foils.append(self.rect_foil)
        self.assertAlmostEqual(1570.796,
                               self.det.calculate_solid(),
                               places=3)
