# coding=utf-8
"""
Created on 08.03.2020

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
from unittest.mock import patch

from tests.utils import change_wd_to_root
import tests.mock_objects as mo

from dialogs.simulation.optimization import OptimizationDialog

from PyQt5.QtWidgets import QApplication
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt


app = QApplication(sys.argv)


class MyTestCase(unittest.TestCase):
    @change_wd_to_root
    @patch("modules.nsgaii.Nsgaii")
    @patch("modules.nsgaii.Nsgaii.start_optimization")
    def test_something(self, mock_nsgaii, mock_start):
        opt_dialog = OptimizationDialog(mo.get_simulation(), None)

        down_btn = opt_dialog.ui.downButton
        QTest.mouseClick(down_btn, Qt.LeftButton)



if __name__ == '__main__':
    unittest.main()