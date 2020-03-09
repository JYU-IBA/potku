# coding=utf-8
"""
Created on 08.03.2020

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
__author__ = ""  # TODO
__version__ = ""  # TODO

import unittest

from modules.nsgaii import pick_final_solutions


class TestNsgaii(unittest.TestCase):
    def test_pick_final_solutions(self):
        front = [
            (4, 4), (3, 1), (2, 2), (1, 3)
        ]

        self.assertEqual(((1, 3), (3, 1)), pick_final_solutions(front))


if __name__ == '__main__':
    unittest.main()