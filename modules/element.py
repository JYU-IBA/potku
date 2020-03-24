# coding=utf-8
"""
Created on 10.4.2013
Updated on 31.1.2020

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
             "Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen \n " \
             "Juhani Sundell"
__version__ = "2.0"

import re

import modules.masses as masses


class Element:
    """
    Element class that handles information about one element.
    """
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
            # FIXME crashes here. Steps:
            #           - open sample request from JYU web site
            #           - redo cuts by saving them
            #           - create a composition change graph or energy spectra
            #           - crashes here because of an empty string
            raise ValueError("Incorrect string given.")

    def __str__(self):
        """Transform element into string.

        Return:
            Returns element, isotope and amount in string format.
        """
        if self.isotope and self.amount:
            return "{0}{1} {2}".format(int(round(self.isotope)), self.symbol,
                                       self.amount)
        if self.isotope:    # TODO unnecessary int?
            return "{0}{1}".format(int(round(self.isotope)), self.symbol)
        if self.amount:
            return "{0} {1}".format(self.symbol, self.amount)
        return self.symbol

    def __eq__(self, other):
        """Compare object.

        Return:
            Boolean representing equality.
        """
        if not isinstance(other, Element):
            return NotImplemented
        return str(self) == str(other)

    def __lt__(self, other):
        """Comparison function for Elements. Elements are compared first by
        symbols, and if those match, then by isotopes and amounts.
        """
        # TODO could also use atomic number for comparison
        # TODO could use standard isotope to sort when no isotope is defined
        if not isinstance(other, Element):
            return NotImplemented

        if self.symbol != other.symbol:
            return self.symbol < other.symbol

        # Elements that have no isotopes come before elements that do
        if self.isotope is None and other.isotope is not None:
            return True

        if self.isotope is not None and other.isotope is None:
            return False

        return str(self) < str(other)

    def __repr__(self):
        return str(self)

    def get_prefix(self):
        """Returns a string representation of an element without amount.

        Return:
            '[isotope][symbol]' if isotope is specified, otherwise '[symbol]'
        """
        if self.isotope is None:
            return self.symbol
        return f"{round(self.isotope)}{self.symbol}"

    def get_mass(self):
        if self.isotope:
            return masses.find_mass_of_isotope(self)
        else:
            return masses.get_standard_isotope(self.symbol)

    def get_mcerd_params(self, return_amount=False):
        """Returns the element's mass or amount as a parameter for MCERD.

        Args:
            return_amount: whether amount is returned or mass and symbol.

        Return:
            string.
        """
        if return_amount:
            if self.amount is None:
                raise ValueError(
                    "Cannot return amount as mcerd parameter as the "
                    "element has no amount.")

            if self.amount > 1:
                amount = self.amount / 100
            else:
                amount = self.amount
            return f"%0.3f" % amount

        return "%0.2f %s" % (self.get_mass(), self.symbol)
