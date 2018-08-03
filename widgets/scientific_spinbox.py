# coding=utf-8
"""
Created on 3.8.2018

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

import re

from modules.input_validator import InputValidator

from PyQt5 import QtWidgets

from sys import float_info


class ScientificDoubleSpinBox(QtWidgets.QDoubleSpinBox):
    """
    Class for custom double spinbox that handles scientific notation.
    """
    def __init__(self):
        """
        Initializes the spinbox.
        """
        super().__init__()
        self.setMinimum(float_info.min)
        self.setMaximum(float_info.max)

        self.validator = InputValidator()
        self.setDecimals(1000)

        self.__float_re = re.compile(
            r'(([+-]?\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?)')

    def validate(self, p_str, p_int):
        return self.validator.validate(p_str, p_int)

    def fixup(self, p_str):
        return self.validator.fixup(p_str)

    def textFromValue(self, p_float):
        string = "{:g}".format(p_float).replace("e+", "e")
        string_2 = re.sub("e(-?)0*(\d+)", r"e\1\2", string)

        return string_2

    def valueFromText(self, p_str):
        return float(p_str)

    def stepBy(self, p_int):
        text = self.cleanText()
        groups = self.__float_re.search(text).groups()
        decimal = float(groups[1])
        decimal += p_int
        new_string = "{:g}".format(decimal) + (groups[3] if groups[3] else "")
        self.lineEdit().setText(new_string)
