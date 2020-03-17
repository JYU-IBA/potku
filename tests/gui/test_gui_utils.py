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
__version__ = ""  # TODO

import unittest
import sys

import widgets.gui_utils as gutils

import numpy as np

from unittest.mock import Mock

from widgets.gui_utils import GUIReporter

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTime
from PyQt5 import QtWidgets
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt

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

    @unittest.skip("Threading test is not yet implemented for GUIReporter")
    def test_threading(self):
        # This test should test that the callback is always executed in the
        # main thread.
        self.assertTrue(False)


class BWidget(QtWidgets.QWidget, gutils.BindingPropertyWidget,
              metaclass=gutils.QtABCMeta):
    foo = gutils.bind("spinbox")
    bar = gutils.bind("doubleSpinbox")
    baz = gutils.bind("textBox")
    tim = gutils.bind("timeEdit")
    che = gutils.bind("checkBox")
    lab = gutils.bind("label")
    pla = gutils.bind("plaintext")

    def __init__(self):
        super().__init__()
        self.spinbox = QtWidgets.QSpinBox()
        self.doubleSpinbox = QtWidgets.QDoubleSpinBox()
        self.textBox = QtWidgets.QTextEdit()
        self.timeEdit = QtWidgets.QTimeEdit()
        self.checkBox = QtWidgets.QCheckBox()
        self.label = QtWidgets.QLabel()
        self.plaintext = QtWidgets.QPlainTextEdit()


class TestBinding(unittest.TestCase):
    def setUp(self):
        self.widget = BWidget()

    def test_getproperties(self):
        self.assertEqual(
            {
                "foo": 0,
                "bar": 0.0,
                "baz": "",
                "tim": 0,
                "che": False,
                "pla": "",
                "lab": ""
            }, self.widget.get_properties()
        )

    def test_spinbox_value(self):
        """Tests that spinbox value is bound to a property."""
        self.widget.spinbox.setValue(2)
        self.assertEqual(2, self.widget.foo)

        self.widget.foo = 5
        self.assertEqual(5, self.widget.spinbox.value())

        self.widget.doubleSpinbox.setValue(3.3)
        self.assertEqual(3.3, self.widget.bar)
        self.widget.textBox.setText("kissa istuu")
        self.assertEqual("kissa istuu", self.widget.baz)

        self.widget.tim = 4485
        self.assertEqual(QTime(1, 14, 45), self.widget.timeEdit.time())

    def test_set_properties(self):
        """Tests setting multiple properties at once."""
        self.widget.set_properties(foo=3, bar=4.5)
        self.assertEqual({
                "foo": 3,
                "bar": 4.5,
                "baz": "",
                "tim": 0,
                "che": False,
                "pla": "",
                "lab": ""
            }, self.widget.get_properties()
        )

        self.widget.set_properties(baz="test", tim=100, che=True)
        self.assertEqual({
            "foo": 3,
            "bar": 4.5,
            "baz": "test",
            "tim": 100,
            "che": True,
            "pla": "",
            "lab": ""
        }, self.widget.get_properties())

        self.widget.set_properties(pla="foo", lab="bar")
        self.assertEqual({
            "foo": 3,
            "bar": 4.5,
            "baz": "test",
            "tim": 100,
            "che": True,
            "pla": "foo",
            "lab": "bar"
        }, self.widget.get_properties())


class TestTimeConversion(unittest.TestCase):
    def test_conversion(self):
        for i in range(100):
            s = np.random.randint(0, 86_399)
            self.assertEqual(
                s, gutils.from_qtime(gutils.to_qtime(s))
            )
        # QTime wraps around at 86 400 seconds (i.e. 24 hours)
        self.assertEqual(86_399, gutils.from_qtime(gutils.to_qtime(86_399)))
        self.assertEqual(0, gutils.from_qtime(gutils.to_qtime(86_400)))
        self.assertEqual(86_399, gutils.from_qtime(gutils.to_qtime(-1)))


if __name__ == '__main__':
    unittest.main()
