# coding=utf-8
"""
Created on 16.05.2020

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
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program (file named 'LICENCE').
"""
__author__ = "Juhani Sundell"
__version__ = "2.0"

import unittest
import tempfile
import tests.mock_objects as mo
import random

from modules.enums import IonDivision
from modules.enums import CrossSection
from modules.global_settings import GlobalSettings
from pathlib import Path


class TestGlobalSettings(unittest.TestCase):
    def setUp(self) -> None:
        self.gs = GlobalSettings(tempfile.gettempdir(), save_on_creation=False)

    def test_initialization(self):
        """Upon initialization, global settings creates a directory containing
        an ini file and request directory if save on creation is True.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir, "settings")
            file = path / "potku2.ini"
            global_settings = GlobalSettings(
                config_dir=path, save_on_creation=False)

            self.assertFalse(path.exists())
            self.assertFalse(file.exists())
            self.assertFalse(global_settings.get_request_directory().exists())

            global_settings = GlobalSettings(
                config_dir=path, save_on_creation=True)

            self.assertTrue(path.exists())
            self.assertTrue(file.exists())
            # Request directory is not created
            self.assertFalse(global_settings.get_request_directory().exists())

    def test_boolean_getters(self):
        self.gs.set_tofe_transposed(False)
        self.assertFalse(self.gs.get_tofe_transposed())
        self.gs.set_tofe_transposed(True)
        self.assertTrue(self.gs.get_tofe_transposed())

        self.gs.set_tofe_invert_y(False)
        self.assertFalse(self.gs.get_tofe_invert_y())
        self.gs.set_tofe_invert_y(True)
        self.assertTrue(self.gs.get_tofe_invert_y())

    def test_int_getters(self):
        self.gs.set_import_coinc_count(555)
        self.assertEqual(555, self.gs.get_import_coinc_count())

        # Some keys have default values in case conversion fails
        self.gs.set_import_coinc_count("seven")
        self.assertEqual(10000, self.gs.get_import_coinc_count())

    def test_cross_section(self):
        self.assertEqual(CrossSection.ANDERSEN, self.gs.get_cross_sections())
        self.gs.set_cross_sections(CrossSection.LECUYER)
        self.assertEqual(CrossSection.LECUYER, self.gs.get_cross_sections())
        self.gs.set_cross_sections(CrossSection.RUTHERFORD)
        self.assertEqual(CrossSection.RUTHERFORD, self.gs.get_cross_sections())

    def test_ion_division(self):
        self.gs.set_ion_division(IonDivision.BOTH)
        self.assertEqual(IonDivision.BOTH, self.gs.get_ion_division())

        self.gs.set_ion_division(IonDivision.SIM)
        self.assertEqual(IonDivision.SIM, self.gs.get_ion_division())

        self.gs.set_ion_division(IonDivision.NONE)
        self.assertEqual(IonDivision.NONE, self.gs.get_ion_division())

    def test_serialiazation(self):
        """Deserialized GlobalSettings object should have the same
        values as the serialized object.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir, "settings")
            gs1 = GlobalSettings(config_dir=path, save_on_creation=False)
            gs1.set_cross_sections(2)
            gs1.set_element_color("He", "blue")
            gs1.set_tofe_transposed(False)
            gs1.set_request_directory(Path(tmp_dir, "requests2"))
            gs1.set_tofe_bin_range_x(444, 555)
            gs1.set_num_iterations(13)
            gs1.save_config()

            gs2 = GlobalSettings(config_dir=path, save_on_creation=False)
            self.assert_settings_equal(gs1, gs2)

    def test_reading_empty_or_half_file(self):
        """If the ini file is empty or keys are missing, GlobalSettings
        reverts to default values."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            ini_file = Path(tmp_dir, "potku2.ini")
            open(ini_file, "a").close()
            gs = GlobalSettings(tmp_dir, save_on_creation=False)
            # Update directories
            self.gs.set_config_dir(tmp_dir)
            self.gs.set_request_directory(Path(tmp_dir, "requests"))
            self.gs.set_request_directory_last_open(Path(tmp_dir, "requests"))
            self.assert_settings_equal(self.gs, gs)

            # Save the file
            self.gs.save_config()
            # Remove every second line from the ini file
            with open(ini_file, "r") as f:
                lines = f.readlines()
            self.assertTrue(1 < len(lines))
            with open(ini_file, "w") as f:
                for line in lines[::2]:
                    f.write(line)

            gs = GlobalSettings(tmp_dir, save_on_creation=False)
            self.assert_settings_equal(self.gs, gs)

    def test_reading_bad_values(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            self.gs.set_config_dir(tmp_dir)
            self.gs.set_request_directory(Path(tmp_dir, "requests"))
            self.gs.set_request_directory_last_open(Path(tmp_dir, "requests"))
            self.gs.save_config()

            ini_file = self.gs.get_config_file()
            with open(ini_file, "r") as f:
                lines = f.readlines()
            self.assertTrue(1 < len(lines))
            with open(ini_file, "w") as f:
                for line in lines:
                    if line.strip().startswith("compression_y"):
                        line = "compression_y = True\n"
                    elif line.strip().startswith("transpose"):
                        line = "transpose =\n"
                    f.write(line)
                f.write("foo = bar\n")
                f.write("bar\n")

            gs = GlobalSettings(config_dir=tmp_dir, save_on_creation=False)
            self.assert_settings_equal(self.gs, gs)

    def assert_settings_equal(self, gs1: GlobalSettings, gs2: GlobalSettings):
        getters = [
            method for method in dir(gs1) if
            method.startswith("get") or method.startswith("is")
        ]

        for getter in getters:
            if getter == "get_element_color":
                args = mo.get_element(randomize=True).symbol,
            elif getter == "get_import_timing":
                args = random.randint(0, 2),
            else:
                args = ()

            val1 = getattr(gs1, getter)(*args)
            val2 = getattr(gs2, getter)(*args)

            if getter == "get_element_colors":

                continue    # FIXME
                val1 = dict(val1)
                val2 = dict(val2)
            self.assertEqual(val1, val2)

