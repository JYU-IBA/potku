# coding=utf-8
"""
Created on 06.05.2020

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
__author__ = "Juhani Sundel"
__version__ = "2.0"

import unittest
import tempfile
import shutil

import tests.mock_objects as mo
import tests.gui

from pathlib import Path

from widgets.detector_settings import DetectorSettingsWidget


class TestDetectorSettings(unittest.TestCase):
    DETECTOR_DIR = Path(tempfile.gettempdir(), "potku_detector_test_dir")

    def setUp(self):
        self.detector = mo.get_detector()
        self.request = mo.get_request()
        self.eff_files = [
            "H.eff", "1H.eff", "1H-comment.eff", "2H.eff", "O.efff"]

        self.detector.update_directories(self.DETECTOR_DIR)
        for eff in self.eff_files:
            fp = self.DETECTOR_DIR / eff
            open(fp, "a").close()
            self.detector.add_efficiency_file(fp)

    def tearDown(self):
        self.assertTrue(self.DETECTOR_DIR.exists())
        shutil.rmtree(self.DETECTOR_DIR)
        self.assertFalse(
            self.DETECTOR_DIR.exists(),
            msg=f"Temporary directory {self.DETECTOR_DIR} was not removed.")

    def test_initialization(self):
        """Upon initialization the widget should load the values from the
        Detector object.
        """
        det_widget = DetectorSettingsWidget(
            self.detector, self.request, None, None)
        props = det_widget.get_properties()
        self.assertEqual(
            props.pop("efficiency_files"), self.detector.get_efficiency_files()
        )
        self.assertEqual(
            props, self.detector.get_settings()
        )
