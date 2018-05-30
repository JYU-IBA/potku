# coding=utf-8
"""
Created on 10.5.2013
Updated on 30.5.2018

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
__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen \n " \
             "Samuli Rahkonen \n Miika Raunio \n Severi Jääskeläinen \n " \
             "Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"
__version__ = "2.0"
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtGui import QValidator
from sys import float_info


class InputValidator(QDoubleValidator):
    """Validator to check the validity of user inputs.
    
    Accepts double values with scientific notation (i.e. 0.232, 12.5e-12) and
    turns empty input to 0.0 and commas (,) to points (.).
    """
    def __init__(self, bottom=float_info.min, top=float_info.max,
                 decimals=float_info.dig, parent=None):
        """Initiates the class.
        
        Args:
            bottom: Float minimum value.
            top: Float maximum value.
            decimals: Integer representing decimals.
            parent: Parent object.
        """
        QDoubleValidator.__init__(self, bottom, top, decimals, parent)
        self.setNotation(QDoubleValidator.ScientificNotation)

    def validate(self, input_value, pos):
        """Validates the given input. Overrides the QDoubleValidator's validate 
        function.
        
        Args:
            input_value: User given string to be validated.
            pos: Cursor position (if required).
        """
        input_value = input_value.replace(",", ".")
        state, pos, a = QDoubleValidator.validate(self, input_value, pos)
        if input_value == "" or input_value == '.':
            pos = "0.0"
            return QValidator.Intermediate, pos, a
        if state != QValidator.Acceptable:
            return QValidator.Invalid, pos, a
        return QValidator.Acceptable, pos, a
