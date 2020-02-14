# coding=utf-8
"""
Created on 14.02.2020

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
__author__ = "Juhani Sundell"
__version__ = ""  # TODO

import unittest
import os
import tempfile

import dialogs.dialog_functions as df

from tests.utils import ListdirSwitcher

from pathlib import Path


class TestUpdateCuts(unittest.TestCase):

    @classmethod
    def setUp(cls):
        # UpdateCuts works for both strings and Paths so both need to
        # be tested
        old_prefix = "m1"
        new_prefix = "m2"
        cls.directory = Path(tempfile.gettempdir(), "foo.po.tku")

        unprefixed_files = [
            "12C-default.ERD.0.cut",
            "12C.ERD.1.cut",
            "16O.ERD.0.cut",
        ]
        old_files = [
            f"{old_prefix}.{f}"
            for f in unprefixed_files
        ]
        cls.new_files = [
            f"{new_prefix}.{f}"
            for f in unprefixed_files
        ]
        cls.old_paths = [
            os.path.join(cls.directory, f)
            for f in old_files
        ]
        cls.new_paths = [
            os.path.join(cls.directory, f)
            for f in cls.new_files
        ]

        # Path versions of absolute paths
        cls.old_paths_p = [
            Path(f)
            for f in cls.old_paths
        ]
        cls.new_paths_p = [
            Path(f)
            for f in cls.new_paths
]

    def test_update_cuts_with_strs(self):
        # Testing strings
        with ListdirSwitcher(self.new_files):
            df._update_cuts(self.old_paths, self.directory)
            self.assertEqual(self.new_paths_p, self.old_paths)

    def test_update_cuts_with_paths(self):
        # Testing Paths
        with ListdirSwitcher(self.new_files):
            df._update_cuts(self.old_paths_p, self.directory)
            self.assertEqual(self.new_paths_p, self.old_paths_p)


if __name__ == '__main__':
    unittest.main()
