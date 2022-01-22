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

import numpy as np
import hypothesis as hy
from hypothesis import strategies as st

from widgets.scientific_spinbox import ScientificSpinBox


class TestScientificSpinBoxInit(unittest.TestCase):
    def test_value_can_be_set(self):
        sbox = ScientificSpinBox(3)
        self.assertEqual(3, sbox.value())

    def test_minimum_and_maximum_can_be_set(self):
        sbox = ScientificSpinBox(minimum=2, maximum=4)
        self.assertEqual(2, sbox.minimum())
        self.assertEqual(4, sbox.maximum())

    def test_decimal_places_can_be_set(self):
        sbox = ScientificSpinBox(decimal_places=13)
        self.assertEqual(13, sbox.decimals())


class TestScientifiSpinBox(unittest.TestCase):
    def setUp(self) -> None:
        self.sbox = ScientificSpinBox(minimum=-math.inf, maximum=math.inf)


class TestSettingAndGettingValues(TestScientifiSpinBox):
    def test_set_value_takes_a_float(self):
        self.sbox.setValue(1.23456)
        self.assertEqual(1.23456, self.sbox.value())

    def test_set_value_takes_an_int(self):
        self.sbox.setValue(1)
        self.assertEqual(1, self.sbox.value())

    def test_set_value_takes_a_decimal(self):
        self.sbox.setValue(Decimal(str("-5.54321e20")))
        self.assertEqual(-5.54321e20, self.sbox.value())

    def test_passing_string_to_set_value_raises_error(self):
        self.assertRaises(TypeError, lambda: self.sbox.setValue("5"))  # noqa

    def test_nan_is_changed_to_infinity(self):
        self.sbox.setValue(math.nan)
        self.assertEqual(math.inf, self.sbox.value())

    def test_values_default_to_minimum_and_maximum_value(self):
        minimum, maximum = 0, 10
        self.sbox.setRange(minimum, maximum)

        self.sbox.setValue(maximum + 10)
        self.assertEqual(maximum, self.sbox.value())

        self.sbox.setValue(minimum - 10)
        self.assertEqual(minimum, self.sbox.value())

    def test_setting_the_text_to_invalid_number_does_not_change_the_value(self):
        self.sbox.setValue(-3)
        line_edit = self.sbox.lineEdit()
        line_edit.setText("foo")
        self.assertEqual("foo", self.sbox.text())
        self.assertEqual(-3, self.sbox.value())

    def test_decimal_places_does_not_affect_the_number_of_decimals_shown(self):
        self.sbox.setValue(1.23456789e10)
        self.assertEqual(1.23456789e+10, self.sbox.value())
        self.sbox.setDecimals(3)
        self.assertEqual(1.23456789e+10, self.sbox.value())


class TestDisplayingValuesAsText(TestScientifiSpinBox):
    def test_display_positive_value_positive_exponent(self):
        self.sbox.setValue(12)
        self.assertEqual("1.2e+1", self.sbox.text())

    def test_display_positive_value_zero_exponent(self):
        self.sbox.setValue(3.313)
        self.assertEqual("3.313e+0", self.sbox.text())

    def test_display_positive_value_negative_exponent(self):
        self.sbox.setValue(0.001)
        self.assertEqual("1.0e-3", self.sbox.text())

    def test_display_zero(self):
        self.sbox.setValue(0)
        self.assertEqual("0.0e+0", self.sbox.text())

    def test_display_negative_value_positive_exponent(self):
        self.sbox.setValue(-104.54321)
        self.assertEqual("-1.0454321e+2", self.sbox.text())

    def test_display_negative_value_negative_exponent(self):
        self.sbox.setValue(-0.00054321)
        self.assertEqual("-5.4321e-4", self.sbox.text())

    def test_trailing_zeroes_are_not_shown(self):
        self.sbox.setValue(1.00000e21)
        self.assertEqual("1.0e+21", self.sbox.text())

        self.sbox.setValue(1.23000e-2)
        self.assertEqual("1.23e-2", self.sbox.text())

    def test_infinity_is_displayed_as_text(self):
        self.sbox.setValue(math.inf)
        self.assertEqual("Infinity", self.sbox.text())

        self.sbox.setValue(-math.inf)
        self.assertEqual("-Infinity", self.sbox.text())

    def test_decimal_places_affects_the_number_of_decimals_shown(self):
        self.sbox.setValue(1.23456789e10)
        self.assertEqual("1.23456789e+10", self.sbox.text())
        self.sbox.setDecimals(3)
        self.assertEqual("1.234e+10", self.sbox.text())


