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
__version__ = "2.0"

import unittest
import tempfile
import os
import time
import platform
import threading

import modules.file_paths as fp
import tests.mock_objects as mo
import tests.utils as utils

from modules.recoil_element import RecoilElement
from modules.element import Element
from modules.element_simulation import ERDFileHandler
from modules.element_simulation import ElementSimulation
from modules.enums import OptimizationType

from tests.utils import expected_failure_if

from pathlib import Path
from unittest.mock import patch


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
        self.assertEqual(0, handler.get_active_atom_count())
        self.assertEqual(0, handler.get_old_atom_count())

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
            handler.add_active_file(
                os.path.join(tmp_dir, "4He-Default.103.erd"))

            # Append a line to each file
            for erd_file, _, _ in handler:
                write_line(erd_file)

            self.assertEqual(1, handler.get_active_atom_count())
            self.assertEqual(4, handler.get_old_atom_count())
            self.assertEqual(5, handler.get_total_atom_count())

            # As the results of old files are cached, only counts in active
            # files are incremented
            for erd_file, _, _ in handler:
                write_line(erd_file)

            self.assertEqual(2, handler.get_active_atom_count())
            self.assertEqual(4, handler.get_old_atom_count())
            self.assertEqual(6, handler.get_total_atom_count())

            # If the handler is updated, active file is moved to old files
            handler.update()
            self.assertEqual(0, handler.get_active_atom_count())
            self.assertEqual(6, handler.get_old_atom_count())
            self.assertEqual(6, handler.get_total_atom_count())

            # Now the atom count will no longer update in the added file
            for erd_file, _, _ in handler:
                write_line(erd_file)

            self.assertEqual(0, handler.get_active_atom_count())
            self.assertEqual(6, handler.get_old_atom_count())
            self.assertEqual(6, handler.get_total_atom_count())

        # Assert that clearing also clears cache
        handler.clear()
        self.assertEqual(0, handler.get_active_atom_count())
        self.assertEqual(0, handler.get_old_atom_count())
        self.assertEqual(0, handler.get_total_atom_count())

        # Assert that tmp dir got deleted
        self.assertFalse(os.path.exists(tmp_dir))

    def test_results_exists(self):
        handler = ERDFileHandler([], self.elem_4he)
        self.assertFalse(handler.results_exist())
        handler.add_active_file(self.valid_erd_files[0])
        self.assertTrue(handler.results_exist())
        handler.update()
        self.assertTrue(handler.results_exist())
        handler.clear()
        self.assertFalse(handler.results_exist())

    def test_thread_safety(self):
        """Tests that ErdFileHandler is thread safe."""
        n = 1000
        delay = 0.001
        handler = ERDFileHandler([], self.elem_4he)

        def adder():
            for i in range(n):
                handler.add_active_file(f"4He-Default.{i}.erd")

        self.assert_runs_ok(adder, handler.get_active_atom_count)
        self.assertEqual(n, len(handler))

        def updater():
            time.sleep(delay)
            handler.update()

        self.assert_runs_ok(handler.get_active_atom_count, updater)
        self.assertEqual(n, len(handler))

        def clearer():
            time.sleep(delay)
            handler.clear()

        self.assert_runs_ok(handler.get_old_atom_count, clearer)
        self.assertEqual(0, len(handler))

        # Add the files again and see if counting old atoms works when updating
        adder()
        self.assert_runs_ok(handler.get_old_atom_count, updater)
        self.assertEqual(n, len(handler))

        clearer()
        self.assertEqual(0, len(handler))

        self.assert_runs_ok(adder, updater)
        # TODO Updating and adding at the same time may cause the total count
        #  to be more than n, hence the less or equal comparison. A better
        #  multithreading test is needed to test this thing properly.
        self.assertTrue(n <= len(handler))

    @staticmethod
    def assert_runs_ok(func1, func2):
        """Runs the func1 and func2 in different threads at the same time.
        Raises RuntimeError if something goes wrong.
        """
        t = threading.Thread(target=func2)

        t.start()
        func1()
        t.join()


