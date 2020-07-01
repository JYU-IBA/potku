# coding=utf-8
"""
Created on 26.06.2020

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
import tests.gui

from PyQt5.QtWidgets import QWidget
from unittest.mock import Mock
from widgets.matplotlib.measurement.depth_profile import \
    MatplotlibDepthProfileWidget
from modules.selection import Selector


class TestDepthProfile(unittest.TestCase):
    def test_initialization(self):
        parent = QWidget()
        parent.measurement = mo.get_measurement()
        parent.measurement.selector = Selector(
            parent.measurement, mo.get_global_settings().get_default_colors())
        parent.icon_manager = Mock()
        depth_dir, all_elems, _ = mo.get_sample_depth_files_and_elements()
        w = MatplotlibDepthProfileWidget(
            parent, depth_dir, all_elems, {})

        w.close()


if __name__ == '__main__':
    unittest.main()
