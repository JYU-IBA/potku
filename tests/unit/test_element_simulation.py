# coding=utf-8
"""
Created on 2.2.2020
Updated on 5.2.2020

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
__version__ = ""  # TODO

import unittest
import tempfile
import os
import time
import platform

import modules.file_paths as fp
import tests.mock_objects as mo

from modules.recoil_element import RecoilElement
from modules.element import Element
from modules.element_simulation import ERDFileHandler
from modules.element_simulation import ElementSimulation

from tests.utils import expected_failure_if


class TestErdFileHandler(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # default recoil element
        cls.elem_4he = RecoilElement(Element.from_string("4He"),
                                     [], "red")

        # Valid file names for the recoil element
        cls.valid_erd_files = [
            "4He-Default.101.erd",
            "4He-Default.102.erd"
        ]

        # Invalid file names for the recoil element
        cls.invalid_erd_files = [
            "4He-Default.101",
            ".4He-Default.102.erd",
            ".4He-Default..erd",
            "4He-Default.101.erf",
            "4He-Default./.103.erd",
            "4He-Default.\\.104.erd",
            "3He-Default.102.erd"
        ]

        cls.expected_values = [
            (f, s + 101)
            for s, f in enumerate(cls.valid_erd_files)
        ]

    def test_get_seed(self):
        # get_seed looks for an integer in the second part of the string
        # split by dots
        self.assertEqual(102, fp.get_seed("O.102.erd"))
        self.assertEqual(0, fp.get_seed("..3.2.1.0."))
        self.assertEqual(-1, fp.get_seed("..-1.2"))

        # File paths are also valid arguments
        self.assertEqual(101, fp.get_seed("/tmp/.101.erd"))
        self.assertEqual(101, fp.get_seed("\\tmp\\.101.erd"))

        # get_seed makes no attempt to check if the entire string
        # is a valid file name or path to an erd file
        self.assertEqual(101, fp.get_seed(".101./erd"))
        self.assertEqual(101, fp.get_seed(".101.\\erd"))

        # Having less split parts before or after returns None
        self.assertIsNone(fp.get_seed("111."))
        self.assertIsNone(fp.get_seed("0-111."))
        self.assertIsNone(fp.get_seed(".111.."))

        # So does having no splits at all
        self.assertIsNone(fp.get_seed("100"))

    # Expect failure on *nix systems because they accept different file names
    # compared to Windows.
    # TODO correct behaviour should be specified in the future
    @expected_failure_if(platform.system() != "Windows")
    def test_get_valid_erd_files(self):
        self.assertEqual([], list(fp.validate_erd_file_names(
            self.invalid_erd_files, self.elem_4he)))

        res = list(fp.validate_erd_file_names(self.valid_erd_files,
                                              self.elem_4he))

        self.assertEqual(self.expected_values, res)

        # Combining invalid files with valid files does not change the
        # result
        new_files = self.invalid_erd_files + self.valid_erd_files

        res = list(fp.validate_erd_file_names(new_files,
                                              self.elem_4he))

        self.assertEqual(self.expected_values, res)

    def test_erdfilehandler_init(self):
        handler = ERDFileHandler(self.valid_erd_files, self.elem_4he)

        exp = [(f, s, False) for f, s in self.expected_values]
        self.assertEqual(exp, [f for f in handler])
        self.assertEqual(0, handler.get_active_atom_counts())
        self.assertEqual(0, handler.get_old_atom_counts())

    def test_max_seed(self):
        handler = ERDFileHandler([], self.elem_4he)

        self.assertEqual(None, handler.get_max_seed())

        handler.add_active_file(self.valid_erd_files[0])
        self.assertEqual(101, handler.get_max_seed())

        handler.add_active_file(self.valid_erd_files[1])
        self.assertEqual(102, handler.get_max_seed())

    def test_erdfilehandler_add(self):
        handler = ERDFileHandler(self.valid_erd_files, self.elem_4he)

        # already existing files, or files belonging to another
        # recoil element cannot be added
        self.assertRaises(ValueError,
                          lambda: handler.add_active_file(
                              self.valid_erd_files[0]))
        self.assertRaises(ValueError,
                          lambda: handler.add_active_file("4He-New.101.erd"))

        # new file can be added, but only once
        new_file = "4He-Default.103.erd"
        handler.add_active_file(new_file)

        self.assertRaises(ValueError, lambda: handler.add_active_file(new_file))

        # new file appears as the first element when iterating
        # over the handler and its status is active
        exp = [(new_file, 103, True)] + [(f, s, False)
                                         for f, s, in self.expected_values]

        self.assertEqual(exp, [f for f in handler])

    def test_len(self):
        """Tests for handler's __len__ function"""
        handler = ERDFileHandler([], self.elem_4he)
        self.assertEqual(0, len(handler))
        for f in self.valid_erd_files:
            handler.add_active_file(f)

        self.assertEqual(len(self.valid_erd_files), len(handler))
        handler.update()
        handler.add_active_file("4He-Default.103.erd")
        self.assertEqual(len(self.valid_erd_files) + 1, len(handler))

    def test_clear(self):
        """Tests handler's clear method."""
        handler = ERDFileHandler(self.valid_erd_files, self.elem_4he)
        self.assertEqual(len(self.valid_erd_files), len(handler))
        handler.clear()
        self.assertEqual(0, len(handler))

    def test_atom_counts(self):
        """Tests atom counting by writing lines to temporary files"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create files in the tmp dir
            for file in self.valid_erd_files:
                write_line(os.path.join(tmp_dir, file))

            # Initialise a handler from the tmp_dir and add an active file
            handler = ERDFileHandler.from_directory(tmp_dir, self.elem_4he)
            handler.add_active_file(os.path.join(tmp_dir,
                                                 "4He-Default.103.erd"))

            # Append a line to each file
            for erd_file, _, _ in handler:
                write_line(erd_file)

            self.assertEqual(1, handler.get_active_atom_counts())
            self.assertEqual(4, handler.get_old_atom_counts())

            # As the results of old files are cached, only counts in active
            # files are incremented
            for erd_file, _, _ in handler:
                write_line(erd_file)

            self.assertEqual(2, handler.get_active_atom_counts())
            self.assertEqual(4, handler.get_old_atom_counts())

            # If the handler is updated, active file is moved to old files
            handler.update()
            self.assertEqual(0, handler.get_active_atom_counts())
            self.assertEqual(6, handler.get_old_atom_counts())

            # Now the atom count will no longer update in the added file
            for erd_file, _, _ in handler:
                write_line(erd_file)

            self.assertEqual(0, handler.get_active_atom_counts())
            self.assertEqual(6, handler.get_old_atom_counts())

        # Assert that clearing also clears cache
        handler.clear()
        self.assertEqual(0, handler.get_old_atom_counts())

        # Assert that tmp dir got deleted
        self.assertFalse(os.path.exists(tmp_dir))


class TestElementSimulation(unittest.TestCase):
    def setUp(self):
        self.main_rec = mo.get_recoil_element()
        self.kwargs = {
            "minimum_energy": 42.0,
            "minimum_scattering_angle": 17.0,
            "minimum_main_scattering_angle": 14.0,
            "number_of_preions": 3
        }
        self.elem_sim = ElementSimulation(tempfile.gettempdir(),
                                          mo.get_request(),
                                          [self.main_rec],
                                          save_on_creation=False,
                                          **self.kwargs)

    def test_get_full_name(self):
        self.assertEqual("Default", self.elem_sim.get_full_name())
        self.elem_sim.name = "foo"
        self.assertEqual("foo", self.elem_sim.get_full_name())
        self.elem_sim.name_prefix = "bar"
        self.assertEqual("bar-foo", self.elem_sim.get_full_name())

    def test_to_dict(self):
        self.elem_sim.use_default_settings = False
        expected = {
            "name": "Default",
            "description": "",
            "modification_time": time.strftime("%c %z %Z", time.localtime(
                time.time())),
            "simulation_type": "ERD",
            "simulation_mode": "narrow",
            "number_of_ions": 1_000_000,
            "seed_number": 101,
            "number_of_recoils": 10,
            "number_of_scaling_ions": 5,
            "main_recoil": self.main_rec.name
        }
        # Update expected with kwargs
        original_keys = set(expected.keys())
        expected.update(self.kwargs)
        result = self.elem_sim.to_dict()

        # Remove time from result and test it separately
        timestamp = time.time()
        self.assertAlmostEqual(timestamp, result.pop(
            "modification_time_unix"), places=2,
                               msg="This assertion may fail if the test "
                                   "is running particularly slow. Run the "
                                   "test again to confirm results."
                               )
        self.assertEqual("False", result.pop("use_default_settings"))
        self.assertEqual(expected, result)

        # Test default settings
        self.elem_sim.use_default_settings = True
        result_default = self.elem_sim.to_dict()
        timestamp = time.time()
        self.assertAlmostEqual(timestamp, result_default.pop(
            "modification_time_unix"), places=2,
                               msg="This assertion may fail if the test "
                                   "is running particularly slow. Run the "
                                   "test again to confirm results.")
        self.assertEqual("True", result_default.pop("use_default_settings"))
        self.assertCountEqual(expected, result_default)

        # Assert that default keys contain expected values:
        for k in original_keys:
            self.assertEqual(expected[k], result_default[k])

        # Assert that other values differ from nondefault dict
        set_dif = set(result.keys()) - original_keys
        for k in set_dif:
            self.assertNotEqual(result[k], result_default[k])

    def test_copy_from_another(self):
        another = ElementSimulation(
            tempfile.gettempdir(),
            mo.get_request(),
            [RecoilElement(Element.from_string("16O"),
                           [], "red")],
            save_on_creation=False,
            description="foo",
            simulation_mode="RBS",
            detector=mo.get_detector(),
            number_of_ions=15,
            number_of_recoils=14,
            seed_number=16,
            channel_width=2,
            __opt_seed=4
        )

        another.copy_settings_from(self.elem_sim)

        self.assertEqual(another.name, self.elem_sim.name)
        self.assertEqual(another.description, self.elem_sim.description)
        self.assertEqual(another.seed_number, self.elem_sim.seed_number)
        self.assertEqual(another.number_of_recoils,
                         self.elem_sim.number_of_recoils)
        self.assertEqual(another.simulation_mode,
                         self.elem_sim.simulation_mode)
        self.assertEqual(another.number_of_preions,
                         self.elem_sim.number_of_preions)

        self.assertNotEqual(another.channel_width, self.elem_sim.channel_width)


def write_line(file):
    with open(file, "a") as file:
        # ERDFileHandler is only counting lines,
        # it does not care if the file contains
        # nonsensical data.
        file.write("foo\n")
