# coding=utf-8
"""
Created on 05.06.2020

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
import copy
import os

import tests.utils as utils
import tests.mock_objects as mo

from pathlib import Path

from modules.measurement import Measurement


class TestFolderStructure(unittest.TestCase):
    def setUp(self):
        self.mesu_name = "foo"
        self.settings_file = "baz"
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
            }
        }
        self.after_to_file = copy.deepcopy(self.folder_structure)
        self.after_to_file["mesu"].update({
            "Detector": {
                "Default.detector": None
            },
            f"{self.mesu_name}.info": None,
            f"Default.profile": None,
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
                save_on_creation=False,
                enable_logging=False)

            # No files or folders should be created...
            utils.assert_folder_structure_equal({}, Path(tmp_dir))

            # ... until create_folder_structure is called
            mesu.create_folder_structure(path)
            utils.assert_folder_structure_equal(
                self.folder_structure, Path(tmp_dir))

            mesu.to_file()

            utils.assert_folder_structure_equal(
                self.after_to_file, Path(tmp_dir))

    def test_get_measurement_files(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir, self.mesu_folder)
            mesu = Measurement(
                mo.get_request(), path / "mesu.info",
                measurement_setting_file_name=self.mesu_name,
                save_on_creation=False,
                enable_logging=False)
            mesu.create_folder_structure(path)
            mesu.to_file()

            profile_file, mesu_file, tgt_file, det_file = \
                Measurement.find_measurement_files(path)

            self.assertEqual(
                path / f"Default.profile", profile_file)
            self.assertEqual(
                path / f"{self.mesu_name}.measurement", mesu_file)

            self.assertEqual(
                path / f"Default.target", tgt_file)
            self.assertEqual(
                path / "Detector" / f"Default.detector", det_file)

    def test_rename_cuts(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir, self.mesu_folder)
            mesu = Measurement(
                mo.get_request(), path / f"foo.info",
                name="foo",
                measurement_setting_file_name=self.settings_file,
                save_on_creation=False,
                enable_logging=False)
            mesu.create_folder_structure(path)
            mesu.to_file()

            cuts = [
                "foo.H.0.0.cut",
                "foo.He.0.0.cut"
            ]
            for cut in cuts:
                fp = mesu.get_cuts_dir() / cut
                fp.open("w").close()
                fp = mesu.get_changes_dir() / cut
                fp.open("w").close()

            mesu.name = "bar"
            mesu.rename_cut_files()
            expected = sorted([
                "bar.H.0.0.cut",
                "bar.He.0.0.cut"
            ])
            self.assertEqual(
                expected, sorted(os.listdir(mesu.get_cuts_dir()))
            )
            self.assertEqual(
                expected, sorted(os.listdir(mesu.get_changes_dir()))
            )

    def test_rename_measurement(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir)
            mesu_path = path / "mesu"
            mesu_name = "foo"
            measurement = Measurement(
                mo.get_request(), path=mesu_path / f"{mesu_name}.info",
                name=mesu_name, save_on_creation=False, enable_logging=False)
            measurement.create_folder_structure(mesu_path)
            measurement.to_file()

            utils.assert_folder_structure_equal(
                get_extected_folder_structure("mesu", "foo"),
                path)

            measurement.rename("bar")

            utils.assert_folder_structure_equal(
                get_extected_folder_structure('Measurement_00-bar', "bar"),
                path
            )


def get_extected_folder_structure(root, name):
    return {
        root: {
            f"{name}.info": None,
            "Default.measurement": None,
            "Default.profile": None,
            "Default.target": None,
            "Detector": {
                "Default.detector": None
            },
            "Composition_changes": {
                "Changes": {}
            },
            "Data": {
                "Cuts": {}
            },
            "Depth_profiles": {},
            "Energy_spectra": {},
            "tof_in": {}
        }
    }