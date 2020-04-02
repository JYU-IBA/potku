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
import warnings

import tests.utils as utils
import numpy as np

import widgets.binding as bnd
import widgets.gui_utils as gutils

from widgets.scientific_spinbox import ScientificSpinBox

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTime
from PyQt5 import QtWidgets

app = QApplication(sys.argv)


class BWidget(QtWidgets.QWidget, bnd.PropertyBindingWidget,
              metaclass=gutils.QtABCMeta):
    foo = bnd.bind("spinbox")
    bar = bnd.bind("doubleSpinbox")
    baz = bnd.bind("textBox")
    tim = bnd.bind("timeEdit")
    che = bnd.bind("checkBox")
    lab = bnd.bind("label")
    pla = bnd.bind("plaintext")
    not2way = bnd.bind("not2waySpinBox", twoway=False)
    sci = bnd.bind("scibox")

    def __init__(self):
        super().__init__()
        self.spinbox = QtWidgets.QSpinBox()
        self.doubleSpinbox = QtWidgets.QDoubleSpinBox()
        self.textBox = QtWidgets.QTextEdit()
        self.timeEdit = QtWidgets.QTimeEdit()
        self.checkBox = QtWidgets.QCheckBox()
        self.label = QtWidgets.QLabel()
        self.plaintext = QtWidgets.QPlainTextEdit()
        self.not2waySpinBox = QtWidgets.QSpinBox()
        self.scibox = ScientificSpinBox(0, 1, 0, 10)


class TestBinding(unittest.TestCase):
    @utils.change_wd_to_root
    def setUp(self):
        with warnings.catch_warnings():
            # PyQt triggers a DeprecationWarning when loading an ui file.
            # Suppress the it so the test output does not get cluttered by
            # unnecessary warnings.
            warnings.simplefilter("ignore")
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
                "lab": "",
                "not2way": 0,
                "sci": 0
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
                "lab": "",
                "not2way": 0,
                "sci": 0
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
            "lab": "",
            "not2way": 0,
            "sci": 0
        }, self.widget.get_properties())

        # Setting the not2way changes nothing as well as setting tim to
        # unsuitable type
        self.widget.set_properties(pla="foo", lab="bar", not2way=7,
                                   tim="foo", sci=1)
        self.assertEqual({
            "foo": 3,
            "bar": 4.5,
            "baz": "test",
            "tim": 100,
            "che": True,
            "pla": "foo",
            "lab": "bar",
            "not2way": 0,
            "sci": 1
        }, self.widget.get_properties())


class Multibinder:
    foo = bnd.multi_bind(["xbox", "ybox", "zbox"])

    def __init__(self):
        self.xbox = QtWidgets.QSpinBox()
        self.ybox = QtWidgets.QLabel()
        self.zbox = QtWidgets.QPlainTextEdit()


class TestMultibinding(unittest.TestCase):
    def setUp(self):
        self.mb = Multibinder()

    def test_multibinding(self):
        self.mb.foo = 1, "bar", "baz"
        self.assertEqual(self.mb.xbox.value(), 1)
        self.assertEqual(self.mb.ybox.text(), "bar")
        self.assertEqual(self.mb.zbox.toPlainText(), "baz")

        self.mb.xbox.setValue(2)
        self.assertEqual((2, "bar", "baz"), self.mb.foo)

    def test_bad_inputs(self):
        self.mb.foo = "test", "test", "test"
        self.assertEqual((0, "test", "test"), self.mb.foo)

        self.mb.foo = 2, "test", True
        self.assertEqual((2, "test", "test"), self.mb.foo)


