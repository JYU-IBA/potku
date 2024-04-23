# coding=utf-8
"""
Created on 20.3.2013
Updated on 18.4.2024

Potku

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
along with this program (file named 'LICENSE').

Reads element, isotope and abundance information from masses.dat and abundances.dat (from JIBAL)
"""
__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen \n " \
             "Samuli Rahkonen \n Miika Raunio \n Severi Jääskeläinen \n " \
             "Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen \n " \
             "Juhani Sundell \n Jaakko Julin"
__version__ = "2.0"

from collections import defaultdict

from . import general_functions as gf
from .parsing import CSVParser

_MAX_ELEMENTS = 120
_ISOTOPES = defaultdict(list)
_ELEMENTS = [""] * _MAX_ELEMENTS
MASS_NUMBER_KEY = "mass_number"
ABUNDANCE_KEY = "abundance"
MASS_KEY = "mass"

masses_file = gf.get_data_dir() / "jibal" / "masses.dat"

# Parser to parse data from masses.dat. Empty rows are ignored, first line
# is skipped since it contains information about the neutron, which we can ignore
parser = CSVParser((1, str), (3, int), (4, int), (5, float))
data = parser.parse_file(masses_file, method="row", skip=1)

for elem, Z, A, m in data:
    if 0 < Z < _MAX_ELEMENTS:
        _ELEMENTS[Z] = elem

    _ISOTOPES[elem].append({
        MASS_NUMBER_KEY: A,
        ABUNDANCE_KEY: 0.0,
        MASS_KEY: m
    })

# Parsing abundances.dat, filling abundances in _ISOTOPES table

abundances_file = gf.get_data_dir() / "jibal" / "abundances.dat"
parser = CSVParser((0, int), (1, int), (2, float))
data = parser.parse_file(abundances_file, method="row")
for Z, A, abundance in data:
    for isotope in _ISOTOPES[_ELEMENTS[Z]]:
        if isotope[MASS_NUMBER_KEY] == A:
            isotope[ABUNDANCE_KEY] = abundance * 100.0


# TODO maybe sort the isotopes by abundance already at this point. Most of the
#  time we need them sorted anyway

# Remove extra variables
del elem, A, Z, m
del masses_file
del parser, data


def get_isotopes(symbol, sort_by_abundance=True, filter_unlikely=True):
    """Get isotopes of given element.

    Args:
        symbol: string representing element's symbol, e.g. "He".
        sort_by_abundance: whether isotopes are sorted by abundance.
        filter_unlikely: whether isotopes that have an abundance of 0 will
            be filtered out.

    Return:
        Returns a list of element's isotopes as dictionaries. Keys are
        'number', 'natural_abundance' and 'exact_mass'. Dictionaries are
        copies of the original values so it is safe to mutate them.
    """
    # Note: as _ISOTOPES is a defaultdict, we could just use _ISOTOPES[symbol]
    # without risking a KeyError. However this would also add the symbol as a
    # key to the dictionary which we want to avoid. get method can be used to
    # return a default value without adding new keys.
    isos = (dict(iso) for iso in _ISOTOPES.get(symbol, []))

    if filter_unlikely:
        isos = filter(lambda iso: iso[ABUNDANCE_KEY], isos)
    if sort_by_abundance:
        return sorted(isos, key=lambda iso: iso[ABUNDANCE_KEY],
                      reverse=True)
    return list(isos)


def find_mass_of_isotope(symbol, isotope):
    """Find the mass of the Element object (isotope).

    Args:
         symbol: string representation of the element
         isotope: number representation of the isotope

    Return:
         Returns the mass of the wanted isotope.
    """
    rounded_isotope = round(isotope)
    for isotope in get_isotopes(symbol):
        if rounded_isotope == isotope[MASS_NUMBER_KEY]:
            return isotope[MASS_KEY]


def get_standard_isotope(symbol):
    """Calculate standard element weight.

    Args:
        symbol: a string symbol representing an element, e.g. 'He'

    Return:
        Returns standard weight of given element (float). If the symbol is
        unknown, 0 is returned.
    """
    # TODO should this be called get_standard_mass?
    return sum(iso[MASS_KEY] * iso[ABUNDANCE_KEY]
               for iso in get_isotopes(symbol, sort_by_abundance=False)) / 100


def get_most_common_isotope(symbol: str) -> dict:
    """Get the most common isotope for an element.

    Args:
        symbol: String representing element.

    Return:
        dictionary representing the isotope or None if the symbol is unknown.
        Keys are 'number', 'natural_abundance' and 'exact_mass.
    """
    isotopes = get_isotopes(symbol, sort_by_abundance=True,
                            filter_unlikely=True)
    return isotopes[0] if isotopes else None
