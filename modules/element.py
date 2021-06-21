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
Sinikka Siironen, 2020 Juhani Sundell

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
             "Juhani Sundell \n Tuomas Pitkänen"
__version__ = "2.0"

import re

from . import masses as masses

from .base import MCERDParameterContainer


class Element(MCERDParameterContainer):
    """
    Element class that handles information about one element.
    """
    def __init__(self, symbol, isotope=None, amount=0.0):
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
        m = re.match(r"(?P<isotope>[0-9]{0,3})(?P<symbol>[a-zA-Z]{1,2})"
                     r"(\s(?P<amount>\d*(\.?\d+)?))?", element_str.strip())
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
            raise ValueError(
                f"Could not intialize an Element from the given "
                f"string: {element_str}")

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
        return all((
            self.isotope == other.isotope,
            self.symbol == other.symbol,
            self.amount == other.amount
        ))

    def __lt__(self, other):
        """Comparison function for Elements. Elements are compared first by
        standard isotopes, and if those match (i.e. they are the same element),
        then by isotopes and amounts.
        """
        if not isinstance(other, Element):
            return NotImplemented

        if self.symbol != other.symbol:
            m1 = masses.get_standard_isotope(self.symbol)
            m2 = masses.get_standard_isotope(other.symbol)
            if m1 and m2:
                # If both standard masses have been defined, compare which one
                # is smaller
                return m1 < m2
            elif m1 != m2:
                # If one of the standard masses is not defined, compare which
                # one is bigger
                return m1 > m2

        # Elements that have no isotopes come before elements that do
        if self.isotope is None and other.isotope is not None:
            return True

        if self.isotope is not None and other.isotope is None:
            return False

        return str(self) < str(other)

    def __repr__(self):
        """Returns a human readable representation of the Element object.
        """
        return f"Element(symbol={self.symbol}, isotope={self.isotope}, " \
               f"amount={self.amount})"

    def __hash__(self):
        return hash((self.isotope, self.symbol, self.amount))

    def get_prefix(self):
        """Returns a string representation of an element without amount.

        Return:
            '[isotope][symbol]' if isotope is specified, otherwise '[symbol]'
        """
        if self.isotope is None:
            return self.symbol
        return f"{round(self.isotope)}{self.symbol}"

    def get_mass(self):
        """Returns the mass of the Element. If the element has no
        defined isotope, standard mass is returned.
        """
        if self.isotope:
            return masses.find_mass_of_isotope(self.symbol, self.isotope)
        else:
            return masses.get_standard_isotope(self.symbol)

    def get_st_mass(self):
        """Returns the standard mass of the Element.
        """
        return masses.get_standard_isotope(self.symbol)

    def get_most_common_isotope(self):
        """Returns the isotope number of the most common isotope of this type
        of element.
        """
        isot = masses.get_most_common_isotope(self.symbol)
        if isot is None:
            return None
        return isot[masses.NUMBER_KEY]

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

    def create_copy(self):
        """Returns a copy of self"""
        return self.__class__(self.symbol, self.isotope, self.amount)

    @classmethod
    def get_isotopes(cls, symbol, include_st_mass=True):
        """Returns all isotopes of an element with given symbol. Isotopes are
        returned as a list of dictionaries. Each dictionary contains an
        Element object as well as natural abundance and mass values.

        Args:
            symbol: symbol of the element
            include_st_mass: whether a standard mass option is included in
                the returned list. If True, the first element in the list is
                a dictionary that contains an Element with no isotope defined
                and the mass value will be the same as standard mass for the
                element.

        Return:
            list of dictionaries.
        """
        isotopes = []
        if include_st_mass:
            st_mass = masses.get_standard_isotope(symbol)
            if st_mass:
                isotopes.append({
                    "element": cls(symbol),
                    masses.ABUNDANCE_KEY: None,
                    masses.MASS_KEY: st_mass
                })

        isotopes.extend({
                "element": cls(symbol, iso.pop("number")),
                **iso
            }
            for iso in masses.get_isotopes(
                symbol, filter_unlikely=True, sort_by_abundance=True))

        return isotopes
