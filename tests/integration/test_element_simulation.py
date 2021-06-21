# coding=utf-8
"""
Created on 07.03.2020

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2020 Juhani Sundell, Tuomas Pitkänen

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
__author__ = "Juhani Sundell \n Tuomas Pitkänen"
__version__ = "2.0"

import unittest
import tempfile

import tests.utils as utils
import tests.mock_objects as mo

from pathlib import Path
from unittest.mock import patch
from unittest.mock import Mock

from modules.request import Request
from modules.element_simulation import ElementSimulation
from modules.detector import Detector
from modules.element import Element
from modules.simulation import Simulation
from modules.global_settings import GlobalSettings
from modules.recoil_element import RecoilElement
from modules.point import Point
from modules.run import Run
from modules.sample import Sample


class TestElementSimulationSettings(unittest.TestCase):
    # TODO: This test doesn't make much sense after changing how default
    #       settings work with ElementSimulations. Convert this into a
    #       general integration test for ElementSimulation.
    def test_elementsimulation_settings(self):
        """This tests that ElementSimulation is run with the correct settings
        depending on how 'use_default_settings' and 'use_request_settings'
        have been set.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            # File paths
            tmp_dir = Path(tmp_dir).resolve()
            req_dir = tmp_dir / "req"
            sim_dir = req_dir / "Sample_01-foo" / \
                f"{Simulation.DIRECTORY_PREFIX}01-bar"
            simu_file = sim_dir / "bar.simulation"

            # Request
            request = Request(
                req_dir, "test_req", GlobalSettings(config_dir=tmp_dir), {})

            self.assertEqual(req_dir, request.directory)
            self.assertEqual("test_req", request.request_name)

            # Sample
            sample = request.samples.add_sample(name="foo")
            self.assertIs(sample, request.samples.samples[0])
            self.assertIsInstance(sample, Sample)
            self.assertEqual("foo", sample.name)
            self.assertEqual(request, sample.request)
            self.assertEqual("Sample_01-foo", sample.directory)

            # Simulation
            sim = sample.simulations.add_simulation_file(
                sample, simu_file, 0)
            self.assertIs(sim, sample.simulations.get_key_value(0))
            self.assertIsInstance(sim.detector, Detector)
            self.assertIsInstance(sim.run, Run)
            self.assertEqual("bar", sim.name)
            self.assertEqual(request, sim.request)
            self.assertEqual(sample, sim.sample)

            # ElementSimulation
            rec_elem = RecoilElement(
                Element.from_string("Fe"), [Point((1, 1))], name="recoil_name")
            elem_sim = sim.add_element_simulation(rec_elem)
            self.assertIs(elem_sim, sim.element_simulations[0])
            elem_sim.number_of_preions = 2
            elem_sim.number_of_ions = 3
            self.assertEqual(request, elem_sim.request)
            self.assertEqual("Fe-Default", elem_sim.get_full_name())

            # Disable logging so the logging file handlers do not cause
            # an exception when the tmp dir is removed
            utils.disable_logging()

            # Some pre-simulation checks
            self.assertIsNot(sim.target, request.default_target)
            self.assertIsNot(elem_sim, request.default_element_simulation)
            self.assertIsNot(sim.detector, request.default_detector)
            self.assertIsNot(sim.run, request.default_run)
            self.assertIsNot(sim.run.beam, request.default_run.beam)
            self.assertNotEqual(
                elem_sim.number_of_ions,
                request.default_element_simulation.number_of_ions)

            self.assert_expected_settings(elem_sim, request, sim)

            # # Test with all setting combinations
            # elem_sim.use_default_settings = True
            # sim.use_request_settings = True
            # self.assert_expected_settings(elem_sim, request, sim)
            #
            # elem_sim.use_default_settings = True
            # sim.use_request_settings = False
            # self.assert_expected_settings(elem_sim, request, sim)
            #
            # elem_sim.use_default_settings = False
            # sim.use_request_settings = True
            # self.assert_expected_settings(elem_sim, request, sim)
            #
            # elem_sim.use_default_settings = False
            # sim.use_request_settings = False
            # self.assert_expected_settings(elem_sim, request, sim)

        self.assertFalse(tmp_dir.exists())

    @patch("modules.mcerd.MCERD.__init__", return_value=None)
    @patch("modules.mcerd.MCERD.run", return_value=mo.get_mcerd_stream())
    def assert_expected_settings(self, elem_sim: ElementSimulation,
                                 request: Request, sim: Simulation,
                                 mock_run: Mock, mock_mcerd: Mock):
        elem_sim.start(1, 1, use_old_erd_files=False).run()
        mock_run.assert_called_once()

        elem_sim._set_flags(False)
        args = mock_mcerd.call_args[0]
        seed, d = args[0], args[1]
        settings = {**d, "seed_number": seed}
        self.assertEqual(
            get_expected_settings(elem_sim, request, sim), settings)


def get_expected_settings(elem_sim: ElementSimulation, request: Request,
                          simulation: Simulation):
    detector = simulation.detector
    run = simulation.run
    expected_sim = elem_sim

    return {
        "simulation_type": elem_sim.simulation_type,
        "number_of_ions": expected_sim.number_of_ions,
        "number_of_ions_in_presimu": expected_sim.number_of_preions,
        "number_of_scaling_ions": expected_sim.number_of_scaling_ions,
        "number_of_recoils": elem_sim.number_of_recoils,
        "minimum_scattering_angle": expected_sim.minimum_scattering_angle,
        "minimum_main_scattering_angle":
            expected_sim.minimum_main_scattering_angle,
        "minimum_energy_of_ions": expected_sim.minimum_energy,
        "simulation_mode": expected_sim.simulation_mode,
        "seed_number": 1,
        "beam": run.beam,
        # Always use the target from simulation
        "target": simulation.target,
        "detector": detector,
        "recoil_element": elem_sim.get_main_recoil(),
        "sim_dir": elem_sim.directory
    }


if __name__ == '__main__':
    unittest.main()
