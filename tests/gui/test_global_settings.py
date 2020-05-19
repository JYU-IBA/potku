# coding=utf-8
"""
Created on 18.05.2020

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
import sys

import tests.mock_objects as mo

from modules.enums import CrossSection
from modules.enums import IonDivision
from modules.enums import ToFEColorScheme
from tests.utils import change_wd_to_root
from dialogs.global_settings import GlobalSettingsDialog
from PyQt5.Qt import QApplication

app = QApplication(sys.argv)


class TestGlobalSettings(unittest.TestCase):
    @change_wd_to_root
    def setUp(self):
        self.settings = mo.get_global_settings()
        self.gsd = GlobalSettingsDialog(self.settings)

    def test_cross_section_radios(self):
        self.assertEqual(
            self.settings.get_cross_sections(), self.gsd.cross_section)
        self.assertTrue(self.gsd.cross_section_radios.buttons()[2].isChecked())
        self.gsd.cross_section_radios.buttons()[0].setChecked(True)
        self.assertEqual(
            CrossSection.RUTHERFORD, self.gsd.cross_section
        )
        self.gsd.cross_section = CrossSection.LECUYER
        self.assertTrue(self.gsd.cross_section_radios.buttons()[1].isChecked())

    def test_ion_division(self):
        self.assertEqual(
            self.settings.get_ion_division(), self.gsd.ion_division
        )
        self.gsd.ion_division = IonDivision.SIM
        self.assertTrue(self.gsd.ion_division_radios.buttons()[1].isChecked())
        self.gsd.ion_division_radios.buttons()[0].setChecked(True)
        self.assertEqual(IonDivision.NONE, self.gsd.ion_division)

    def test_color_scheme(self):
        self.assertEqual(
            self.settings.get_tofe_color(), self.gsd.color_scheme
        )
        self.gsd.combo_tofe_colors.setCurrentIndex(1)
        self.assertEqual(
            ToFEColorScheme.GREYSCALE, self.gsd.color_scheme
        )
        self.gsd.combo_tofe_colors.setCurrentIndex(2)
        self.assertEqual(
            ToFEColorScheme.INV_GREYSCALE, self.gsd.color_scheme
        )


if __name__ == '__main__':
    unittest.main()
