# coding=utf-8
"""
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
"""

__author__ = "Juhani Sundell"
__version__ = "2.0"

import unittest
import os
import platform
import tempfile
import modules.comparison as comp
import random
import tests.utils as utils

from pathlib import Path

from modules import general_functions as gf
from modules.element import Element

_DIR_PATH = Path(
    utils.get_sample_data_dir(), "Ecaart-11-mini", "Tof-E_65-mini", "cuts"
)

_FILE_PATHS = (
    Path(_DIR_PATH, "Tof-E_65-mini.1H.0.cut"),
    Path(_DIR_PATH, "Tof-E_65-mini.1H.1.cut")
)


class TestMatchingFunctions(unittest.TestCase):
    def test_match_strs_to_elements(self):
        strs = ["Si", "10C", "C", "12"]
        elements = [
            Element.from_string("Si"),
            Element.from_string("10C"),
            Element.from_string("12C")
        ]
        matches = comp.match_strs_to_elements(strs, elements)

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
        matches = comp.match_elements_to_strs(elements, strs)
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

        self.assertEqual(comp.find_match_in_dicts(1, dicts), 2)
        self.assertIsNone(comp.find_match_in_dicts(2, dicts))
        self.assertEqual(comp.find_match_in_dicts(3, dicts), 4)
        self.assertEqual(comp.find_match_in_dicts(5, dicts), 6)
        self.assertEqual(comp.find_match_in_dicts(7, dicts), 8)
        self.assertIsNone(comp.find_match_in_dicts(9, dicts))

    def test_empty_and_bad_values(self):
        # Testing with empty lists and dicts
        self.assertIsNone(comp.find_match_in_dicts(1, []))
        self.assertIsNone(comp.find_match_in_dicts(None, [{}]))

        # Testing invalid values
        self.assertRaises(
            TypeError, lambda: comp.find_match_in_dicts(1, [[1]]))
        self.assertRaises(
            TypeError, lambda: comp.find_match_in_dicts(1, [set(1, 2)]))
        self.assertRaises(
            TypeError, lambda: comp.find_match_in_dicts([], [{[]: []}]))


class TestGeneralFunctions(unittest.TestCase):

    def test_file_line_counting(self):
        """Tests for counting lines in two files that are in the sample_data
        directory.
        """
        self.assertEqual(23, gf.count_lines_in_file(_FILE_PATHS[0]))
        self.assertEqual(20, gf.count_lines_in_file(_FILE_PATHS[1]))

    def test_nonexisting_files(self):
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

        # Test what happens, when file path points to a folder
        if platform.system() == "Windows":
            self.assertRaises(
                PermissionError,
                lambda: gf.count_lines_in_file(utils.get_sample_data_dir()))
        else:
            self.assertRaises(
                IsADirectoryError,
                lambda: gf.count_lines_in_file(utils.get_sample_data_dir()))

    def test_tmp_files(self):
        # Test with an empty file
        # Create a temporary directory to store a temporary file
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create an empty file by opening and closing it immediately
            tmp_file = Path(tmp_dir, "testfile")
            open(tmp_file, "a").close()

            # Assert that line count is 0
            self.assertEqual(0, gf.count_lines_in_file(tmp_file))

            # Write a newline
            with open(tmp_file, "a") as file:
                file.write("foo")

            self.assertEqual(1, gf.count_lines_in_file(tmp_file))

            with open(tmp_file, "a") as file:
                file.write("\nbar")

            self.assertEqual(2, gf.count_lines_in_file(tmp_file))

        # Final checks that the temporary file and directory were removed
        self.assertFalse(tmp_file.exists(),
                         msg="Temporary file {0} was not removed after "
                             "the test".format(tmp_file))
        self.assertFalse(os.path.exists(tmp_dir),
                         msg="Temporary directory {0} was not removed "
                             "after the test".format(tmp_dir))

        # TODO test opening file in another process and then trying to count it

    def test_rounding(self):
        self.assertEqual(1000, gf.round_value_by_four_biggest(1000))
        self.assertEqual(12340, gf.round_value_by_four_biggest(12345))
        self.assertEqual(123500, gf.round_value_by_four_biggest(123456))
        self.assertEqual(77780, gf.round_value_by_four_biggest(77777))


