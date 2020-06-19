# coding=utf-8
"""
Created on 19.06.2020

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
import os
import tempfile
import random
import tests.utils as utils
import tests.mock_objects as mo

import modules.cut_file as cut_file

from typing import List
from typing import Any
from pathlib import Path
from modules.cut_file import CutFile
from modules.measurement import Measurement


class TestCutFile(unittest.TestCase):
    def setUp(self):
        self.rel_dir = Path(
            f"{Measurement.DIRECTORY_PREFIX}sample-mesu1", "data", "cuts")
        n = random.randint(1, 10)
        self.data = [[random.randint(0, 10) for _ in range(3)]
                     for _ in range(n)]

    def test_saving(self):
        with tempfile.TemporaryDirectory() as tmd_dir:
            path = Path(tmd_dir, self.rel_dir)

            expected_files = {
                "mesu1.He.RBS_Cl.0.cut": None,
                "mesu1.He.RBS_Cl.1.cut": None,
                "mesu1.1He.RBS_He.0.cut": None,
                "mesu1.He.ERD.0.cut": None,
                "mesu1.He.ERD.1.cut": None,
                "mesu1.He.ERD.10.cut": None,
            }
            self._generate_cut_files(path)
            utils.assert_folder_structure_equal(expected_files, path)

    def test_loading(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir, self.rel_dir)
            cut1 = CutFile(directory=path, split_count=4)
            cut1.set_info(mo.get_selection(), self.data)
            cut1.element = mo.get_element(symbol="F")
            cut1.save()

            fp = path / "mesu1.F.RBS_Cl.0.cut"

            cut2 = CutFile()
            cut2.load_file(fp)
            cut1_d = dict(vars(cut1))
            cut2_d = dict(vars(cut2))

            self.assertIsNone(cut1_d.pop("element_number"))
            self.assertEqual(0, cut2_d.pop("element_number"))

            self.assertTrue(len(cut1_d) > 0)
            self.assertEqual(cut1_d, cut2_d)

    def test_get_rbs_selections(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir, self.rel_dir)
            self._generate_cut_files(path)
            files = [
                Path(entry.path) for entry in os.scandir(path)
            ]
            rbs = cut_file.get_rbs_selections(files)
            self.assertEqual({
                "1He.RBS_He.0.cut": mo.get_element(symbol="He"),
                "He.RBS_Cl.0.cut": mo.get_element(symbol="Cl"),
                "He.RBS_Cl.1.cut": mo.get_element(symbol="Cl"),
            }, rbs)

    def _generate_cut_files(self, directory):
        cut = CutFile(directory=directory)
        cut.set_info(mo.get_selection(), self.data)
        cut.save()
        cut.save()

        cut2 = CutFile(directory=directory)
        cut2.set_info(mo.get_selection(), self.data)
        cut2.element = mo.get_element(symbol="He", isotope=1)
        cut2.element_scatter = mo.get_element()
        cut2.save()

        cut3 = CutFile(directory=directory)
        cut3.set_info(mo.get_selection(), self.data)
        cut3.type = "ERD"
        cut3.element_scatter = ""
        cut3.save()
        cut3.save()
        cut3.save(element_count=10)


if __name__ == '__main__':
    unittest.main()
