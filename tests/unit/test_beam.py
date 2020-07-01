# coding=utf-8
"""
Created on 8.2.2020

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

import tests.mock_objects as mo

from modules.beam import Beam
from modules.element import Element
from modules.enums import Profile


class TestBeam(unittest.TestCase):
    def test_get_mcerd_params(self):
        beam = Beam(ion=Element.from_string("4He"), energy=14)
        self.assertEqual(
            ["Beam ion: 4He",
             "Beam energy: 14 MeV"],
            beam.get_mcerd_params()
        )

    def test_adjustable_settings(self):
        beam = mo.get_beam()
        kwargs = {
            "energy": 1,
            "charge": 2,
            "ion": mo.get_element(randomize=True),
            "energy_distribution": 3,
            "spot_size": (1, 2),
            "profile": "foo",
            "divergence": 7
        }
        self.assertNotEqual(kwargs, beam.get_settings())
        beam.set_settings(**kwargs)
        self.assertEqual(kwargs, beam.get_settings())

    def test_profile(self):
        self.assertEqual(Profile.UNIFORM, Beam().profile)
        self.assertEqual(
            Profile.GAUSSIAN, Beam(profile=Profile.GAUSSIAN).profile)
        self.assertEqual(
            Profile.UNIFORM, Beam(profile="unIfoRm").profile)
        self.assertEqual(
            Profile.GAUSSIAN, Beam(profile="gaUssIan").profile)

        self.assertEqual(
            Profile.UNIFORM, Beam(profile="gaussiann").profile)

        self.assertEqual(
            Profile.UNIFORM, Beam(profile=None).profile)
