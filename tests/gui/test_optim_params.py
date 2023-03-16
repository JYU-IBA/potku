# coding=utf-8
"""
Created on 10.03.2020

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

from modules.nsgaii import OptimizationType

from widgets.simulation.optimization_parameters import \
    OptimizationRecoilParameterWidget
from widgets.simulation.optimization_parameters import \
    OptimizationFluenceParameterWidget

from PyQt5.QtCore import QTime


class TestRecoilParameters(unittest.TestCase):
    def test_kwargs(self):
        # Tests for settings parameters with kwargs
        widget = OptimizationRecoilParameterWidget(
            check_max=100.7, upper_limits=(1, 2))
        self.assertEqual(1, widget.upperXDoubleSpinBox.value())
        self.assertEqual(2, widget.upperYDoubleSpinBox.value())
        self.assertEqual(QTime(0, 1, 40), widget.maxTimeEdit.time())

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
        self.assertRaises(TypeError, lambda: set_val())

        # Previously set values remain the same
        self.assertEqual(9, widget.sol_size)
        self.assertEqual("two-peak", widget.recoil_type)
        self.assertEqual("8-point two-peak",
                         widget.recoilTypeComboBox.currentText())

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
            widget.optimization_type = False
        self.assertRaises(AttributeError, assign_false)

        # Providing the value as kwargs does nothing as the exception is
        # handled in the set_properties method
        widget = OptimizationRecoilParameterWidget(optimize_recoil=False)
        self.assertIs(widget.optimization_type, OptimizationType.RECOIL)

    def test_get_properties(self):
        """Test that get_properties returns the default values of each type
        of optimization widget after initialization.
        """
        common = {
            "pop_size": 100,
            "number_of_processes": 1,
            "cross_p": 0.9,
            "mut_p": 1.0,
            "check_time": 20,
        }
        fluence_expected = {
            "stop_percent": 0.7,
            "gen": 5,
            "lower_limits": 0.0,
            "sol_size": 1,
            "optimization_type": OptimizationType.FLUENCE,
            "upper_limits": 10000000000000.0,
            "dis_c": 20,
            "dis_m": 20,
            "check_max": 900,
            "check_min": 600,
            "skip_simulation": False
        }
        fluence_expected.update(common)

        recoil_expected = {
            "stop_percent": 0.3,
            "gen": 50,
            "upper_limits": (120.0, 1.0),
            "lower_limits": (0.01, 0.0001),
            "sol_size": 5,
            "recoil_type": "box",
            "optimization_type": OptimizationType.RECOIL,
            "check_max": 600,
            "check_min": 0,
            "skip_simulation": True
        }
        recoil_expected.update(common)

        fluence_widget = OptimizationFluenceParameterWidget()
        self.assertEqual(fluence_expected,
                         fluence_widget.get_properties())

        recoil_widget = OptimizationRecoilParameterWidget()
        self.assertEqual(recoil_expected,
                         recoil_widget.get_properties())


if __name__ == '__main__':
    unittest.main()
