# coding=utf-8
"""
Created on 16.02.2020

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
import sys

import widgets.gui_utils as gutils

from unittest.mock import Mock

from modules.element import Element
from widgets.gui_utils import GUIReporter

from PyQt5 import QtWidgets
from PyQt5.Qt import QApplication

app = QApplication(sys.argv)


class TestGUIReporter(unittest.TestCase):
    def setUp(self):
        self.prg_bar = Mock()
        self.reporter = GUIReporter(self.prg_bar)

    def test_reporting(self):
        self.reporter.report(10)
        self.prg_bar.setValue.assert_called_with(10)

        self.reporter.report(15.5)
        self.prg_bar.setValue.assert_called_with(15.5)

    def test_sub_reporting(self):
        sub_reporter = self.reporter.get_sub_reporter(lambda x: x / 2)
        sub_reporter.report(10)
        self.prg_bar.setValue.assert_called_with(5)

    def test_bad_report_values(self):
        # reporter.report only accepts single number as its argument
        self.assertRaises(TypeError,
                          lambda: self.reporter.report())

        self.assertRaises(TypeError,
                          lambda: self.reporter.report(None))

        self.assertRaises(TypeError,
                          lambda: self.reporter.report(10, 15.5))

        self.assertRaises(TypeError,
                          lambda: self.reporter.report("10"))

        self.assertRaises(TypeError,
                          lambda: self.reporter.report([10]))


class TestLoadCombobox(unittest.TestCase):
    def test_load_combox(self):
        combo = QtWidgets.QComboBox()
        gutils.load_isotopes("He", combo)
        self.assertEqual(Element("He", 4), combo.currentData()["element"])
        self.assertTrue(combo.isEnabled())

        gutils.load_isotopes("U", combo)
        self.assertIsNone(combo.currentData())
        self.assertEqual(0, combo.count())

        gutils.load_isotopes("He", combo, show_std_mass=True)
        self.assertEqual(Element("He", None), combo.currentData()["element"])

        gutils.load_isotopes("He", combo, show_std_mass=True, current_isotope=4)
        self.assertEqual(Element("He", 4), combo.currentData()["element"])


class TestFillCombobox(unittest.TestCase):
    def test_fill_combobox(self):
        values = [1, {"foo": "bar"}, "foo", [1, 2]]
        combobox = QtWidgets.QComboBox()
        gutils.fill_combobox(combobox, values)
        self.assertEqual(len(values), combobox.count())
        for i, value in enumerate(values):
            self.assertEqual(value, combobox.itemData(i))
            self.assertEqual(str(value), combobox.itemText(i))

        # Combobox is cleared when fill_combobox is called
        gutils.fill_combobox(combobox, ["kissa istuu"])
        self.assertEqual(1, combobox.count())
        self.assertEqual("kissa istuu", combobox.currentData())


if __name__ == '__main__':
    unittest.main()
