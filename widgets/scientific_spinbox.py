# coding=utf-8
"""
Created on 3.8.2018
Updated on 16.8.2018

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2018 Heta Rekilä

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
__author__ = "Heta Rekilä"
__version__ = "2.0"

import math
import widgets.input_validation as iv
import decimal

from widgets.input_validation import ScientificValidator

from decimal import Decimal
from typing import Union
from pathlib import Path

from PyQt5 import QtWidgets
from PyQt5 import uic


class ScientificSpinBox(QtWidgets.QWidget):
    """
    Class for custom double spinbox that handles scientific notation.
    """
    _UP = 0
    _DOWN = 1

    def __init__(self, value=0.0, minimum=0.0, maximum=math.inf, decimals=17,
                 show_btns=True):
        """
        Initializes the spinbox.

        Args:
            value: value of spinbox
            minimum: minimum allowed value
            maximum: maximum allowed value
            decimals: maximum number of decimals to show
            show_btns: Whether buttons that increase or decrease the value
                are shown.
        """
        super().__init__()
        uic.loadUi(Path("ui_files", "ui_scientific_spinbox_widget.ui"), self)
        self._value = Decimal(str(value))
        self.minimum = minimum
        self.maximum = maximum
        if 1 <= decimals <= 17:
            self.decimals = decimals
        else:
            self.decimals = decimals

        self.scientificLineEdit: QtWidgets.QLineEdit
        self._validator = ScientificValidator(
            self.minimum, self.maximum, self.decimals, self,
            accepted=lambda: iv.set_input_field_white(self.scientificLineEdit),
            intermediate=lambda: iv.set_input_field_yellow(
                self.scientificLineEdit),
            invalid=lambda: iv.set_input_field_red(self.scientificLineEdit)
            )
        self.scientificLineEdit.setValidator(self._validator)

        self.set_value(self._value)

        if show_btns:
            self.upButton.clicked.connect(lambda *_: self._step_adjustment(
                self._UP))
            self.downButton.clicked.connect(lambda *_: self._step_adjustment(
                self._DOWN))
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
            self._format_value(value, self.decimals))

    @staticmethod
    def _format_value(value: Decimal, decimals: int) -> str:
        """Helper function for formatting Decimal into string.
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

    def _step_adjustment(self, direction):
        """Adjusts current value of the spinbox either up or down a step.
        """
        # TODO currently this does not take into account changes in magnitude.
        #   So for example when stepping down, this goes
        #       10.1e10 -> 10.0e10 -> 9.0e9, instead of
        #       10.1e10 -> 10.0e10 -> 9.9e9
        try:
            cur_val = self._get_value()
        except decimal.InvalidOperation:
            return
        sign, digits, exp = cur_val.as_tuple()
        adj_digits = 1, *(0 for _ in range(len(digits) - 2))
        adjustment = Decimal((direction, adj_digits, exp))
        self.set_value(cur_val + adjustment)

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

