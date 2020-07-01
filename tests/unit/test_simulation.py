# coding=utf-8
"""
Created on 2.2.2020

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
import tempfile
import os

import tests.mock_objects as mo
import tests.utils as utils

from pathlib import Path
from unittest.mock import patch
from modules.simulation import Simulation
from modules.enums import OptimizationType


class TestSimulation(unittest.TestCase):
    def test_slots(self):
        """Tests that __slots__ work correctly for Simulation."""

        with tempfile.TemporaryDirectory() as temp_dir:
            req = mo.get_request()
            sim = Simulation(Path(temp_dir, "test.simu"), req)

            # Logging needs to be disabled, otherwise loggers retain file
            # handlers that prevent removing the temp_dir
            utils.disable_logging()

            self.assertRaises(AttributeError, lambda: utils.slots_test(sim))

        # Just in case make sure that the temp_dir got deleted
        self.assertFalse(os.path.exists(temp_dir))

    @patch("modules.mcerd.MCERD.run", return_value=mo.get_mcerd_stream())
    def test_get_active_simulation(self, mock_run):
        sim = mo.get_simulation()

        sim.add_element_simulation(
            mo.get_recoil_element(), save_on_creation=False)
        self.assertEqual(([], [], [], []), sim.get_active_simulations())

        elem_sim = sim.element_simulations[0]
        elem_sim.use_default_settings = False
        elem_sim.start(1, 1).run()
        self.assertEqual(([], [elem_sim], [], []), sim.get_active_simulations())
        mock_run.assert_called_once()

        elem_sim.optimization_recoils = [mo.get_recoil_element()]
        elem_sim.start(1, 1, optimization_type=OptimizationType.RECOIL).run()
        self.assertEqual(
            ([], [elem_sim], [], [elem_sim]), sim.get_active_simulations())

    def test_serialization(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            fp = Path(tmp_dir, "test.simu")
            sim = Simulation(
                Path(tmp_dir, "foo.simulation"), mo.get_request(), name="foo",
                description="bar", save_on_creation=False, run=mo.get_run(),
                detector=mo.get_detector(), target=mo.get_target(),
                enable_logging=False)

            sim.to_file(fp)

            sim2 = Simulation.from_file(
                mo.get_request(), fp, detector=mo.get_detector(),
                target=mo.get_target(), run=mo.get_run(), enable_logging=False,
                save_on_creation=False)

            self.assertEqual(sim.name, sim2.name)
            self.assertEqual(sim.description, sim2.description)
            self.assertEqual(sim.measurement_setting_file_description,
                             sim2.measurement_setting_file_description)
            self.assertEqual(sim.measurement_setting_file_name,
                             sim2.measurement_setting_file_name)
            self.assertEqual(sim.use_request_settings,
                             sim2.use_request_settings)

            self.assertEqual(sim.detector.name, sim2.detector.name)
            self.assertEqual(sim.detector.angle_offset,
                             sim2.detector.angle_offset)

            self.assertEqual(sim.target.scattering_element,
                             sim2.target.scattering_element)
            self.assertEqual(sim.target.target_type, sim2.target.target_type)

            self.assertEqual(sim.run.fluence, sim2.run.fluence)

    def test_get_recoils(self):
        sim = mo.get_simulation()
        n = 10
        elems = set(mo.get_element(randomize=True, amount_p=0) for _ in
                    range(n))
        rec_elems = [
            mo.get_recoil_element(element=elem) for elem in elems
        ]
        for rec in rec_elems:
            sim.add_element_simulation(rec, save_on_creation=False)

        self.assertEqual(rec_elems, sim.get_recoil_elements())

    def test_has_element(self):
        sim = mo.get_simulation()
        elem = mo.get_element()

        self.assertFalse(sim.has_element(elem))

        rec = mo.get_recoil_element(symbol=elem.symbol)

        sim.add_element_simulation(rec, save_on_creation=False)

        self.assertTrue(sim.has_element(elem))

    def test_can_add_recoil(self):
        sim = mo.get_simulation()
        rec = mo.get_recoil_element()
        self.assertTrue(sim.can_add_recoil(rec))
        sim.add_element_simulation(rec, save_on_creation=False)

        rec2 = mo.get_recoil_element()
        self.assertFalse(sim.can_add_recoil(rec2))

        rec2.element.isotope = 1
        self.assertTrue(sim.can_add_recoil(rec2))

    def test_add_element_simulation(self):
        sim = mo.get_simulation()
        rec_c = mo.get_recoil_element(symbol="C")
        rec_16c = mo.get_recoil_element(symbol="C", isotope=16)

        elem_sim_c = sim.add_element_simulation(rec_c, save_on_creation=False)
        elem_sim_16c = sim.add_element_simulation(
            rec_16c, save_on_creation=False)

        self.assertEqual([elem_sim_c, elem_sim_16c], sim.element_simulations)

    def test_raises_exception_if_recoil_added_twice(self):
        sim = mo.get_simulation()
        rec = mo.get_recoil_element()
        sim.add_element_simulation(rec, save_on_creation=False)
        self.assertRaises(
            ValueError, lambda: sim.add_element_simulation(
                rec, save_on_creation=False))


