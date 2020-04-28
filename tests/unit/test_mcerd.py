# coding=utf-8
"""
Created on 27.04.2020

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

import modules.mcerd as mcerd


class TestParseOutput(unittest.TestCase):
    def test_calculated_amounts(self):
        s1 = b"Calculated 0 of 0 ions (0%)"
        s2 = b"Calculated 9595 of 10100 ions (95%)"
        s3 = b"Calculated 0 of n ions (50%)"
        s4 = b"Calculated -10 of -1000 ions (10%)"

        self.assertEqual({
            "calculated": 0,
            "total": 0
        }, mcerd.parse_raw_output(s1))

        self.assertEqual({
            "calculated": 9595,
            "total": 10100
        }, mcerd.parse_raw_output(s2))

        self.assertEqual({
            "msg": "Calculated 0 of n ions (50%)"
        }, mcerd.parse_raw_output(s3))

        self.assertEqual({
            "msg": "Calculated -10 of -1000 ions (10%)"
        }, mcerd.parse_raw_output(s4))

    def test_others(self):
        s1 = b"Presimulation finished"
        s2 = b"Energy would change too much in virtual detector"
        s3 = b"Energy would change too much in virtual detector     -1.582 MeV"

        self.assertEqual({
            "msg": "Presimulation finished"
        }, mcerd.parse_raw_output(s1))

        self.assertEqual({
            "msg": "Energy would change too much in virtual detector"
        }, mcerd.parse_raw_output(s2))

        self.assertEqual({
            "msg": "Energy would change too much in virtual detector     "
                   "-1.582 MeV",
        }, mcerd.parse_raw_output(s3))


if __name__ == '__main__':
    unittest.main()
