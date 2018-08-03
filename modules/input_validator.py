# coding=utf-8
"""
Created on 10.5.2013
Updated on 3.8.2018

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

import re

from PyQt5.QtGui import QValidator


class InputValidator(QValidator):
    """Validator to check the validity of user inputs.
    
    Accepts double values with scientific notation (i.e. 0.232, 12.5e-12) and
    turns empty input to 0.0 and commas (,) to points (.).
    """
    def __init__(self):
        """Initiates the class.
        """
        super().__init__()

        self.float_re = re.compile(r'(([+-]?\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?)')

    def validate(self, input_value, pos):
        """Validates the given input. Overrides the QDoubleValidator's validate 
        function.
        
        Args:
            input_value: User given string to be validated.
            pos: Cursor position (if required).
        """
        match = self.float_re.search(input_value)
        if match.groups()[0] == input_value:
            return QValidator.Acceptable
        if input_value == "" or input_value[pos - 1] in "e.-+":
            return QValidator.Intermediate
        return QValidator.Invalid

        # input_value = input_value.replace(",", ".")
        # state, pos, a = QValidator.validate(self, input_value, pos)
        # if input_value == "" or input_value == '.':
        #     pos = "0.0"
        #     return QValidator.Intermediate, pos, a
        # if state != QValidator.Acceptable:
        #     return QValidator.Invalid, pos, a
        # return QValidator.Acceptable, pos, a

    def fixup(self, text):
        """
        Fix the text
        """
        match = self.float_re.search(text)
        if match:
            return match.groups()[0]
        else:
            return ""
