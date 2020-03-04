# coding=utf-8
"""
Created on 04.03.2020

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

from graphs.base_graphs import LineChart


class TestLineChart(unittest.TestCase):
    def test_init(self):
        lc = LineChart()
        self.assertEqual(75, lc.figure.dpi)
        self.assertEqual("white", lc.figure.patch._original_facecolor)

        self.assertIsNotNone(lc.axes)
        self.assertIsNotNone(lc.canvas)

        lc = LineChart(dpi=100, facecolor="green")
        self.assertEqual(100, lc.figure.dpi)
        self.assertEqual("green", lc.figure.patch._original_facecolor)

    def test_update_graph(self):
        lc = LineChart()
        x = [0, 1, 2]
        y = [3, 4, 5]

        # Update with one graph element
        lc.update_graph([
            {
                "line_id": "foo",
                "x": x,
                "y": y
            }
        ])

        self.assertEqual(["foo"], list(lc.lines.keys()))
        self.assertEqual(x, list(lc.lines["foo"].get_xdata()))
        self.assertEqual(y, list(lc.lines["foo"].get_ydata()))

        # Update with two graph elements
        lc.update_graph([
            {
                "line_id": "foo",
                "x": x,
                "y": [z + 1 for z in y]
            },
            {
                "line_id": "bar",
                "x": x,
                "y": y
            }
        ])
        self.assertNotEqual(y, list(lc.lines["foo"].get_ydata()))

        self.assertEqual(["foo", "bar"], list(lc.lines.keys()))
        self.assertEqual(x, list(lc.lines["bar"].get_xdata()))
        self.assertEqual(y, list(lc.lines["bar"].get_ydata()))


if __name__ == '__main__':
    unittest.main()
