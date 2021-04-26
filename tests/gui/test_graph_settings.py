# coding=utf-8
"""
Created on 25.04.2021

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2021 Juhani Sundell

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

import tests.gui

from modules.enums import AxisRangeMode, ToFEColorScheme

from dialogs.graph_settings import TofeGraphSettingsWidget


class TestTofeGraphSettingsWidget(unittest.TestCase):
    def test_default_values(self):
        self.widget = TofeGraphSettingsWidget()
        self.assertEqual(AxisRangeMode.AUTOMATIC, self.widget.axis_range_mode)
        self.assertEqual(ToFEColorScheme.DEFAULT, self.widget.color_scheme)
        self.assertEqual((0, 8000), self.widget.x_range)
        self.assertEqual((0, 8000), self.widget.y_range)


if __name__ == '__main__':
    unittest.main()
