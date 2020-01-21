# coding=utf-8
"""
Created on 15.1.2020
Updated on 21.1.2020

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2013-2020 TODO

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

import unittest

from modules import parsing


class TestFileParsing(unittest.TestCase):
    def test_parse_strs(self):
        """Tests for parsing multiple strings"""
        self.assertEqual((), parsing.parse_strs([], [], []))
        self.assertEqual((["foo"],), parsing.parse_strs(["foo"], [0], [str]))

        self.assertEqual((["foo"], ["bar"]),
                         parsing.parse_strs(["foo bar"], [0, 1], [str, str]))
        self.assertEqual((["foo", "foo"], ["bar", "baz"]),
                         parsing.parse_strs(["foo bar", "foo  baz"],
                                            [0, 1],
                                            [str, str]))

    def test_parse_str(self):
        """Tests for parsing single string"""
        self.assertEqual((), parsing.parse_str("", [], []))
        self.assertEqual((), parsing.parse_str("foo", [], []))
        self.assertEqual(("foo",), parsing.parse_str("foo", [0], [str]))

        # Conversion test
        self.assertEqual(("bar",), parsing.parse_str(
            "foo", [0], [lambda x: "bar" if x == "foo" else x]))

        # By default, parse_str will split strings into a list of
        # non-whitespace characters
        self.assertEqual(
            (1, 2, 4.5, "foo"),
            parsing.parse_str("    1 \n  2   3 4.5   foo  ",
                              [0, 1, 3, 4],
                              [int, int, float, str])
        )

        # Caller can also define a custom separator
        self.assertEqual(
            (1, 2, 4.5, "foo"),
            parsing.parse_str("1,2,3,4.5,foo,",
                              [0, 1, 3, 4],
                              [int, int, float, str],
                              separator=",")
        )

        # Same column can be parsed multiple times
        self.assertEqual((1, "1", True),
                         parsing.parse_str("1", [0, 0, 0], [int, str, bool]))

    def test_bad_inputs(self):
        # Column index must be within the column range and number of indexes
        # must match the number of converters
        self.assertRaises(IndexError,
                          lambda: parsing.parse_str("foo", [1], [str]))
        self.assertRaises(ValueError,
                          lambda: parsing.parse_str("foo", [0], []))
        # If converter is not callable, TypeError is raised
        self.assertRaises(
            TypeError, lambda: parsing.parse_str("foo", [0], ["bar"]))
        # If string cannot be parsed with the converter, ValueError is raised
        self.assertRaises(
            ValueError, lambda: parsing.parse_str("0 foo", [0], [int, int]))

        # Note that converter functions are not validated so arbitrary
        # code execution can happen.
        # Here the value 'foo' in the last column is changed to 'bar'
        # by passing the first column to the converter function.
        parsed_columns = parsing.parse_str("lst[1]='bar' foo",
                                           [0, 1],
                                           [exec, str])
        self.assertEqual((None, "bar"), parsed_columns)


if __name__ == "__main__":
    unittest.main()
