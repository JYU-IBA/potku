# coding=utf-8
"""
Created on 25.02.2020

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
__version__ = ""  # TODO

import sys
import unittest
import warnings

from tests.utils import change_wd_to_root

from widgets.scientific_spinbox import ScientificSpinBox

from PyQt5.QtWidgets import QApplication
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt


app = QApplication(sys.argv)


class TestSciSpinbox(unittest.TestCase):
    # Change working directory to root so the Spinbox can load ui-files
    @change_wd_to_root
    def setUp(self):
        with warnings.catch_warnings():
            # PyQt triggers a DeprecationWarning when loading an ui file.
            # Suppress the it so the test output does not get cluttered by
            # unnecessary warnings.
            warnings.simplefilter("ignore")
            self.sbox = ScientificSpinBox(10.0, 1e+22, 5.0e+20, 10.0e+23)

    def test_decrease(self):
        down_btn = self.sbox.ui.downButton
        QTest.mouseClick(down_btn, Qt.LeftButton)
        self.assertEqual(
            "9.9e+22",
            self.sbox.ui.scientificLineEdit.text()
        )
        QTest.mouseClick(down_btn, Qt.LeftButton)
        self.assertEqual(
            "9.8e+22",
            self.sbox.ui.scientificLineEdit.text()
        )

    def test_increase(self):
        up_btn = self.sbox.ui.upButton
        QTest.mouseClick(up_btn, Qt.LeftButton)
        self.assertEqual(
            "10.1e+22",
            self.sbox.ui.scientificLineEdit.text()
        )
        QTest.mouseClick(up_btn, Qt.LeftButton)
        self.assertEqual(
            "10.2e+22",
            self.sbox.ui.scientificLineEdit.text()
        )


if __name__ == '__main__':
    unittest.main()
