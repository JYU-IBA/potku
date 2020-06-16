# coding=utf-8
"""
Created on 06.06.2020

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
__author__ = ""  # TODO
__version__ = ""  # TODO

import unittest
import tempfile
import os
import tests.utils as utils
import tests.mock_objects as mo

from pathlib import Path

from modules.request import Request


class TestInit(unittest.TestCase):
    def setUp(self):
        # Expected folder structure when request is saved
        self.folder_name = "foo"
        self.folder_structure = {
            "Default": {
                "Detector": {
                    "Efficiency_files": {},
                    "Default.detector": None
                },
                "Default.measurement": None,
                "default.log": None,
                "Default.simulation": None,
                "Default.mcsimu": None,
                "Default.profile": None,
                "4He-Default.rec": None,
                "Default.target": None,
                "Default_element.profile": None,
                "Default.info": None,
                "errors.log": None
            },
            "request.log": None,
            f"{self.folder_name}.request": None
        }

    def test_folder_structure(self):
        """Tests the folder structure when request is created"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir, self.folder_name)
            Request(path, "bar", mo.get_global_settings(),
                    save_on_creation=False, enable_logging=False)

            self.assertEqual([], os.listdir(tmp_dir))

            request = Request(path, "bar", mo.get_global_settings(),
                              save_on_creation=True, enable_logging=False)

            utils.assert_folder_structure_equal(self.folder_structure, path)

            request.to_file()
            utils.assert_folder_structure_equal(self.folder_structure, path)

            utils.disable_logging()


class TestSerialization(unittest.TestCase):
    def test_serialization(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir, "request")
            request = Request(path, "foo", mo.get_global_settings(),
                              save_on_creation=False, enable_logging=False)

            request.default_run.charge = 1
            request.default_run.fluence = 2
            request.default_target.description = "foo"

            request.to_file()

            request_from_file = Request.from_file(
                request.request_file, mo.get_global_settings())

            self.assertEqual(
                request.default_run.get_settings(),
                request_from_file.default_run.get_settings()
            )

            self.assertEqual(
                request.default_target.description,
                request_from_file.default_target.description
            )

            utils.disable_logging()

    def test_default_values_are_same(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir, "request")
            request = Request(path, "foo", mo.get_global_settings(),
                              save_on_creation=True, enable_logging=False)
            self.assert_request_values_are_same(request)

            request_from_file = Request.from_file(
                request.request_file, mo.get_global_settings())
            self.assert_request_values_are_same(request_from_file)

            self.assertEqual(
                request.request_file, request_from_file.request_file
            )
            self.assertEqual(
                request.directory, request_from_file.directory
            )

            self.assertIsNot(
                request, request_from_file
            )
            self.assertIsNot(
                request.default_measurement,
                request_from_file.default_measurement
            )
            self.assertIsNot(
                request.default_simulation,
                request_from_file.default_simulation
            )
            utils.disable_logging()

    @staticmethod
    def assert_request_values_are_same(request: Request):
        utils.assert_all_same(
            request,
            request.default_measurement.request,
            request.default_simulation.request
        )
        utils.assert_all_same(
            request.default_detector,
            request.default_measurement.detector,
            request.default_simulation.detector
        )
        utils.assert_all_same(
            request.default_run,
            request.default_measurement.run,
            request.default_simulation.run
        )
        utils.assert_all_same(
            request.default_target,
            request.default_measurement.target,
            request.default_simulation.target
        )
