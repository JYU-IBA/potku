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

import widgets.input_validation as iv
import widgets.gui_utils as gutils

from widgets.input_validation import ScientificValidator

from decimal import Decimal
from typing import Union
from typing import Tuple

from PyQt5 import QtWidgets
from PyQt5 import uic


class ScientificSpinBox(QtWidgets.QWidget):
    """
    Class for custom double spinbox that handles scientific notation.
    """

    def __init__(self, value=0.0, minimum=0.0, maximum=math.inf,
                 decimal_places=17, show_btns=True):
        """
        Initializes the spinbox.

        Args:
            value: value of spinbox
            minimum: minimum allowed value
            maximum: maximum allowed value
            decimal_places: maximum number of decimals to show
            show_btns: Whether buttons that increase or decrease the value
                are shown.
        """
        super().__init__()
        uic.loadUi(
            gutils.get_ui_dir() / "ui_scientific_spinbox_widget.ui", self)
        self._value = Decimal(str(value))
        self.minimum = minimum
        self.maximum = maximum
        if decimal_places < 1:
            self._decimal_places = 1
        elif decimal_places > 17:
            self._decimal_places = 17
        else:
            self._decimal_places = decimal_places

        self.scientificLineEdit: QtWidgets.QLineEdit
        self._validator = ScientificValidator(
            self.minimum, self.maximum, self._decimal_places, self,
            accepted=lambda: iv.set_input_field_white(self.scientificLineEdit),
            intermediate=lambda: iv.set_input_field_yellow(
                self.scientificLineEdit),
            invalid=lambda: iv.set_input_field_red(self.scientificLineEdit)
            )
        self.scientificLineEdit.setValidator(self._validator)

        self.set_value(self._value)

        if show_btns:
            self.upButton.clicked.connect(lambda *_: self._step_adjustment(
                self._up_step))
            self.downButton.clicked.connect(lambda *_: self._step_adjustment(
                self._down_step))
        else:
            self.upButton.hide()
            self.downButton.hide()

    def set_value(self, value: Union[float, Decimal]):
        """Sets the value of the Spin box, provided that the given value is
        valid.
        """
        if isinstance(value, Decimal):
            value = value
        else:
            value = Decimal(str(value))

        if value < self.minimum:
            value = self.minimum
        if value > self.maximum:
            value = self.maximum

        self.scientificLineEdit.setText(
            self._format_value(value, self._decimal_places))

    @staticmethod
    def _format_value(value: Decimal, decimals: int) -> str:
        """Helper function for formatting Decimal into scientific
        notation string. Removes trailing zeroes from the decimal part.
        """
        if not value:
            return "0.0e+0"
        s = f"{value:e}"
        v, m = s.split("e")
        v = v[:decimals - 2].rstrip("0")
        if v.endswith("."):
            v = f"{v}0"
        elif "." not in v:
            v = f"{v}.0"
        return f"{v}e{m}"

    def _step_adjustment(self, step_func: callable):
        """Adjusts current value of the spinbox either up or down a step.
        """
        try:
            cur_val = self._get_value()
        except decimal.InvalidOperation:
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
        # TODO this stuff could be done in the math_functions module
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
        try:
            return float(self._get_value())
        except decimal.InvalidOperation:
            raise TypeError(f"Could not convert text into a number.")

    def _get_value(self) -> Decimal:
        """Returns the value of the spinbox as a Decimal. This is used
        for internal handling of the value.
        """
        return Decimal(self.scientificLineEdit.text())