class TestElementSimulation(unittest.TestCase):
    def setUp(self):
        self.main_rec = mo.get_recoil_element()
        self.kwargs = {
            "minimum_energy": 42.0,
            "minimum_scattering_angle": 17.0,
            "minimum_main_scattering_angle": 14.0,
            "number_of_preions": 3
        }
        self.elem_sim = ElementSimulation(
            tempfile.gettempdir(), mo.get_request(), [self.main_rec],
            save_on_creation=False, **self.kwargs)

    def test_get_full_name(self):
        self.assertEqual("Default", self.elem_sim.get_full_name())
        self.elem_sim.name = "foo"
        self.assertEqual("foo", self.elem_sim.get_full_name())
        self.elem_sim.name_prefix = "bar"
        self.assertEqual("bar-foo", self.elem_sim.get_full_name())

    def test_json_contents(self):
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
        expected.update(self.kwargs)
        result = self.elem_sim.get_json_content()

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

    def test_simulation_settings(self):
        new_settings = {
            "simulation_type": "RBS",
            "simulation_mode": "narrow",
            "number_of_ions": 1,
            "number_of_ions_in_presimu": 2,
            "number_of_scaling_ions": 3,
            "number_of_recoils": 4,
            "minimum_scattering_angle": 5,
            "minimum_main_scattering_angle": 6,
            "minimum_energy_of_ions": 7,
            "seed_number": 8
        }
        self.assertNotEqual(new_settings,
                            self.elem_sim.get_settings())
        self.elem_sim.set_settings(**new_settings)
        self.assertEqual(new_settings,
                         self.elem_sim.get_settings())

    def test_bad_simulation_settings(self):
        orig_settings = dict(self.elem_sim.get_settings())

        # Using some unknown value does not change the settings
        self.elem_sim.set_settings(foo=2)
        self.assertEqual(orig_settings, self.elem_sim.get_settings())

        # Other values can still be set if some values are unknown.
        self.elem_sim.set_settings(foo=2,
                                   number_of_ions_in_presimu=1234)
        self.assertEqual(1234, self.elem_sim.number_of_preions)

        # Values are not validated (yet)
        self.elem_sim.set_settings(
            number_of_ions_in_presimu="i dunno, two maybe?")
        self.assertEqual("i dunno, two maybe?", self.elem_sim.number_of_preions)

    def test_slots(self):
        """Tests that __slots__ declaration works.
        """
        self.assertRaises(AttributeError,
                          lambda: utils.slots_test(self.elem_sim))

    @patch("modules.get_espe.GetEspe.__init__", return_value=None)
    @patch("modules.get_espe.GetEspe.run", return_value=None)
    def test_calculate_spectrum(self, mock_run, mock_get_espe):
        """Tests that the file paths generated during energy spectrum
        calculation are correct depending on the type of optimization.
        """
        self.main_rec.name = "main_rec"
        optim_recoil = mo.get_recoil_element()
        optim_recoil.prefix = "C"
        optim_recoil.name = "optimized"
        espe_recoil = mo.get_recoil_element()
        espe_recoil.prefix = "H"
        espe_recoil.name = "spectrum"

        self.elem_sim.optimization_recoils = [optim_recoil]
        self.elem_sim.simulation = mo.get_simulation()

        with tempfile.TemporaryDirectory() as tmp_dir:
            self.elem_sim.directory = tmp_dir

            # No optimization
            rec_file = Path(
                tmp_dir, f"{espe_recoil.get_full_name()}.recoil")
            erd_file = Path(
                tmp_dir, f"{self.main_rec.get_full_name()}.*.erd")
            espe_file = Path(
                tmp_dir, f"{espe_recoil.get_full_name()}.simu")

            kwargs = {
                "recoil_element": espe_recoil
            }
            self.assert_files_equal(
                mock_get_espe, kwargs, rec_file, erd_file, espe_file)

            # Recoil optimization
            rec_file = Path(
                tmp_dir, f"{espe_recoil.get_full_name()}.recoil")
            erd_file = Path(
                tmp_dir, f"{optim_recoil.prefix}-opt.*.erd")
            espe_file = Path(
                tmp_dir, f"{espe_recoil.get_full_name()}.simu")

            kwargs = {
                "recoil_element": espe_recoil,
                "optimization_type": OptimizationType.RECOIL
            }
            self.assert_files_equal(
                mock_get_espe, kwargs, rec_file, erd_file, espe_file)

            # Fluence optimization
            rec_file = Path(
                tmp_dir, f"{espe_recoil.prefix}-optfl.recoil")
            erd_file = Path(
                tmp_dir, f"{self.main_rec.prefix}-optfl.*.erd")
            espe_file = Path(
                tmp_dir, f"{espe_recoil.prefix}-optfl.simu")

            kwargs = {
                "recoil_element": espe_recoil,
                "optimization_type": OptimizationType.FLUENCE
            }
            self.assert_files_equal(
                mock_get_espe, kwargs, rec_file, erd_file, espe_file)

    def assert_files_equal(self, mock_get_espe, kwargs, rec_file, erd_file,
                           espe_file):
        _, file = self.elem_sim.calculate_espe(**kwargs)

        args = mock_get_espe.call_args[1]
        self.assertEqual(rec_file, args["recoil_file"])
        self.assertEqual(erd_file, args["erd_file"])
        self.assertEqual(espe_file, args["spectrum_file"])
        self.assertEqual(espe_file, file)

        self.assertTrue(rec_file.exists())
        rec_file.unlink()

    @patch("modules.element_simulation.ERDFileHandler.results_exist")
    def test_elem_sim_state(self, mock_exist):
        """Tests for ElementSimulation's state booleans.
        """
        mock_exist.side_effect = [False, True, True, True]
        self.assertFalse(self.elem_sim.is_simulation_running())
        self.assertFalse(self.elem_sim.is_simulation_finished())
        self.assertFalse(self.elem_sim.is_optimization_running())
        self.assertFalse(self.elem_sim.is_optimization_finished())

        self.elem_sim._set_flags(True)

        self.assertTrue(self.elem_sim.is_simulation_running())
        self.assertFalse(self.elem_sim.is_simulation_finished())
        self.assertFalse(self.elem_sim.is_optimization_running())
        self.assertFalse(self.elem_sim.is_optimization_finished())

        self.elem_sim._set_flags(False)

        self.assertFalse(self.elem_sim.is_simulation_running())
        self.assertTrue(self.elem_sim.is_simulation_finished())
        self.assertFalse(self.elem_sim.is_optimization_running())
        self.assertFalse(self.elem_sim.is_optimization_finished())

        self.elem_sim._set_flags(True, OptimizationType.RECOIL)

        self.assertFalse(self.elem_sim.is_simulation_running())
        self.assertTrue(self.elem_sim.is_simulation_finished())
        self.assertTrue(self.elem_sim.is_optimization_running())
        self.assertFalse(self.elem_sim.is_optimization_finished())

        self.elem_sim.optimized_fluence = 1
        self.assertFalse(self.elem_sim.is_optimization_finished())

        self.elem_sim._set_flags(False)
        self.assertTrue(self.elem_sim.is_optimization_finished())

    def test_has_element(self):
        rec_he = mo.get_recoil_element(symbol="He")
        rec_1he = mo.get_recoil_element(symbol="He", isotope=1)
        rec_1he_2 = mo.get_recoil_element(symbol="He", isotope=1, amount=2)

        self.elem_sim.recoil_elements = []
        self.assertFalse(self.elem_sim.has_element(rec_he.element))

        self.elem_sim.recoil_elements = [rec_he]
        self.assertTrue(self.elem_sim.has_element(rec_he.element))
        self.assertFalse(self.elem_sim.has_element(rec_1he.element))
        self.assertFalse(self.elem_sim.has_element(rec_1he_2.element))

        self.elem_sim.recoil_elements = [rec_1he]
        self.assertFalse(self.elem_sim.has_element(rec_he.element))
        self.assertTrue(self.elem_sim.has_element(rec_1he.element))
        self.assertTrue(self.elem_sim.has_element(rec_1he_2.element))

        self.elem_sim.recoil_elements = [rec_1he, rec_he]
        self.assertTrue(self.elem_sim.has_element(rec_he.element))
        self.assertTrue(self.elem_sim.has_element(rec_1he.element))
        self.assertTrue(self.elem_sim.has_element(rec_1he_2.element))


def write_line(file):
    with open(file, "a") as file:
        # ERDFileHandler is only counting lines,
        # it does not care if the file contains
        # nonsensical data.
        file.write("foo\n")
