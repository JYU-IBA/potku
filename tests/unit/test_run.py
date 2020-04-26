# coding=utf-8
"""
Created on 05.04.2020

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
__version__ = "2.0"

import unittest
import tempfile
import random

from pathlib import Path

from modules.run import Run


class TestRun(unittest.TestCase):
    def test_settings_parameters(self):
        run = Run()
        self.assertEqual(
            ["fluence", "current", "charge", "time"],
            list(run.get_setting_parameters().keys())
        )

    def test_serialization(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            run1 = Run(fluence=random.random(), current=random.random(),
                       run_time=random.randint(0, 100), charge=random.random())
            mesu_path = Path(tmp_dir, "mesu")

            run1.to_file(mesu_path)

            run2 = Run.from_file(mesu_path)
            self.assertIsNot(run1, run2)
            self.assertEqual(
                get_run_and_beam_vars(run1),
                get_run_and_beam_vars(run2)
            )


def get_run_and_beam_vars(run):
    run_vars = vars(run)
    beam_vars = vars(run_vars.pop("beam"))
    return run_vars, beam_vars


if __name__ == '__main__':
    unittest.main()
