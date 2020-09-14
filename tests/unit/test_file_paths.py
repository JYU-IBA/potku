# coding=utf-8
"""
Created on 10.2.2020

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

import modules.file_paths as fp

import tempfile
from pathlib import Path

from modules.nsgaii import OptimizationType
from modules.recoil_element import RecoilElement
from modules.element import Element


class TestFilePaths(unittest.TestCase):
    def test_get_erd_file_path(self):
        rec_elem = RecoilElement(Element.from_string("He"), [], "red")

        self.assertEqual("He-Default.101.erd",
                         fp.get_erd_file_name(rec_elem, 101))
        self.assertEqual("He-Default.102.erd",
                         fp.get_erd_file_name(rec_elem, 102))

        self.assertEqual(
            "He-opt.101.erd",
            fp.get_erd_file_name(
                rec_elem, 101, optim_mode=OptimizationType.RECOIL))

        self.assertEqual(
            "He-optfl.101.erd",
            fp.get_erd_file_name(
                rec_elem, 101, optim_mode=OptimizationType.FLUENCE))

        self.assertRaises(ValueError,
                          lambda: fp.get_erd_file_name(rec_elem, 101,
                                                       optim_mode="foo"))

    def test_recoil_filter(self):
        filter_func = fp.recoil_filter("C")

        self.assertTrue(filter_func(Path("C.rec")))
        self.assertTrue(filter_func(Path("C.optfl.rec")))
        self.assertTrue(filter_func(Path("C.sct")))
        self.assertFalse(filter_func(Path("Cu.sct")))
        self.assertFalse(filter_func(Path("Cu.rec")))

        # Testing with some irregular inputs
        self.assertTrue(filter_func(Path("C..rec")))
        self.assertFalse(filter_func(Path("C!rec")))
        self.assertFalse(filter_func(Path("C.re")))
        self.assertFalse(filter_func(Path("c.rec")))
        self.assertFalse(filter_func(Path("C4rec")))
        self.assertFalse(filter_func(Path("Crec")))

        # Testing the other way around
        filter_func = fp.recoil_filter("Cu")

        self.assertTrue(filter_func(Path("Cu.rec")))
        self.assertTrue(filter_func(Path("Cu.sct")))
        self.assertFalse(filter_func(Path("C.sct")))
        self.assertFalse(filter_func(Path("C.rec")))

    def test_is_optfl_res(self):
        self.assertTrue(fp.is_optfl_result("C", Path("C-optfl.result")))
        self.assertFalse(fp.is_optfl_result("C", Path("Cu-optfl.result")))

        self.assertTrue(fp.is_optfl_result("Cu", Path("Cu-optfl.result")))
        self.assertFalse(fp.is_optfl_result("Cu", Path("C-optfl.result")))

        self.assertTrue(fp.is_optfl_result("Cu", Path("Cu.foo-optfl.result")))
        self.assertFalse(fp.is_optfl_result("Cu", Path("Cu.optfl.result")))

    def test_assert_raises(self):
        # Function only accept Path objects
        self.assertRaises(
            AttributeError, lambda: fp.is_optfl_result("C", "C-optfl.result"))

        self.assertRaises(
            AttributeError, lambda: fp.is_optfirst("C", "C-optfl.result"))
        self.assertRaises(
            AttributeError, lambda: fp.is_optmed("C", "C-optfl.result"))
        self.assertRaises(
            AttributeError, lambda: fp.is_optfl_result("C", "C-optfl.result"))


class TestFindNextAvailableFilePath(unittest.TestCase):
    def test_with_non_existing_files(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir = Path(tmp_dir)
            file_paths = (tmp_dir / f"foo_{i}.bar" for i in range(10))
            self.assertEqual(
                tmp_dir / "foo_0.bar",
                fp.find_available_file_path(file_paths)
            )

    def test_with_some_existing_files(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir = Path(tmp_dir)
            file_paths = (tmp_dir / f"foo_{i}.bar" for i in range(10))
            (tmp_dir / "foo_0.bar").open("w").close()
            (tmp_dir / "foo_1.bar").open("w").close()
            self.assertEqual(
                tmp_dir / "foo_2.bar",
                fp.find_available_file_path(file_paths)
            )

    def test_all_files_existing_raises_error(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir = Path(tmp_dir)
            file_paths = (tmp_dir / f"foo_{i}.bar" for i in range(10))
            for j in range(10):
                (tmp_dir / f"foo_{j}.bar").open("w").close()
            self.assertRaises(
                ValueError,
                lambda: fp.find_available_file_path(file_paths)
            )

    def test_empty_file_list_raises_error(self):
        self.assertRaises(
            ValueError,
            lambda: fp.find_available_file_path([])
        )

    def test_with_a_folder_instead_of_a_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            paths = [Path(tmp_dir), Path(tmp_dir, "foo")]
            self.assertEqual(
                Path(tmp_dir, "foo"),
                fp.find_available_file_path(paths)
            )


if __name__ == '__main__':
    unittest.main()