class TestSteppingUpAndDown(TestScientifiSpinBox):
    def test_step_up_positive_value_positive_exponent(self):
        self.sbox.setValue(5.123e10)
        self.sbox.stepUp()
        self.assertEqual(5.223e10, self.sbox.value())

    def test_step_up_positive_value_positive_exponent_exponent_changes(self):
        self.sbox.setValue(9.9e10)
        self.sbox.stepUp()
        self.assertEqual(1.0e11, self.sbox.value())

    def test_step_up_positive_value_positive_exponent_exponent_changes_2(self):
        self.sbox.setValue(9.95e10)
        self.sbox.stepUp()
        self.assertEqual(1.05e11, self.sbox.value())

    def test_step_up_positive_value_negative_exponent(self):
        self.sbox.setValue(3.923e-5)
        self.sbox.stepUp()
        self.assertEqual(4.023e-5, self.sbox.value())

    def test_step_up_positive_value_negative_exponent_exponent_changes(self):
        self.sbox.setValue(9.9e-11)
        self.sbox.stepUp()
        self.assertEqual(1.0e-10, self.sbox.value())

    def test_step_up_positive_value_negative_exponent_exponent_changes_2(self):
        self.sbox.setValue(9.9003e-11)
        self.sbox.stepUp()
        self.assertEqual(1.0003e-10, self.sbox.value())

    def test_step_up_negative_value_positive_exponent(self):
        self.sbox.setValue(-7.08e12)
        self.sbox.stepUp()
        self.assertEqual(-6.98e12, self.sbox.value())

    def test_step_up_negative_value_positive_exponent_exponent_changes(self):
        self.sbox.setValue(-1.0e2)
        self.sbox.stepUp()
        self.assertEqual(-9.9e1, self.sbox.value())

    def test_step_up_negative_value_positive_exponent_exponent_changes_2(self):
        self.sbox.setValue(-1.04e2)
        self.sbox.stepUp()
        self.assertEqual(-9.94e1, self.sbox.value())

    def test_step_up_negative_value_negative_exponent(self):
        self.sbox.setValue(-6.7e-13)
        self.sbox.stepUp()
        self.assertEqual(-6.6e-13, self.sbox.value())

    def test_step_up_negative_value_negative_exponent_exponent_changes(self):
        self.sbox.setValue(-1.0e-12)
        self.sbox.stepUp()
        self.assertEqual(-9.9e-13, self.sbox.value())

    def test_step_up_negative_value_negative_exponent_exponent_changes_2(self):
        self.sbox.setValue(-1.073235e-8)
        self.sbox.stepUp()
        self.assertEqual(-9.973235e-9, self.sbox.value())

    def test_step_up_from_zero(self):
        self.sbox.setValue(0.0e0)
        self.sbox.stepUp()
        self.assertEqual(1.0e-2, self.sbox.value())

    def test_step_up_from_negative_exponent_to_non_negative(self):
        self.sbox.setValue(9.9e-1)
        self.sbox.stepUp()
        self.assertEqual(1.0e0, self.sbox.value())

    def test_step_up_from_negative_exponent_to_non_negative_2(self):
        self.sbox.setValue(9.999e-1)
        self.sbox.stepUp()
        self.assertEqual(1.099e0, self.sbox.value())

    def test_step_down_positive_value_positive_exponent(self):
        self.sbox.setValue(5.123e10)
        self.sbox.stepDown()
        self.assertEqual(5.023e10, self.sbox.value())

    def test_step_down_positive_value_positive_exponent_exponent_changes(self):
        self.sbox.setValue(1.0e10)
        self.sbox.stepDown()
        self.assertEqual(9.9e9, self.sbox.value())

    def test_step_down_positive_value_positive_exponent_exponent_changes_2(
            self):
        self.sbox.setValue(1.0998e10)
        self.sbox.stepDown()
        self.assertEqual(9.9998e9, self.sbox.value())

    def test_step_down_positive_value_negative_exponent(self):
        self.sbox.setValue(3.023e-5)
        self.sbox.stepDown()
        self.assertEqual(2.923e-5, self.sbox.value())

    def test_step_down_positive_value_negative_exponent_exponent_changes(self):
        self.sbox.setValue(1.0e-11)
        self.sbox.stepDown()
        self.assertEqual(9.9e-12, self.sbox.value())

    def test_step_down_positive_value_negative_exponent_exponent_changes_2(
            self):
        self.sbox.setValue(1.00001e-11)
        self.sbox.stepDown()
        self.assertEqual(9.90001e-12, self.sbox.value())

    def test_step_down_negative_value_positive_exponent(self):
        self.sbox.setValue(-7.91e12)
        self.sbox.stepDown()
        self.assertEqual(-8.01e12, self.sbox.value())

    def test_step_down_negative_value_positive_exponent_exponent_changes(self):
        self.sbox.setValue(-9.9e2)
        self.sbox.stepDown()
        self.assertEqual(-1.0e3, self.sbox.value())

    def test_step_down_negative_value_positive_exponent_exponent_changes_2(
            self):
        self.sbox.setValue(-9.92e2)
        self.sbox.stepDown()
        self.assertEqual(-1.02e3, self.sbox.value())

    def test_step_down_negative_value_negative_exponent(self):
        self.sbox.setValue(-6.7e-13)
        self.sbox.stepDown()
        self.assertEqual(-6.8e-13, self.sbox.value())

    def test_step_down_negative_value_negative_exponent_exponent_changes(self):
        self.sbox.setValue(-9.9e-12)
        self.sbox.stepDown()
        self.assertEqual(-1.0e-11, self.sbox.value())

    def test_step_down_negative_value_negative_exponent_exponent_changes_2(
            self):
        self.sbox.setValue(-9.93e-12)
        self.sbox.stepDown()
        self.assertEqual(-1.03e-11, self.sbox.value())

    def test_step_down_from_zero(self):
        self.sbox.setValue(0.0e0)
        self.sbox.stepDown()
        self.assertEqual(-1.0e-2, self.sbox.value())

    def test_step_down_from_non_negative_exponent_to_negative(self):
        self.sbox.setValue(1.0e0)
        self.sbox.stepDown()
        self.assertEqual(9.9e-1, self.sbox.value())

    def test_step_down_from_non_negative_exponent_to_negative_2(self):
        self.sbox.setValue(1.05e0)
        self.sbox.stepDown()
        self.assertEqual(9.95e-1, self.sbox.value())

    def test_stepping_below_minimum_is_not_possible(self):
        sbox = ScientificSpinBox(1.01e10, minimum=1e10)
        sbox.stepDown()
        self.assertEqual(1e10, sbox.value())
        sbox.stepDown()
        self.assertEqual(1e10, sbox.value())

    def test_stepping_over_maximum_is_not_possible(self):
        sbox = ScientificSpinBox(9.99e9, maximum=1e10)
        sbox.stepUp()
        self.assertEqual(1e10, sbox.value())
        sbox.stepUp()
        self.assertEqual(1e10, sbox.value())

    def test_stepping_up_or_down_from_infinity_is_a_no_op(self):
        self.sbox.setValue(math.inf)
        self.sbox.stepUp()
        self.assertEqual(math.inf, self.sbox.value())
        self.sbox.stepDown()
        self.assertEqual(math.inf, self.sbox.value())

        self.sbox.setValue(-math.inf)
        self.sbox.stepUp()
        self.assertEqual(-math.inf, self.sbox.value())
        self.sbox.stepDown()
        self.assertEqual(-math.inf, self.sbox.value())

    def test_step_up_by_10(self):
        self.sbox.setValue(1.0e1)
        self.sbox.stepBy(10)
        self.assertEqual(2.0e1, self.sbox.value())

    def test_step_down_by_10(self):
        self.sbox.setValue(1.0e1)
        self.sbox.stepBy(-10)
        self.assertEqual(9.0e0, self.sbox.value())


