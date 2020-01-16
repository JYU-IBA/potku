# coding=utf-8
"""
TODO
"""

import unittest
from modules import list_integration as li

class TestListIntegration(unittest.TestCase):
    def test_concentration_without_limits(self):
        self.assertEqual(0, li.integrate([0], [1], t="concentrations"))
        self.assertEqual(0, li.integrate([], [], t="concentrations"))
        self.assertEqual(3, li.integrate([0, 1], [1, 2], t="concentrations"))
        self.assertEqual(30, li.integrate([0, 10], [1, 2], t="concentrations"))
        self.assertEqual(70, li.integrate([0, 10, 20], [1, 2, 4], t="concentrations"))

        # Currently step size is assumed to be constant, so variable changes are
        # not taken into account. This may change in the future
        self.assertEqual(
            120, li.integrate([0, 10, 300, 600], [1, 2, 4, 5], t="concentrations"))
        # Negative steps also do not affect calculation
        self.assertEqual(
            120, li.integrate([0, -10, -300, 600], [1, 2, 4, 5], t="concentrations"))
        # TODO zero width should probably be changed
        self.assertEqual(
            0, li.integrate([0, 0, -300, 600], [1, 2, 4, 5], t="concentrations"))

    def test_bad_inputs(self):
        self.assertRaises(
            ValueError, lambda: li.integrate([1], [1, 2], t="concentrations"))
        self.assertRaises(
            ValueError, lambda: li.integrate([1, 2], [1], t="concentrations"))
        self.assertRaises(
            TypeError, lambda: li.integrate(["bar", "foo"], [1, 2], t="concentrations"))
        self.assertRaises(
            TypeError, lambda: li.integrate([1, 1], ["foo", "bar"], t="concentrations"))

    def test_limits(self):
        # TODO these results may change in the future
        self.assertEqual(
            30, li.integrate([0, 1, 2, 3, 4, 5],
                             [10, 10, 10, 10, 10, 10],
                             lim_a=1.5, lim_b=3.5,
                             t="concentrations"))
        self.assertEqual(
            20, li.integrate([0, 1, 2, 3, 4, 5],
                             [10, 10, 10, 10, 10, 10],
                             lim_a=2, lim_b=3,
                             t="concentrations"))
        self.assertEqual(
            20, li.integrate([0, 1, 2, 3, 4, 5],
                             [10, 10, 10, 10, 10, 10],
                             lim_a=1.5, lim_b=3,
                             t="concentrations"))
        self.assertEqual(
            30, li.integrate([0, 1, 2, 3, 4, 5],
                             [10, 10, 10, 10, 10, 10],
                             lim_a=2, lim_b=3.5,
                             t="concentrations"))

        # Turning limits aroung return 0
        self.assertEqual(
            0, li.integrate([0, 1, 2, 3, 4, 5],
                            [10, 10, 10, 10, 10, 10],
                            lim_a=3, lim_b=2,
                            t="concentrations"))
        # As well as setting them to same value
        self.assertEqual(
            0, li.integrate([0, 1, 2, 3, 4, 5],
                            [10, 10, 10, 10, 10, 10],
                            lim_a=3, lim_b=3,
                            t="concentrations"))


if __name__ == "__main__":
    unittest.main()
