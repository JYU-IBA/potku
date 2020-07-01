# coding=utf-8
"""
Created on 16.05.2020

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
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program (file named 'LICENCE').
"""
__author__ = "Juhani Sundell"
__version__ = "2.0"

import unittest
import random
import math

from modules.enums import IonDivision
from modules.enums import SimulationMode
from modules.enums import SimulationType


class TestIonDivision(unittest.TestCase):
    def test_ion_counts(self):
        presim = 10_000
        sim = 1_000_000
        processes = 4
        args = presim, sim, processes

        self.assertEqual(
            (presim, sim),
            IonDivision.NONE.get_ion_counts(*args)
        )

        self.assertEqual(
            (presim, 250_000),
            IonDivision.SIM.get_ion_counts(*args)
        )

        self.assertEqual(
            (2_500, 250_000),
            IonDivision.BOTH.get_ion_counts(*args)
        )

    def test_negative_ions(self):
        """Negative ions default to 0
        """
        self.assertEqual(
            (0, 25),
            IonDivision.BOTH.get_ion_counts(-100, 100, 4)
        )
        self.assertEqual(
            (25, 0),
            IonDivision.BOTH.get_ion_counts(100, -100, 4)
        )

    def test_non_positive_processes(self):
        """Process counts that are zero or less default to 1.
        """
        self.assertEqual(
            (200, 200),
            IonDivision.BOTH.get_ion_counts(200, 200, 0)
        )

        self.assertEqual(
            (200, 200),
            IonDivision.BOTH.get_ion_counts(200, 200, -10)
        )

    def test_properties(self):
        """Ion counts should always be non-negative integers.
        """
        n = 100
        a = -1_000
        b = 1_000
        for _ in range(n):
            division = random.choice(list(IonDivision))
            args = list(random.uniform(a, b) for _ in range(3))
            presim, sim = division.get_ion_counts(*args)
            self.assertTrue(0 <= presim <= math.fabs(args[0]))
            self.assertTrue(0 <= sim <= math.fabs(args[1]))
            self.assertIsInstance(presim, int)
            self.assertIsInstance(sim, int)


class TestSimulationEnums(unittest.TestCase):
    def test_init(self):
        self.assertEqual(SimulationMode.NARROW, SimulationMode("narrow"))
        self.assertEqual(SimulationMode.WIDE, SimulationMode("wide"))
        self.assertRaises(ValueError, lambda: SimulationMode("Narrow"))
        self.assertRaises(ValueError, lambda: SimulationMode("Wide"))

        self.assertEqual(SimulationType.RBS, SimulationType("RBS"))
        self.assertEqual(SimulationType.ERD, SimulationType("ERD"))
        self.assertRaises(ValueError, lambda: SimulationMode("rbs"))
        self.assertRaises(ValueError, lambda: SimulationMode("erd"))

    def test_str(self):
        self.assertEqual("Narrow", str(SimulationMode.NARROW))
        self.assertEqual("Wide", str(SimulationMode.WIDE))

        self.assertEqual("SCT", str(SimulationType("RBS")))
        self.assertEqual("REC", str(SimulationType("ERD")))
