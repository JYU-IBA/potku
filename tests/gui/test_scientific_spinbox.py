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
import tests.gui
import math
import random
from decimal import Decimal

from PyQt5.QtWidgets import QAbstractSpinBox
import hypothesis as hy
from hypothesis import strategies as st

from widgets.scientific_spinbox import ScientificSpinBox


class TestSciSpinbox(unittest.TestCase):
    def setUp(self) -> None:
        self.sbox = ScientificSpinBox(minimum=-math.inf, maximum=math.inf)

    def test_value_is_displayed_as_text(self):
        self.sbox.set_value(5.5e+22)
        self.assertEqual("5.5e+22", self.sbox.text())

        self.sbox.set_value(math.pi * 1e-20)
        self.assertEqual("3.141592653589793e-20", self.sbox.text())

        self.sbox.set_value(-1.0e-21)
        self.assertEqual("-1.0e-21", self.sbox.text())

    def test_trailing_zeroes_are_not_shown(self):
        self.sbox.set_value(1.00000e21)
        self.assertEqual("1.0e+21", self.sbox.text())

        self.sbox.set_value(1.23000e-21)
        self.assertEqual("1.23e-21", self.sbox.text())

    def test_ints_and_floats_are_formatted_to_scientific_notation(self):
        self.sbox.set_value(0.1)
        self.assertEqual("1.0e-1", self.sbox.text())

        self.sbox.set_value(0)
        self.assertEqual("0.0e+0", self.sbox.text())

    def test_infinities_are_shown_as_text(self):
        self.sbox.set_value(math.inf)
        self.assertEqual("Infinity", self.sbox.text())

        self.sbox.set_value(-math.inf)
        self.assertEqual("-Infinity", self.sbox.text())

    def test_nan_is_shown_as_text(self):
        self.sbox.set_value(math.nan)
        self.assertEqual("NaN", self.sbox.text())

    def test_get_value_returns_value_as_a_float(self):
        self.sbox.set_value(5e22)
        self.assertEqual(5e22, self.sbox.get_value())

        self.sbox.set_value(math.nan)
        self.assertTrue(math.isnan(self.sbox.get_value()))

        self.sbox.set_value(math.inf)
        self.assertEqual(math.inf, self.sbox.get_value())

        self.sbox.set_value(-math.inf)
        self.assertEqual(-math.inf, self.sbox.get_value())

    def test_set_value_takes_a_string(self):
        self.sbox.set_value("5.14e21")
        self.assertEqual(5.14e21, self.sbox.get_value())

    def test_set_value_takes_a_decimal(self):
        self.sbox.set_value(Decimal(str("5.54321e20")))
        self.assertEqual(5.54321e20, self.sbox.get_value())

    def test_setting_a_bad_value_raises_type_error(self):
        self.assertRaises(TypeError, lambda: self.sbox.set_value("foo"))

    def test_values_default_to_minimum_and_maximum_value(self):
        minimum = 0
        maximum = 10
        sbox = ScientificSpinBox(minimum=minimum, maximum=maximum)

        sbox.set_value(maximum + 10)
        self.assertEqual(maximum, sbox.get_value())

        sbox.set_value(minimum - 10)
        self.assertEqual(minimum, sbox.get_value())

    def test_minimum_and_maximum_can_be_changed_using_properties(self):
        self.sbox.minimum = 20
        self.sbox.set_value(10)
        self.assertEqual(20, self.sbox.get_value())

        self.sbox.maximum = 30
        self.sbox.set_value(40)
        self.assertEqual(30, self.sbox.get_value())

    def test_decimal_places_can_be_changed_using_properties(self):
        self.sbox.decimal_places = 1
        self.sbox.set_value(1.234567)
        self.assertEqual(1.2, self.sbox.get_value())

    def test_get_value_tries_to_parse_the_value_from_line_edit(self):
        self.sbox.scientificLineEdit.setText("1.321e20")
        self.assertEqual(1.321e20, self.sbox.get_value())

        self.sbox.scientificLineEdit.setText("0")
        self.assertEqual(0, self.sbox.get_value())

        self.sbox.scientificLineEdit.setText("foo")
        self.assertRaises(TypeError, lambda: self.sbox.get_value())

    def test_number_of_decimal_places_shown_can_be_changed(self):
        sbox_with_three_decimal_places = ScientificSpinBox(
            minimum=-math.inf, maximum=math.inf, decimal_places=3)

        sbox_with_three_decimal_places.set_value(1.2345678e10)
        self.assertEqual(1.234e10, sbox_with_three_decimal_places.get_value())

    def test_step_enabled(self):
        minimum = 0
        maximum = 10
        sbox = ScientificSpinBox(value=5, minimum=minimum, maximum=maximum)

        self.assertEqual(
            QAbstractSpinBox.StepUpEnabled | QAbstractSpinBox.StepDownEnabled,
            sbox.stepEnabled(),
            msg="Stepping up and stepping down should be enabled when value is "
                "between minimum and maximum"
        )

        sbox.set_value(minimum)
        self.assertEqual(
            QAbstractSpinBox.StepUpEnabled | ~QAbstractSpinBox.StepDownEnabled,
            sbox.stepEnabled(),
            msg="Only stepping up should be enabled when value is set to "
                "minimum"
        )

        sbox.set_value(maximum)
        self.assertEqual(
            ~QAbstractSpinBox.StepUpEnabled | QAbstractSpinBox.StepDownEnabled,
            sbox.stepEnabled(),
            msg="Only stepping down should be enabled when value is set to "
                "maximum"
        )

    def test_stepping_down_decreases_the_first_decimal_by_one(self):
        self.sbox.set_value(5.5e+22)
        self.sbox.stepDown()
        self.assertEqual(5.4e+22, self.sbox.get_value())

        self.sbox.set_value(1.0001e+22)
        self.sbox.stepDown()
        self.assertEqual(9.9001e+21, self.sbox.get_value())

        self.sbox.set_value(0.0e0)
        self.sbox.stepDown()
        self.assertEqual(-1.0e-2, self.sbox.get_value())

        self.sbox.set_value(1.05e-3)
        self.sbox.stepDown()
        self.assertEqual(9.95e-4, self.sbox.get_value())

        self.sbox.set_value(-9.95e-4)
        self.sbox.stepDown()
        self.assertEqual(-1.05e-3, self.sbox.get_value())

    def test_stepping_up_increases_the_first_decimal_by_one(self):
        self.sbox.set_value(9.81e+22)
        self.sbox.stepUp()
        self.assertEqual(9.91e+22, self.sbox.get_value())

        self.sbox.stepUp()
        self.assertEqual(1.01e+23, self.sbox.get_value())

        self.sbox.set_value(0.0e0)
        self.sbox.stepUp()
        self.assertEqual(1.0e-2, self.sbox.get_value())

        self.sbox.set_value(9.9e0)
        self.sbox.stepUp()
        self.assertEqual(1.0e1, self.sbox.get_value())

        self.sbox.set_value(-1.05e-10)
        self.sbox.stepUp()
        self.assertEqual(-9.95e-11, self.sbox.get_value())

    def test_cannot_step_down_below_minimum(self):
        sbox = ScientificSpinBox(1.01e10, minimum=1e10)
        sbox.stepDown()
        self.assertEqual(1e10, sbox.get_value())
        sbox.stepDown()
        self.assertEqual(1e10, sbox.get_value())

    def test_cannot_step_up_over_maximum(self):
        sbox = ScientificSpinBox(9.99e9, maximum=1e10)
        sbox.stepUp()
        self.assertEqual(1e10, sbox.get_value())
        sbox.stepUp()
        self.assertEqual(1e10, sbox.get_value())

    def test_stepping_up_or_down_from_infinity_is_a_no_op(self):
        self.sbox.set_value(math.inf)
        self.sbox.stepUp()
        self.assertEqual(math.inf, self.sbox.get_value())
        self.sbox.stepDown()
        self.assertEqual(math.inf, self.sbox.get_value())

        self.sbox.set_value(-math.inf)
        self.sbox.stepUp()
        self.assertEqual(-math.inf, self.sbox.get_value())
        self.sbox.stepDown()
        self.assertEqual(-math.inf, self.sbox.get_value())

    def test_stepping_up_or_down_from_nan_is_a_no_op(self):
        self.sbox.set_value(math.nan)
        self.sbox.stepUp()
        self.assertTrue(math.isnan(self.sbox.get_value()))

        self.sbox.stepDown()
        self.assertTrue(math.isnan(self.sbox.get_value()))

    def test_stepping_up_or_down_from_invalid_value_is_a_no_op(self):
        self.sbox.scientificLineEdit.setText("foo")
        self.sbox.stepUp()
        self.assertEqual("foo", self.sbox.text())
        self.sbox.stepDown()
        self.assertEqual("foo", self.sbox.text())

    @hy.given(st.floats(allow_nan=False))
    def test_value_is_always_less_or_equal_after_step_down(self, value: float):
        self.sbox.set_value(value)
        before = self.sbox.get_value()
        self.sbox.stepDown()
        after = self.sbox.get_value()
        self.assertLessEqual(after, before)

    @hy.given(st.floats(allow_nan=False))
    def test_value_is_always_more_or_equal_after_step_up(self, value: float):
        self.sbox.set_value(value)
        before = self.sbox.get_value()
        self.sbox.stepUp()
        after = self.sbox.get_value()
        self.assertLessEqual(before, after)

    @hy.given(
        st.floats(
            allow_nan=False, allow_infinity=False, min_value=0,
            exclude_min=True),
        st.integers(min_value=1, max_value=20))
    def test_value_remains_same_after_equal_number_of_step_ups_and_step_downs(
            self, value: float, number_of_steps: int):
        # NOTE: zero is excluded from input values as it is its own special
        # case
        self.sbox.set_value(value)
        before = self.sbox.get_value()

        steps = [self.sbox.stepUp, self.sbox.stepDown] * number_of_steps
        random.shuffle(steps)
        for step in steps:
            step()

        after = self.sbox.get_value()
        self.assertEqual(before, after)

    def test_cannot_step_down_to_zero(self):
        # Special case where we start from zero, step up one step
        # and step down again multiple times. Value should always
        # be more than zero
        # NOTE: this behaviour could change in the future
        self.sbox.set_value(0)
        self.sbox.stepUp()
        for _ in range(10):
            self.sbox.stepDown()
        self.assertLess(0, self.sbox.get_value())

    def test_cannot_step_up_to_zero(self):
        # Another special case where we start from zero, step down
        # one step and step up again multiple times. Value should always
        # be less than zero
        # NOTE: this behaviour could change in the future
        self.sbox.set_value(0)
        self.sbox.stepDown()
        for _ in range(10):
            self.sbox.stepUp()
        self.assertLess(self.sbox.get_value(), 0)
