# coding=utf-8
'''
Created on 10.4.2013
Updated on 23.5.2013

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
    def __init__(self, element="", isotope=None):
        '''Inits element class.        
        
        >>> test_a = Element("1H")
        >>> test_b = Element("H")
        >>> test_c = Element("H", 1)
        >>> test_d = Element("Ca", 40)
        >>> test_e = Element("")
        >>> test_f = Element("H1")
        >>> print(test_a)
        1H
        >>> print(test_b)
        H
        >>> print(test_c)
        1H
        >>> print(test_d)
        40Ca
        >>> print(test_f) # Suppose we ignore numbers or whatever after element.
        H
        '''
        if element:
            m = re.match("(?P<isotope>[0-9]{0,2})(?P<element>[a-zA-Z]{1,2})", 
                         element.strip())
            if m:
                self.name = m.group("element")
                if isotope:
                    self.isotope = Isotope(isotope)
                else:
                    self.isotope = Isotope(m.group("isotope"))
            else: 
                raise ValueError("Incorrect string given.")
        else:
            self.name = element
            self.isotope = Isotope(isotope)

    
    def __str__(self):
        '''Transform element into string.
        
        Return:
            Returns element and its isotope in string format.
        '''
        return "{0}{1}".format(self.isotope, self.name)


    def get_element_and_isotope(self):
        '''Get Element's name and isotope.
        
        Return:
            Returns element's name (string) and its isotope (class object).
        '''
        return self.name, self.isotope




class Isotope:
    def __init__(self, isotope):
        '''Inits isotope class.
        
        >>> test_a = Isotope(2)
        >>> test_b = Isotope("a")
        Traceback (most recent call last):
        ...
        ValueError: invalid literal for int() with base 10: 'a'
        >>> print(str(test_a))
        2
        '''
        if isotope == "" or isotope == "None" or not isotope:  # Mundane check
            self.mass = None
        else:
            self.mass = int(isotope)
    
    
    def __str__(self):
        '''Transform isotope into string.
        
        Return:
            Returns isotope in string format.
        '''
        if not self.mass:  # Otherwise will get "NoneO".
            return ""
        else:
            return str(self.mass)


if __name__ == "__main__":
    import doctest
    doctest.testmod()
