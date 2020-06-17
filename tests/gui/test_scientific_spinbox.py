# coding=utf-8
"""
Created on 25.02.2020

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
import tests.utils as utils
import tests.gui
import math

from widgets.scientific_spinbox import ScientificSpinBox

from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt


class TestSciSpinbox(unittest.TestCase):
    # Change working directory to root so the Spinbox can load ui-files
    @utils.change_wd_to_root
    def setUp(self):
        self.minimum = 1.0e20
        self.maximum = 9.9e23
        self.sbox = ScientificSpinBox(
            1.123e+22, minimum=self.minimum, maximum=self.maximum)

        down_btn = self.sbox.downButton
        up_btn = self.sbox.upButton
        self.click_down = lambda: QTest.mouseClick(down_btn, Qt.LeftButton)
        self.click_up = lambda: QTest.mouseClick(up_btn, Qt.LeftButton)

    def test_display(self):
        self.sbox.minimum = -math.inf

        self.sbox.set_value(5.5e+22)
        self.assertEqual("5.5e+22", self.sbox.scientificLineEdit.text())

        self.sbox.set_value(math.pi * 1e20)
        self.assertEqual(
            "3.1415926535897e+20", self.sbox.scientificLineEdit.text())

        self.sbox.set_value(1.00000e21)
        self.assertEqual("1.0e+21", self.sbox.scientificLineEdit.text())

        self.sbox.set_value(1.00000e-21)
        self.assertEqual("1.0e-21", self.sbox.scientificLineEdit.text())

        self.sbox.set_value(-1.00000e-21)
        self.assertEqual("-1.0e-21", self.sbox.scientificLineEdit.text())

        self.sbox.set_value(0.1)
        self.assertEqual("1.0e-1", self.sbox.scientificLineEdit.text())

        self.sbox.set_value(0)
        self.assertEqual("0.0e+0", self.sbox.scientificLineEdit.text())

    def test_typed_values(self):
        self.sbox.scientificLineEdit.setText("1.321e20")
        self.assertEqual(1.321e20, self.sbox.get_value())

        self.sbox.scientificLineEdit.setText("0")
        self.assertEqual(0, self.sbox.get_value())

        self.sbox.scientificLineEdit.setText("foo")
        self.assertRaises(TypeError, lambda: self.sbox.get_value())

    def test_decrease(self):
        self.sbox.set_value(5.5e+22)
        self.click_down()
        self.assertEqual(5.4e+22, self.sbox.get_value())

        # Note: following behaviour may change
        self.sbox.set_value(1.0001e+22)
        self.click_down()
        self.assertEqual(9.001e+21, self.sbox.get_value())

        self.sbox.scientificLineEdit.setText("foo")
        self.click_down()
        self.assertEqual("foo", self.sbox.scientificLineEdit.text())

    def test_increase(self):
        self.sbox.set_value(9.81e+22)
        self.click_up()
        self.assertEqual(9.91e+22, self.sbox.get_value())

        # Note: following behaviour may change
        self.click_up()
        self.assertEqual(1.001e+23, self.sbox.get_value())

    def test_set_value(self):
        self.sbox.set_value(5e22)
        self.assertEqual(5e22, self.sbox.get_value())

        # Value below min
        self.sbox.set_value(10)
        self.assertEqual(self.minimum, self.sbox.get_value())

        # Value over max
        self.sbox.set_value(5e25)
        self.assertEqual(self.maximum, self.sbox.get_value())

        # Try setting a string
        self.sbox.set_value("5e21")
        self.assertEqual(5e21, self.sbox.get_value())
