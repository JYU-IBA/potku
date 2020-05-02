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
import rx
import itertools

import modules.mcerd as mcerd


class TestParseOutput(unittest.TestCase):
    def test_calculated_amounts(self):
        s1 = "Calculated 0 of 0 ions (0%)"
        s2 = "Calculated 9595 of 10100 ions (5%)"
        s3 = "Calculated 0 of n ions (50%)"
        s4 = "Calculated -10 of -1000 ions (10%)"

        self.assertEqual({
            "calculated": 0,
            "total": 0,
            "percentage": 0
        }, mcerd.parse_raw_output(s1))

        self.assertEqual({
            "calculated": 9595,
            "total": 10100,
            "percentage": 5
        }, mcerd.parse_raw_output(s2))

        self.assertEqual({
            "msg": "Calculated 0 of n ions (50%)"
        }, mcerd.parse_raw_output(s3))

        self.assertEqual({
            "msg": "Calculated -10 of -1000 ions (10%)"
        }, mcerd.parse_raw_output(s4))

    def test_others(self):
        s1 = "Presimulation finished"
        s2 = "Energy would change too much in virtual detector"
        s3 = "Energy would change too much in virtual detector     -1.582 MeV"

        self.assertEqual({
            "calculated": 0,
            "percentage": 0,
            "msg": "Presimulation finished"
        }, mcerd.parse_raw_output(s1))

        self.assertEqual({
            "msg": "Energy would change too much in virtual detector"
        }, mcerd.parse_raw_output(s2))

        self.assertEqual({
            "msg": "Energy would change too much in virtual detector     "
                   "-1.582 MeV",
        }, mcerd.parse_raw_output(s3))

    def test_pipeline(self):
        output = [
            b"Calculated 0 of 100 ions (0%)",
            b"Calculated 100 of 100 ions (100%)",
            b"Presimulation finished",
            b"Energy would change too much in virtual detector",
            b"Calculated 50 of 100 ions (50%)",
            b"Beam ion: Z=17, M=34.969",
            b"Atom:   5 6.0000 12.000000",
            b"angave 25.6119865",
            b"bar"
        ]

        class Observer:
            def __init__(self):
                self.nexts = []
                self.errs = []
                self.compl_called = False

            def on_next(self, x):
                self.nexts.append(x)

            def on_error(self, x):
                self.errs.append(x)

            def on_completed(self):
                self.compl_called = True

        obs = Observer()
        rx.from_iterable(iter(output)).pipe(
            mcerd.MCERD.get_pipeline(100, "foo")
        ).subscribe(obs)

        self.assertEqual(len(output) - 1, len(obs.nexts))
        self.assertTrue(all(
            x.keys() == y.keys() for x, y in itertools.combinations(
                obs.nexts, 2)
        ))
        self.assertEqual([], obs.errs)
        self.assertTrue(obs.compl_called)

        self.assertEqual({
            "presim": True,
            "calculated": 100,
            "total": 100,
            "percentage": 100,
            "seed": 100,
            "name": "foo",
            "msg": ""
        }, obs.nexts[1])

        self.assertEqual({
            "presim": False,
            "msg": "Presimulation finished",
            "seed": 100,
            "name": "foo",
            "calculated": 0,
            "percentage": 0,
            "total": 100
        }, obs.nexts[2])

        self.assertEqual({
            "presim": False,
            "msg": "angave 25.6119865",
            "seed": 100,
            "name": "foo",
            "percentage": 100,
            "calculated": 50,
            "total": 100
        }, obs.nexts[-1])


if __name__ == '__main__':
    unittest.main()
