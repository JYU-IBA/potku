# coding=utf-8
"""
Created on 22.06.2020

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
import tests.utils as utils

from unittest.mock import patch
from unittest.mock import Mock
from widgets.icon_manager import IconManager
from widgets.simulation.target import TargetWidget

from PyQt5.QtWidgets import QWidget


class TestTargetWidget(unittest.TestCase):
    def test_initialization(self):
        tab = Mock()
        sim = mo.get_simulation()
        target = mo.get_target()
        icons = IconManager()
        settings = mo.get_global_settings()

        widget = TargetWidget(
            tab, sim, target, icons, settings, auto_save=False)
        rec_dist = widget.recoil_distribution_widget

        self.assertFalse(rec_dist.main_recoil_selected())
        self.assertIsNone(rec_dist.get_current_main_recoil())

        widget.close()


if __name__ == '__main__':
    unittest.main()
