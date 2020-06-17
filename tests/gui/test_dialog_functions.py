# coding=utf-8
"""
Created on 14.02.2020

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
import os
import tempfile
import tests.gui

import dialogs.dialog_functions as df

from tests.utils import ListdirSwitcher

from pathlib import Path


class TestUpdateCuts(unittest.TestCase):
    def setUp(self):
        # UpdateCuts works for both strings and Paths so both need to
        # be tested
        old_prefix = "m1"
        new_prefix = "m2"
        self.directory = Path(tempfile.gettempdir(), "foo.po.tku")

        unprefixed_files = [
            "12C-default.ERD.0.cut",
            "12C.ERD.1.cut",
            "16O.ERD.0.cut",
        ]
        self.old_files = [
            f"{old_prefix}.{f}"
            for f in unprefixed_files
        ]
        self.new_files = [
            f"{new_prefix}.{f}"
            for f in unprefixed_files
        ]
        self.expected_paths = [
            Path(self.directory, f)
            for f in self.new_files
        ]

    def test_update_cuts_with_strs(self):
        # Testing strings
        paths = [
            os.path.join(self.directory, f)
            for f in self.old_files
        ]
        with ListdirSwitcher(self.new_files):
            df._update_cuts(paths, self.directory)
            self.assertEqual(self.expected_paths, paths)

    def test_update_cuts_with_paths(self):
        # Testing Paths
        # Path versions of absolute paths
        paths = [
            Path(self.directory, f)
            for f in self.old_files
        ]
        with ListdirSwitcher(self.new_files):
            df._update_cuts(paths, self.directory)
            self.assertEqual(self.expected_paths, paths)


class TestDeleteConfirmation(unittest.TestCase):
    def test_confirmation_msg(self):
        self.assertIsNone(df._get_confirmation_msg())
        self.assertIsNone(df._get_confirmation_msg(False, False, False, False))

        msg = df._get_confirmation_msg(running_simulations=[1])
        self.assertIsInstance(msg, tuple)
        self.assertEqual("Simulations running", msg.title)

        msg = df._get_confirmation_msg(finished_simulations=True)
        self.assertEqual("Finished simulations", msg.title)

        msg = df._get_confirmation_msg(running_optimizations=True)
        self.assertEqual("Optimization running", msg.title)

        msg = df._get_confirmation_msg(finished_optimizations=True)
        self.assertEqual("Optimization results", msg.title)


if __name__ == '__main__':
    unittest.main()
