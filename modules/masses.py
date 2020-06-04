# coding=utf-8
"""
Created on 20.3.2013
Updated on 6.5.2018

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

Reads data of the elements isotopes from masses.dat
"""
__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen \n " \
             "Samuli Rahkonen \n Miika Raunio \n Severi Jääskeläinen \n " \
             "Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen \n " \
             "Juhani Sundell"
__version__ = "2.0"

import os

from .parsing import CSVParser

from pathlib import Path
from collections import defaultdict

_ISOTOPES = defaultdict(list)
NUMBER_KEY = "number"
ABUNDANCE_KEY = "abundance"
MASS_KEY = "mass"

this_dir = Path(__file__).parent
file_path = Path(this_dir, os.pardir, "external", "Potku-data",
                 "masses.dat").resolve()

# Parser to parse data from masses.dat. Empty rows are ignored, first line
# is skipped.
parser = CSVParser((3, str), (2, int), (5, float), (4, float))
data = parser.parse_file(file_path, ignore="e", method="row", skip=1)

for elem, n, a, m in data:
    _ISOTOPES[elem].append({
        NUMBER_KEY: n,
        ABUNDANCE_KEY: a,
        MASS_KEY: m
    })

# TODO maybe sort the isotopes by abundance already at this point. Most of the
#  time we need them sorted anyway

# Remove extra variables
del elem, n, a, m
del this_dir, file_path
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
        if rounded_isotope == isotope[NUMBER_KEY]:
            return isotope[MASS_KEY] / 1_000_000


def get_standard_isotope(symbol):
    """Calculate standard element weight.

    Args:
        symbol: a string symbol representing an element, e.g. 'He'

    Return:
        Returns standard weight of given element (float). If the symbol is
        unknown, 0 is returned.
    """
    # TODO should this be called get_standard_mass?
    return sum(iso[NUMBER_KEY] * iso[ABUNDANCE_KEY]
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