class TestHistogramming(unittest.TestCase):
    def test_hist(self):
        data = [
            (0, 2),
            (1, 2),
            (1.5, 2),
            (2, 2),
            (3, 2),
            (5, 2)
        ]
        expected = [
            (-1, 0.0),
            (1.0, 3.0),
            (3.0, 2.0),
            (5.0, 1.0)
        ]
        self.assertEqual(expected, gf.hist(data, col=0, width=2))

        expected2 = [(x, 2 * y) for x, y in expected]
        self.assertEqual(expected2, gf.hist(data, col=0, weight_col=1, width=2))

    def test_bad_inputs(self):
        self.assertEqual([], gf.hist([]))
        self.assertRaises(IndexError, lambda: gf.hist([[1]], col=1))

    def test_hist_properties(self):
        """hist function should have following properties:
            - the sum of values on the y axis should equal the sum of values
              in the y_col if y_col is defined
            - the sum of values on the y axis should equal the number of rows
              in data if y_col is undefined
            - the distance between each bin should equal width parameter
        """
        n = 10
        max_count = 1000
        max_cols = 10
        value_range = (-100, 100)

        for _ in range(n):
            data_count = random.randint(0, max_count)
            col_count = random.randint(1, max_cols)
            x_col = random.randint(0, col_count - 1)
            y_col = random.choice([None, random.randint(0, col_count - 1)])
            bin_width = random.uniform(0, 2)
            data = [
                tuple(random.uniform(*value_range) for _ in range(col_count))
                for _ in range(data_count)
            ]
            res = gf.hist(data, col=x_col, weight_col=y_col, width=bin_width)

            if y_col is None:
                expected_sum = data_count
            else:
                expected_sum = sum(row[y_col] for row in data)

            self.assertAlmostEqual(
                expected_sum, sum(y for x, y in res), places=5)

            pairwise_iter = zip(res, res[1:])
            self.assertTrue(
                x2 - x1 == bin_width for (_, x1), (_, x2) in pairwise_iter
            )


class TestBinDir(unittest.TestCase):
    def test_get_bin_dir(self):
        # get_bin_dir should always return the same absolute Path
        # regardless of current working directory
        cur_dir = os.getcwd()
        try:
            d1 = gf.get_bin_dir()

            self.assertTrue(d1.is_absolute())
            self.assertEqual("bin", d1.name)

            os.chdir(tempfile.gettempdir())

            d2 = gf.get_bin_dir()

            self.assertEqual(d1, d2)
            self.assertNotEqual(cur_dir, os.getcwd())
        finally:
            os.chdir(cur_dir)


