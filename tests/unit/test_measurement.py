# coding=utf-8
"""
Created on 05.06.2020

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
import copy

import tests.utils as utils
import tests.mock_objects as mo

from pathlib import Path

from modules.measurement import Measurement


class TestFolderStructure(unittest.TestCase):
    def setUp(self):
        self.mesu_name = "foo"
        self.settings_file = "baz"
        self.profile_name = "bar"
        self.mesu_folder = "mesu"
        self.folder_structure = {
            "mesu": {
                "Depth_profiles": {},
                "tof_in": {},
                "Data": {
                    "Cuts": {}
                },
                "Energy_spectra": {},
                "Composition_changes": {
                    "Changes": {}
                },
                "default.log": None,
                "errors.log": None
            }
        }
        self.after_to_file = copy.deepcopy(self.folder_structure)
        self.after_to_file["mesu"].update({
            "Detector": {
                "measurement.detector": None
            },
            f"{self.mesu_name}.info": None,
            f"{self.profile_name}.profile": None,
            f"{self.settings_file}.measurement": None,
            "Default.target": None
        })

    def test_folder_structure(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir, self.mesu_folder)
            mesu = Measurement(
                mo.get_request(), path / f"{self.mesu_name}.info",
                name=self.mesu_name,
                measurement_setting_file_name=self.settings_file,
                profile_name=self.profile_name, save_on_creation=False)
            utils.disable_logging()

            # No files or folders should be created...
            utils.assert_folder_structure_equal({}, Path(tmp_dir))

            # ... until create_folder_structure is called
            mesu.create_folder_structure(path)
            utils.assert_folder_structure_equal(
                self.folder_structure, Path(tmp_dir))

            mesu.to_file()

            utils.assert_folder_structure_equal(
                self.after_to_file, Path(tmp_dir))

            utils.disable_logging()

    def test_get_measurement_files(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir, self.mesu_folder)
            mesu = Measurement(
                mo.get_request(), path / "mesu.info",
                measurement_setting_file_name=self.mesu_name,
                profile_name=self.profile_name, save_on_creation=False)
            utils.disable_logging()
            mesu.create_folder_structure(path)
            mesu.to_file()

            profile_file, mesu_file, tgt_file, det_file = \
                Measurement.find_measurement_files(path)

            self.assertEqual(
                path / f"{self.profile_name}.profile", profile_file)
            self.assertEqual(
                path / f"{self.mesu_name}.measurement", mesu_file)

            self.assertEqual(
                path / f"Default.target", tgt_file)
            self.assertEqual(
                path / "Detector" / f"measurement.detector", det_file)

            utils.disable_logging()
