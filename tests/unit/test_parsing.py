# coding=utf-8
"""
Created on 15.1.2020
Updated on 27.1.2020

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
__version__ = ""    # TODO

import unittest
import tempfile
import os

from modules.parsing import CSVParser


class TestParsing(unittest.TestCase):
    def test_parse_strs(self):
        """Tests for parsing multiple strings"""
        parser = CSVParser()
        self.assertEqual((), tuple(parser.parse_strs([])))
        parser = CSVParser((0, str))
        self.assertEqual((("foo", "bar"),),
                         tuple(parser.parse_strs(["foo", "bar"])))

        # Strings can be parsed column wise or row wise
        strs = ["r11 r12", "r21 r22"]
        parser = CSVParser((0, str), (1, str))
        self.assertEqual((("r11", "r21"), ("r12", "r22")),
                         tuple(parser.parse_strs(strs, method="col")))

        self.assertEqual((("r11", "r12"), ("r21", "r22")),
                         tuple(parser.parse_strs(strs, method="row")))

        # Strings can be skipped
        self.assertEqual((("r21", "r22"),),
                         tuple(parser.parse_strs(strs, method="row",
                                                 skip=1)))

        # Negative value causes no change
        self.assertEqual((("r11", "r12"), ("r21", "r22")),
                         tuple(parser.parse_strs(strs, method="row",
                                                 skip=-100)))

        # Empty collection is returned if skip value is more than the length
        # of the data
        self.assertEqual((),
                         tuple(parser.parse_strs(strs, method="row",
                                                 skip=100)))

    def test_parse_str(self):
        """Tests for parsing single string"""
        # If no conversion functions are provided, result will be an
        # empty tuple
        parser = CSVParser()
        self.assertEqual((), parser.parse_str(""))
        self.assertEqual((), parser.parse_str("1"))
        self.assertEqual((), parser.parse_str("1 2"))

        # Parse first column as int
        parser = CSVParser((0, int))
        self.assertEqual((0,), parser.parse_str("0"))
        self.assertEqual((15,), parser.parse_str("15 42"))
        self.assertEqual((-99,), parser.parse_str("-99 99 0"))

        # Parse first column as int and third as float
        parser = CSVParser((0, int), (2, float))
        self.assertEqual((0, 3.14), parser.parse_str("0 1 3.14"))
        self.assertEqual((15, 22.0), parser.parse_str("15 42 22"))
        self.assertEqual((-99, 0.0), parser.parse_str("-99 99 0"))

        # Negative indexes works too
        parser = CSVParser((-1, int))
        self.assertEqual((4,), parser.parse_str("1 2 3 4"))

        # Trickier conversion (by default, white space is removed)
        parser = CSVParser((0, lambda x: x if x == "foo" else "bar"),
                           (1, str))
        self.assertEqual(
            ("bar", "bar"),
            parser.parse_str("   baz        \r\n  \t  \n       bar    ")
        )
        self.assertEqual(
            ("foo", "bar"),
            parser.parse_str("   foo        \r\n  \t  \n       bar    ")
        )

        # Caller can also set a custom separator
        parser = CSVParser((0, str), (1, str))
        self.assertEqual(
            (" foo", "baz "),
            parser.parse_str(" foobarbaz ", separator="bar")
        )

        # Same column can be parsed multiple times
        parser = CSVParser((0, str), (0, int), (0, lambda x: bool(int(x))))
        self.assertEqual(
            ("0", 0, False),
            parser.parse_str("0")
        )

    def test_bad_inputs(self):
        """Testing parsing with some nasty inputs."""
        # Indexes must be integers and converters callables
        self.assertRaises(TypeError,
                          lambda: CSVParser((1.5, int)))
        self.assertRaises(TypeError,
                          lambda: CSVParser((1, 2)))

        # If index is outside the column range or value cannot be converted
        # with given function, exception is raised
        parser = CSVParser((1, int))
        self.assertRaises(IndexError,
                          lambda: parser.parse_str("foo"))
        self.assertRaises(ValueError,
                          lambda: parser.parse_str("foo bar"))

        # TypeError is raised when argument list is too long or too
        # short
        self.assertRaises(TypeError,
                          lambda: CSVParser((1, int, "hello")))
        self.assertRaises(TypeError,
                          lambda: CSVParser((1,)))

        # Note that converter functions are not validated so arbitrary
        # code execution can happen.
        # Here the value 'foo' in the last column is changed to 'bar'
        # by passing the value lst[1]='bar' to exec function.
        parser = CSVParser((0, exec), (1, str))
        self.assertEqual((None, "bar"),
                         parser.parse_str("lst[1]='bar' foo"))

    def test_file_parsing(self):
        """Tests parsing a tmp file"""
        parser = CSVParser((0, int), (1, int))
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = os.path.join(tmp_dir, "csvtest")
            with open(file_path, "w") as file:
                file.write("0 3\n")
                file.write("1 4\n")
                file.write("2 5\n")

            # Parse columns
            self.assertEqual(
                [(0, 1, 2), (3, 4, 5)],
                list(parser.parse_file(file_path, method="col")))

            # Skip first line
            self.assertEqual(
                [(1, 2), (4, 5)],
                list(parser.parse_file(file_path, skip=1,
                                       method="col")))

            # Parse rows
            self.assertEqual(
                [(0, 3), (1, 4), (2, 5)],
                list(parser.parse_file(file_path, method="row")))

            # Skip 2
            self.assertEqual(
                [(2, 5)],
                list(parser.parse_file(file_path, skip=2,
                                       method="row")))

            # If the generators are established, but not iterated
            # before file is removed, FileNotFoundError is raised
            gen1 = parser.parse_file(file_path, method="col")
            gen2 = parser.parse_file(file_path, method="row")

        self.assertRaises(FileNotFoundError, lambda: list(gen1))
        self.assertRaises(FileNotFoundError, lambda: list(gen2))

        self.assertFalse(os.path.exists(tmp_dir),
                         msg="Temporary directory was not removed.")

    def test_skip_empty(self):
        """Tests skipping empty strings."""
        parser = CSVParser((0, int), (1, int), (2, int))
        strs = ["1 2 3", "", "4 5 6"]

        self.assertEqual(((1, 4), (2, 5), (3, 6)),
                         tuple(parser.parse_strs(strs,
                                                 skip_empty=True,
                                                 method="col")))

        self.assertEqual(((1, 2, 3), (4, 5, 6)),
                         tuple(parser.parse_strs(strs,
                                                 skip_empty=True,
                                                 method="row")))

        # If the string contains only whitespace chars, it is not considered
        # empty
        strs = ["1 2 3", " ", "4 5 6"]

        self.assertRaises(IndexError,
                          lambda: tuple(parser.parse_strs(strs,
                                                          skip_empty=True,
                                                          method="col")))


if __name__ == "__main__":
    unittest.main()
