# coding=utf-8
"""
Created on 05.04.2020

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
__author__ = ""  # TODO
__version__ = ""  # TODO

import unittest
import sys
import warnings

import tests.mock_objects as mo
import tests.utils as utils

from modules.element import Element
from widgets.measurement.settings import MeasurementSettingsWidget

from PyQt5.QtWidgets import QApplication
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt


app = QApplication(sys.argv)


class MyTestCase(unittest.TestCase):

    @utils.change_wd_to_root
    def setUp(self):
        with warnings.catch_warnings():
            # Ignore deprecation warning from uic
            warnings.simplefilter("ignore")
            self.mesu_widget = MeasurementSettingsWidget(mo.get_measurement())

    def test_ion_binding(self):
        # This is the default beam ion
        elem = Element("Cl", 35)
        self.assertEqual(elem, self.mesu_widget.beam_ion)
        self.assertFalse(self.mesu_widget.are_values_changed())

        # Change the ion and assert that values are changed and correct
        # values are shown in inputs
        elem = Element.from_string("13C")
        self.mesu_widget.beam_ion = elem

        self.assertTrue(self.mesu_widget.are_values_changed())
        self.assertIsNot(elem, self.mesu_widget.beam_ion)
        self.assertEqual(elem, self.mesu_widget.beam_ion)
        self.assertEqual("C", self.mesu_widget.beamIonButton.text())
        idx = self.mesu_widget.isotopeComboBox.currentIndex()
        self.assertEqual(13, self.mesu_widget.isotopeComboBox.itemData(idx)[0])

        # Set ion to None
        self.mesu_widget.beam_ion = None
        self.assertIsNone(self.mesu_widget.beam_ion)
        self.assertEqual("Select", self.mesu_widget.beamIonButton.text())
        self.assertFalse(self.mesu_widget.isotopeComboBox.isEnabled())

        # Assert that measurement's ion is changed to widget's ion after update
        self.assertNotEqual(self.mesu_widget.obj.run.beam.ion,
                            self.mesu_widget.beam_ion)
        self.mesu_widget.update_settings()
        self.assertEqual(self.mesu_widget.obj.run.beam.ion,
                         self.mesu_widget.beam_ion)


if __name__ == '__main__':
    unittest.main()