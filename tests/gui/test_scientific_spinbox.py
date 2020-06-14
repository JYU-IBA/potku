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

import sys
import unittest
import tests.utils as utils

from widgets.scientific_spinbox import ScientificSpinBox

from PyQt5.QtWidgets import QApplication
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt


app = QApplication(sys.argv)


class TestSciSpinbox(unittest.TestCase):
    # Change working directory to root so the Spinbox can load ui-files
    @utils.change_wd_to_root
    def setUp(self):
        self.sbox = ScientificSpinBox(
            1.123e+22, minimum=1.0e+20, maximum=9.9e+23)

    def test_decrease(self):
        down_btn = self.sbox.downButton
        QTest.mouseClick(down_btn, Qt.LeftButton)
        self.assertAlmostEqual(
            1.023e+22, self.sbox.get_value(), places=1
        )
        QTest.mouseClick(down_btn, Qt.LeftButton)
        self.assertEqual(
            0.923e+22, self.sbox.get_value()
        )

    def test_increase(self):
        up_btn = self.sbox.upButton
        QTest.mouseClick(up_btn, Qt.LeftButton)
        self.assertEqual(
            1.223e+22, self.sbox.get_value()
        )
        QTest.mouseClick(up_btn, Qt.LeftButton)
        self.assertEqual(
            1.323e+22, self.sbox.get_value()
        )

    def test_set_value(self):
        self.sbox.set_value(5e22)
        self.assertEqual(5e22, self.sbox.get_value())

        # Value below min
        self.sbox.set_value(10)
        self.assertEqual(1.0e20, self.sbox.get_value())

        # Value over max
        self.sbox.set_value(5e25)
        self.assertEqual(9.9e23, self.sbox.get_value())

        # Try setting a string
        self.assertRaises(
            TypeError, lambda: self.sbox.set_value("5e21"))
