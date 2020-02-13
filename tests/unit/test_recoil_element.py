# coding=utf-8
"""
Created on 13.02.2020

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
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program (file named 'LICENCE').
"""
__author__ = "Juhani Sundell"
__version__ = ""  # TODO

import unittest
import tempfile
import time
import os

import tests.mock_objects as mo
import modules.file_paths as fp

from modules.recoil_element import RecoilElement
from modules.point import Point
from modules.element import Element


class TestRecoilElement(unittest.TestCase):
    @classmethod
    def setUp(cls):
        cls.timestamp = time.time()
        cls.rec_type = "rec"
        cls.ch_width = 4
        cls.rec_elem = RecoilElement(
            mo.get_element(),
            [Point((0, 4)),
             Point((1, 5)),
             Point((2, 6))],
            color="black",
            description="foo",
            name="bar",
            rec_type="rec",
            multiplier=2,
            reference_density=3,
            channel_width=cls.ch_width,
            modification_time=cls.timestamp
        )

    def test_get_full_name(self):
        self.assertEqual("He-bar", self.rec_elem.get_full_name())

        rec_elem = RecoilElement(Element.from_string("16O"), [], name=None)
        self.assertEqual("16O-Default", rec_elem.get_full_name())

        rec_elem = RecoilElement(Element.from_string("16O"), [], name="")
        self.assertEqual("16O-Default", rec_elem.get_full_name())

    def test_serialization(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = fp.get_recoil_file_path(self.rec_elem, tmp_dir)
            self.rec_elem.to_file(tmp_dir)

            rec_elem2 = RecoilElement.from_file(file_path,
                                                channel_width=self.ch_width,
                                                rec_type=self.rec_type)

            self.compare_rec_elems(self.rec_elem, rec_elem2)

            rec_elem3 = RecoilElement(Element.from_string("O"), [])
            file_path = fp.get_recoil_file_path(rec_elem3, tmp_dir)
            rec_elem3.to_file(tmp_dir)
            rec_elem4 = RecoilElement.from_file(file_path)

            self.compare_rec_elems(rec_elem3, rec_elem4)
            self.assertEqual([], rec_elem4.get_points())

        self.assertFalse(os.path.exists(tmp_dir))

    def compare_rec_elems(self, rec_elem1, rec_elem2):
        fst = dict(vars(rec_elem1))
        snd = dict(vars(rec_elem2))

        self.assertEqual(fst.pop("_points"), snd.pop("_points"))
        self.assertEqual(fst.pop("element"), snd.pop("element"))
        self.assertNotEqual(fst.pop("modification_time"),
                            snd.pop("modification_time"))
        self.assertEqual(fst, snd)


if __name__ == '__main__':
    unittest.main()