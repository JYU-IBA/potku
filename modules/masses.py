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
             "Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"
__version__ = "2.0"

import csv
import os

__path_to_this_dir = os.path.dirname(__file__)
__FILE_PATH = os.path.join(__path_to_this_dir,
                           os.pardir,
                           "external",
                           "Potku-data",
                           "masses.dat")

_isotopes = {}

with open(__FILE_PATH) as file:
    for line in csv.reader(file, delimiter=" ", skipinitialspace=True):
        if line:  # skips empty lines
            if line[3] not in _isotopes:
                _isotopes[line[3]] = []
            _isotopes[line[3]].append((int(line[2]), float(line[5]),
                                       float(line[4])))
            # line[2] isotope number, line[5] natural abundance, line[4]
            # exact mass


def _get_isotopes(element):
    """Get isotopes of given element.

    Args:
        element: String representing element's symbol, e.g. "He".
    Return:
        Returns a list of element's isotopes.
    """
    try:
        isotopes = _isotopes[element]
    except KeyError:
        isotopes = []
    return isotopes


def find_mass_of_isotope(element):
    """
    Find the mass of the Element object (isotope).
    Args:
         element: Element object.
    Return:
         Returns the mass of the wanted element.
    """
    isotopes = _get_isotopes(element.symbol)
    element_isotope = int(round(element.isotope))
    for isotope in isotopes:
        if element_isotope == isotope[0]:
            return isotope[2]/1000000


def load_isotopes(element, combobox, current_isotope=None, show_std_mass=False):
    """Load isotopes into given combobox.

    Args:
        element: A two letter symbol representing selected element of which
            isotopes are loaded, e.g. 'He'.
        combobox: QComboBox to which items are added.
        current_isotope: Current isotope to select it on combobox by default.
        show_std_mass: if True, std mass is shown for the most common isotope
    """
    # TODO this function could be moved to gui_utils
    if not element:
        return
    combobox.clear()
    # Sort isotopes based on their natural abundance
    isotopes = sorted(_get_isotopes(element),
                      key=lambda i: i[1],
                      reverse=True)
    for idx, (isotope, tn, mass) in enumerate(isotopes):
        # We don't need rare isotopes to be shown
        if float(tn) > 0.0:
            if idx == 0 and show_std_mass:
                st_iso = get_standard_isotope(element)
                stmass = f" (st. mass {round(st_iso, 3)})"
            else:
                stmass = ""
            combobox.addItem(f"{isotope} ({round(float(tn), 3)}%){stmass}",
                             userData=(isotope, tn))
            if isotope == current_isotope:
                combobox.setCurrentIndex(idx)

    combobox.setEnabled(combobox.count() > 0)


def get_standard_isotope(element):
    """Calculate standard element weight.
    Args:
        element: A two letter symbol representing an element, e.g. 'He'
    Return:
        Returns standard weight of given element (float).
    """
    standard = 0.0
    for isotope in _get_isotopes(element):
        # Has to have float() on both, else we crash.
        standard += float(isotope[0]) * float(isotope[1])
    return standard / 100.0


def get_most_common_isotope(element):
    """Get the most common isotope for an element.

    Args:
        element: String representing element.

    Return:
        Returns the most common isotope for the element (int)
        and the probability (commonness) of the isotope (float)
        as a tuple(int, float).
    """
    isotopes = sorted(_get_isotopes(element),
                      key=lambda isotope: isotope[1],
                      reverse=True)
    return int(isotopes[0][0]), float(isotopes[0][1])
