# coding=utf-8
"""
TODO
"""

import unittest
from modules import list_integration as li


class TestListIntegration(unittest.TestCase):
    def test_bins_without_limits(self):
        self.assertEqual(0, li.integrate_bins([0], [1]))
        self.assertEqual(0, li.integrate_bins([], []))
        self.assertEqual(3, li.integrate_bins([0, 1], [1, 2]))
        self.assertEqual(30, li.integrate_bins([0, 10], [1, 2]))
        self.assertEqual(70, li.integrate_bins([0, 10, 20], [1, 2, 4]))

        # Currently step size is assumed to be constant, so variable changes are
        # not taken into account. This may change in the future
        self.assertEqual(
            120, li.integrate_bins([0, 10, 300, 600], [1, 2, 4, 5]))
        # Negative steps also do not affect calculation
        self.assertEqual(
            120, li.integrate_bins([0, -10, -300, 600], [1, 2, 4, 5]))
        # TODO zero width should probably raise exception
        self.assertEqual(
            0, li.integrate_bins([0, 0, -300, 600], [1, 2, 4, 5]))

    def test_bad_inputs(self):
        # These should all raise exceptions
        self.assertRaises(
            ValueError, lambda: li.integrate_bins([1], [1, 2]))
        self.assertRaises(
            ValueError, lambda: li.integrate_bins([1, 2], [1]))
        self.assertRaises(
            TypeError, lambda: li.integrate_bins(["bar", "foo"], [1, 2]))
        self.assertRaises(
            TypeError, lambda: li.integrate_bins([1, 1], ["foo", "bar"]))

    def test_limits(self):
        # Values before a are not included in the integral, but first
        # value after b is
        self.assertEqual(
            30, li.integrate_bins([0, 1, 2, 3, 4, 5],
                                  [10, 10, 10, 10, 10, 10],
                                  a=1.5, b=3.5))
        self.assertEqual(
            30, li.integrate_bins([0, 1, 2, 3, 4, 5],
                                  [10, 10, 10, 10, 10, 10],
                                  a=2, b=3))
        self.assertEqual(
            30, li.integrate_bins([0, 1, 2, 3, 4, 5],
                                  [10, 10, 10, 10, 10, 10],
                                  a=1.5, b=3))
        self.assertEqual(
            30, li.integrate_bins([0, 1, 2, 3, 4, 5],
                                  [10, 10, 10, 10, 10, 10],
                                  a=2, b=3.5))

        # Turning limits around returns 0
        self.assertEqual(
            0, li.integrate_bins([0, 1, 2, 3, 4, 5],
                                 [10, 10, 10, 10, 10, 10],
                                 a=3, b=2))

        # If a = b, only one bin is counted
        self.assertEqual(
            10, li.integrate_bins([0, 1, 2, 3, 4, 5],
                                  [10, 10, 10, 10, 10, 10],
                                  a=3, b=3))


if __name__ == "__main__":
    unittest.main()