class TestFileIO(unittest.TestCase):
    def test_remove_files(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            bar_file = Path(tmp_dir, "foo.bar")
            foo_file = Path(tmp_dir, "bar.foo")
            foo2_file = Path(tmp_dir, "bar.foo2")
            bar_dir = Path(tmp_dir, "x.bar")
            open(bar_file, "a").close()
            open(foo_file, "a").close()
            open(foo2_file, "a").close()
            os.makedirs(bar_dir)

            self.assertTrue(bar_file.exists())
            self.assertTrue(foo_file.exists())
            self.assertTrue(foo2_file.exists())
            self.assertTrue(bar_dir.exists())

            gf.remove_matching_files(tmp_dir, exts={".bar"})

            self.assertFalse(bar_file.exists())
            self.assertTrue(foo_file.exists())
            self.assertTrue(foo2_file.exists())
            self.assertTrue(bar_dir.exists())

            gf.remove_matching_files(tmp_dir, exts={".foo", ".foo2"})

            self.assertFalse(foo_file.exists())
            self.assertFalse(foo2_file.exists())
            self.assertTrue(bar_dir.exists())

    def test_remove_files_no_ext(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            no_ext = Path(tmp_dir, "foo")
            open(no_ext, "a").close()
            self.assertTrue(no_ext.exists())

            self.assertRaises(
                TypeError, lambda: gf.remove_matching_files(tmp_dir))
            gf.remove_matching_files(tmp_dir, exts=[])

            self.assertTrue(no_ext.exists())

            gf.remove_matching_files(tmp_dir, exts=[""])
            self.assertFalse(no_ext.exists())

    def test_file_name_conditions(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            bar_file = Path(tmp_dir, "foo.bar")
            bar2_file = Path(tmp_dir, "bar.bar")
            foo_file = Path(tmp_dir, "bar.foo")
            foo2_file = Path(tmp_dir, "bar2.foo")

            open(bar_file, "a").close()
            open(bar2_file, "a").close()
            open(foo_file, "a").close()
            open(foo2_file, "a").close()

            self.assertTrue(bar_file.exists())
            self.assertTrue(bar2_file.exists())
            self.assertTrue(foo_file.exists())
            self.assertTrue(foo2_file.exists())

            gf.remove_matching_files(
                tmp_dir, exts={".bar"},
                filter_func=lambda f: f.startswith("bar."))

            self.assertTrue(bar_file.exists())
            self.assertFalse(bar2_file.exists())
            self.assertTrue(foo_file.exists())
            self.assertTrue(foo2_file.exists())

            gf.remove_matching_files(
                tmp_dir, filter_func=lambda f: f.startswith("bar."))

            self.assertTrue(bar_file.exists())
            self.assertFalse(foo_file.exists())
            self.assertTrue(foo2_file.exists())

    def test_remove_files_with_bad_inputs(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Nonexistent directories cause no changes
            path = Path(tmp_dir, "foo.bar")
            self.assertFalse(path.exists())
            gf.remove_matching_files(path, exts={".bar"})
            self.assertFalse(path.exists())

            # Neither if the directory is actually a file
            open(path, "a").close()
            self.assertTrue(path.is_file())
            gf.remove_matching_files(path, exts={".bar"})
            self.assertTrue(path.is_file())

    def test_find_files_by_extension(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            files = ["a.foo", "b.foo", "c.fooo", "d.foo.fo", "e", "d.bar"]
            paths = [Path(tmp_dir, f) for f in files]
            for p in paths:
                p.open("w").close()

            self.assertEqual({
                ".foo": [Path(tmp_dir, "a.foo"), Path(tmp_dir, "b.foo")]
            }, sorted_values(gf.find_files_by_extension(Path(tmp_dir), ".foo")))

            self.assertEqual({
                ".foo": [Path(tmp_dir, "a.foo"), Path(tmp_dir, "b.foo")],
                ".bar": [Path(tmp_dir, "d.bar")],
                ".zip": []
            }, sorted_values(gf.find_files_by_extension(
                Path(tmp_dir), ".foo", ".bar", ".zip")))

            self.assertEqual({}, gf.find_files_by_extension(Path(tmp_dir)))

        self.assertRaises(
            OSError, lambda: gf.find_files_by_extension(Path(tmp_dir)))


class TestStringMethods(unittest.TestCase):
    def test_lower_first(self):
        self.assertEqual("", gf.lower_case_first(""))
        self.assertEqual("aA", gf.lower_case_first("AA"))
        self.assertEqual("aa", gf.lower_case_first("Aa"))
        self.assertEqual("a ", gf.lower_case_first("A "))
        self.assertEqual(" A", gf.lower_case_first(" A"))
        self.assertEqual("?A", gf.lower_case_first("?A"))


def sorted_values(dictionary):
    """Helper function for sorting values in a dictionary.
    """
    return {
        k: sorted(v) for k, v in dictionary.items()
    }
