# coding=utf-8
"""
Created on 3.8.2018
Updated on 16.8.2018


Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2013-2018 Jarkko Aalto, Severi Jääskeläinen, Samuel Kaiponen,
Timo Konu, Samuli Kärkkäinen, Samuli Rahkonen, Miika Raunio, Heta Rekilä and
Sinikka Siironen

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

__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen \n Samuli " \
             "Rahkonen \n Miika Raunio \n" \
             "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä " \
             "\n Sinikka Siironen \n Juhani Sundell"
__version__ = "2.0"

import re

from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore


class InputValidator(QtGui.QValidator):
    """Validator to check the validity of user inputs.
    
    Accepts double values with scientific notation (i.e. 0.232, 12.5e-12) and
    turns empty input to 0.0 and commas (,) to points (.).
    """
    def __init__(self, double):
        """Initiates the class.

        Args:
            double: Whether to validate for double or int.
        """
        super().__init__()

        if double:
            self.float_re_1 = re.compile(
                r'(-?\d+(((\.\d+)|\d*)[eE]?[+-]?\d*))|(-?)')
            self.float_re_2 = re.compile(r'(-?\d+\.$)')
            self.float_re_4 = re.compile(r'(-?\d+\.$)')
            self.float_re_3 = re.compile(r'(.*[^eE][+-].*)')
        else:
            self.float_re_1 = re.compile(r'(-?\d+([eE]?[+-]?\d*))|(-?)')
            self.float_re_2 = re.compile(r'(-?\d+$)')
            self.float_re_4 = re.compile(r'(-?\d+\.$)')
            self.float_re_3 = re.compile(r'(.*[^eE][+-].*)')

    def validate(self, input_value, pos):
        """Validates the given input. Overrides the QDoubleValidator's validate 
        function.
        
        Args:
            input_value: User given string to be validated.
            pos: Cursor position (if required).
        """
        new_result_2 = None
        match_2 = re.match(self.float_re_3, input_value)
        if match_2:
            new_result = input_value[1:].replace("-", "")
            new_result_2 = input_value[0] + new_result.replace("+", "")
            if "e+" in input_value and "e+" not in new_result_2:
                nr = new_result_2[1:].replace("e", "e+")
                new_result_2 = input_value[0] + nr
            elif "e-" in input_value and "e-" not in new_result_2:
                nr = new_result_2[1:].replace("e", "e-")
                new_result_2 = input_value[0] + nr

        if new_result_2:
            inp = new_result_2
        else:
            inp = input_value

        match = re.match(self.float_re_2, inp)
        if match:
            return match.group(0)
        else:
            if len(inp) > 1 and inp[len(inp) - 1] == 'e':
                match = re.match(self.float_re_4, inp[:len(inp) - 1])
                if match:
                    return match.group(0)
            match = re.match(self.float_re_1, inp)
            if match:
                return match.group(0)
            else:
                return ""


class ScientificValidator(QtGui.QDoubleValidator):
    """Validator for scientific notation.
    """
    def __init__(self, *args, accepted=None, intermediate=None, invalid=None):
        """Initializes a new ScientificValidator.

        Args:
            *args: positional arguments passed down to QDoubleValidator
            accepted: function that is called if validation result is
                QDoubleValidator.Acceptable
            intermediate: function that is called if validation result is
                QDoubleValidator.Intermediate
            invalid: function that is called if validation result is
                QDoubleValidator.Invalid
        """
        super().__init__(*args)
        self.setNotation(QtGui.QDoubleValidator.ScientificNotation)
        self.setLocale(QtCore.QLocale.c())
        self._accepted = accepted
        self._intermediate = intermediate
        self._invalid = invalid

    def validate(self, value: str, position: int):
        """Overrides QDoubleValidator's validate method.
        """
        state, inp, pos = super().validate(value, position)
        if state == QtGui.QDoubleValidator.Acceptable:
            if self._accepted is not None:
                self._accepted()
        elif state == QtGui.QDoubleValidator.Intermediate:
            if self._intermediate is not None:
                self._intermediate()
        else:
            if self._invalid is not None:
                self._invalid()
        return state, inp, pos


def check_text(input_field: QtWidgets.QLineEdit, qwidget=None):
    """Checks if the given QLineEdit input field contains text. If not,
    field's background is set red.

    Args:
        input_field: QLineEdit object.
        qwidget: parent of input_field or None

    Return:
        True for white, False for red.
    """
    if not input_field.text():
        set_input_field_red(input_field)
        if qwidget is not None:
            qwidget.fields_are_valid = False
        return False
    else:
        set_input_field_white(input_field)
        if qwidget is not None:
            qwidget.fields_are_valid = True
        return True


def set_input_field_red(input_field: QtWidgets.QWidget):
    """Sets the background of given input field red.

    Args:
        input_field: Qt widget that supports Qt Style Sheets.
    """
    input_field.setStyleSheet("background-color: %s" % "#f6989d")


def set_input_field_white(input_field: QtWidgets.QWidget):
    """Sets the background of given input field white.

    Args:
        input_field: Qt widget that supports Qt Style Sheets.
    """
    input_field.setStyleSheet("background-color: %s" % "#ffffff")


def set_input_field_yellow(input_field: QtWidgets.QWidget):
    """Sets the background of given input field yellow.

    Args:
        input_field: Qt widget that supports Qt Style Sheets.
    """
    input_field.setStyleSheet("background-color: %s" % "#ebde34")


def validate_text_input(text, regex):
    """
    Validate the text using given regular expression. If not valid, remove
    invalid characters.

    Args:
        text: Text to validate.
        regex: Regular expression to match.
    """
    valid = re.match(regex + "$", text)

    if "_" in regex:  # Request name
        substitute_regex = "[^A-Za-z0-9_ÖöÄäÅå-]"
    else:  # Other names
        substitute_regex = "[^A-Za-z0-9-ÖöÄäÅå]"

    if not valid:
        valid_text = re.sub(substitute_regex, '', text)
        return valid_text
    else:
        return text


def sanitize_file_name(line_edit: QtWidgets.QLineEdit):
    """Sanitizes the text in the given input so that it is okay to use in a
    file name.

    Args:
        line_edit: QLineEdit object.
    """
    text = line_edit.text()
    regex = "^[A-Za-z0-9-ÖöÄäÅå]*"
    valid_text = validate_text_input(text, regex)

    line_edit.setText(valid_text)
