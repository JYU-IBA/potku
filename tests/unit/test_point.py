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
import random
import modules.math_functions as mf

from modules.point import Point


class TestPoint(unittest.TestCase):
    def test_eq(self):
        # Point(x, y) should be equal to Point((x, y))
        self.assertEqual(Point((0, 0)), Point(0, 0))
        self.assertEqual(Point((1, 0)), Point(1, 0))
        self.assertEqual(Point((0, 1)), Point(0, 1))
        self.assertNotEqual(Point((1, 0)), Point(0, 0))
        self.assertNotEqual(Point((0, 0)), Point(1, 1))
        self.assertNotEqual(Point((1, 0)), Point(0, 1))

    def test_get_item(self):
        p = Point(1, 2)
        self.assertEqual(1, p[0])
        self.assertEqual(1, p["x"])
        self.assertEqual(2, p[1])
        self.assertEqual(2, p["y"])

        self.assertRaises(ValueError, lambda: p[-1])
        self.assertRaises(ValueError, lambda: p[2])
        self.assertRaises(ValueError, lambda: p["z"])

    def test_get_in_range(self):
        # Due to being iterable, Point objects can be used in the
        # get_elements_in_range function of the math_functions module.
        points = [
            Point(0, 3),
            Point(1, 4),
            Point(2, 5)
        ]

        in_range = mf.get_elements_in_range(points, a=0.5, b=1.5,
                                            include_before=False,
                                            include_after=False)
        self.assertEqual([Point(1, 4)],
                         [Point(x, y) for x, y in in_range])

    def test_lt(self):
        self.assertLess(Point((0, 0)), Point((1, 0)))
        self.assertLess(Point((0, 2)), Point((1, 0)))

        self.assertRaises(TypeError, lambda: Point((0, 2)) < (1, 2))
        self.assertRaises(TypeError, lambda: (1, 2) < Point((0, 2)))

    def test_str(self):
        self.assertEqual("1 4.0", str(Point((1, 4.0))))
        self.assertEqual("1.23 4.5624", str(Point((1.2332236, 4.562389))))

    def test_calculate_new_point(self):
        p1 = Point(0, 1)
        p2 = Point(1, 2)

        self.assertEqual(Point(0.5, 1.5), p1.calculate_new_point(p2, 0.5))
        self.assertEqual(Point(2, 3), p1.calculate_new_point(p2, 2))
        self.assertEqual(Point(-1, 0), p1.calculate_new_point(p2, -1))

        def rand():
            return random.uniform(-100, 100)

        for i in range(100):
            x = rand()
            p1 = Point((rand(), rand()))
            p2 = Point((rand(), rand()))

            # To avoid dealing with floating point precision while testing,
            # turn the points into strings.
            self.assertEqual(str(p1.calculate_new_point(p2, x)),
                             str(p2.calculate_new_point(p1, x)))


if __name__ == '__main__':
    unittest.main()
