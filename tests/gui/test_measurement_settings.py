# coding=utf-8
"""
Created on 05.04.2020

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
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program (file named 'LICENCE').
"""
__author__ = "Juhani Sundell"
__version__ = "2.0"

import unittest

import tests.gui
import tests.mock_objects as mo
import tests.utils as utils

from modules.element import Element
from modules.enums import Profile
from widgets.measurement.settings import MeasurementSettingsWidget


class MyTestCase(unittest.TestCase):
    @utils.change_wd_to_root
    def setUp(self):
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
        self.assertEqual(
            13,
            self.mesu_widget.isotopeComboBox.currentData()["element"].isotope)

        # Set ion to None
        self.mesu_widget.beam_ion = None
        self.assertIsNone(self.mesu_widget.beam_ion)
        self.assertEqual("Select", self.mesu_widget.beamIonButton.text())
        self.assertFalse(self.mesu_widget.isotopeComboBox.isEnabled())

    def test_update_settings(self):
        # Assert that measurement's ion is changed to widget's ion after update
        elem = Element("H", 2)
        self.mesu_widget.beam_ion = elem
        self.assertNotEqual(self.mesu_widget.obj.run.beam.ion,
                            self.mesu_widget.beam_ion)
        self.mesu_widget.update_settings()
        self.assertEqual(self.mesu_widget.obj.run.beam.ion,
                         self.mesu_widget.beam_ion)

    def test_profile_value(self):
        self.assertEqual(self.mesu_widget.beam_profile, Profile.UNIFORM)
        self.mesu_widget.beam_profile = Profile.GAUSSIAN
        self.assertEqual(self.mesu_widget.beam_profile, Profile.GAUSSIAN)


if __name__ == '__main__':
    unittest.main()
