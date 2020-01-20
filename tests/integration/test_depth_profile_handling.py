# coding=utf-8
"""
Created on 19.1.2020

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2013-2020 TODO

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
__version__ = ""  # TODO

import unittest
import os

from modules.depth_files import DepthProfileHandler
from modules.element import Element
from tests.utils import verify_files, get_sample_data_dir

# These tests require reading files from the sample data directory
# Path to the depth file directory
_DIR_PATH = os.path.join(get_sample_data_dir(),
                         "Ecaart-11-mini",
                         "Tof-E_65-mini",
                         "depthfiles")

# List of depth files to be read from the directory
_FILE_NAMES = [
    "depth.C",
    "depth.F",
    "depth.H",
    "depth.Li",
    "depth.Mn",
    "depth.O",
    "depth.Si",
    "depth.total"
]

# Expected checksum for all files
# Checksum is valid as of 19.1.2020
# If depths files are modified or removed, these tests will be skipped
_CHECKSUM = b'\xa7OH\x9d`G]N\xf3ic\xa0\x93\xf1\t\xd1'

# Combined absolute file paths
_file_paths = [os.path.join(_DIR_PATH, fname) for fname in _FILE_NAMES]


class TestDepthProfileHandling(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.all_elements = [
            Element.from_string("C"),
            Element.from_string("F"),
            Element.from_string("H"),
            Element.from_string("Li"),
            Element.from_string("Mn"),
            Element.from_string("O"),
            Element.from_string("Si")
        ]
        cls.some_elements = [
            Element.from_string("F"),
            Element.from_string("H"),
            Element.from_string("Mn"),
            Element.from_string("Si")
        ]

    @verify_files(_file_paths, _CHECKSUM,
                  msg="testing file reading with DepthProfileHandler")
    def test_file_reading(self):
        """Tests that the files can be read and all given elements are
        stored in the profile handler"""
        handler = DepthProfileHandler()
        handler.read_directory(_DIR_PATH, self.all_elements)
        self.check_handler_profiles(handler, self.all_elements)

        # Read just some of the elements. This should remove existing
        # profiles from the handler
        handler.read_directory(_DIR_PATH, self.some_elements)
        self.check_handler_profiles(handler, self.some_elements)

    def check_handler_profiles(self, handler, elements):
        """Checks that handler contains all the expected element
        profiles"""
        # Check that the handler contains absolute profiles
        # of all elements
        abs_profiles = handler.get_absolute_profiles()
        for elem in elements:
            self.assertIn(str(elem), abs_profiles)

        self.assertIn("total", abs_profiles)
        self.assertEqual(len(abs_profiles), len(elements) + 1)

        # Relative profiles also contain all elements
        rel_profiles = handler.get_relative_profiles()
        for elem in elements:
            self.assertIn(str(elem), rel_profiles)

        # But it does not contain total profile
        self.assertNotIn("total", rel_profiles)
        self.assertEqual(len(rel_profiles), len(elements))


if __name__ == "__main__":
    unittest.main()