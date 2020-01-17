# coding=utf-8
"""
TODO
"""

import unittest

from modules.depth_files import DepthProfile, \
                                sanitize_depth_file_names
from modules.element import Element


class TestDepthProfile(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.default_total_profile = DepthProfile(
            [0, 1, 2], [10, 11, 12]
        )
        cls.default_elem_profile = DepthProfile(
            [0, 1, 2], [3, 4, 5], [6, 7, 8],
            element=Element.from_string("Si")
        )

    def test_initialization(self):
        """Tests the initialization of a DepthProfile object"""
        dp = DepthProfile([1], [2])
        self.assertEqual([1], dp.depths)
        self.assertEqual([2], dp.concentrations)
        self.assertIsNone(dp.events)
        self.assertEqual("total", dp.get_profile_name())

        # Currently the order of depth counts, or validity of
        # numerical values is not checked so following is ok.
        dp = DepthProfile([2, 1], [True, "Foo"])
        self.assertEqual([2, 1], dp.depths)
        self.assertEqual([True, "Foo"], dp.concentrations)

        dp = DepthProfile([1], [2], [3], element=Element.from_string("Si"))
        self.assertEqual([1], dp.depths)
        self.assertEqual([2], dp.concentrations)
        self.assertEqual([3], dp.events)
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

    def test_adding(self):
        dp1 = DepthProfile(
            [0, 1, 2], [10, 11, 12], [21, 22, 23], element=Element.from_string("Si"))
        dp2 = DepthProfile(
            [0, 1, 2], [15, 16, 17], [31, 32, 33], element=Element.from_string("C"))

        dp3 = dp1 + dp2
        self.assertIsInstance(dp3, DepthProfile)
        self.assertEqual(dp3.depths, [0, 1, 2])
        self.assertEqual(dp3.concentrations, [25, 27, 29])
        self.assertIsNone(dp3.events)
        self.assertEqual(dp3.get_profile_name(), "total")

        # DepthProfile can be incremented by another DepthProfile
        dp3 += dp3
        self.assertIsInstance(dp3, DepthProfile)
        self.assertEqual(dp3.depths, [0, 1, 2])
        self.assertEqual(dp3.concentrations, [50, 54, 58])
        self.assertIsNone(dp3.events)
        self.assertEqual(dp3.get_profile_name(), "total")

        # Arbitrary collection of lists cannot be added
        self.assertRaises(TypeError,
                          dp3 + ([0, 1, 2], [10, 11, 12], [21, 22, 23]))

    def test_subtraction(self):
        pass

    def test_merging(self):
        pass

    def test_identities(self):
        # Currently inputs are not being cloned when new depth profile is
        # created so when two profiles are added or merged, the depths
        # list of the new profile is the same instance as the first profile's
        # depth list
        dp1 = DepthProfile([0], [0])
        dp2 = DepthProfile([0], [0])

        self.assertIsNot(dp1.depths, dp2.depths)
        dp3 = dp1 + dp2
        self.assertIs(dp3.depths, dp1.depths)
        self.assertIsNot(dp3.concentrations, dp1.concentrations)


class TestDepthFiles(unittest.TestCase):
    def test_sanitizise_depth_files(self):
        # Testing with file names that are ok
        file_names = [
            "depth.total",
            "depth.Mn",
            "depth.10C"
        ]
        expected = {
            "total": "depth.total",
            "Mn": "depth.Mn",
            "10C": "depth.10C"
        }
        self.assertEqual(sanitize_depth_file_names(file_names), expected)

        # Invalid and duplicated strings are not included in the result
        file_names = [
            "depth.total",
            "depth.total",
            "Mn",
            "depth.10C"
        ]
        expected = {
            "total": "depth.total",
            "10C": "depth.10C"
        }
        self.assertEqual(sanitize_depth_file_names(file_names), expected)

        # Testing various invalid names
        file_names = [
            "depth.depth.total",
            "depth.",
            "depth",
            "depth.total.total",
            " depth.total",
            "\rdepth.total",
            ".depth.total",
            "depthh.total",
            "depth..total"
        ]
        expected = {}
        self.assertEqual(sanitize_depth_file_names(file_names), expected)

        # Function does not check if the file name is actually valid file name
        file_names = [
            "depth.!",
            "depth.|/foo\\bar"
        ]
        expected = {
            "!": "depth.!",
            "|/foo\\bar": "depth.|/foo\\bar"
        }
        self.assertEqual(sanitize_depth_file_names(file_names), expected)


if __name__ == "__main__":
    unittest.main()
