# coding=utf-8
"""
Created on 18.03.2020

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

import numpy as np

import widgets.binding as bnd
import widgets.gui_utils as gutils

from widgets.binding import BindingPropertyWidget

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTime
from PyQt5 import QtWidgets

app = QApplication(sys.argv)


class BWidget(QtWidgets.QWidget, bnd.BindingPropertyWidget,
              metaclass=gutils.QtABCMeta):
    foo = bnd.bind("spinbox")
    bar = bnd.bind("doubleSpinbox")
    baz = bnd.bind("textBox")
    tim = bnd.bind("timeEdit")
    che = bnd.bind("checkBox")
    lab = bnd.bind("label")
    pla = bnd.bind("plaintext")

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

    def test_track_change(self):
        class Foo(BindingPropertyWidget):
            bar = bnd.bind("_bar", getattr, setattr, track_change=True)

            def __init__(self):
                self._bar = None

        f = Foo()
        self.assertFalse(f.are_values_changed())
        f.bar = 1
        self.assertFalse(f.are_values_changed())
        f.bar = 2
        self.assertTrue(f.are_values_changed())

        f2 = Foo()
        self.assertFalse(f2.are_values_changed())
        f2.bar = 3
        self.assertFalse(f2.are_values_changed())
        f2.bar = 4
        self.assertTrue(f2.are_values_changed())


class TestTimeConversion(unittest.TestCase):
    def test_conversion(self):
        for i in range(100):
            s = np.random.randint(0, 86_399)
            self.assertEqual(
                s, bnd.from_qtime(bnd.to_qtime(s))
            )
        # QTime wraps around at 86 400 seconds (i.e. 24 hours)
        self.assertEqual(86_399, bnd.from_qtime(bnd.to_qtime(86_399)))
        self.assertEqual(0, bnd.from_qtime(bnd.to_qtime(86_400)))
        self.assertEqual(86_399, bnd.from_qtime(bnd.to_qtime(-1)))


if __name__ == '__main__':
    unittest.main()
