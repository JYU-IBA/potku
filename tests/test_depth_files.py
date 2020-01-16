# coding=utf-8
"""
TODO
"""

import unittest

from modules.depth_files import DepthProfile
from modules.element import Element


class TestDepthProfile(unittest.TestCase):
    def test_initialization(self):
        """Tests the initialization of a DepthProfile object"""
        dp = DepthProfile([1], [2])
        self.assertEqual([1], dp.depths)
        self.assertEqual([2], dp.concentrations)
        self.assertEqual([], dp.absolute_counts)
        self.assertEqual("total", dp.get_profile_name())

        # Currently the order of depth counts, or validity of
        # numerical values is not checked so following is ok.
        dp = DepthProfile([2, 1], [True, "Foo"])
        self.assertEqual([2, 1], dp.depths)
        self.assertEqual([True, "Foo"], dp.concentrations)

        dp = DepthProfile([1], [2], [3], element=Element.from_string("Si"))
        self.assertEqual([1], dp.depths)
        self.assertEqual([2], dp.concentrations)
        self.assertEqual([3], dp.absolute_counts)
        self.assertEqual("Si", dp.get_profile_name())

        self.assertRaises(ValueError,
                          lambda: DepthProfile([], [], [1]))
        self.assertRaises(ValueError,
                          lambda: DepthProfile([], [1], []))
        self.assertRaises(ValueError,
                          lambda: DepthProfile(
                              [1], [], [1], element=Element.from_string("Si")))
        self.assertRaises(ValueError,
                          lambda: DepthProfile(
                              [1], [1], [], element=Element.from_string("Si")))

    def test_bad_inputs(self):
        # Note: these behaviours may change in the future
        # Currently DepthProfile accepts non-numerical values that have __len__
        dp = DepthProfile("foo", "bar")
        self.assertEqual(dp.depths, "foo")
        self.assertEqual(dp.concentrations, "bar")

        # These can also be iterated over
        for val in dp:
            self.assertEqual(("f", "b", 0), val)
            break

        # Numerical operations such as calculating relative concentrations
        # will fail
        self.assertRaises(TypeError,
                          lambda: dp.get_relative_concentrations(dp))

    def test_iteration(self):
        """Tests that a DepthProfile object can be iterated over."""
        # Testing element profile
        dp = DepthProfile([i for i in range(10)],
                          [i for i in range(10, 20)],
                          [i for i in range(20, 30)],
                          element=Element.from_string("Si")
                          )

        x1 = (i for i in range(10))
        x2 = (i for i in range(10, 20))
        x3 = (i for i in range(20, 30))
        for val in dp:
            self.assertEqual((next(x1), next(x2), next(x3)), val)

        self.assertEqual(10, len(list(dp)))

        # Testing total profile
        dp = DepthProfile([i for i in range(10)],
                          [i for i in range(10, 20)],
                          [])

        x1 = (i for i in range(10))
        x2 = (i for i in range(10, 20))
        for val in dp:
            self.assertEqual((next(x1), next(x2), 0), val)

        self.assertEqual(10, len(list(dp)))


if __name__ == "__main__":
    unittest.main()
