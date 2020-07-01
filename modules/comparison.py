# coding=utf-8
"""
Created on 29.1.2020

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2020 Juhani Sundell

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

Comparison module contains various helper functions for comparing
and matching different objects
"""

__author__ = "Juhani Sundell"
__version__ = "2.0"


def match_strs_to_elements(strs, elements, match_by_symbol=True):
    """Matches strings to a collection of elements and yields a tuple that
    contains the string and its matching element for each given string.

    Args:
        strs: iterable of strings to be matched
        elements: iterable of elements that the strings will be matched to
        match_by_symbol: if this is True and string is not prefixed with an
                         isotope value, string can be matched to an element that
                         does have an isotope

    Yield:
        tuple that contains the string and either element or None depending
        on whether a match was found
    """
    full = dict((str(elem), elem) for elem in elements)
    if match_by_symbol:
        just_symbols = dict((element.symbol, element) for element in elements)
        search_dicts = [
            full, just_symbols
        ]
    else:
        search_dicts = [full]

    for s in strs:
        yield s, find_match_in_dicts(s, search_dicts)


def match_elements_to_strs(elements, strs, match_by_symbol=True):
    """Matches elements to string.

    Args:
        elements: collection of elements
        strs: collection of strings
        match_by_symbol: bool. If False, function only tries to find
                         matching isotope.

    Yield:
        tuple that contains the element and either a string or None
        depending on whether a match was found or not.
    """
    str_dict = [{s: s for s in strs}]
    for elem in elements:
        res = find_match_in_dicts(str(elem), str_dict)
        if not res and match_by_symbol:
            res = find_match_in_dicts(elem.symbol, str_dict)
        yield elem, res


def find_match_in_dicts(search_value, search_dicts):
    """Tries to find a key in search_dicts that matches the
    search_value. If match is found, returns the key-value pair
    from the dict.

    If multiple dictionaries contain the search_value, only the
    first match is returned.

    Args:
        search_value: value to be searched
        search_dicts: collection of dict
    Return:
        key-value pair as a tuple. Value is None if no match was
        found.
    """
    for sd in search_dicts:
        if not isinstance(sd, dict):
            raise TypeError("Expected dictionary")
        if search_value in sd:
            return sd[search_value]
    return None
