# coding=utf-8
"""
Created on 08.04.2020

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

from modules.layer import Layer
from modules.element import Element


class TestLayer(unittest.TestCase):
    def test_to_dict(self):
        layer = Layer("foo", [Element("He"), Element("C", 4, 2)], 3, 5,
                      start_depth=10)
        self.assertEqual({
            "name": "foo",
            "thickness": 3,
            "density": 5,
            "elements": ["He", "4C 2"],
            "start_depth": 10
        }, layer.to_dict())


if __name__ == '__main__':
    unittest.main()