class TestTrackingProperties(unittest.TestCase):
    """For simplicity, these tests always use getattr and setattr as getter
    and setter.
    """
    def test_track_change_with_two_objects(self):
        """Tests that two instances of PropertyTrackingWidget track their own
        properties.
        """
        class Foo(bnd.PropertyTrackingWidget):
            bar = bnd.bind("_bar", getattr, setattr, track_change=True)

            def __init__(self):
                self._bar = None
                self._orig = {}

            def get_original_property_values(self):
                return self._orig

        f = Foo()
        self.assertFalse(f.are_values_changed())
        f.bar = 1
        self.assertFalse(f.are_values_changed())
        f.bar = 2
        self.assertTrue(f.are_values_changed())
        f.bar = 1
        self.assertFalse(f.are_values_changed())

        f2 = Foo()
        self.assertFalse(f2.are_values_changed())
        f2.bar = 3
        self.assertFalse(f2.are_values_changed())
        f2.bar = 4
        self.assertTrue(f2.are_values_changed())

    def test_tracking_and_nontracking_properties(self):
        """Tests for object that has both tracking and normal
        properties.
        """
        class Foo(bnd.PropertyTrackingWidget):
            @property
            def foo(self):
                return self._foo

            @foo.setter
            def foo(self, value):
                self._foo = value

            bar = bnd.bind("_bar", getattr, setattr, track_change=True)
            baz = bnd.bind("_baz", getattr, setattr, track_change=False)

            def __init__(self):
                self.orig_props = {}
                self.set_properties(foo=1, bar=2, baz=3)

            def get_original_property_values(self):
                return self.orig_props

        f = Foo()
        # Assert that the attributes got created when f was initialized
        self.assertTrue(all((hasattr(f, "_foo"),
                             hasattr(f, "_bar"),
                             hasattr(f, "_baz"))))
        self.assertFalse(f.are_values_changed())

        # These properties are not tracked so changing them does not affect
        # are_values_changed
        f.foo = 4
        f.baz = 5
        self.assertFalse(f.are_values_changed())

        f.bar = 6
        self.assertTrue(f.are_values_changed())

        # Test individual properties
        self.assertRaises(AttributeError, lambda: Foo.foo.is_value_changed(f))
        self.assertFalse(Foo.baz.is_value_changed(f))
        self.assertTrue(Foo.bar.is_value_changed(f))

        self.assertEqual({"_bar": 2}, f.get_original_property_values())

    def test_setting_attribute_directly(self):
        """Tracking only works when property is set. If the attribute is set
        directly, changes are not detected.
        """
        class Foo(bnd.PropertyTrackingWidget):
            foo = bnd.bind("_foo", getattr, setattr, track_change=True)

            def __init__(self):
                self._foo = 1
                self.orig = {}

            def get_original_property_values(self):
                return self.orig

        f = Foo()
        f._foo = 2
        self.assertEqual({}, f.get_original_property_values())
        self.assertEqual(2, f.foo)
        self.assertFalse(f.are_values_changed())

        f.foo = 3
        f.foo = 4
        self.assertTrue(f.are_values_changed())

    def test_unset_property(self):
        """If the property is bound to a nonexisting attribute,
        AttributeErrors will be raised.
        """
        class Foo(bnd.PropertyTrackingWidget):
            bar = bnd.bind("_bar", getattr, setattr, track_change=True)

            def get_original_property_values(self):
                return {}

        f = Foo()
        self.assertRaises(AttributeError, lambda: f.bar)
        self.assertRaises(AttributeError, lambda: f.are_values_changed())
        self.assertRaises(AttributeError, lambda: f.get_properties())

    def test_const_original_properties(self):
        """It is possible for the PropertyTrackingWidget to return an
        arbitrary dictionary when original values are requested.
        """
        class Foo(bnd.PropertyTrackingWidget):
            foo = bnd.bind("_foo", getattr, setattr, track_change=True)

            def __init__(self):
                self.foo = 1

            def get_original_property_values(self):
                return {"_foo": 2}

        f = Foo()
        self.assertTrue(f.are_values_changed())

        f.foo = 2
        self.assertFalse(f.are_values_changed())

    def test_bad_values(self):
        """Tests property tracking when setting the property raises
        an exception."""
        def setter(instance, attr, value):
            setattr(instance, attr, 10 / value)

        class Foo(bnd.PropertyTrackingWidget):
            foo = bnd.bind("_foo", getattr, setter, track_change=True)

            def __init__(self):
                self.orig = {}
                self.foo = 1

            def get_original_property_values(self):
                return self.orig

        f = Foo()
        self.assertFalse(f.are_values_changed())

        def set_to_zero():
            f.foo = 0
        self.assertRaises(ZeroDivisionError, set_to_zero)
        self.assertFalse(f.are_values_changed())

        f.foo = 2
        self.assertTrue(f.are_values_changed())

        self.assertRaises(ZeroDivisionError, set_to_zero)
        self.assertTrue(f.are_values_changed())


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
