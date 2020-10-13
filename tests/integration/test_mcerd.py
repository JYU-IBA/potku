# coding=utf-8
"""
Created on 8.2.2020

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

import tests.mock_objects as mo
import tests.utils as utils

import modules.general_functions as gf

from modules.enums import SimulationType
from modules.enums import SimulationMode
from modules.mcerd import MCERD
from modules.target import Target
from modules.layer import Layer
from modules.element import Element
from pathlib import Path


class TestMCERD(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = Path(tempfile.gettempdir())
        target = Target(layers=[
            Layer("layer1", [
                Element.from_string("Li 1.0")
            ], 0.01, 0.01, start_depth=0.0),
            Layer("layer2", [
                Element.from_string("Li 0.048"),
                Element.from_string("O 0.649"),
                Element.from_string("Mn 0.303")
            ], 90.0, 4.0, start_depth=0.01),
            Layer("subtrate", [
                Element.from_string("Si 1.0")
            ], 1000.0, 2.32, start_depth=90.01)
        ])
        cls.mcerd = MCERD(101, {
            "recoil_element": mo.get_recoil_element(),
            "sim_dir": tempfile.gettempdir(),
            "simulation_type": SimulationType.ERD,
            "target": target,
            "detector": mo.get_detector(),
            "beam": mo.get_beam(),

            # Following simulation parameters have been determined by the
            # rigorous application of the Stetson-Harrison method.
            "minimum_scattering_angle": 5.5,
            "minimum_main_scattering_angle": 6.5,
            "minimum_energy_of_ions": 8.15,
            "number_of_recoils": 15,
            "simulation_mode": SimulationMode.NARROW,
            "number_of_scaling_ions": 14,
            "number_of_ions_in_presimu": 100,
            "number_of_ions": 1000
        }, mo.get_element_simulation().get_full_name())

    def test_get_command(self):
        """Tests the get_command function on different platforms.
        """
        # PlatformSwitcher cannot change the separator char in file paths.
        # Therefore the same bin_path and file_path is used for each system
        bin_path = gf.get_bin_dir() / "mcerd"
        file_path = self.directory / "He-Default"

        with utils.PlatformSwitcher("Windows"):
            cmd = f"{bin_path}.exe", str(file_path)
            self.assertEqual(cmd, self.mcerd.get_command())

        with utils.PlatformSwitcher("Linux"):
            cmd = "./mcerd", str(file_path)
            self.assertEqual(cmd, self.mcerd.get_command())

        with utils.PlatformSwitcher("Darwin"):
            # file_path and command stay same
            self.assertEqual(cmd, self.mcerd.get_command())

    def test_paths(self):
        """Testing various file paths that MCERD uses."""
        self.assertEqual(
            self.directory / "He-Default.recoil",
            self.mcerd.recoil_file)
        self.assertEqual(
            self.directory / "He-Default.101.erd",
            self.mcerd.result_file)
        self.assertEqual(
            self.directory / "He-Default",
            self.mcerd.command_file)

        # These use the parent prefix, therefore they do not start with 'He'
        self.assertEqual(
            self.directory / "Default.erd_target",
            self.mcerd.target_file)
        self.assertEqual(
            self.directory / "Default.erd_detector",
            self.mcerd.detector_file)
        self.assertEqual(
            self.directory / "Default.foils",
            self.mcerd.foils_file)
        self.assertEqual(
            self.directory / "Default.pre",
            self.mcerd.presimulation_file)

    def test_get_command_file_contents(self):
        detector_file = utils.get_resource_dir() / "mcerd_command.txt"

        expected = utils.get_template_file_contents(
            detector_file,
            tgt_file=self.directory / "Default.erd_target",
            det_file=self.directory / "Default.erd_detector",
            rec_file=self.directory / "He-Default.recoil",
            pre_file=self.directory / "Default.pre"
        )
        output = self.mcerd.get_command_file_contents()

        self.assertEqual(expected, output)

    def test_get_detector_file_contents(self):
        detector_file = utils.get_resource_dir() / "detector_file.txt"

        expected = utils.get_template_file_contents(
            detector_file,
            foils_file=self.directory / "Default.foils"
        )
        output = self.mcerd.get_detector_file_contents()

        self.assertEqual(expected, output)

    def test_get_target_file_contents(self):
        target_file = utils.get_resource_dir() / "target_file.txt"

        expected = utils.get_template_file_contents(
            target_file
        )
        output = self.mcerd.get_target_file_contents()

        self.assertEqual(expected, output)

    def test_get_foils_file_contents(self):
        foils_file = utils.get_resource_dir() / "foils_file.txt"
        expected = utils.get_template_file_contents(
            foils_file
        )
        output = self.mcerd.get_foils_file_contents()

        self.assertEqual(expected, output)

    def test_recoil_file_contents(self):
        recoil_file = utils.get_resource_dir() / "mcerd_recoil_file.txt"
        expected = utils.get_template_file_contents(
            recoil_file
        )
        output = self.mcerd.get_recoil_file_contents()

        self.assertEqual(expected, output)
