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

            Request(path, "bar", mo.get_global_settings(),
                    save_on_creation=True, enable_logging=False)

            utils.assert_folder_structure_equal(self.folder_structure, path)
