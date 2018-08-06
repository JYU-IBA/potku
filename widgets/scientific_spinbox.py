# coding=utf-8
"""
Created on 3.8.2018
Updated on 6.8.2018

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

import os

from modules.input_validator import InputValidator

from PyQt5 import QtWidgets
from PyQt5 import uic


class ScientificDoubleSpinBox(QtWidgets.QWidget):
    """
    Class for custom double spinbox that handles scientific notation.
    """
    def __init__(self, recoil_element, minimum, maximum, decimals):
        """
        Initializes the spinbox.

        Args:
            recoil_element: A RecoilElement object.
            minimum: Minimum allowed value.
            maximum: Maximum allowed value.
            decimals: Number of decimals.
        """
        super().__init__()
        self.ui = uic.loadUi(os.path.join("ui_files",
                                          "ui_scientific_spinbox_widget.ui"),
                             self)

        self.validator = InputValidator()
        self.minimum = minimum
        self.maximum = maximum
        self.decimals = decimals

        self.recoil_element = recoil_element
        self.ui.scientificLineEdit.setText(str(
            self.recoil_element.reference_density) + str(
            self.recoil_element.multiplier)[1:])

        self.ui.scientificLineEdit.textChanged.connect(lambda: self.validate(
            self.ui.scientificLineEdit.cursorPosition()
        ))

    def validate(self, pos):
        str = self.ui.scientificLineEdit.text()
        match = self.validator.validate(str, pos)
        try:
            if not self.minimum <= float(match) <= self.maximum:
                match = match[:pos - 1]
        except ValueError:
            pass
        self.ui.scientificLineEdit.setText(match)
        self.ui.scientificLineEdit.setCursorPosition(pos)
