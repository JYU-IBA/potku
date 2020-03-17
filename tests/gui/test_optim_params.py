# coding=utf-8
"""
Created on 10.03.2020

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

import unittest
import sys

from tests.utils import change_wd_to_root
from widgets.simulation.optimization_parameters import \
    OptimizationRecoilParameterWidget
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTime

app = QApplication(sys.argv)


class TestRecoilParameters(unittest.TestCase):
    @change_wd_to_root
    def test_kwargs(self):
        # Tests for settings parameters with kwargs
        widget = OptimizationRecoilParameterWidget(check_max=100.7,
                                                   upper_limits=(1, 2))
        self.assertEqual(1, widget.upperXDoubleSpinBox.value())
        self.assertEqual(2, widget.upperYDoubleSpinBox.value())
        self.assertEqual(QTime(0, 1, 40), widget.maxTimeEdit.time())

    @change_wd_to_root
    def test_recoil_combobox(self):
        # Tests for recoil combobox that has custom binding functions
        widget = OptimizationRecoilParameterWidget()
        self.assertEqual(5, widget.sol_size)
        self.assertEqual("box", widget.recoil_type)
        self.assertEqual("4-point box",
                         widget.recoilTypeComboBox.currentText())

        widget.sol_size = 9
        self.assertEqual(9, widget.sol_size)
        self.assertEqual("two-peak", widget.recoil_type)
        self.assertEqual("8-point two-peak",
                         widget.recoilTypeComboBox.currentText())

        # recoil_type is not two-way bound, so setting it raises an error
        def set_val():
            widget.recoil_type = "box"
        self.assertRaises(AttributeError,
                          lambda: set_val())

        # Previously set values remain the same
        self.assertEqual(9, widget.sol_size)
        self.assertEqual("two-peak", widget.recoil_type)
        self.assertEqual("8-point two-peak",
                         widget.recoilTypeComboBox.currentText())

    @change_wd_to_root
    def test_bad_inputs(self):
        # Widget should be able to handle bad inputs by retaining previous
        # or default values
        widget = OptimizationRecoilParameterWidget(foo=1)
        self.assertFalse(hasattr(widget, "foo"))

        widget.sol_size = "foo"
        self.assertEqual(5, widget.sol_size)

        # Zero is not a valid solution size so property value should stay at 9
        widget.sol_size = 9
        widget.sol_size = 0
        self.assertEqual(9, widget.sol_size)

        widget.pop_size = "foo"
        self.assertEqual(100, widget.pop_size)

        widget.upper_limits = "foo"
        self.assertEqual((120.0, 1.0), widget.upper_limits)

        widget.upper_limits = "foo", 2.0
        self.assertEqual((120.0, 2.0), widget.upper_limits)

        # Directly setting optimize_recoil to False will cause an
        # AttributeError.
        def assign_false():
            widget.optimize_recoil = False
        self.assertRaises(AttributeError, assign_false)

        # Providing the value as kwargs does nothing as the exception is
        # handled in the set_properties method
        widget = OptimizationRecoilParameterWidget(optimize_recoil=False)
        self.assertTrue(widget.optimize_recoil)


if __name__ == '__main__':
    unittest.main()
