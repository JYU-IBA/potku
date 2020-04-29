# coding=utf-8
"""
Created on TODO
Updated on 27.1.2020

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
import random
import numpy as np
import itertools
import math

from modules import math_functions as mf
from modules.point import Point


class TestListIntegration(unittest.TestCase):

    def test_bins_without_limits(self):
        """Tests integrate_bins function without limits"""

        # Empty lists return 0
        self.assertEqual(0, mf.integrate_bins([], []))

        # If x axis contains only one value, step size parameter
        # must be defined
        self.assertRaises(ValueError, lambda: mf.integrate_bins([0], [1]))
        self.assertEqual(10, mf.integrate_bins([0], [1], step_size=10))

        # Some regular integrals
        self.assertEqual(3, mf.integrate_bins([0, 1], [1, 2]))
        self.assertEqual(30, mf.integrate_bins([0, 10], [1, 2]))
        self.assertEqual(70, mf.integrate_bins([0, 10, 20], [1, 2, 4]))

        # Step size is calculated from first two bins. This can be overridden
        # with step size parameter
        self.assertEqual(30, mf.integrate_bins([0, 1], [1, 2], step_size=10))
        self.assertEqual(0, mf.integrate_bins([0, 10], [1, 2], step_size=0))
        self.assertEqual(-7, mf.integrate_bins([0, 10, 20], [1, 2, 4],
                                               step_size=-1))

    def test_uneven_axes(self):
        """Tests integrate_bins with uneven x and y axis sizes."""
        # Having uneven axis length does not matter as long as x axis
        # contains at least two values. Iteration stops, when the smaller
        # axis is exhausted.
        self.assertEqual(2, mf.integrate_bins([1, 2], [1, 1, 1]))
        self.assertEqual(1, mf.integrate_bins([1, 2, 3], [1]))

    def test_uneven_step_sizes(self):
        """Tests integrate_bins with uneven step sizes."""

        # Currently step size is assumed to be constant, so variations are
        # not taken into account. This may change in the future
        self.assertEqual(120,
                         mf.integrate_bins([0, 10, 300, 600], [1, 2, 4, 5]))

        # Negative first step negates all other bins. X axis is assumed
        # to be in ascending order, no checks are performed.
        self.assertEqual(-120,
                         mf.integrate_bins([0, -10, -300, 600], [1, 2, 4, 5]))

        # In similar vein, zero step size nullifies all other bins
        self.assertEqual(0, mf.integrate_bins([0, 0, -300, 600], [1, 2, 4, 5]))

    def test_bad_inputs(self):
        """Tests integrate_bins function with bad input values for x
        or y."""
        # Non-numerical values are included
        self.assertRaises(
            TypeError, lambda: mf.integrate_bins(["bar", "foo"], [1, 2]))
        self.assertRaises(
            TypeError, lambda: mf.integrate_bins([1, 1], ["foo", "bar"]))

        # Note that this will still work as strings are not in the integral
        # range
        self.assertEqual(20, mf.integrate_bins([0, 1, 2, "foo"],
                                               ["foo", 10, 10, 10],
                                               a=1, b=1))

    def test_integrating_with_limits(self):
        """Tests integrate_bins function with set limit values
        """
        x_axis = [0, 1, 2, 3, 4, 5]
        y_axis = [10, 10, 10, 10, 10]

        self.assertEqual(50, mf.integrate_bins(x_axis, y_axis, a=0, b=4.5))
        self.assertEqual(20, mf.integrate_bins(x_axis, y_axis, a=3, b=3))
        # Values before a are not included in the integral, but first
        # value after b is
        self.assertEqual(30, mf.integrate_bins(x_axis, y_axis, a=1.5, b=3.5))
        self.assertEqual(30, mf.integrate_bins(x_axis, y_axis, a=2, b=3))
        self.assertEqual(30, mf.integrate_bins(x_axis, y_axis, a=1.5, b=3))
        self.assertEqual(30, mf.integrate_bins(x_axis, y_axis, a=2, b=3.5))

        # Turning limits around returns 0,
        self.assertEqual(0, mf.integrate_bins(x_axis, y_axis, a=3, b=2))

        # as well as integrating outside the range
        self.assertEqual(0, mf.integrate_bins(x_axis, y_axis, a=10, b=15))
        self.assertEqual(0, mf.integrate_bins(x_axis, y_axis, a=-10, b=-15))

    def test_sum_y_values(self):
        """Tests sum_y_values function"""
        x_axis = [0, 1, 2, 3, 4, 5]
        y_axis = [10, 11, 12, 13, 14, 15]

        # Without limits, sum_y_values is same as sum
        self.assertEqual(sum(y_axis), mf.sum_y_values(x_axis, y_axis))

        self.assertEqual(29, mf.sum_y_values(x_axis, y_axis, a=4))
        self.assertEqual(21, mf.sum_y_values(x_axis, y_axis, b=0))
        self.assertEqual(50, mf.sum_y_values(x_axis, y_axis, a=1, b=3))

        self.assertEqual(12, mf.sum_y_values(x_axis, y_axis, a=1.5, b=1.5))
        self.assertEqual(0, mf.sum_y_values(x_axis, y_axis, a=2, b=1))

    def test_sum_running_avgs(self):
        """Tests sum_running_avgs function"""
        x_axis = [0, 1, 2]
        y_axis = [10, 11, 12]
        self.assertEqual(27, mf.sum_running_avgs(x_axis, y_axis))
        self.assertEqual(0, mf.sum_running_avgs(x_axis, y_axis, a=2, b=1))
        self.assertEqual(0, mf.sum_running_avgs(x_axis, y_axis, a=10))

    def test_calculate_running_avgs(self):
        """Tests calculate_running_avgs function"""
        x_axis = [0, 1, 2]
        y_axis = [10, 11, 12]

        self.assertEqual([(0, 5), (1, 10.5), (2, 11.5)],
                         list(mf.calculate_running_avgs(x_axis, y_axis)))

        self.assertEqual([(1, 5.5), (2, 11.5)],
                         list(mf.calculate_running_avgs(x_axis, y_axis, a=1)))

        self.assertEqual([(0, 5), (1, 10.5)],
                         list(mf.calculate_running_avgs(x_axis, y_axis, b=0)))

        self.assertEqual([(0, 5)],
                         list(mf.calculate_running_avgs(x_axis, y_axis, b=-1)))

        self.assertEqual([],
                         list(mf.calculate_running_avgs(x_axis, y_axis, a=100)))

    def test_get_elements_in_range(self):
        """Tests get_elements_in_range function"""
        x_axis = [0, 1, 2, 3, 4, 5]
        y_axis = [10, 11, 12, 13, 14, 15]

        # Without limits, get_elements_in_range is the same as zip
        self.assertEqual(list(zip(x_axis, y_axis)),
                         list(mf.get_elements_in_range(x_axis, y_axis)))

        # If a > b, nothing is returned
        self.assertEqual([],
                         list(mf.get_elements_in_range(x_axis, y_axis,
                                                       a=2, b=1)))

        # First element after b is also returned by default,
        self.assertEqual([(0, 10)],
                         list(mf.get_elements_in_range(x_axis, y_axis,
                                                       b=-100)))

        # whereas first before a is not
        self.assertEqual([],
                         list(mf.get_elements_in_range(x_axis, y_axis,
                                                       a=100)))

        # Limits can be set for only a or b
        self.assertEqual([(0, 10), (1, 11), (2, 12), (3, 13)],
                         list(mf.get_elements_in_range(x_axis, y_axis,
                                                       b=2)))

        self.assertEqual([(3, 13), (4, 14), (5, 15)],
                         list(mf.get_elements_in_range(x_axis, y_axis,
                                                       a=3)))

    def test_inclusion(self):
        x_axis = [0, 1, 2]
        y_axis = [1, 1, 1]
        # Tests for a = b = 0.5
        self.assertEqual([],
                         list(mf.get_elements_in_range(x_axis, y_axis,
                                                       a=0.5, b=0.5,
                                                       include_after=False,
                                                       include_before=False)))

        self.assertEqual([(0, 1)],
                         list(mf.get_elements_in_range(x_axis, y_axis,
                                                       a=0.5, b=0.5,
                                                       include_after=False,
                                                       include_before=True)))

        self.assertEqual([(1, 1)],
                         list(mf.get_elements_in_range(x_axis, y_axis,
                                                       a=0.5, b=0.5,
                                                       include_after=True,
                                                       include_before=False)))

        self.assertEqual([(0, 1), (1, 1)],
                         list(mf.get_elements_in_range(x_axis, y_axis,
                                                       a=0.5, b=0.5,
                                                       include_after=True,
                                                       include_before=True)))

        # Tests for a = b = 1
        self.assertEqual([(1, 1)],
                         list(mf.get_elements_in_range(x_axis, y_axis,
                                                       a=1, b=1,
                                                       include_after=False,
                                                       include_before=False)))

        self.assertEqual([(0, 1), (1, 1)],
                         list(mf.get_elements_in_range(x_axis, y_axis,
                                                       a=1, b=1,
                                                       include_after=False,
                                                       include_before=True)))

        self.assertEqual([(1, 1), (2, 1)],
                         list(mf.get_elements_in_range(x_axis, y_axis,
                                                       a=1, b=1,
                                                       include_after=True,
                                                       include_before=False)))

    def test_nonnumerical(self):
        # Function works for any x values that can be compared
        x_axis_str = ["a", "b", "c"]
        y_axis_str = [True, False, None]
        self.assertEqual([("a", True), ("b", False)],
                         list(mf.get_elements_in_range(x_axis_str, y_axis_str,
                                                       a="a", b="a")))

    def test_incomparable_element_ranges(self):
        # TypeError is raised if the range generator has to compare
        # objects that cannot be compared with each other (such as
        # str to int)
        x_axis = [0, 1, 2, 3, "foo", 5]
        y_axis = [10, "foo", "bar", 13, 14, 15]
        self.assertRaises(TypeError,
                          lambda: list(mf.get_elements_in_range(x_axis,
                                                                y_axis)))

        self.assertRaises(TypeError,
                          lambda: list(mf.get_elements_in_range(x_axis,
                                                                y_axis,
                                                                a=2,
                                                                b=3)))

        # Note that this will work as iteration stops before reaching an
        # incomparable value
        self.assertEqual(
            [(0, 10), (1, "foo"), (2, "bar"), (3, 13)],
            list(mf.get_elements_in_range(x_axis, y_axis, b=2))
        )


class TestPercentage(unittest.TestCase):
    def test_calculate_percentages(self):
        self.assertEqual([], mf.calculate_percentages([]))
        self.assertEqual([0], mf.calculate_percentages([0]))
        self.assertEqual([100], mf.calculate_percentages([1]))
        self.assertEqual([50, 50], mf.calculate_percentages([1, 1]))
        self.assertEqual([33.33, 66.67], mf.calculate_percentages([1, 2]))
        self.assertEqual([25, 25, 25, 25],
                         mf.calculate_percentages([1, 1, 1, 1]))

    def test_rounding_percentages(self):
        self.assertEqual([33, 67], mf.calculate_percentages([1, 2], rounding=0))
        self.assertEqual([33.3, 66.7],
                         mf.calculate_percentages([1, 2], rounding=1))
        self.assertEqual([33.33333, 66.66667],
                         mf.calculate_percentages([1, 2], rounding=5))

    def test_negative_values(self):
        # Calculating percentages with negative values is somewhat
        # counter-intuitive. Someone could take a look at it.
        self.assertEqual([100], mf.calculate_percentages([-1]))
        self.assertEqual([100, 0], mf.calculate_percentages([-1, 0]))
        self.assertEqual([0, 0], mf.calculate_percentages([-1, 1]))
        self.assertEqual([-100, 200], mf.calculate_percentages([-1, 2]))

    def test_calculate_percentages_prop_based(self):
        # property based testing
        max_count = 100
        iterations = 100
        for _ in range(iterations):
            count = random.randint(0, max_count)
            values = [random.random() for _ in range(count)]
            results = mf.calculate_percentages(values)
            self.assertEqual(count, len(results))
            for r in results:
                self.assertTrue(0 <= r <= 100)


class TestContinuousRange(unittest.TestCase):
    """Tests for continuous range and the area calculation that uses
    continuous range.
    """
    def test_continuous_range(self):
        xs = [i for i in range(4)]
        ys = list(xs)

        self.assertEqual(
            list(zip(xs, ys)),
            list(mf.get_continuous_range(xs, ys)))

        self.assertEqual(
            [],
            list(mf.get_continuous_range(xs, ys, a=5, b=12)))

        self.assertEqual(
            [],
            list(mf.get_continuous_range(xs, ys, a=2, b=1)))

        self.assertEqual(
            [(0, 0)],
            list(mf.get_continuous_range(xs, ys, a=0, b=0)))

        self.assertEqual(
            [(0, 0)],
            list(mf.get_continuous_range(xs, ys, a=-1, b=0)))

        self.assertEqual(
            [(0, 0), (0.25, 0.25)],
            list(mf.get_continuous_range(xs, ys, a=-1, b=0.25)))

        self.assertEqual(
            [(3, 3)],
            list(mf.get_continuous_range(xs, ys, a=3, b=4)))

        self.assertEqual(
            [(2.3, 2.3)],
            list(mf.get_continuous_range(xs, ys, a=2.3, b=2.3)))

        self.assertEqual(
            [(2.3, 2.3), (2.5, 2.5)],
            list(mf.get_continuous_range(xs, ys, a=2.3, b=2.5)))

        self.assertEqual(
            [(2.3, 2.3), (3, 3)],
            list(mf.get_continuous_range(xs, ys, a=2.3, b=3.5)))

    def test_calculate_area(self):
        # Test with single line
        self.assertEqual(0, mf.calculate_area([]))
        self.assertEqual(0, mf.calculate_area([(1, 1)]))
        self.assertEqual(1, mf.calculate_area([(0, 1), (1, 1)]))
        self.assertEqual(2, mf.calculate_area([(0, 1), (1, 1), (2, 1)]))
        self.assertEqual(2.5, mf.calculate_area([(0, 1), (1, 1), (2, 2)]))
        self.assertEqual(0.5, mf.calculate_area([(0, -1), (1, 2)]))

        # Test with two lines.
        self.assertEqual(0, mf.calculate_area([], []))

        # Area of a line (= 0)
        self.assertEqual(0, mf.calculate_area([(0, 1), (1, 1)], []))
        self.assertEqual(0, mf.calculate_area([(1, 1)], [(0, 0)]))

        # Area of a rectangle
        self.assertEqual(2, mf.calculate_area([(0, 1), (1, 1)],
                                              [(-1, -1), (0, -1)]))

        # Area of a triangle
        self.assertEqual(0.5, mf.calculate_area([(0, 1), (1, 1)], [(0.5, 0)]))
        self.assertEqual(0.5, mf.calculate_area([(0, 1), (1, 1), (1, 0)], []))


class TestPropertyBased(unittest.TestCase):
    """Various property based tests.
    """

    def test_get_elements_in_range(self):
        """Tests that providing the x and y values as a single list is the
        same as providing them as separate lists when getting elements from
        range."""
        self.assert_range_function_equal(mf.get_elements_in_range,
                                         add_inclusions=True)
        self.assert_range_function_equal(mf.get_continuous_range)

    def assert_range_function_equal(self, range_function, add_inclusions=False):
        """Asserts that the given range_function returns the same values
        when arguments are either separate lists of x and y values, a single
        list of tuples or a single list of Points.
        """
        iterations = 10
        n = 100
        for _ in range(iterations):
            kwargs = {
                "a": np.random.random(),
                "b": np.random.random()
            }
            if add_inclusions:
                kwargs.update({
                    "include_before": np.random.random() > 0.5,
                    "include_after": np.random.random() > 0.5
                })

            x_axis = sorted(np.random.random_sample(n))
            y_axis = np.random.random_sample(n)
            zipped = list(zip(x_axis, y_axis))
            points = [Point(x, y) for x, y in zipped]

            points_in_range = list(range_function(points, **kwargs))
            self.assertEqual(points_in_range,
                             list(range_function(x_axis, y_axis, **kwargs)))

            self.assertEqual(points_in_range,
                             list(range_function(zipped, **kwargs)))


class TestMisc(unittest.TestCase):
    def test_split_scientific_notation(self):
        self.assertEqual((2, 1e10), mf.split_scientific_notation(2e10))
        self.assertEqual((3.123, 1e-11), mf.split_scientific_notation(
            3.123e-11))
        self.assertEqual((4.321, 1e14), mf.split_scientific_notation(432.1e+12))
        self.assertEqual((5, 1e13), mf.split_scientific_notation(5E13))

        self.assertEqual((2, 1e0), mf.split_scientific_notation(2))

        self.assertRaises(ValueError,
                          lambda: mf.split_scientific_notation("2e2e2"))


class TestPointInside(unittest.TestCase):
    # TODO do a performance test and compare current implementation to numpy
    #   or shapely
    def test_bad_inputs(self):
        self.assertRaises(IndexError,
                          lambda: mf.point_inside_polygon(Point(0, 0), []))

        square = [
            (0, 0), (0, 1), (1, 1), (1, 0)
        ]
        self.assertRaises(ValueError,
                          lambda: mf.point_inside_polygon([], square))
        self.assertRaises(ValueError,
                          lambda: mf.point_inside_polygon([1, 2, 3], square))

    def test_point_and_straight(self):
        self.assertFalse(mf.point_inside_polygon(Point(0, 0), [Point(0, 0)]))
        self.assertFalse(mf.point_inside_polygon(Point(0, 0),
                                                 [Point(-1, 0), Point(1, 0)]))

    def test_triangle(self):
        triangle = (
            Point(0, 0), Point(10, 10), Point(20, 0)
        )
        self.assertTrue(mf.point_inside_polygon(Point(10, 5), triangle))
        self.assertFalse(mf.point_inside_polygon(Point(5, 5), triangle))
        self.assertFalse(mf.point_inside_polygon(Point(20, 5), triangle))

        self.assertFalse(mf.point_inside_polygon(Point(20, 0), triangle))

    def test_rectangle(self):
        rectangle = (
            Point(0, 0),
            Point(1, 1),
            Point(2, 1),
            Point(1, 0)
        )
        self.assertFalse(mf.point_inside_polygon(Point(0, 0), rectangle))
        self.assertFalse(mf.point_inside_polygon(Point(1, 0), rectangle))
        self.assertFalse(mf.point_inside_polygon(Point(1, 1), rectangle))

        # TODO why are these two True?
        self.assertTrue(mf.point_inside_polygon(Point(1.5, 1), rectangle))
        self.assertTrue(mf.point_inside_polygon(Point(2, 1), rectangle))

        self.assertTrue(mf.point_inside_polygon(Point(1, 0.5), rectangle))
        self.assertTrue(mf.point_inside_polygon(Point(1.5, 0.8), rectangle))

        self.assertFalse(mf.point_inside_polygon(Point(0, 0.25), rectangle))
        self.assertFalse(mf.point_inside_polygon(Point(0.5, -0.1), rectangle))
        self.assertFalse(mf.point_inside_polygon(Point(1.5, 0.25), rectangle))


class TestBinCounts(unittest.TestCase):
    def setUp(self):
        a, b = 0, 100
        n = 50
        dim = 2
        self.unsorted_data = [
            [random.uniform(a, b) for _ in range(n)] for _ in range(dim)
        ]
        # Make sure that list contains min and max values
        for lst in self.unsorted_data:
            idx_a, idx_b = random.sample(range(0, n), 2)
            lst[idx_a] = a
            lst[idx_b] = b
        self.asc_sorted_data = [
            sorted(lst) for lst in self.unsorted_data
        ]
        self.desc_sorted_data = [
            list(reversed(lst)) for lst in self.asc_sorted_data
        ]
        self.all_data = [
            self.unsorted_data, self.asc_sorted_data, self.desc_sorted_data
        ]

    def test_calculate_bins(self):
        kwargs = {
            "comp_x": 10,
            "comp_y": 20
        }
        self.assertEqual(((10, 5), None), mf.calculate_bin_counts(
            self.unsorted_data, **kwargs
        ))
        self.assert_all_equal(
            lambda data: mf.calculate_bin_counts(data, **kwargs),
            self.all_data
        )

    def test_max_count(self):
        kwargs = {
            "comp_x": 5,
            "comp_y": 10,
            "max_count": 15
        }
        self.assertEqual(
            ((15, 10), "Bin count exceeded maximum value of 15. Adjustment "
                       "made."),
            mf.calculate_bin_counts(self.unsorted_data, **kwargs))

        self.assert_all_equal(
            lambda data: mf.calculate_bin_counts(data, **kwargs),
            self.all_data
        )

    def test_min_count(self):
        kwargs = {
            "comp_x": 5,
            "comp_y": 10,
            "min_count": 15
        }
        self.assertEqual(((20, 15), None), mf.calculate_bin_counts(
            self.unsorted_data, **kwargs
        ))
        self.assert_all_equal(
            lambda data: mf.calculate_bin_counts(data, **kwargs),
            self.all_data
        )

    def test_sorted_count(self):
        kwargs = {
            "comp_x": 10,
            "comp_y": 10,
            "data_sorted": True
        }
        expected_x = int(math.fabs(self.unsorted_data[0][0] -
                                   self.unsorted_data[0][-1]) / 10)
        expected_y = int(math.fabs(self.unsorted_data[1][0] -
                                   self.unsorted_data[1][-1]) / 10)

        if not expected_x:
            expected_x = 1
        if not expected_y:
            expected_y = 1

        self.assertEqual(((expected_x, expected_y), None),
                         mf.calculate_bin_counts(self.unsorted_data, **kwargs))

        self.assert_all_equal(
            lambda data: mf.calculate_bin_counts(data, **kwargs),
            [self.asc_sorted_data, self.desc_sorted_data]
        )

    def test_bad_inputs(self):
        self.assertRaises(
            ValueError,
            lambda: mf.calculate_bin_counts(self.unsorted_data, 0, 0))

        self.assertRaises(
            ValueError,
            lambda: mf.calculate_bin_counts(self.unsorted_data, 10, -1))

        self.assertRaises(
            ValueError,
            lambda: mf.calculate_bin_counts(self.unsorted_data, 1, 1,
                                            min_count=20, max_count=10))

    def test_empty_list(self):
        self.assertEqual(((1, 1), None),
                         mf.calculate_bin_counts([[1], []], 1, 1))

    def test_return_type(self):
        # bin counts should always be integers
        n = 10
        for _ in range(n):
            kwargs = {
                "data": [
                    [random.random() for _ in range(20)],
                    [random.random() for _ in range(20)]
                ],
                "comp_x": random.random(),
                "comp_y": random.random(),
                "min_count": random.uniform(5.5, 15.5),
                "max_count": random.uniform(25.5, 35.5),
                "data_sorted": random.random() > 0.5
            }
            (x_bins, y_bins), _ = mf.calculate_bin_counts(**kwargs)
            self.assertIsInstance(x_bins, int)
            self.assertIsInstance(y_bins, int)

    def assert_all_equal(self, func, data_sets):
        bins = [func(ds) for ds in data_sets]
        self.assertTrue(all(x == y for x, y in itertools.combinations(bins, 2)))


if __name__ == "__main__":
    unittest.main()
