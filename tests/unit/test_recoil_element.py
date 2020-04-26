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
__version__ = "2.0"

import unittest
import tempfile
import time
import os
import random

import tests.mock_objects as mo
import modules.file_paths as fp

from modules.recoil_element import RecoilElement
from modules.point import Point
from modules.element import Element


class TestRecoilElement(unittest.TestCase):
    def setUp(self):
        self.timestamp = time.time()
        self.rec_type = "rec"
        self.ch_width = 4
        self.rec_elem = RecoilElement(
            mo.get_element(),
            [Point((0, 4)),
             Point((1, 5)),
             Point((2, 10))],
            color="black",
            description="foo",
            name="bar",
            rec_type="rec",
            multiplier=2,
            reference_density=3,
            channel_width=self.ch_width,
            modification_time=self.timestamp
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

            # Test with an empty list of points and no rec_type or ch_width
            rec_elem3 = RecoilElement(Element.from_string("O"), [])
            file_path = fp.get_recoil_file_path(rec_elem3, tmp_dir)
            rec_elem3.to_file(tmp_dir)
            rec_elem4 = RecoilElement.from_file(file_path)

            self.compare_rec_elems(rec_elem3, rec_elem4)

        self.assertFalse(os.path.exists(tmp_dir))

    def compare_rec_elems(self, rec_elem1, rec_elem2):
        fst = dict(vars(rec_elem1))
        snd = dict(vars(rec_elem2))

        self.assertEqual(fst.pop("_points"), snd.pop("_points"))
        self.assertEqual(fst.pop("element"), snd.pop("element"))

        times = fst.pop("modification_time"), snd.pop("modification_time")

        if None not in times:
            self.assertAlmostEqual(times[0], times[1], places=2)

        self.assertEqual(fst, snd)

    def test_calculate_area(self):
        self.assertEqual(12, self.rec_elem.calculate_area_for_interval())
        self.assertEqual(4.5, self.rec_elem.calculate_area_for_interval(
            start=0, end=1))

        self.assertEqual(0, self.rec_elem.calculate_area_for_interval(
            start=0.5, end=0.5))
        self.assertEqual(2.25, self.rec_elem.calculate_area_for_interval(
            start=0.25, end=0.75))

        self.assertEqual(5.5, self.rec_elem.calculate_area_for_interval(
            start=0.5, end=1.5))

        # If the interval is outside the point range, 0 is returned
        self.assertEqual(0, self.rec_elem.calculate_area_for_interval(
            start=2, end=3))
        self.assertEqual(0, self.rec_elem.calculate_area_for_interval(
            start=-2, end=0))

        # If the length of the interval is non-positive, 0 is returned
        self.assertEqual(0, self.rec_elem.calculate_area_for_interval(
            start=1, end=1))
        self.assertEqual(0, self.rec_elem.calculate_area_for_interval(
            start=1, end=0))

    def test_sorting(self):
        # Checks that recoil elements are sorted in the same way as elements
        n = 10
        iterations = 10
        for _ in range(iterations):
            elems = [mo.get_element(randomize=True) for _ in range(n)]
            rec_elems = [RecoilElement(elem, []) for elem in elems]
            random.shuffle(elems)
            random.shuffle(rec_elems)

            elems.sort()
            rec_elems.sort()
            for e, r in zip(elems, rec_elems):
                self.assertEqual(e, r.element)


if __name__ == '__main__':
    unittest.main()
