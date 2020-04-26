# coding=utf-8
"""
Created on 2.2.2020

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
__version__ = "2.0"


import unittest
import tempfile
import os
import tests.mock_objects as mo

from unittest.mock import patch
from tests.utils import disable_logging
from modules.simulation import Simulation


class TestSimulation(unittest.TestCase):
    def test_slots(self):
        """Tests that __slots__ work correctly for Simulation."""

        with tempfile.TemporaryDirectory() as temp_dir:
            req = mo.get_request()
            sim = Simulation(os.path.join(temp_dir, "test.simu"), req)

            # Logging needs to be disabled, otherwise loggers retain file
            # handlers that prevent removing the temp_dir
            disable_logging()

            def assign():
                sim.x = 10

            self.assertRaises(AttributeError, lambda: assign())

        # Just in case make sure that the temp_dir got deleted
        self.assertFalse(os.path.exists(temp_dir))

    @patch("modules.mcerd.MCERD")
    @patch("modules.mcerd.MCERD.run")
    @patch("modules.mcerd.MCERD.stop_process")
    def test_get_active_simulation(self, mock1, mock2, mock3):
        sim = mo.get_simulation()

        sim.add_element_simulation(mo.get_recoil_element())
        self.assertEqual(([], [], [], []), sim.get_active_simulations())

        elem_sim = sim.element_simulations[0]
        elem_sim.use_default_settings = False
        elem_sim.start(1, 1)
        self.assertEqual(([elem_sim], [], [], []),
                         sim.get_active_simulations())

        elem_sim.stop()
        self.assertEqual(([], [elem_sim], [], []),
                         sim.get_active_simulations())
