# coding=utf-8
"""
Created on 13.02.2020

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
from modules.enums import DefaultReferenceDensity

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
            reference_density=DefaultReferenceDensity.PROFILE_REFERENCE_DENSITY,
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
        self.assertEqual(12, self.rec_elem.calculate_area())
        self.assertEqual(4.5, self.rec_elem.calculate_area(
            start=0, end=1))

        self.assertEqual(0, self.rec_elem.calculate_area(
            start=0.5, end=0.5))
        self.assertEqual(2.25, self.rec_elem.calculate_area(
            start=0.25, end=0.75))

        self.assertEqual(5.5, self.rec_elem.calculate_area(
            start=0.5, end=1.5))

        # If the interval is outside the point range, 0 is returned
        self.assertEqual(0, self.rec_elem.calculate_area(
            start=2, end=3))
        self.assertEqual(0, self.rec_elem.calculate_area(
            start=-2, end=0))

        # If the length of the interval is non-positive, 0 is returned
        self.assertEqual(0, self.rec_elem.calculate_area(
            start=1, end=1))
        self.assertEqual(0, self.rec_elem.calculate_area(
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

    def test_identities(self):
        rec_elem1 = mo.get_recoil_element()
        rec_elem2 = mo.get_recoil_element()

        self.assertNotEqual(rec_elem1, rec_elem2)
        self.assertEqual(rec_elem1, rec_elem1)

        self.assertIs(rec_elem2, rec_elem2)


class TestPoints(unittest.TestCase):
    def setUp(self):
        self.p2_args = 1, 1
        self.p1 = Point(0, 0)
        self.p2 = Point(self.p2_args)
        self.p3 = Point(2, 0)

        points = [
            self.p1, self.p2, self.p3
        ]
        self.rec_elem = RecoilElement(mo.get_element(), points)

    def test_sorting_points(self):
        """Points should always remain sorted.
        """
        n = 10
        iters = 10
        maximum = 20
        minimum = 0
        rand = lambda: random.uniform(minimum, maximum)
        for _ in range(iters):
            points = [
                Point(rand(), rand())
                for _ in range(n)
            ]
            points_sorted = sorted(points)

            rec_elem = RecoilElement(
                mo.get_element(), points)

            self.assertEqual(points_sorted, rec_elem.get_points())

            p_0 = Point(minimum - 1, rand())
            p_n = Point(maximum + 1, rand())
            rec_elem.add_point(p_0)
            rec_elem.add_point(p_n)

            self.assertIs(p_0, rec_elem.get_first_point())
            self.assertIs(p_n, rec_elem.get_last_point())

    def test_remove_point(self):
        self.rec_elem.remove_point(self.p1)
        self.assertEqual([self.p2, self.p3], self.rec_elem.get_points())

        self.rec_elem.remove_point(self.p3)
        self.assertEqual([self.p2], self.rec_elem.get_points())

        self.rec_elem.remove_point(Point(self.p2_args))
        self.assertEqual([], self.rec_elem.get_points())

        self.assertRaises(
            ValueError, lambda: self.rec_elem.remove_point(self.p1))

    def test_get_neighbours(self):
        ln, rn = self.rec_elem.get_neighbors(self.p1)
        self.assertIsNone(ln)
        self.assertIs(rn, self.p2)

        ln, rn = self.rec_elem.get_neighbors(self.p2)
        self.assertIs(ln, self.p1)
        self.assertIs(rn, self.p3)

        ln, rn = self.rec_elem.get_neighbors(self.p3)
        self.assertIs(ln, self.p2)
        self.assertIsNone(rn)

        ln, rn = self.rec_elem.get_neighbors(Point(1, 1))
        self.assertIs(ln, self.p1)
        self.assertIs(rn, self.p3)

    def test_between_zeros(self):
        self.assertFalse(self.rec_elem.between_zeros(self.p1))
        self.assertTrue(self.rec_elem.between_zeros(self.p2))
        self.assertFalse(self.rec_elem.between_zeros(self.p3))

        self.assertTrue(self.rec_elem.between_zeros(Point(1, 1)))
        self.assertRaises(
            ValueError, lambda: self.rec_elem.between_zeros(Point(0.5, 1)))

    def test_dist_length(self):
        self.assertEqual(2, self.rec_elem.distribution_length())
        self.rec_elem.add_point(Point(10.5, 0))
        self.assertEqual(10.5, self.rec_elem.distribution_length())
        for p in list(self.rec_elem.get_points()):
            self.rec_elem.remove_point(p)

        self.assertRaises(IndexError, self.rec_elem.distribution_length)


if __name__ == '__main__':
    unittest.main()
