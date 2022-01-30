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
from typing import Union, Optional, Tuple
from enum import IntEnum

from PyQt5.QtWidgets import QDoubleSpinBox, QWidget

import widgets.input_validation as iv
from widgets.input_validation import ScientificValidator


class _StepDirection(IntEnum):
    UP = 1
    DOWN = -1


class ScientificSpinBox(QDoubleSpinBox):
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

        line_edit = self.lineEdit()
        self._validator = ScientificValidator(
            minimum,
            maximum,
            decimal_places,
            self,
            accepted=lambda: iv.set_input_field_white(line_edit),
            intermediate=lambda: iv.set_input_field_yellow(line_edit),
            invalid=lambda: iv.set_input_field_red(line_edit)
        )
        self.setRange(minimum, maximum)
        self.setDecimals(decimal_places)
        self.setValue(value)

        line_edit.textChanged.connect(self._update_value_from_text)
        line_edit.setValidator(self._validator)

    def setMinimum(self, minimum: float) -> None:
        super(ScientificSpinBox, self).setMinimum(minimum)
        self._update_validator()

    def setMaximum(self, maximum: float) -> None:
        super(ScientificSpinBox, self).setMaximum(maximum)
        self._update_validator()

    def setRange(self, minimum: float, maximum: float) -> None:
        super(ScientificSpinBox, self).setRange(minimum, maximum)
        self._update_validator()

    def setDecimals(self, decimal_places: int) -> None:
        super(ScientificSpinBox, self).setDecimals(decimal_places)
        self._update_validator()

    def _update_validator(self) -> None:
        """Updates validator range with current minimum, maximum and decimal
        places.
        """
        self._validator.setRange(
            self.minimum(), self.maximum(), self.decimals()
        )

    def stepBy(self, steps: int) -> None:
        """Called whenever the user triggers a step. The steps parameter
        indicates how many steps were taken.

        Overrides QDoubleSpinBox.stepBy.
        """
        if steps > 0:
            direction = _StepDirection.UP
        else:
            direction = _StepDirection.DOWN

        value = _cast_to_decimal(self.value())
        for _ in range(abs(steps)):
            value = ScientificSpinBox._step(value, direction)

        self.setValue(value)

    def textFromValue(self, value: float) -> str:
        """Called whenever ScientificSpinBox needs to display the given value.
        """
        value = _cast_to_decimal(value)
        return ScientificSpinBox._format_value(value, self.decimals())

    def _update_value_from_text(self, input_text: str) -> None:
        """Updates the value of this ScientificSpinBox based on the
        text input. Input has to be a valid number between minimum
        and maximum, otherwise the value is not updated.
        """
        try:
            new_value = _cast_to_decimal(input_text)
        except ValueError:
            return

        if self.minimum() <= new_value <= self.maximum():
            self.setValue(new_value)

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

    @staticmethod
    def _step(value: Decimal, direction: _StepDirection):
        """Helper function for incrementing and decrementing first decimal in
        scientific notation.

        We need to check if the decimal part starts with 9.9 or 1.0 depending
        on the direction of the step and sign of the value as simple
        addition or subtraction here would cause a too big of a gap in step
        size.
        """
        if value.is_infinite():
            return value

        step_from, step_to = _determine_step_threshold(value, direction)

        sign, digits, exp = value.as_tuple()
        padded_digits = *digits, 0, 0

        if padded_digits[:2] == step_from:
            # Handle special cases where incrementing or decrementing a decimal
            # causes a change in the exponent part.
            new_digits = *step_to, *digits[2:]
            if value < 0:
                direction *= -1
            exp += direction
            if len(digits) == 1:
                exp += direction
            return Decimal((sign, new_digits, exp))
        diff_sign = 0 if direction is _StepDirection.UP else 1
        diff = Decimal((diff_sign, (1, *(0 for _ in digits)), exp - 2))
        return value + diff


def _cast_to_decimal(value: Union[float, str, Decimal]) -> Decimal:
    """Casts given value to Decimal. Raises ValueError if casting fails.
    """
    if not isinstance(value, Decimal):
        try:
            value = Decimal(str(value))
        except decimal.InvalidOperation:
            raise ValueError(
                f"Could not convert value '{value}' into a number.")
    return value


def _determine_step_threshold(
        value: Union[float, Decimal],
        direction: _StepDirection) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    is_step_up = direction == _StepDirection.UP
    is_positive = value > 0

    if (is_step_up and is_positive) or (not is_step_up and not is_positive):
        return (9, 9), (1, 0)
    return (1, 0), (9, 9)
