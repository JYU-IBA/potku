# coding=utf-8
'''
Created on 13.5.2013
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

# http://code.activestate.com/recipes/68205-null-object-design-pattern/
class Null:
    """A class for implementing Null objects.

    This class ignores all parameters passed when constructing or 
    calling instances and traps all attribute and method requests. 
    Instances of it always (and reliably) do 'nothing'.

    The code might benefit from implementing some further special 
    Python methods depending on the context in which its instances 
    are used. Especially when comparing and coercing Null objects
    the respective methods' implementation will depend very much
    on the environment and, hence, these special methods are not
    provided here.
    """

    # object constructing
    
    def __init__(self, *args, **kwargs):
        "Ignore parameters."
        return None

    # object calling

    def __call__(self, *args, **kwargs):
        "Ignore method calls."
        return self

    # attribute handling

    def __getattr__(self, mname):
        "Ignore attribute requests."
        return self

    def __setattr__(self, name, value):
        "Ignore attribute setting."
        return self

    def __delattr__(self, name):
        "Ignore deleting attributes."
        return self

    # misc.

    def __repr__(self):
        "Return a string representation."
        return "<Null>"

    def __str__(self):
        "Convert to a string and return it."
        return "Null"
