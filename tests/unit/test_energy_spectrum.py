# coding=utf-8
"""
Created on 04.10.2020

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
import tests.utils as utils
import tempfile
import os
import numpy as np

from pathlib import Path

from modules.energy_spectrum import EnergySpectrum
from modules.parsing import ToFListParser

parser = ToFListParser()


class TestCalculateMeasuredSpectra(unittest.TestCase):
    def test_calculation_returns_expected_values_when_ch_equals_02(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir = Path(tmp_dir)
            mesu = mo.get_measurement(
                path=tmp_dir / "mesu.info", save_on_creation=True)
            es = self.run_spectra_calculation(
                mesu, tmp_dir, spectrum_width=0.2)
            self.assertEqual(self.expected_02, es)

    def test_calculation_returns_expected_values_when_ch_equals_05(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir = Path(tmp_dir)
            mesu = mo.get_measurement(
                path=tmp_dir / "mesu.info", save_on_creation=True)
            es = self.run_spectra_calculation(
                mesu, tmp_dir, spectrum_width=0.5)
            self.assertEqual(self.expected_05, es)

    def test_spectra_files_are_created(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir = Path(tmp_dir)
            mesu = mo.get_measurement(
                path=tmp_dir / "mesu.info", save_on_creation=True)
            self.run_spectra_calculation(
                mesu, tmp_dir, spectrum_width=0.5)

            expected = sorted([
                *self.expected_hist_files, *self.expected_tof_list_files
            ])
            spectra_files = sorted(os.listdir(mesu.get_energy_spectra_dir()))
            self.assertEqual(expected, spectra_files)

    def test_tof_list_file_contents_are_expected(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir = Path(tmp_dir)
            mesu = mo.get_measurement(
                path=tmp_dir / "mesu.info", save_on_creation=True)
            self.run_spectra_calculation(
                mesu, tmp_dir, spectrum_width=0.5)

            tof_file = mesu.get_energy_spectra_dir() / "cuts.1H.ERD.0.tof_list"

            expected = list(
                parser.parse_strs(
                    self.expected_1h_0_tof_list_content, method=parser.COLUMN)
            )
            actual = list(
                parser.parse_file(tof_file, method=parser.COLUMN)
            )

            # energy spectrum must match with certain precision
            np.testing.assert_almost_equal(actual[2], expected[2], decimal=3)

            # other values must match exactly
            self.assertEqual(
                expected[:1] + expected[3:],
                actual[:1] + actual[3:]
            )

    @staticmethod
    def run_spectra_calculation(mesu, tmp_dir: Path, **kwargs):
        """Helper for running spectra calculations"""
        det = mesu.get_detector_or_default()
        det.update_directories(tmp_dir / "Detector")
        resource_dir = utils.get_resource_dir()
        cuts = [
            resource_dir / "cuts.1H.ERD.0.cut",
            resource_dir / "cuts.1H.ERD.1.cut",
            resource_dir / "cuts.35Cl.RBS_Mn.0.cut",
            resource_dir / "cuts.7Li.0.0.0.cut",
        ]
        es = EnergySpectrum.calculate_measured_spectra(
            mesu, cuts, **kwargs, verbose=False
        )
        return es

    @property
    def expected_02(self):
        return {
            "1H.ERD.0": [
                (0.10000000000000003, 0),
                (0.30000000000000004, 0.0),
                (0.5000000000000001, 10.0),
                (0.7000000000000002, 0),
            ],
            "1H.ERD.1": [
                (-0.30000000000000004, 0),
                (-0.1, 0.0),
                (0.1, 1.0),
                (0.30000000000000004, 2.0),
                (0.5000000000000001, 5.0),
                (0.7000000000000002, 0),
            ],
            "35Cl.RBS_Mn.0": [
                (2.5, 0),
                (2.7, 0.0),
                (2.9000000000000004, 3.0),
                (3.1000000000000005, 5.0),
                (3.3000000000000007, 0.0),
                (3.500000000000001, 1.0),
                (3.700000000000001, 0),
            ],
            "7Li.0.0.0": [
                (1.5, 0),
                (1.7, 0.0),
                (1.9, 2.0),
                (2.1, 8.0),
                (2.3000000000000003, 0),
            ]
        }

    @property
    def expected_05(self):
        return {
            "1H.ERD.0": [
                (-0.25, 0),
                (0.25, 0.0),
                (0.75, 10.0),
                (1.25, 0),
            ],
            "1H.ERD.1": [
                (-0.75, 0),
                (-0.25, 0.0),
                (0.25, 7.0),
                (0.75, 1.0),
                (1.25, 0),
            ],
            "35Cl.RBS_Mn.0": [
                (1.75, 0),
                (2.25, 0.0),
                (2.75, 3.0),
                (3.25, 6.0),
                (3.75, 0),
            ],
            "7Li.0.0.0": [
                (0.75, 0),
                (1.25, 0.0),
                (1.75, 2.0),
                (2.25, 8.0),
                (2.75, 0),
            ]
        }

    @property
    def expected_tof_list_files(self):
        return [
            "cuts.1H.ERD.0.tof_list",
            "cuts.1H.ERD.1.tof_list",
            "cuts.35Cl.RBS_Mn.0.tof_list",
            "cuts.7Li.0.0.0.tof_list",
        ]

    @property
    def expected_hist_files(self):
        return [
            "Default.1H.ERD.0.hist",
            "Default.1H.ERD.1.hist",
            "Default.35Cl.RBS_Mn.0.hist",
            "Default.7Li.0.0.0.hist",
        ]

    @property
    def expected_1h_0_tof_list_content(self):
        return [
            '0.0 0.0 0.53703 1 1.0078 ERD 1.0 764\n',
            '0.0 0.0 0.54982 1 1.0078 ERD 1.0 3688\n',
            '0.0 0.0 0.55655 1 1.0078 ERD 1.0 7581\n',
            '0.0 0.0 0.54644 1 1.0078 ERD 1.0 18325\n',
            '0.0 0.0 0.53343 1 1.0078 ERD 1.0 28211\n',
            '0.0 0.0 0.55838 1 1.0078 ERD 1.0 41176\n',
            '0.0 0.0 0.5287 1 1.0078 ERD 1.0 53683\n',
            '0.0 0.0 0.53113 1 1.0078 ERD 1.0 57440\n',
            '0.0 0.0 0.53419 1 1.0078 ERD 1.0 109997\n',
            '0.0 0.0 0.5434 1 1.0078 ERD 1.0 113722\n'
        ]


class TestGetTofListFileName(unittest.TestCase):
    def test_when_no_foil_is_false(self):
        directory = Path("tmp", "espes")
        cut_file = Path("tmp", "cuts", "cuts.1H.ERD.0.cut")
        no_foil = False
        self.assertEqual(
            directory / "cuts.1H.ERD.0.tof_list",
            EnergySpectrum.get_tof_list_file_name(directory, cut_file, no_foil)
        )

    def test_when_no_foil_is_true(self):
        directory = Path("tmp", "espes")
        cut_file = Path("tmp", "cuts", "cuts.1H.ERD.0.cut")
        no_foil = True
        self.assertEqual(
            directory / "cuts.1H.ERD.0.no_foil.tof_list",
            EnergySpectrum.get_tof_list_file_name(directory, cut_file, no_foil)
        )


if __name__ == '__main__':
    unittest.main()
