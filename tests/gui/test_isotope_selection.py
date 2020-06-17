# coding=utf-8
"""
Created on 13.04.2020

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
import tests.gui

from unittest.mock import Mock
from modules.element import Element

from widgets.isotope_selection import IsotopeSelectionWidget

from PyQt5 import QtWidgets


class TestIsotopeSelectionWidget(unittest.TestCase):
    def setUp(self):
        self.elem_btn = QtWidgets.QPushButton()
        self.isot_box = QtWidgets.QComboBox()
        self.amount_box = QtWidgets.QDoubleSpinBox()
        self.info_label = QtWidgets.QLabel()
        self.parent = Mock()

    def test_elem_btn_and_isot(self):
        """Tests a widget with only element button and """
        w = IsotopeSelectionWidget(self.elem_btn, self.isot_box)

        self.assertEqual("Select", self.elem_btn.text())
        self.assertEqual(0, self.isot_box.count())
        self.assertIsNone(w.get_element())

        w.set_element("He")

        self.assertEqual("He", self.elem_btn.text())
        self.assertEqual(3, self.isot_box.count())
        self.assertEqual(Element("He"), w.get_element())

        # Test changing the index
        self.isot_box.setCurrentIndex(1)

        self.assertEqual(Element("He", 4), w.get_element())

        # Test setting a new element
        w.set_element("13C")
        self.assertEqual("C", self.elem_btn.text())
        self.assertEqual(Element("C", 13), w.get_element())

    def test_bad_inputs(self):
        w = IsotopeSelectionWidget(self.elem_btn, self.isot_box)
        w.set_element("")
        self.assertEqual("Select", self.elem_btn.text())
        self.assertIsNone(w.get_element())

        w.set_element(None)
        self.assertEqual("Select", self.elem_btn.text())

        w.set_element("C")
        self.assertEqual("C", self.elem_btn.text())
        w.set_element("")
        self.assertEqual("Select", self.elem_btn.text())
        self.assertIsNone(w.get_element())
        self.assertEqual(0, self.isot_box.count())

    def test_amount_box(self):
        w = IsotopeSelectionWidget(self.elem_btn, self.isot_box,
                                   amount_input=self.amount_box)

        self.assertEqual(0, self.amount_box.value())

        w.set_element("2H 15.5")
        self.assertEqual(15.5, self.amount_box.value())
        self.assertEqual(Element("H", 2, 15.5), w.get_element())

        self.amount_box.setValue(25.5)
        self.assertEqual(Element("H", 2, 25.5), w.get_element())

    def test_element_with_no_isotopes(self):
        w = IsotopeSelectionWidget(self.elem_btn, self.isot_box,
                                   info_label=self.info_label,
                                   parent=self.parent)

        self.assertEqual("", self.info_label.text())

        w.set_element("U")

        self.assertFalse(self.isot_box.isEnabled())
        self.assertNotEqual("", self.info_label.text())

        self.assertFalse(self.parent.fields_are_valid)


if __name__ == '__main__':
    unittest.main()
