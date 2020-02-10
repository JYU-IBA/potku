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

import re

from PyQt5.QtGui import QValidator


class InputValidator(QValidator):
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
