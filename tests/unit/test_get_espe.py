# coding=utf-8
"""
Created on 01.06.2020

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
import tests.mock_objects as mo
import tempfile

import modules.general_functions as gf

from modules.get_espe import GetEspe
from pathlib import Path
from tests.utils import PlatformSwitcher


class TestGetEspe(unittest.TestCase):
    def setUp(self):
        det = mo.get_detector()
        self.rec_file = Path(tempfile.gettempdir(), "rec")
        self.erd_file = Path(tempfile.gettempdir(), "erd")
        self.spe_file = Path(tempfile.gettempdir(), "spe")

        self.espe = GetEspe(
            mo.get_beam(), det, mo.get_target(), det.calculate_solid(),
            self.rec_file, self.erd_file, self.spe_file)

    def test_get_command(self):
        with PlatformSwitcher("Windows"):
            cmd = self.espe.get_command()
            self.assertEqual(str(gf.get_bin_dir() / "get_espe.exe"), cmd[0])
            self.assertEqual(str(self.rec_file), cmd[-1])

        with PlatformSwitcher("Darwin"):
            cmd = self.espe.get_command()
            self.assertEqual("./get_espe", cmd[0])


if __name__ == '__main__':
    unittest.main()
