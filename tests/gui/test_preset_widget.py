# coding=utf-8
"""
Created on 28.06.2020

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
import tests.gui
import tempfile
import random

from unittest.mock import patch
from pathlib import Path

from widgets.preset_widget import PresetWidget

from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest


class TestPresetWidget(unittest.TestCase):
    def setUp(self) -> None:
        pass

    def test_load_files(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir = Path(tmp_dir)
            widget = PresetWidget(tmp_dir, "foo", enable_load_btn=True)
            widget.preset_combobox: QComboBox

            # Initially, the widget is empty
            self.assertIsNone(widget.preset)
            self.assertEqual(0, widget.preset_combobox.count())

            p1 = tmp_dir / f"abc.preset"
            p2 = tmp_dir / f"foo.preset"
            p3 = tmp_dir / f"foo.txt"

            for p in (p1, p2, p3):
                p.open("w").close()

            # Only .preset files should be shown in the combobox
            widget.load_files()
            self.assertTrue(widget.preset == p1 or widget.preset == p2)
            self.assertEqual(2, widget.preset_combobox.count())

        # After folder is removed, combobox will be empty after loading
        self.assertFalse(tmp_dir.exists())
        widget.load_files()
        self.assertIsNone(widget.preset)
        self.assertEqual(0, widget.preset_combobox.count())

    def test_get_next_file_name(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir = Path(tmp_dir)
            widget = PresetWidget(tmp_dir, "foo")
            widget.preset_combobox: QComboBox

            p1 = widget.get_next_available_file()
            self.assertEqual(tmp_dir / "foo-001.preset", p1)

            p1.open("w").close()
            p2 = widget.get_next_available_file()
            self.assertEqual(tmp_dir / "foo-002.preset", p2)

            p3 = widget.get_next_available_file()
            self.assertEqual(p2, p3)

            self.assertIsNone(widget.get_next_available_file(max_iterations=1))

        self.assertFalse(tmp_dir.exists())
        widget.load_files()
        self.assertEqual(p1, widget.get_next_available_file())

    def test_max_count(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir = Path(tmp_dir)
            widget = PresetWidget(tmp_dir, "foo")
            widget.preset_combobox: QComboBox
            n = 10
            iterations = 10

            for _ in range(n):
                widget.get_next_available_file().open("w").close()

            for _ in range(iterations):
                max_count = random.randint(-10, n + 10)
                if max_count < 0:
                    expected = 0
                elif max_count > n:
                    expected = n
                else:
                    expected = max_count
                widget.load_files(max_count=max_count)
                # When load button is not enabled, add +1 to the count for
                # 'None' option
                self.assertEqual(expected + 1, widget.preset_combobox.count())

    # @patch("PyQt5.QWidgets.QMessageBox.question",
    # return_value=QMessageBox.Yes)
    def test_load_file_signal(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir = Path(tmp_dir)
            widget = PresetWidget(tmp_dir, "foo", enable_load_btn=True)
            widget.load_btn: QPushButton

            files_returned = []

            def add_file(fp):
                files_returned.append(fp)

            widget.load_file.connect(add_file)

            widget.load_btn.click()
            self.assertEqual([], files_returned)

            p = widget.get_next_available_file()
            p.open("w").close()
            widget.load_files()

            widget.load_btn.click()
            self.assertEqual([p], files_returned)

    def test_save_file_signal(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir = Path(tmp_dir)
            widget = PresetWidget(tmp_dir, "foo")
            widget.save_btn: QPushButton

            next_file = widget.get_next_available_file()
            files_returned = []

            def add_file(fp):
                files_returned.append(fp)

            widget.save_file.connect(add_file)
            widget.save_btn.click()
            self.assertEqual([next_file], files_returned)

            widget.save_btn.click()
            self.assertEqual([next_file, next_file], files_returned)


if __name__ == '__main__':
    unittest.main()
