# coding=utf-8
"""
Created on 19.1.2020

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
import math

import tests.mock_objects as mo

from modules.depth_files import DepthProfileHandler
from modules.enums import DepthProfileUnit
from timeit import default_timer as timer


class TestDepthProfileHandling(unittest.TestCase):
    def setUp(self):
        self.depth_dir, self.all_elements, self.some_elements = \
            mo.get_sample_depth_files_and_elements()
        self.handler = DepthProfileHandler()

    def test_file_reading(self):
        """Tests that the files can be read and all given elements are
        stored in the profile handler"""
        self.handler.read_directory(self.depth_dir, self.all_elements)
        self.check_handler_profiles(self.handler, self.all_elements)

        # Read just some of the elements. This should remove existing
        # profiles from the handler
        self.handler.read_directory(self.depth_dir, self.some_elements)
        self.check_handler_profiles(self.handler, self.some_elements)

    def check_handler_profiles(self, handler, elements):
        """Checks that handler contains all the expected element
        profiles"""
        # Check that the handler contains absolute profiles
        # of all elements and a profile called total
        elem_set = set(str(elem) for elem in elements)
        abs_profiles = handler.get_absolute_profiles()
        self.assertEqual(
            set(abs_profiles.keys()).difference(elem_set),
            {"total"})

        # Relative profiles also contain all elements, but no total
        # profile
        rel_profiles = handler.get_relative_profiles()
        self.assertEqual(set(rel_profiles.keys()),
                         elem_set)

    def test_calculate_ratios(self):
        all_elem_names = set(str(elem) for elem in self.all_elements)
        some_elem_names = set(str(elem) for elem in self.all_elements)
        self.handler.read_directory(self.depth_dir, self.all_elements)

        # All elements are ignored, so all values returned by the calculation
        # are None
        percentages, moes = self.handler.calculate_ratios(
            all_elem_names, -math.inf, math.inf, 3)

        self.assertEqual(all_elem_names, set(percentages.keys()))
        self.assertEqual(all_elem_names, set(moes.keys()))
        for pval, mval in zip(percentages.values(), moes.values()):
            self.assertIsNone(pval)
            self.assertIsNone(mval)

        # Only some elements are ignored
        percentages, moes = self.handler.calculate_ratios(
            some_elem_names, -math.inf, math.inf, 3)
        self.assertEqual(all_elem_names, set(percentages.keys()))
        self.assertEqual(all_elem_names, set(moes.keys()))
        for p, m in zip(percentages, moes):
            if p in some_elem_names:
                self.assertIsNone(percentages[p])
            else:
                self.assertTrue(0 <= percentages[p] <= 100)
            if m in some_elem_names:
                self.assertIsNone(moes[m])
            else:
                self.assertTrue(0 <= moes[m])

    def test_get_depth_range(self):
        """Tests depth ranges with different depth units"""
        # First read files while using depth units other than nanometers
        self.handler.read_directory(
            self.depth_dir, self.some_elements,
            depth_units=DepthProfileUnit.ATOMS_PER_SQUARE_CM)
        fst_range = self.handler.get_depth_range()

        # Then read files using nanometers
        self.handler.read_directory(
            self.depth_dir, self.some_elements,
            depth_units=DepthProfileUnit.NM)
        snd_range = self.handler.get_depth_range()

        # First and second ranges are different and both are not
        # None
        self.assertNotEqual(fst_range, snd_range)
        self.assertNotEqual((None, None), fst_range)
        self.assertNotEqual((None, None), snd_range)

        # However, if one were to delete the 'total' profile
        del self.handler._DepthProfileHandler__absolute_profiles["total"]
        self.assertEqual((None, None),
                         self.handler.get_depth_range())

    def test_statistics(self):
        """Tests the values for some of the statistics. If the
        calculations methods change, expected values in this test
        must also be changed."""
        self.handler.read_directory(self.depth_dir, self.some_elements)

        self.assertEqual((-27.632, 310.992),
                         self.handler.get_depth_range())

        self.assertAlmostEqual(
            25.97,
            sum(self.handler.integrate_concentrations(0, 100).values()),
            places=2
        )

        p, m = self.handler.calculate_ratios(set(), 0, 100, 0.1)
        self.assertAlmostEqual(34.94, sum(p.values()), places=2)
        self.assertAlmostEqual(0.57, sum(m.values()), places=2)

    def test_caching_with_merge(self):
        """Tests caching functionality in DepthProfile merging"""

        # Maximum cache size currently set for merge function is 32
        max_cache = 32
        n = 100

        inf = self.handler.merge_profiles.cache_info()
        self.assertEqual(inf.currsize, 0)
        self.assertEqual(inf.maxsize, max_cache)

        self.handler.read_directory(self.depth_dir, self.all_elements)
        a, b = self.handler.get_depth_range()

        # First merge is called with same parameters for n times
        start = timer()
        for _ in range(n):
            self.handler.merge_profiles(a + 100, b - 100, method="abs_rel_abs")
            self.handler.merge_profiles(a + 100, b - 100, method="rel_abs_rel")
        stop = timer()

        # As only two different sets of parameters were used, current cache
        # size is 2
        self.assertEqual(2, self.handler.merge_profiles.cache_info().currsize)

        with_caching = stop - start

        # Then it is called with different parameters so caching will not help
        start = timer()
        for i in range(n):
            self.handler.merge_profiles(a + 100 + i, b - 100 - i,
                                        method="abs_rel_abs")
            self.handler.merge_profiles(a + 100 + i, b - 100 - i,
                                        method="rel_abs_rel")
        stop = timer()

        # Assert that maximum size has been reached
        self.assertEqual(max_cache,
                         self.handler.merge_profiles.cache_info().currsize)

        without_caching = stop - start

        # Cached runs should be at least 10 times faster, depending on n
        # print(with_caching, without_caching)
        self.assertTrue(with_caching < without_caching * 0.1,
                        msg="Caching was slower than expected. This is not a "
                            "failure per se, but something that should happen "
                            "only on rare occasions. Rerun the test to see if "
                            "the problem persist.")

        # Assert that cache gets cleared when directory is read
        m1 = self.handler.merge_profiles(a + 100, b - 100, method="abs_rel_abs")
        self.handler.read_directory(self.depth_dir, elements=self.some_elements)

        self.assertEqual(0, self.handler.merge_profiles.cache_info().currsize)
        m2 = self.handler.merge_profiles(a + 100, b - 100, method="abs_rel_abs")

        self.assertNotEqual(m1.keys(), m2.keys())
        self.assertEqual(1, self.handler.merge_profiles.cache_info().currsize)

    def test_merge_identities(self):
        """This tests that objects returned by the merge are same when
        retrieved from cache"""
        # Caching means that same object is returned
        # This needs to be taken into consideration if caller needs to modify
        # the results
        self.handler.read_directory(self.depth_dir, self.some_elements)

        # Set initial ranges that fall within handlers depth range
        a, b = self.handler.get_depth_range()
        a += 100
        b -= 100

        m1 = self.handler.merge_profiles(a, b, method="abs_rel_abs")
        m2 = self.handler.merge_profiles(a, b, method="abs_rel_abs")
        self.assertIs(m1, m2)
        m3 = self.handler.merge_profiles(a, b, method="rel_abs_rel")
        m4 = self.handler.merge_profiles(a, b, method="rel_abs_rel")
        self.assertIs(m3, m4)
        self.assertIsNot(m1, m3)

        # Deleting a key from m3 also deletes it from m4
        self.assertIn("H", m3)
        self.assertIn("H", m4)
        del m3["H"]
        self.assertNotIn("H", m3)
        self.assertNotIn("H", m4)

        # When a new ProfileHandler is created, new cache is also established
        new_dp = DepthProfileHandler()
        new_dp.read_directory(self.depth_dir, self.some_elements)

        m5 = new_dp.merge_profiles(a, b, method="abs_rel_abs")
        self.assertIsNot(m1, m5)


if __name__ == "__main__":
    unittest.main()
