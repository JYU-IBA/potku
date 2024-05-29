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
from typing import Optional, Callable, Tuple

from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore


class ScientificValidator(QtGui.QDoubleValidator):
    """Validator for scientific notation.
    """
    def __init__(
            self,
            minimum: float,
            maximum: float,
            decimal_places: int,
            parent: Optional[QtWidgets.QWidget] = None,
            accepted: Optional[Callable[[], None]] = None,
            intermediate: Optional[Callable[[], None]] = None,
            invalid: Optional[Callable[[], None]] = None):
        """Initializes a new ScientificValidator.

        Args:
            minimum: minimum allowed value
            maximum: maximum allowed value
            decimal_places: decimal places allowed
            parent: parent QWidget for this validator
            accepted: function that is called if validation result is
                QDoubleValidator.Acceptable
            intermediate: function that is called if validation result is
                QDoubleValidator.Intermediate
            invalid: function that is called if validation result is
                QDoubleValidator.Invalid
        """
        super().__init__(minimum, maximum, decimal_places, parent=parent)
        self.setNotation(QtGui.QDoubleValidator.ScientificNotation)
        self.setLocale(QtCore.QLocale.c())
        self._accepted = accepted
        self._intermediate = intermediate
        self._invalid = invalid

    def validate(
            self,
            value: str,
            position: int) -> Tuple[QtGui.QDoubleValidator.State, str, int]:
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
    input_field.setStyleSheet("background-color: #f6989d")


def set_input_field_white(input_field: QtWidgets.QWidget):
    """Sets the background of given input field white.

    Args:
        input_field: Qt widget that supports Qt Style Sheets.
    """
    if input_field.styleSheet():
        # Only set background white if style sheet has already
        # been defined, otherwise use default style. This fixes
        # an issue where ScientificSpinBoxes may appear smaller
        # than regular spin boxes on Windows.
        # FIXME this is a quick hack. There is probably a better
        #   way to do this.
        input_field.setStyleSheet("background-color: #ffffff")


def set_input_field_yellow(input_field: QtWidgets.QWidget):
    """Sets the background of given input field yellow.

    Args:
        input_field: Qt widget that supports Qt Style Sheets.
    """
    input_field.setStyleSheet("background-color: #ebde34")


def validate_text_input(text):
    """
    Validate the text using a hard coded regular expression. If not valid, remove
    invalid characters.

    Args:
        text: Text to validate.
    """

    valid_text = re.sub(r"[^\w\-]", '', text)
    valid_text = re.sub(r"[_]", '', valid_text)
    return valid_text


def sanitize_file_name(line_edit: QtWidgets.QLineEdit):
    """Sanitizes the text in the given input so that it is okay to use in a
    file name.

    Args:
        line_edit: QLineEdit object.
    """
    text = line_edit.text()
    valid_text = validate_text_input(text)

    line_edit.setText(valid_text)
