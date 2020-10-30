# coding=utf-8
"""
Created on 05.04.2020

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
from modules.element import Element

__author__ = "Juhani Sundell"
__version__ = "2.0"

import unittest
import random
import tempfile

import tests.mock_objects as mo

from pathlib import Path

from modules.target import Target


class TestTarget(unittest.TestCase):
    def test_serialization(self):
        t = Target(name="foo", modification_time=random.randint(0, 100),
                   description="bar", target_type="AFM",
                   image_size=(random.randint(0, 99), random.randint(0, 99)),
                   image_file="test", target_theta=random.random(),
                   scattering_element=mo.get_element(randomize=True),
                   layers=[mo.get_layer()])

        with tempfile.TemporaryDirectory() as tmp_dir:
            tgt_file = Path(tmp_dir, ".target")
            t.to_file(tgt_file)

            t2 = Target.from_file(tgt_file, mo.get_request())
            self.assertIsNot(t, t2)
            self.assertEqual(t.name, t2.name)
            self.assertEqual(t.description, t2.description)
            self.assertEqual(t.layers[0].elements, t2.layers[0].elements)
            self.assertEqual(t.image_size, t2.image_size)
            self.assertEqual(t.target_theta, t2.target_theta)
            self.assertEqual(t.target_type, t2.target_type)
            self.assertEqual(t.scattering_element, t2.scattering_element)

    def test_adjustable_settings(self):
        target = mo.get_target()
        kwargs = {
            "name": "test",
            "description": "Some description.",
            "modification_time": 1601838503.492942,
            "target_type": "AFM",
            "scattering_element": Element("H", 2),
            "image_size": [
                1024,
                1024
            ],
            "image_file": "",
            "layers": [],
            "target_theta": 30
        }
        self.assertNotEqual(kwargs, target.get_settings())
        target.set_settings(**kwargs)
        self.assertEqual(kwargs, target.get_settings())


if __name__ == '__main__':
    unittest.main()