class TestStepProperties(TestScientifiSpinBox):
    # Limit for decimal places in input values generated by hypothesis.
    # Floating point comparisons become more and more unreliable with
    # more decimal places.
    MAX_DECIMALS = 16

    @hy.given(
        st.floats(allow_nan=False, allow_infinity=False, width=MAX_DECIMALS))
    def test_value_is_always_less_after_step_down(self, value: float):
        self.sbox.setValue(value)
        before = self.sbox.value()
        self.sbox.stepDown()
        after = self.sbox.value()
        self.assertLess(after, before)

    @hy.given(
        st.floats(allow_nan=False, allow_infinity=False, width=MAX_DECIMALS))
    def test_value_is_always_more_after_step_up(self, value: float):
        self.sbox.setValue(value)
        before = self.sbox.value()
        self.sbox.stepUp()
        after = self.sbox.value()
        self.assertLess(before, after)

    @hy.given(
        st.floats(
            allow_nan=False, allow_infinity=False, width=MAX_DECIMALS,
            min_value=0, exclude_min=True),
        st.integers(min_value=1, max_value=20))
    def test_value_remains_same_after_equal_number_of_step_ups_and_step_downs(
            self, value: float, number_of_steps: int):
        # NOTE: zero is excluded from input values as it is its own special
        # case.
        self.sbox.setValue(value)
        before = self.sbox.value()

        steps = [self.sbox.stepUp, self.sbox.stepDown] * number_of_steps
        random.shuffle(steps)
        for step in steps:
            step()

        after = self.sbox.value()
        np.testing.assert_allclose(before, after, rtol=1e-7)

    def test_stepping_down_to_zero_is_not_possible(self):
        # Special case where we start from zero, step up one step
        # and step down again multiple times. Value should always
        # be more than zero
        # NOTE: this behaviour could change in the future
        self.sbox.setValue(0)
        self.sbox.stepUp()
        for _ in range(10):
            self.sbox.stepDown()
        self.assertLess(0, self.sbox.value())

    def test_stepping_up_to_zero_is_not_possible(self):
        # Another special case where we start from zero, step down
        # one step and step up again multiple times. Value should always
        # be less than zero
        # NOTE: this behaviour could change in the future
        self.sbox.setValue(0)
        self.sbox.stepDown()
        for _ in range(10):
            self.sbox.stepUp()
        self.assertLess(self.sbox.value(), 0)

    @hy.given(st.floats(allow_nan=False))
    def test_step_down_from_positive_x_is_inverse_to_step_up_from_negative_x(
            self, value: float):
        self.sbox.setValue(value)
        self.sbox.stepDown()
        x0 = self.sbox.value()

        self.sbox.setValue(-value)
        self.sbox.stepUp()
        x1 = self.sbox.value()
        self.assertEqual(x0, -x1)
