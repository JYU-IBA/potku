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
import tests.utils as utils
import time

import modules.general_functions as gf

from modules.get_espe import GetEspe
from pathlib import Path
from tests.utils import PlatformSwitcher

resource_dir = utils.get_resource_dir()
_RECOIL_FILE = resource_dir / "C-Default.recoil"
_ERD_FILE = resource_dir / "C-Default.*.erd"
_EXPECTED_SPECTRUM_FILE = resource_dir / "C-Default-expected.simu"

del resource_dir


class TestGetCommand(unittest.TestCase):
    def setUp(self):
        beam = mo.get_beam()
        det = mo.get_detector()
        self.rec_file = Path(tempfile.gettempdir(), "rec")
        self.erd_file = Path(tempfile.gettempdir(), "erd")

        self.espe = GetEspe(
            beam.ion.get_prefix(), beam.energy, det.detector_theta,
            mo.get_target().target_theta, det.calculate_tof_length(),
            det.calculate_solid(), self.rec_file, self.erd_file)

    def test_get_command(self):
        with PlatformSwitcher("Windows"):
            cmd = self.espe.get_command()
            self.assertEqual(str(gf.get_bin_dir() / "get_espe.exe"), cmd[0])
            self.assertEqual(str(self.rec_file), cmd[-1])
            self.assertEqual(24, len(cmd))

        with PlatformSwitcher("Darwin"):
            cmd = self.espe.get_command()
            self.assertEqual("./get_espe", cmd[0])
            self.assertEqual(str(self.rec_file), cmd[-1])
            self.assertEqual(24, len(cmd))


class TestReadEspeFile(unittest.TestCase):
    def test_read_espe_file_returns_expected_data(self):
        spectrum = GetEspe.read_espe_file(_EXPECTED_SPECTRUM_FILE)
        self.assertEqual(96, len(spectrum))
        for fst, snd in zip(spectrum[:-1], spectrum[1:]):
            # x values are in ascending order
            self.assertLess(fst[0], snd[0])

    def test_read_espe_from_non_existing_file_return_empty_list(self):
        spectrum = GetEspe.read_espe_file(Path.cwd() / "foo.bar.baz")
        self.assertEqual([], spectrum)


class TestReadErdData(unittest.TestCase):
    def test_read_erd_data_returns_expected_data(self):
        erd_data = list(GetEspe.read_erd_data(_ERD_FILE))
        self.assertEqual(20, len(erd_data))
        for line in erd_data:
            self.assertIsInstance(line, str)

    def test_read_erd_data_returns_nothing_if_no_erd_files(self):
        erd_data = list(GetEspe.read_erd_data(Path.cwd() / "foo.bar.baz"))
        self.assertEqual([], erd_data)


class TestGetEspeRun(unittest.TestCase):
    def setUp(self):
        self.beam = mo.get_beam()
        self.detector = mo.get_detector()
        self.target = mo.get_target()

        self.default_kwargs = {
            "beam_ion": self.beam.ion.get_prefix(),
            "energy": self.beam.energy,
            "theta": self.detector.detector_theta,
            "toflen": self.detector.calculate_tof_length(),
            "tangle": self.target.target_theta,
            "solid": self.detector.calculate_solid(),
            "recoil_file": _RECOIL_FILE,
            "erd_file": _ERD_FILE,
            "reference_density": 4.98e22,
            "ch": 0.025,
            "fluence": 1.00e+12,
            "timeres": self.detector.timeres,
        }

    def test_get_espe_run_returns_expected_spectrum(self):
        get_espe = GetEspe(**self.default_kwargs)
        res = get_espe.run(verbose=False)
        self.assertEqual(
            GetEspe.read_espe_file(_EXPECTED_SPECTRUM_FILE),
            res
        )

    def test_get_espe_writes_results_to_given_spectrum_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_file = Path(tmp_dir, "C-Default.simu")
            get_espe = GetEspe(**self.default_kwargs)

            get_espe.run(output_file=output_file, verbose=False)
            self.assertEqual(
                GetEspe.read_espe_file(_EXPECTED_SPECTRUM_FILE),
                GetEspe.read_espe_file(output_file)
            )

    def test_shell_injection(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            injected_file = Path(tmp_dir, "foo.bar")
            injected_str = str(injected_file).replace("\\", "/")
            recoil_file = str(_RECOIL_FILE).replace("\\", "/")
            injected_ch = f"0.025 -dist {recoil_file} && touch " \
                          f"{injected_str} &&"
            kwargs = dict(self.default_kwargs)
            kwargs["ch"] = injected_ch
            get_espe = GetEspe(**kwargs)
            get_espe.run(verbose=False)

            time.sleep(0.1)
            self.assertEqual(24, len(get_espe.get_command()))
            self.assertFalse(injected_file.exists())

    def test_calculate_simulated_spectrum(self):
        get_espe = GetEspe(**self.default_kwargs)
        self.assertEqual(
            GetEspe.calculate_simulated_spectrum(
                beam=self.beam, target=self.target, detector=self.detector,
                recoil_file=_RECOIL_FILE, erd_file=_ERD_FILE,
                reference_density=self.default_kwargs["reference_density"],
                verbose=False
            ),
            get_espe.run(verbose=False)
        )


if __name__ == '__main__':
    unittest.main()
