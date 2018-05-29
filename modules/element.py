# coding=utf-8
"""
Created on 10.4.2013
Updated on 3.5.2018

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
"""
__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen \n " \
             "Samuli Rahkonen \n Miika Raunio \n Severi Jääskeläinen \n " \
             "Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"
__version__ = "2.0"

import re


class Element:
    def __init__(self, symbol, isotope=None, amount=None):
        """Initializes an element object.
        Args:
              symbol: Two letter symbol of the element. E.g. 'He' for Helium.
              isotope: The isotope number. If one wants to use standard mass,
                       then this parameter is not required.
              amount:  This is an optional parameter. It is used to describe
                       the amount of the element in a single layer of a target.
        """
        self.symbol = symbol
        self.isotope = isotope
        self.amount = amount

    @classmethod
    def from_string(cls, element_str):
        """A function that initializes an element object from a string.
        Args:
            element_str: A string from which the element information will be
                         parsed.

        Return:
            Element object.
        """
        m = re.match("(?P<isotope>[0-9]{0,3})(?P<symbol>[a-zA-Z]{1,2})"
                     "(\s(?P<amount>\d*(\.?\d+)?))?", element_str.strip())
        if m:
            symbol = m.group("symbol")
            isotope = m.group("isotope")
            amount = m.group("amount")

            if isotope and amount:
                return cls(symbol, int(isotope), float(amount))
            elif isotope:
                return cls(symbol, int(isotope))
            elif amount:
                return cls(symbol, None, float(amount))
            else:
                return cls(symbol)
        else:
            raise ValueError("Incorrect string given.")

    def __str__(self):
        """Transform element into string.

        Return:
            Returns element, isotope and amount in string format.
        """
        if self.isotope and self.amount:
            return "{0}{1} {2}".format(int(round(self.isotope)), self.symbol,
                                       self.amount)
        if self.isotope:
            return "{0}{1}".format(int(round(self.isotope)), self.symbol)
        if self.amount:
            return "{0} {1}".format(self.symbol, self.amount)
        return self.symbol

    def __eq__(self, other):
        """Compare object.

        Return:
            Boolean representing equality.
        """
        return str(self) == str(other)


if __name__ == "__main__":
    import doctest

    doctest.testmod()
