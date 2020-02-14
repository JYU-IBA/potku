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

from modules.point import Point


class TestPoint(unittest.TestCase):
    def test_eq(self):
        self.assertEqual(Point((0, 0)), Point((0, 0)))
        self.assertEqual(Point((1, 0)), Point((1, 0)))
        self.assertEqual(Point((0, 1)), Point((0, 1)))
        self.assertNotEqual(Point((1, 0)), Point((0, 0)))
        self.assertNotEqual(Point((0, 0)), Point((1, 1)))
        self.assertNotEqual(Point((1, 0)), Point((0, 1)))

    def test_lt(self):
        self.assertLess(Point((0, 0)), Point((1, 0)))
        self.assertLess(Point((0, 2)), Point((1, 0)))

        self.assertRaises(
            TypeError,
            lambda: Point((0, 2)) < (1, 2))

        self.assertRaises(
            TypeError,
            lambda: (1, 2) < Point((0, 2)))

    def test_str(self):
        self.assertEqual("1 4.0", str(Point((1, 4.0))))
        self.assertEqual("1.23 4.5624", str(Point((1.2332236, 4.562389))))


if __name__ == '__main__':
    unittest.main()