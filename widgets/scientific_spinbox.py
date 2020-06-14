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
import modules.math_functions as mf

from widgets.input_validation import InputValidator

from decimal import Decimal
from pathlib import Path

from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5 import uic


class ScientificSpinBox(QtWidgets.QWidget):
    """
    Class for custom double spinbox that handles scientific notation.
    """
    def __init__(self, value=0.0, minimum=0.0, maximum=math.inf,
                 step=0.1, decimals=17, show_btns=True):
        """
        Initializes the spinbox.

        Args:
            value: Number for spinbox.
            minimum: Minimum allowed value.
            maximum: Maximum allowed value.
            double: Whether to validate for double or int.
            show_btns: Whether buttons that increase or decrease the value
                       are shown.
        """
        super().__init__()
        uic.loadUi(Path("ui_files", "ui_scientific_spinbox_widget.ui"), self)
        self.minimum = minimum
        self.maximum = maximum
        self.step = step
        self.decimals = decimals

        self.set_value(value)

        #self.scientificLineEdit.textChanged.connect(lambda: self.validate(
        #    self.scientificLineEdit.cursorPosition()
        #))

        if show_btns:
            self.upButton.clicked.connect(lambda *_: self._set_value(1))
            self.downButton.clicked.connect(lambda *_: self._set_value(-1))
        else:
            self.upButton.hide()
            self.downButton.hide()

        self.scientificLineEdit.installEventFilter(self)

    def _set_value(self, coef):
        cur_value = self.get_value()
        v, m = mf.split_scientific_notation(cur_value)
        self.set_value((v + coef * self.step) * m)

    def eventFilter(self, source, event):
        """
        Check minimum and maximum values when focusing out of the spinbox.
        """
        if event.type() == QtCore.QEvent.FocusOut:
            # self.check_min_and_max()
            return super().eventFilter(source, event)
        return super().eventFilter(source, event)

    def set_value(self, value: float):
        """Sets the value of the Spin box, provided that the given value is
        valid.
        """
        if value < self.minimum:
            value = self.minimum
        if value > self.maximum:
            value = self.maximum

        self.scientificLineEdit.setText(
            mf.format_to_scientific_notation(value, max_decimals=self.decimals)
        )

    def get_value(self) -> float:
        """Returns the value of the spinbox as a float.
        """
        return float(self.scientificLineEdit.text())
