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

        self.float_re_1 = re.compile(
            r'(-?\d+(((\.\d+)|\d*)[eE]?[+-]?\d*))|(-?)')
        self.float_re_2 = re.compile(r'(-?\d+\.)')

    def validate(self, input_value, pos):
        """Validates the given input. Overrides the QDoubleValidator's validate 
        function.
        
        Args:
            input_value: User given string to be validated.
            pos: Cursor position (if required).
        """
        match = re.match(self.float_re_2, input_value)
        if match and match.group(0) == input_value:
            return match.group(0)
        else:
            match = re.match(self.float_re_1, input_value)
            if match:
                return match.group(0)
            else:
                return ""

