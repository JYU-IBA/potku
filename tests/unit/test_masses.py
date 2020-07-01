# coding=utf-8
"""
Created on 10.04.2020

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
import itertools

import modules.masses as masses


class TestMasses(unittest.TestCase):
    def test_identities(self):
        # Assert that lists are cloned
        c_isos1 = masses.get_isotopes("C")
        c_isos2 = masses.get_isotopes("C")
        self.assertEqual(c_isos1, c_isos2)
        self.assertIsNot(c_isos1, c_isos2)

        for c1, c2 in itertools.product(c_isos1, c_isos2):
            self.assertIsNot(c1, c2)

        self.assertNotEqual(masses.get_isotopes("C"),
                            masses.get_isotopes("He"))

    def test_filtering_unlikely(self):
        # By default, unlikely isotopes (i.e. ones with natural abundance of 0)
        # are filtered out
        default = masses.get_isotopes("O")
        filtered = masses.get_isotopes("O", filter_unlikely=True)
        self.assertEqual(default, filtered)

        unfiltered = masses.get_isotopes("O", filter_unlikely=False)
        self.assertNotEqual(filtered, unfiltered)
        self.assertLess(len(filtered), len(unfiltered))

        for iso in filtered:
            self.assertIn(iso, unfiltered)

    def test_sort_by_abundance(self):
        # By default, isotopes are sorted by abundance
        default = masses.get_isotopes("Li", filter_unlikely=False)
        sorted_isos = masses.get_isotopes("Li", sort_by_abundance=True,
                                          filter_unlikely=False)
        self.assertEqual(default, sorted_isos)

        unsorted = masses.get_isotopes("Li", sort_by_abundance=False,
                                       filter_unlikely=False)
        self.assertEqual(len(sorted_isos), len(unsorted))
        self.assertNotEqual(sorted_isos, unsorted)
        for iso in sorted_isos:
            self.assertLessEqual(
                iso["abundance"],
                sorted_isos[0]["abundance"])
            self.assertIn(iso, unsorted)

    def test_rare_and_unknown_isotopes(self):
        # Assert that 'foo' is not in the dictionary, and neither it gets
        # added to it.
        self.assertNotIn("foo", masses._ISOTOPES)
        self.assertEqual([], masses.get_isotopes("foo", filter_unlikely=False))
        self.assertNotIn("foo", masses._ISOTOPES)

        # Uranium has some isotopes, but no abundances so they get filtered out
        self.assertIn("U", masses._ISOTOPES)
        u_all_isos = masses.get_isotopes("U", filter_unlikely=False)
        self.assertNotEqual([], u_all_isos)

        u_filtered = masses.get_isotopes("U", filter_unlikely=True)
        self.assertEqual([], u_filtered)

    def test_get_mass(self):
        self.assertIsNone(masses.find_mass_of_isotope("H", 0))
        self.assertAlmostEqual(1.007825, masses.find_mass_of_isotope("H", 1),
                               places=5)
        self.assertAlmostEqual(2.014101, masses.find_mass_of_isotope("H", 2),
                               places=5)
        self.assertIsNone(masses.find_mass_of_isotope("H", 3))

        self.assertIsNone(masses.find_mass_of_isotope("foo", 42))

    def test_get_st_mass(self):
        self.assertAlmostEqual(1.00015, masses.get_standard_isotope("H"),
                               places=5)
        self.assertAlmostEqual(4, masses.get_standard_isotope("He"),
                               places=5)
        self.assertAlmostEqual(12.0110, masses.get_standard_isotope("C"),
                               places=5)
        self.assertAlmostEqual(6.925, masses.get_standard_isotope("Li"),
                               places=5)

        self.assertEqual(0, masses.get_standard_isotope("U"))
        self.assertEqual(0, masses.get_standard_isotope("foo"))

    def test_get_most_common(self):
        elems = ["C", "He", "Mn", "Li"]
        for elem in elems:
            isotopes = masses.get_isotopes(elem, sort_by_abundance=False,
                                           filter_unlikely=False)

            most_common = masses.get_most_common_isotope(elem)
            self.assertIn(most_common, isotopes)

            for iso in isotopes:
                self.assertLessEqual(
                    iso["abundance"],
                    most_common["abundance"])

        self.assertIsNone(masses.get_most_common_isotope("U"))
        self.assertIsNone(masses.get_most_common_isotope("foo"))


if __name__ == '__main__':
    unittest.main()
