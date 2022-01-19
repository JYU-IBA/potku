# coding=utf-8
"""
Created on 3.8.2018
Updated on 16.8.2018

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2018 Heta Rekilä, 2020 Juhani Sundell

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program (file named 'LICENCE').
"""
__author__ = "Heta Rekilä \n Juhani Sundell"
__version__ = "2.0"

import math
import decimal
from decimal import Decimal
from typing import Union, Tuple, Optional, Callable

from PyQt5.QtWidgets import QAbstractSpinBox, QWidget

import widgets.input_validation as iv
from widgets.input_validation import ScientificValidator


class ScientificSpinBox(QAbstractSpinBox):
    """
    Class for custom double spinbox that handles scientific notation.
    """

    def __init__(
            self,
            value: float = 0.0,
            minimum: float = 0.0,
            maximum: float = math.inf,
            decimal_places: int = 17,
            parent: Optional[QWidget] = None) -> None:
        """
        Initializes the spinbox.

        Args:
            value: value of spinbox
            minimum: minimum allowed value
            maximum: maximum allowed value
            decimal_places: maximum number of decimals to show
        """
        super().__init__(parent)
        self._minimum = minimum
        self._maximum = maximum
        self._decimal_places = decimal_places

        self.scientificLineEdit = self.lineEdit()
        self._validator = ScientificValidator(
            self.minimum,
            self.maximum,
            self._decimal_places,
            self,
            accepted=lambda: iv.set_input_field_white(self.scientificLineEdit),
            intermediate=lambda: iv.set_input_field_yellow(
                 self.scientificLineEdit),
            invalid=lambda: iv.set_input_field_red(self.scientificLineEdit)
        )
        self.scientificLineEdit.setValidator(self._validator)
        self.set_value(value)

    @property
    def minimum(self) -> float:
        """Minimum allowed value.
        """
        return self._minimum

    @minimum.setter
    def minimum(self, value: float) -> None:
        self._validator.setRange(value, self.maximum, self.decimal_places)
        self._minimum = value

    @property
    def maximum(self) -> float:
        """Maximum allowed value.
        """
        return self._maximum

    @maximum.setter
    def maximum(self, value: float) -> None:
        self._validator.setRange(self.minimum, value, self.decimal_places)
        self._maximum = value

    @property
    def decimal_places(self) -> int:
        """Maximum number of decimals to show.
        """
        return self._decimal_places

    @decimal_places.setter
    def decimal_places(self, value: int) -> None:
        self._validator.setRange(self.minimum, self.maximum, value)
        self._decimal_places = value

    def stepBy(self, steps: int) -> None:
        """Called whenever the user triggers a step. The steps parameter
        indicates how many steps were taken.

        Overrides QAbstractSpinBox.stepBy.
        """
        if steps < 0:
            step_func = self._down_step
        else:
            step_func = self._up_step
        self._step_adjustment(step_func)

    def stepEnabled(self) -> QAbstractSpinBox.StepEnabled:
        """Determines whether stepping up and down is legal.

        Overrides QAbstractSpinBox.stepEnabled.
        """
        value = self._get_value()
        if value < self.maximum:
            step_up_enabled = QAbstractSpinBox.StepUpEnabled
        else:
            step_up_enabled = ~QAbstractSpinBox.StepUpEnabled
        if value > self.minimum:
            step_down_enabled = QAbstractSpinBox.StepDownEnabled
        else:
            step_down_enabled = ~QAbstractSpinBox.StepDownEnabled

        return step_up_enabled | step_down_enabled

    def set_value(self, value: Union[float, Decimal, str]) -> None:
        """Sets the value of the Spin box, provided that the given value is
        valid.
        """
        value = _cast_to_decimal(value)

        if not value.is_nan():
            if value < self.minimum:
                value = _cast_to_decimal(self.minimum)
            if value > self.maximum:
                value = _cast_to_decimal(self.maximum)

        self.scientificLineEdit.setText(
            self._format_value(value, self._decimal_places))

    @staticmethod
    def _format_value(value: Decimal, decimals: int) -> str:
        """Helper function for formatting Decimal into scientific
        notation string. Removes trailing zeroes from the decimal part.
        """
        if not value:
            return "0.0e+0"
        elif value.is_nan() or value.is_infinite():
            return str(value)
        s = f"{value:e}"
        v, m = s.split("e")
        v = v[:decimals + 2].rstrip("0")
        if v.endswith("."):
            v = f"{v}0"
        elif "." not in v:
            v = f"{v}.0"
        return f"{v}e{m}"

    def _step_adjustment(self, step_func: Callable[[Decimal], Decimal]):
        """Adjusts current value of the spinbox either up or down a step.
        """
        try:
            cur_val = self._get_value()
        except TypeError:
            return
        new_value = step_func(cur_val)

        self.set_value(new_value)

    @staticmethod
    def _down_step(value: Decimal) -> Decimal:
        """Returns a new value where the first decimal place of the given value
        has been decremented by one (for example 1.0e10 -> 9.9e9).
        """
        return ScientificSpinBox._step(value, -1, (1, 0), (9, 9))

    @staticmethod
    def _up_step(value: Decimal) -> Decimal:
        """Returns a new value where the first decimal place of the given value
        has been incremented by one (for example 9.9e10 -> 1.0e11).
        """
        return ScientificSpinBox._step(value, 1, (9, 9), (1, 0))

    @staticmethod
    def _step(value: Decimal, coef: int, c1: Tuple, c2: Tuple):
        """Helper function for incrementing and decrementing first decimal in
        scientific notation.

        We need to check if the decimal part starts with 9.9 or 1.0 depending
        on the direction of the step and sign of the value as simple
        addition or subtraction here would cause a too big of a gap in step
        size.
        """
        if value.is_nan() or value.is_infinite():
            return value
        sign, digits, exp = value.as_tuple()
        padded_digits = *digits, 0, 0
        if sign:
            c1, c2 = c2, c1

        if padded_digits[:2] == c1:
            # Handle special cases where incrementing or decrementing a decimal
            # causes a change in the exponent part.
            digits = *c2, *digits[2:]
            if sign:
                coef *= -1
            exp += coef * 1
            return Decimal((sign, digits, exp))
        diff_sign = 1 if coef < 0 else 0
        diff = Decimal((diff_sign, (1, *(0 for _ in digits)), exp - 2))
        return value + diff

    def get_value(self) -> float:
        """Returns the value of the spinbox as a float.
        """
        return float(self._get_value())

    def _get_value(self) -> Decimal:
        """Returns the value of the spinbox as a Decimal. This is used
        for internal handling of the value.
        """
        return _cast_to_decimal(self.text())


def _cast_to_decimal(value: Union[float, str, Decimal]) -> Decimal:
    """Casts given value to Decimal. Raises TypeError if casting fails.
    """
    if not isinstance(value, Decimal):
        try:
            value = Decimal(str(value))
        except decimal.InvalidOperation:
            raise TypeError(f"Could not convert value '{value}' into a number.")
    return value
