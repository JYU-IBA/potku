# coding=utf-8
"""
Created on TODO
Updated on 23.1.2020

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2020 TODO

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

__author__ = "Juhani Sundell"
__version__ = ""  # TODO

import unittest
import os
import platform

from modules import general_functions as gf
from modules.element import Element
from tests.utils import get_sample_data_dir, verify_files

_DIR_PATH = os.path.join(get_sample_data_dir(),
                         "Ecaart-11-mini",
                         "Tof-E_65-mini",
                         "cuts")
_FILE_PATHS = [
    os.path.join(_DIR_PATH, "Tof-E_65-mini.1H.0.cut"),
    os.path.join(_DIR_PATH, "Tof-E_65-mini.1H.1.cut")
]

_os = platform.system()
if _os == "Windows":
    _CHECKSUM = "cc2089d41ad55f206b941fe83d079add"
elif _os == "Linux" or _os == "Darwin":
    _CHECKSUM = "6bbf2f7faf8a708046d8d038c4ea8e97"
else:
    _CHECKSUM = None


class TestMatchingFunctions(unittest.TestCase):
    def test_match_strs_to_elements(self):
        strs = ["Si", "10C", "C", "12"]
        elements = [
            Element.from_string("Si"),
            Element.from_string("10C"),
            Element.from_string("12C")
        ]
        matches = gf.match_strs_to_elements(strs, elements)

        self.assertEqual(
            ("Si", Element.from_string("Si")),
            next(matches))
        self.assertEqual(
            ("10C", Element.from_string("10C")),
            next(matches))
        self.assertEqual(
            ("C", Element.from_string("12C")),
            next(matches))
        self.assertEqual(
            ("12", None),
            next(matches))

    def test_match_elements_to_strs(self):
        strs = ["Si", "10C", "C", "12"]
        elements = [
            Element.from_string("Si"),
            Element.from_string("10C"),
            Element.from_string("12C"),
            Element.from_string("Br")
        ]
        matches = gf.match_elements_to_strs(elements, strs)
        self.assertEqual(next(matches),
                         (Element.from_string("Si"), "Si"))
        self.assertEqual(next(matches),
                         (Element.from_string("10C"), "10C"))
        self.assertEqual(next(matches),
                         (Element.from_string("12C"), "C"))
        self.assertEqual(next(matches),
                         (Element.from_string("Br"), None))

        # Matches has been exhausted and this will produce an
        # exception
        self.assertRaises(StopIteration, lambda: next(matches))

    def test_find_match_in_dicts(self):
        dicts = [{
            1: 2,
            3: 4,
            5: 6
        }, {
            1: 11,      # these values wont be found because
            3: 12,      # the dict has the same keys as the
            5: 13       # first dict
        }, {
            7: 8,
            9: None
        }]

        self.assertEqual(gf.find_match_in_dicts(1, dicts), 2)
        self.assertIsNone(gf.find_match_in_dicts(2, dicts))
        self.assertEqual(gf.find_match_in_dicts(3, dicts), 4)
        self.assertEqual(gf.find_match_in_dicts(5, dicts), 6)
        self.assertEqual(gf.find_match_in_dicts(7, dicts), 8)
        self.assertIsNone(gf.find_match_in_dicts(9, dicts))

        # Testing with empty lists and dicts
        self.assertIsNone(gf.find_match_in_dicts(1, []))
        self.assertIsNone(gf.find_match_in_dicts(None, [{}]))

        # Testing invalid values
        self.assertRaises(
            TypeError, lambda: gf.find_match_in_dicts(1, [[1]]))
        self.assertRaises(
            TypeError, lambda: gf.find_match_in_dicts(1, [set(1, 2)]))
        self.assertRaises(
            TypeError, lambda: gf.find_match_in_dicts([], [{[]: []}]))


class TestGeneralFunctions(unittest.TestCase):

    @verify_files(_FILE_PATHS, _CHECKSUM,
                  msg="testing counting lines in a file")
    def test_file_line_counting(self):
        """Tests for counting lines in a file"""
        self.assertEqual(23, gf.count_lines_in_file(_FILE_PATHS[0]))
        self.assertEqual(20, gf.count_lines_in_file(_FILE_PATHS[1]))

        self.assertRaises(
            FileNotFoundError,
            lambda: gf.count_lines_in_file("this file does not exist"))
        self.assertRaises(
            FileNotFoundError,
            lambda: gf.count_lines_in_file("this file does not exist",
                                           check_file_exists=False))
        self.assertEqual(
            0,
            gf.count_lines_in_file("this file does not exist",
                                   check_file_exists=True))

        if _os == "Windows":
            self.assertRaises(
                PermissionError,
                lambda: gf.count_lines_in_file(get_sample_data_dir()))
        else:
            self.assertRaises(
                IsADirectoryError,
                lambda: gf.count_lines_in_file(get_sample_data_dir()))

        # Uncomment this to test with an empty file, assuming that __init__.py
        # stays empty. Note that this can only be run from a directory that
        # contains an __init__.py
        # self.assertEqual(0, gf.count_lines_in_file("__init__.py"))

        # TODO test opening file in another process and then trying to count it
        # TODO proper test with an empty file


if __name__ == "__main__":
    unittest.main()
