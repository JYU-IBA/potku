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
from unittest.mock import Mock
import tempfile
from pathlib import Path

import tests.gui
import tests.mock_objects as mo

from modules.measurement import Measurement
from modules.selection import Selector
from widgets.measurement.tofe_histogram import TofeHistogramWidget
from widgets.icon_manager import IconManager


def set_up_selector(measurement: Measurement):
    """Initializes a Selector instance for the given Measurement.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # call create_folder_structure to initialize the selector instance
        # of the measurement
        measurement.create_folder_structure(
            Path(tmpdir), selector_cls=Selector)


class TestWidget(unittest.TestCase):
    def setUp(self) -> None:
        self.measurement = mo.get_measurement()
        set_up_selector(self.measurement)
        tab = Mock()
        icon_manager = IconManager()
        self.widget = TofeHistogramWidget(self.measurement, icon_manager, tab)

    def test_title_is_set(self):
        self.assertEqual(
            f"ToF-E Histogram - Event count: {len(self.measurement.data)}",
            self.widget.windowTitle()
        )

    def test_save_cuts_is_enabled_if_measurement_has_selections(self):
        self.assertEqual(
            bool(self.measurement.selector.selections),
            self.widget.saveCutsButton.isEnabled()
        )


if __name__ == '__main__':
    unittest.main()
