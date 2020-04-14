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

import widgets.input_validation as iv

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
    def __init__(self, value, multiplier, minimum, maximum, double=True,
                 show_btns=True):
        """
        Initializes the spinbox.

        Args:
            value: Number for spinbox.
            multiplier: Multiplier for number.
            minimum: Minimum allowed value.
            maximum: Maximum allowed value.
            double: Whether to validate for double or int.
            show_btns: Whether buttons that increase or decrease the value
                       are shown.
        """
        super().__init__()
        uic.loadUi(Path("ui_files", "ui_scientific_spinbox_widget.ui"), self)

        self.validator = InputValidator(double)
        self.minimum = minimum
        self.maximum = maximum

        # There can only be 17 characters in the value part
        if len(str(value)) > 17:
            new_value = str(value)[:18]
            value = float(new_value)
        self.value = value
        self.multiplier = multiplier

        if "e" in str(self.value):
            self.value_str = str(self.value)
        else:
            self.value_str = str(self.value) + str(self.multiplier)[1:]
        self.scientificLineEdit.setText(self.value_str)

        self.scientificLineEdit.textChanged.connect(lambda: self.validate(
            self.scientificLineEdit.cursorPosition()
        ))

        if show_btns:
            self.upButton.clicked.connect(self.increase_value)
            self.downButton.clicked.connect(self.decrease_value)
        else:
            self.upButton.hide()
            self.downButton.hide()

        self.scientificLineEdit.installEventFilter(self)

    def check_min_and_max(self):
        """
        Check that value inside line edit is inside the minimum and maximum.
        Also check that value is floatable.
        """
        value_str = self.scientificLineEdit.text()
        if self.check_valid():
            value = float(value_str)
            if value < self.minimum:
                self.scientificLineEdit.setText(str(self.minimum))
            elif value > self.maximum:
                self.scientificLineEdit.setText(str(self.maximum))
            iv.set_input_field_white(self.scientificLineEdit)
            if 'e' in value_str:
                index = value_str.index('e')
                self.value = float(Decimal(value_str[:index]))
                self.multiplier = float(Decimal("1" + value_str[index:]))
            else:
                self.value = float(value_str)
                self.multiplier = 1
            self.value_str = value_str
            return True
        return False

    def check_valid(self):
        """
        Check if spinbox has a value that can be interpreted as a float.

        Return:
            True or False.
        """
        value_str = self.scientificLineEdit.text()
        try:
            value = float(value_str)
            if value_str.endswith('.'):
                raise ValueError
            iv.set_input_field_white(self.scientificLineEdit)
            self.value = value
            return True
        except ValueError:
            iv.set_input_field_red(self.scientificLineEdit)
            self.value = None
            self.multiplier = None
            return False

    def decrease_value(self):
        """
        Decrease the value of the spinbox. If scientific notation is used,
        decrease before the 'e'. If not, decrease the smallest decimal.
        """
        if not self.scientificLineEdit.hasFocus():
            self.scientificLineEdit.setFocus()
        value_str = self.scientificLineEdit.text()
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
                # TODO remove duplicate code and add tests
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

            self.scientificLineEdit.setText(new_text)
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

            self.scientificLineEdit.setText(new_text)

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
        if not self.scientificLineEdit.hasFocus():
            self.scientificLineEdit.setFocus()
        value_str = self.scientificLineEdit.text()
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

            self.scientificLineEdit.setText(new_text)
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

            self.scientificLineEdit.setText(new_text)

        self.validate(len(new_text))

    def validate(self, pos):
        """
        Validate the input.

        Args:
            pos: Position of the cursor on the string of text.
        """
        string = self.scientificLineEdit.text()
        match = self.validator.validate(string, pos)
        try:
            #if not float(match) <= self.maximum:
            #    match = match[:len(match) - 1]
            if not float(match) <= self.maximum:
                match = str(self.maximum)
            if not self.minimum <= float(match):
                match = str(self.minimum)
        except ValueError:
            pass
        # Find out if number part is longer than 17
        if 'e' in match:
            e_index = match.index('e')
            e_part = match[e_index:]
            number_part = match[:e_index]
            if len(number_part) > 17 and '.' in number_part:
                while len(number_part) > 17:
                    number_part = number_part[:len(number_part) - 1]
                match = number_part + e_part
        else:
            if len(match) > 17 and '.' in match:
                while len(match) > 17:
                    match = match[:len(match) - 1]

        self.scientificLineEdit.setText(match)
        self.scientificLineEdit.setCursorPosition(pos)
        iv.set_input_field_white(self.scientificLineEdit)
        self.check_valid()

    def set_value(self, value):
        """Sets the value of the Spin box, provided that the given value is
        valid.
        """
        # TODO treat the value internally as a float/decimal instead of a
        #  string
        self.scientificLineEdit.setText(str(value))

    def get_value(self):
        """Returns the value of the spinbox as a float.
        """
        return float(self.scientificLineEdit.text())
