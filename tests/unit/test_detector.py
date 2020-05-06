# coding=utf-8
"""
Created on 8.2.2020

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
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program (file named 'LICENCE').
"""

__author__ = "Juhani Sundell"
__version__ = "2.0"

import unittest
import tempfile
import os

import tests.mock_objects as mo

from pathlib import Path

from modules.detector import Detector
from modules.foil import CircularFoil
from modules.foil import RectangularFoil


class TestBeam(unittest.TestCase):
    def setUp(self):
        self.path = Path(tempfile.gettempdir(), ".detector")
        self.mesu = Path(tempfile.gettempdir(), "mesu")
        self.det = Detector(self.path, self.mesu, save_in_creation=False)
        self.unit_foil = CircularFoil(diameter=1, distance=1, transmission=1)
        self.rect_foil = RectangularFoil(size_x=2, size_y=2, distance=2,
                                         transmission=2)

    def test_get_mcerd_params(self):
        self.assertEqual(
            ["Detector type: TOF",
             "Detector angle: 41",
             "Virtual detector size: 2.0 5.0",
             "Timing detector numbers: 1 2"],
            self.det.get_mcerd_params()
        )

    def test_default_init(self):
        # If no foils are given, detector is initialized with 4 default foils
        self.assertEqual(4, len(self.det.foils))
        self.assertEqual([1, 2], self.det.tof_foils)

    def test_calculate_smallest_solid_angle(self):
        self.assertAlmostEqual(0.1805,
                               self.det.calculate_smallest_solid_angle(),
                               places=3)

        self.det.foils.clear()
        self.assertEqual(0, self.det.calculate_smallest_solid_angle())

        self.det.foils.append(self.unit_foil)
        self.assertAlmostEqual(785.398,
                               self.det.calculate_smallest_solid_angle(),
                               places=3)

    def test_calculate_solid(self):
        self.assertAlmostEqual(0.1805,
                               self.det.calculate_solid(),
                               places=3)

        self.det.foils.clear()
        self.assertEqual(0, self.det.calculate_solid())

        self.det.foils.append(self.unit_foil)
        self.assertAlmostEqual(785.398,
                               self.det.calculate_solid(),
                               places=3)

        self.det.foils.append(self.rect_foil)
        self.assertAlmostEqual(1570.796,
                               self.det.calculate_solid(),
                               places=3)

    def test_serialization(self):
        """Tests that a deserialized detector has the same attribute values
        as the serialized detector did.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            det_file = Path(tmp_dir, "d.detector")
            mesu_file = Path(tmp_dir, "mesu")
            det1 = Detector(det_file, mesu_file,
                            name="foo", description="bar", detector_type="TOF",
                            virtual_size=(1, 2), tof_slope=4.4e-10,
                            tof_offset=2, angle_slope=3, angle_offset=4,
                            timeres=251, detector_theta=42, tof_foils=[0, 0],
                            save_in_creation=False, foils=[self.unit_foil,
                                                           self.rect_foil])
            det1.to_file(det_file, mesu_file)

            det2 = Detector.from_file(det_file, mesu_file, mo.get_request(),
                                      save=False)
            self.assertIsNot(det1, det2)
            self.assertEqual(det1.name, det2.name)
            self.assertEqual(det1.description, det2.description)
            self.assertEqual(det1.type, det2.type)
            self.assertEqual(det1.virtual_size, det2.virtual_size)
            self.assertEqual(det1.tof_slope, det2.tof_slope)
            self.assertEqual(det1.tof_offset, det2.tof_offset)
            self.assertEqual(det1.angle_slope, det2.angle_slope)
            self.assertEqual(det1.angle_offset, det2.angle_offset)
            self.assertEqual(det1.detector_theta, det2.detector_theta)
            self.assertEqual(det1.tof_foils, det2.tof_foils)

            for f1, f2 in zip(det1.foils, det2.foils):
                self.assertEqual(f1.get_mcerd_params(), f2.get_mcerd_params())

    def test_copying_eff_files(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            effs_folder = Path(tmp_dir, Detector.EFFICIENCY_DIR)
            used_folder = effs_folder / Detector.USED_EFFICIENCIES_DIR
            det = Detector(Path(tmp_dir, "t.detector"), Path(tmp_dir, "mesu"))
            det.update_directories(tmp_dir)

            self.assertEqual(used_folder, det.get_used_efficiencies_dir())
            self.assertTrue(effs_folder.exists())
            self.assertFalse(used_folder.exists())

            # Efficiency files and expected efficiency files after copying
            eff_files = {
                "1H.eff": "1H.eff",
                "16O.eff": "16O.eff",
                "4C-foo.eff": "4C.eff",
                "4C_foo.eff": "4C_foo.eff",
                "1H.ef": None,
                "H.eff": "H.eff",
                "eff.eff.eff": "eff.eff.eff",
                "h.eff-foo-.eff": "h.eff-foo-.eff",
                ".eff": ".eff",
            }
            expected = sorted([f for f in eff_files.values() if f is not None])
            for f in eff_files:
                open(effs_folder / f, "a").close()

            det.copy_efficiency_files()
            self.assertTrue(used_folder.exists())
            used_effs = sorted(os.listdir(used_folder))
            self.assertEqual(expected, used_effs)

