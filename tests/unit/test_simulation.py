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
__version__ = ""    # TODO


import unittest
import tempfile
import os

from tests.utils import disable_logging
from modules.request import Request
from modules.simulation import Simulation


class TestSimulation(unittest.TestCase):
    def test_slots(self):
        """Tests that __slots__ work correctly for Simulation."""

        with tempfile.TemporaryDirectory() as temp_dir:
            req = Request(temp_dir, "name", "stat", "glo", "tabs")
            sim = Simulation(os.path.join(temp_dir, "test.simu"), req)

            # Logging needs to be disabled, otherwise loggers retain file
            # handlers that prevent removing the temp_dir
            disable_logging()

            def assign():
                sim.x = 10

            self.assertRaises(AttributeError, lambda: assign())

        # Just in case make sure that the temp_dir got deleted
        self.assertFalse(os.path.exists(temp_dir))
