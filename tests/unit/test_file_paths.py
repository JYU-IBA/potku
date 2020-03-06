# coding=utf-8
"""
Created on 10.2.2020

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

import modules.file_paths as fp

from modules.recoil_element import RecoilElement
from modules.element import Element
from tests.utils import stopwatch


class TestFilePaths(unittest.TestCase):
    def test_get_erd_file_path(self):
        rec_elem = RecoilElement(Element.from_string("He"), [], "red")

        self.assertEqual("He-Default.101.erd",
                         fp.get_erd_file_name(rec_elem, 101))
        self.assertEqual("He-Default.102.erd",
                         fp.get_erd_file_name(rec_elem, 102))

        self.assertEqual("He-opt.101.erd",
                         fp.get_erd_file_name(rec_elem, 101,
                                              optim_mode="recoil"))

        self.assertEqual("He-optfl.101.erd",
                         fp.get_erd_file_name(rec_elem, 101,
                                              optim_mode="fluence"))

        self.assertRaises(ValueError,
                          lambda: fp.get_erd_file_name(rec_elem, 101,
                                                       optim_mode="foo"))

    def test_recoil_filter(self):
        filter_func = fp.recoil_filter("C")

        self.assertTrue(filter_func("C.rec"))
        self.assertTrue(filter_func("C.optfl.rec"))
        self.assertTrue(filter_func("C.sct"))
        self.assertFalse(filter_func("Cu.sct"))
        self.assertFalse(filter_func("Cu.rec"))

        # Testing with some irregular inputs
        self.assertTrue(filter_func("C..rec"))
        self.assertFalse(filter_func("C!rec"))
        self.assertFalse(filter_func("C.re"))
        self.assertFalse(filter_func("c.rec"))
        self.assertFalse(filter_func("C4rec"))
        self.assertFalse(filter_func("Crec"))

        # Testing the other way around
        filter_func = fp.recoil_filter("Cu")

        self.assertTrue(filter_func("Cu.rec"))
        self.assertTrue(filter_func("Cu.sct"))
        self.assertFalse(filter_func("C.sct"))
        self.assertFalse(filter_func("C.rec"))

    def test_is_optfl_res(self):
        self.assertTrue(fp.is_optfl_result("C", "C-optfl.result"))
        self.assertFalse(fp.is_optfl_result("C", "Cu-optfl.result"))

        self.assertTrue(fp.is_optfl_result("Cu", "Cu-optfl.result"))
        self.assertFalse(fp.is_optfl_result("Cu", "C-optfl.result"))

        self.assertTrue(fp.is_optfl_result("Cu", "Cu.foo-optfl.result"))
        self.assertFalse(fp.is_optfl_result("Cu", "Cu.optfl.result"))


if __name__ == '__main__':
    unittest.main()
