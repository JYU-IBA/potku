# coding=utf-8
'''
Created on 10.4.2013
Updated on 19.6.2013

Potku is a graphical user interface for analyzation and 
visualization of measurement data collected from a ToF-ERD 
telescope. For physics calculations Potku uses external 
analyzation components.  
Copyright (C) Jarkko Aalto, Timo Konu, Samuli Kärkkäinen, Samuli Rahkonen and 
Miika Raunio

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
'''
__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen \n Samuli Rahkonen \n Miika Raunio"
__versio__ = "1.0"

import re

class Element:
    def __init__(self, element, isotope=None, amount=None):
        """Initializes an element object.
        Args:
              element: Two letter symbol of the element. E.g. 'He' for Helium.
              isotope: The isotope number. If one wants to use standard mass,
                       then this parameter is not required.
              amount:  This is an optional parameter. It is used to describe
                       the amount of the element in a single layer of a target.
        """
        self.element = element
        self.isotope = isotope
        self.amount = amount

    @classmethod
    def from_string(cls, str):
        """A function that initializes an element object from a string.
        Args:
            str: A string from which the element information will be parsed.
        """
        m = re.match("(?P<isotope>[0-9]{0,3})(?P<element>[a-zA-Z]{1,2})"
                     "(\s(?P<amount>\d*(\.?\d+)?))?", str.strip())
        if m:
            name = m.group("element")
            isotope = int(m.group("isotope"))
            amount = float(m.group("amount"))
        else:
            raise ValueError("Incorrect string given.")

        return cls(name, isotope, amount)

    
    def __str__(self):
        '''Transform element into string.
        
        Return:
            Returns element and its isotope in string format.
        '''
        return "{0}{1}".format(self.isotope, self.name)


    def __eq__(self, other): 
        '''Compare object.
        '''
        return str(self) == str(other)
    
                          
    def get_element_and_isotope(self):
        '''Get Element's name and isotope.
        
        Return:
            Returns element's name (string) and its isotope (class object).
        '''
        return self.name, self.isotope

if __name__ == "__main__":
    import doctest
    doctest.testmod()
