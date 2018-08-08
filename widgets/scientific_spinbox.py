# coding=utf-8
"""
Created on 3.8.2018
Updated on 7.8.2018

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

from decimal import Decimal

from modules.general_functions import set_input_field_red
from modules.general_functions import set_input_field_white
from modules.input_validator import InputValidator

from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5 import uic


class ScientificSpinBox(QtWidgets.QWidget):
    """
    Class for custom double spinbox that handles scientific notation.
    """
    def __init__(self, recoil_element, minimum, maximum, double=True):
        """
        Initializes the spinbox.

        Args:
            recoil_element: A RecoilElement object.
            minimum: Minimum allowed value.
            maximum: Maximum allowed value.
            double: Wheter to validate for double or int.
        """
        super().__init__()
        self.ui = uic.loadUi(os.path.join("ui_files",
                                          "ui_scientific_spinbox_widget.ui"),
                             self)

        self.validator = InputValidator(double)
        self.minimum = minimum
        self.maximum = maximum

        self.recoil_element = recoil_element
        self.ui.scientificLineEdit.setText(str(
            self.recoil_element.reference_density) + str(
            self.recoil_element.multiplier)[1:])
        self.value = self.recoil_element.reference_density
        self.multiplier = self.recoil_element.multiplier

        self.ui.scientificLineEdit.textChanged.connect(lambda: self.validate(
            self.ui.scientificLineEdit.cursorPosition()
        ))

        self.ui.upButton.clicked.connect(self.increase_value)
        self.ui.downButton.clicked.connect(self.decrease_value)

        self.ui.scientificLineEdit.installEventFilter(self)

    def check_min_and_max(self):
        """
        Check that value inside line edit is inside the minimum and maximum.
        Also check that value is floatable.
        """
        value_str = self.ui.scientificLineEdit.text()
        if self.check_valid():
            value = float(value_str)
            if value < self.minimum:
                self.ui.scientificLineEdit.setText(str(self.minimum))
            elif value > self.maximum:
                self.ui.scientificLineEdit.setText(str(self.maximum))
            set_input_field_white(self.ui.scientificLineEdit)
            if 'e' in value_str:
                index = value_str.index('e')
                self.value = float(Decimal(value_str[:index]))
                self.multiplier = float(Decimal("1" + value_str[index:]))
            else:
                self.value = float(value_str)
                self.multiplier = 1
            return True
        return False

    def check_valid(self):
        """
        Check if spinbox has a value that can be interpreted as a float.

        Return:
            True or False.
        """
        value_str = self.ui.scientificLineEdit.text()
        try:
            float(value_str)
            if value_str.endswith('.'):
                raise ValueError
            set_input_field_white(self.ui.scientificLineEdit)
            return True
        except ValueError:
            set_input_field_red(self.ui.scientificLineEdit)
            self.value = None
            self.multiplier = None
            return False

    def decrease_value(self):
        """
        Decrease the value of the spinbox. If scientific notation is used,
        decrease before the 'e'. If not, decrease the smallest decimal.
        """
        if not self.ui.scientificLineEdit.hasFocus():
            self.ui.scientificLineEdit.setFocus()
        value_str = self.ui.scientificLineEdit.text()
        try:
            float(value_str)
        except ValueError:
            return
        try:
            # If scientific notation in use
            e_index = value_str.index('e')
            number_part = value_str[:e_index]
            multiply_part = value_str[e_index:]
            parts = number_part.split('.')
            if len(parts) == 1:  # No decimal
                final_value = int(parts[0]) - 1
                new_text = str(final_value) + multiply_part
            else:
                decimals = parts[1]
                decimal_length = len(decimals)
                decrease = 1 / (10 ** decimal_length)
                value_f = float(parts[0]) + float("0." + decimals) - decrease

                final_value = round(value_f, decimal_length)

                check_split = str(final_value).split('.')
                add_zero = False
                if len(check_split[1]) < len(parts[1]):
                    add_zero = True

                if add_zero:
                    new_text = str(final_value) + "0" + multiply_part
                else:
                    new_text = str(final_value) + multiply_part

            self.ui.scientificLineEdit.setText(new_text)
        except ValueError:
            pass
            # Not scientific notation
            parts = value_str.split('.')
            if len(parts) == 1:  # No decimal
                final_value = int(parts[0]) - 1
                new_text = str(final_value)
            else:
                decimals = parts[1]
                decimal_length = len(decimals)
                decrease = 1 / (10 ** decimal_length)
                value_f = float(parts[0]) + float("0." + decimals) - decrease

                final_value = round(value_f, decimal_length)

                check_split = str(final_value).split('.')
                add_zero = False
                if len(check_split[1]) < len(parts[1]):
                    add_zero = True

                if add_zero:
                    new_text = str(final_value) + "0"
                else:
                    new_text = str(final_value)

            self.ui.scientificLineEdit.setText(new_text)

        self.validate(len(new_text))

    def eventFilter(self, source, event):
        """
        Check minimum and maximum values when focusing out of the spinbox.
        """
        if event.type() == QtCore.QEvent.FocusOut:
            self.check_min_and_max()
            return super().eventFilter(source, event)
        return super().eventFilter(source, event)

    def increase_value(self):
        """
        Increase the value of the spinbox. If scientific notation is used,
       increase before the 'e'. If not, increase the smallest decimal.
        """
        if not self.ui.scientificLineEdit.hasFocus():
            self.ui.scientificLineEdit.setFocus()
        value_str = self.ui.scientificLineEdit.text()
        try:
            float(value_str)
        except ValueError:
            return
        try:
            # If scientific notation in use
            e_index = value_str.index('e')
            number_part = value_str[:e_index]
            multiply_part = value_str[e_index:]
            parts = number_part.split('.')
            if len(parts) == 1:  # No decimal
                final_value = int(parts[0]) + 1
                if final_value * float("1" + multiply_part) > self.maximum:
                    new_text = str(self.maximum)
                else:
                    new_text = str(final_value) + multiply_part
            else:
                decimals = parts[1]
                decimal_length = len(decimals)
                increase = 1 / (10 ** decimal_length)
                value_f = float(parts[0]) + float("0." + decimals) + increase

                final_value = round(value_f, decimal_length)

                check_split = str(final_value).split('.')
                add_zero = False
                if len(check_split[1]) < len(parts[1]):
                    add_zero = True

                if add_zero:
                    new_text = str(final_value) + "0" + multiply_part
                else:
                    new_text = str(final_value) + multiply_part

                if final_value * float("1" + multiply_part) > self.maximum:
                    new_text = str(self.maximum)

            self.ui.scientificLineEdit.setText(new_text)
        except ValueError:
            pass
            # Not scientific notation
            parts = value_str.split('.')
            if len(parts) == 1:  # No decimal
                final_value = int(parts[0]) + 1
                new_text = str(final_value)
            else:
                decimals = parts[1]
                decimal_length = len(decimals)
                increase = 1 / (10 ** decimal_length)
                value_f = float(parts[0]) + float("0." + decimals) + increase

                final_value = round(value_f, decimal_length)

                check_split = str(final_value).split('.')
                add_zero = False
                if len(check_split[1]) < len(parts[1]):
                    add_zero = True

                if add_zero:
                    new_text = str(final_value) + "0"
                else:
                    new_text = str(final_value)

            self.ui.scientificLineEdit.setText(new_text)

        self.validate(len(new_text))

    def validate(self, pos):
        """
        Validate the input.

        Args:
            pos: Position of the cursor on the string of text.
        """
        string = self.ui.scientificLineEdit.text()
        match = self.validator.validate(string, pos)
        try:
            if not float(match) <= self.maximum:
                match = match[:len(match) - 1]
            if not float(match) <= self.maximum:
                match = str(self.maximum)
            if not self.minimum <= float(match):
                pass
        except ValueError:
            pass
        self.ui.scientificLineEdit.setText(match)
        self.ui.scientificLineEdit.setCursorPosition(pos)
        set_input_field_white(self.ui.scientificLineEdit)
        self.check_valid()
