# coding=utf-8
"""
Created on 8.2.2020

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

__author__ = "Juhani Sundell \n Tuomas Pitkänen"
__version__ = "2.0"

import unittest
import tempfile
import os
import shutil

import tests.mock_objects as mo

from pathlib import Path

from modules.detector import Detector
from modules.foil import CircularFoil
from modules.foil import RectangularFoil
from modules.enums import DetectorType


class TestBeam(unittest.TestCase):
    def setUp(self):
        self.path = Path(tempfile.gettempdir(), "Detector", ".detector")
        self.mesu = Path(tempfile.gettempdir(), "mesu")
        self.det = Detector(self.path, save_on_creation=False)
        self.unit_foil = CircularFoil(diameter=1, distance=1, transmission=1)
        self.rect_foil = RectangularFoil(size_x=2, size_y=2, distance=2,
                                         transmission=2)

    def compare_foils(self, foils1, foils2):
        """Helper for comparing foils"""
        self.assertEqual(len(foils1), len(foils2))
        for f1, f2 in zip(foils1, foils2):
            self.assertIsNot(f1, f2)
            self.assertEqual(f1.get_mcerd_params(), f2.get_mcerd_params())
            for l1, l2 in zip(f1.layers, f2.layers):
                self.assertIsNot(l1, l2)
                self.assertEqual(l1.get_mcerd_params(), l2.get_mcerd_params())
                for e1, e2 in zip(l1.elements, l2.elements):
                    self.assertIsNot(e1, e2)
                    self.assertEqual(e1, e2)

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
            det1 = Detector(det_file,
                            name="foo", description="bar",
                            detector_type=DetectorType.TOF,
                            virtual_size=(1, 2), tof_slope=4.4e-10,
                            tof_offset=2, angle_slope=3, angle_offset=4,
                            timeres=251, detector_theta=42, tof_foils=[0, 0],
                            save_on_creation=False, foils=[self.unit_foil,
                                                           self.rect_foil])
            det1.to_file(det_file)

            det2 = Detector.from_file(det_file, mo.get_request(),
                                      save_on_creation=False)
            self.assertIsNot(det1, det2)
            self.assertEqual(det1.name, det2.name)
            self.assertEqual(det1.description, det2.description)
            self.assertEqual(det1.detector_type, det2.detector_type)
            self.assertIsInstance(det2.detector_type, DetectorType)
            self.assertEqual(det1.virtual_size, det2.virtual_size)
            self.assertEqual(det1.tof_slope, det2.tof_slope)
            self.assertEqual(det1.tof_offset, det2.tof_offset)
            self.assertEqual(det1.angle_slope, det2.angle_slope)
            self.assertEqual(det1.angle_offset, det2.angle_offset)
            self.assertEqual(det1.detector_theta, det2.detector_theta)
            self.assertEqual(det1.tof_foils, det2.tof_foils)

            self.compare_foils(det1.foils, det2.foils)

    def test_copy_foils(self):
        """Tests that copied foils have the same attributes as the
        original ones."""
        copied_foils = self.det.copy_foils()
        self.compare_foils(self.det.foils, copied_foils)

    def test_copy_tof_foils(self):
        """Tests that copied ToF foils are the same as the original ones."""
        copied_foils = self.det.copy_tof_foils()
        self.assertEqual(self.det.tof_foils, copied_foils)


class TestEfficiencyFiles(unittest.TestCase):
    """Tests for handling .eff files.
    """
    def setUp(self) -> None:
        self.det = Detector(
            Path(tempfile.gettempdir(), "Detector", ".detector"),
            save_on_creation=False)
        # Efficiency files and expected efficiency files after copying
        self.eff_files = {
            "1H.eff": "1H.eff",
            "16O.eff": "16O.eff",
            "4C-foo.eff": "4C.eff",
            "4C_foo.eff": "4C_foo.eff",
            "42H.eff-bar": None,
            "1H.ef": None,
            "H.eff": "H.eff",
            "eff.eff.eff": "eff.eff.eff",
            "2H.eff-foo.eff": "2H.eff",
            "f.eff-foo-.eff": "f.eff",
            ".eff": None,
            "mn-mn-nm-.eff-.eff": "mn.eff"
        }
        self.filtered_effs = sorted([
            Path(f) for f in self.eff_files
            if f.endswith(".eff") and f != ".eff"
        ])

    def test_get_efficiency_files(self):
        """get_efficiency_files only returns files ending in .eff even if
        the directory contains other files.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            # The efficiency directory does not exists yet, get_efficiency_files
            # returns an empty list
            self.assertEqual([], self.det.get_efficiency_files())

            self.det.update_directories(Path(tmp_dir))
            self.assertTrue(self.det.get_efficiency_dir().exists())
            self.create_eff_files(self.det.get_efficiency_dir(), self.eff_files)
            self.assertNotEqual(
                sorted(self.eff_files.keys()),
                sorted(self.det.get_efficiency_files()))
            self.assertEqual(
                self.filtered_effs, sorted(self.det.get_efficiency_files()))

            # full_path parameter returns the eff files with full paths
            full_paths = sorted(Path(self.det.get_efficiency_dir(), f)
                                for f in self.filtered_effs)
            self.assertEqual(
                full_paths, sorted(self.det.get_efficiency_files(
                    return_full_paths=True)))

            # directories are not returned
            dir_path = Path(self.det.get_efficiency_dir(), "O.eff")
            dir_path.mkdir()
            self.assertTrue(dir_path.is_dir())
            self.assertNotIn(Path("O.eff"), self.det.get_efficiency_files())
            dir_path.rmdir()

            # If the Used_efficiency files directory is removed, empty list
            # is returned
            shutil.rmtree(self.det.get_efficiency_dir())
            self.assertEqual([], self.det.get_efficiency_files())

    def test_add_efficiencies(self):
        """When a new efficiency file is added, it will be copied to the
        efficiency directory of the detector. Only files ending with '.eff'
        are copied.

        Used efficiency files folder is not yet created.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            self.create_eff_files(tmp_dir, self.eff_files)
            # If detector dir has not yet been established with the
            # update_directories_method, add_efficiency_file raises an error
            path = Path(tmp_dir, "1H.eff")
            tmp_path = Path(tmp_dir)
            self.assertTrue(path.exists())
            self.assertRaises(
                FileNotFoundError, lambda: self.det.add_efficiency_file(path))

            self.det.update_directories(tmp_path)

            self.assertEqual([], os.listdir(self.det.get_efficiency_dir()))
            for file in self.eff_files:
                self.det.add_efficiency_file(Path(tmp_path, file))

            self.assertNotEqual(
                sorted(self.eff_files.keys()),
                sorted(os.listdir(self.det.get_efficiency_dir()))
            )
            self.assertEqual(
                sorted([str(f) for f in self.filtered_effs]),
                sorted(os.listdir(self.det.get_efficiency_dir()))
            )
            # The used eff files directory is not yet created
            self.assertFalse(self.det.get_used_efficiencies_dir().exists())

            # If a file with same name is added again, the old file is
            # overwritten
            for file in self.eff_files:
                self.det.add_efficiency_file(Path(tmp_dir, file))

            # Adding a file that is already in the folder does nothing
            for file in self.det.get_efficiency_files(return_full_paths=True):
                self.det.add_efficiency_file(file)

            # Adding a directory raises an error
            dir_path = Path(tmp_dir, "O.eff")
            dir_path.mkdir()
            self.assertRaises(
                OSError, lambda: self.det.add_efficiency_file(dir_path)
            )

    def test_copying_eff_files(self):
        """When files are copied to the used efficiencies folder, which will
        then be provided to tof_list as a parameter, file names are validated
        and extra comments are removed.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            effs_folder = Path(tmp_dir, Detector.EFFICIENCY_DIR)
            used_folder = effs_folder / Detector.USED_EFFICIENCIES_DIR
            tmp_path = Path(tmp_dir)
            self.det.update_directories(tmp_path)

            self.assertEqual(effs_folder, self.det.get_efficiency_dir())
            self.assertEqual(used_folder, self.det.get_used_efficiencies_dir())
            self.assertTrue(effs_folder.exists())
            self.assertFalse(used_folder.exists())

            expected = sorted(
                [f for f in self.eff_files.values() if f is not None])
            self.create_eff_files(self.det.get_efficiency_dir(), self.eff_files)

            self.det.copy_efficiency_files_for_tof_list()
            self.assertTrue(used_folder.exists())
            used_effs = sorted(os.listdir(used_folder))
            self.assertEqual(expected, used_effs)

            # Existing files are removed
            path = self.det.get_used_efficiencies_dir() / "O.eff"
            self.create_eff_files(
                self.det.get_used_efficiencies_dir(), ["O.eff"])
            self.assertTrue(path.exists())
            self.det.copy_efficiency_files_for_tof_list()
            self.assertFalse(path.exists())

    def test_remove_efficiencies(self):
        """When an efficiency file is removed, it will be removed from both
        the efficiency directory and the used efficiencies directory.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            self.det.update_directories(Path(tmp_dir))
            self.create_eff_files(self.det.get_efficiency_dir(), self.eff_files)

            self.det.copy_efficiency_files_for_tof_list()
            self.assertNotEqual([], os.listdir(self.det.get_efficiency_dir()))
            self.assertNotEqual(
                [], os.listdir(self.det.get_used_efficiencies_dir()))

            for file in self.eff_files:
                self.det.remove_efficiency_file(file)

            self.assertEqual(
                [Detector.USED_EFFICIENCIES_DIR],
                os.listdir(self.det.get_efficiency_dir()))
            self.assertEqual(
                [], os.listdir(self.det.get_used_efficiencies_dir()))

            # If the file is a directory, exceptions will be handled by the
            # remove method
            path = self.det.get_efficiency_dir() / "O.eff"
            path.mkdir()
            self.det.remove_efficiency_file(path.name)
            self.assertTrue(path.exists())
            path.rmdir()

            used_path = self.det.get_used_efficiencies_dir() / "O.eff"
            used_path.mkdir()
            open(path, "a").close()
            self.assertTrue(path.exists())
            self.assertTrue(used_path.exists())
            self.det.remove_efficiency_file(used_path.name)
            self.assertFalse(path.exists())
            self.assertTrue(used_path.exists())

    def test_update_directory(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            expected = Path(tmp_dir, Detector.EFFICIENCY_DIR)
            self.assertFalse(expected.exists())

            self.det.update_directories(Path(tmp_dir))

            self.assertTrue(self.det.get_efficiency_dir().exists())
            self.assertEqual(expected, self.det.get_efficiency_dir())
            self.assertEqual(expected / Detector.USED_EFFICIENCIES_DIR,
                             self.det.get_used_efficiencies_dir())

    def test_directory_reference_update(self):
        self.assertEqual(
            Path(tempfile.gettempdir(), "Detector", ".detector"), self.det.path)

        mesu = mo.get_measurement()
        mesu_path = Path(tempfile.gettempdir(), "mesu")
        mesu.directory = Path(mesu_path)

        self.det.update_directory_references(mesu)

        self.assertEqual(mesu_path / "Detector" / ".detector", self.det.path)
        self.assertEqual(
            mesu_path / "Detector" / Detector.EFFICIENCY_DIR,
            self.det.get_efficiency_dir())
        # Directory is not yet created
        self.assertFalse(self.det.get_efficiency_dir().exists())

    @staticmethod
    def create_eff_files(directory, eff_files):
        for f in eff_files:
            open(Path(directory, f), "a").close()
