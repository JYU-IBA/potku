# coding=utf-8
"""
Created on 15.1.2020

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
__version__ = ""    # TODO

import math

from shapely.geometry import Polygon


def integrate_bins(x_axis, y_axis, a=-math.inf, b=math.inf,
                   step_size=None):
    """Calculates the closed integral between a and b for series
    of bins.

    Assumes that x_axis is in ascending order and that step size
    between bins is constant.

    Args:
        x_axis: values on the x axis
        y_axis: values on the y axis
        a: minimum x value in the range
        b: maximum x value in the range
        step_size: step size between each bin

    Return:
        integral between a and b
    """
    if len(x_axis) == 0:
        return 0.0

    if step_size is None:
        if len(x_axis) <= 1:
            raise ValueError("Need at least two x values to calculate "
                             "step size")
        # For now, just assume that step_size is constant and x axis
        # is in ascending order
        step_size = x_axis[1] - x_axis[0]

    # Return y values multiplied by step size
    return sum_y_values(x_axis, y_axis, a=a, b=b) * step_size


def sum_running_avgs(*args, a=-math.inf, b=math.inf, **kwargs):
    """Sums together 2-step running averages for y axis values over
    the range [a, b] on the x axis.

    Args:
        args: either a single collection of (x, y) values or x values and
            y values as separate collections.
        a: minimum x value in the range
        b: maximum x value in the range

    Return:
        sum of running averages on the y axis
    """
    return sum(y for (_, y) in calculate_running_avgs(*args, a=a, b=b,
                                                      **kwargs))


def sum_y_values(*args, a=-math.inf, b=math.inf, **kwargs):
    """Sums the values on y axis over the range [a, b] on the x axis.

    Args:
        args: either a single collection of (x, y) values or x values and
            y values as separate collections.
        a: minimum x value in the range
        b: maximum x value in the range

    Return:
        sum of y values within range
    """
    return sum(y for (_, y) in get_elements_in_range(*args, a=a, b=b,
                                                     **kwargs))


def calculate_running_avgs(*args, a=-math.inf, b=math.inf, **kwargs):
    """Generates 2-step running averages of y axis value over the
    range [a, b] on the x axis.

    Args:
        args: either a single collection of (x, y) values or x values and
            y values as separate collections.
        a: minimum x value in the range
        b: maximum x value in the range

    Yield:
        (x, y) tuples where y is the running average of current
        and previous y value
    """
    prev_y = 0
    for x, y in get_elements_in_range(*args, a=a, b=b, **kwargs):
        yield x, (prev_y + y) / 2
        prev_y = y


def get_elements_in_range(*args, a=-math.inf, b=math.inf,
                          include_before=False, include_after=True):
    """Generates (x, y) tuples from the given x and y values where the
    x value is in within the range defined by a and b.

    It is assumed that x axis is sorted in ascending order.

    Args:
        args: either a single collection of (x, y) values or x values and
            y values as separate collections.
        a: minimum x value in the range
        b: maximum x value in the range
        include_before: whether first (x, y) value before a is yielded.
        include_after: whether first (x, y) value after b is yielded.


    Yield:
        (x, y) tuple where x is within the range and y is the corresponding
        value on the y axis
    """
    if len(args) == 1:
        coords = args[0]
    else:
        coords = zip(args[0], args[1])

    if a > b:
        # If a is bigger than b, there are no values to yield
        return

    prev_point = None
    for x, y in coords:
        if x < a:
            prev_point = (x, y)
            continue
        elif x >= a and include_before and prev_point is not None:
            yield prev_point
            include_before = False

        if a <= x <= b:
            # Yield (x, y) when x is between a and b
            yield x, y

        elif x > b:
            if include_after:
                yield x, y
            return


def get_rounding_decimals(floater):
    """Find correct decimal count for rounding to 15-rule.
    """
    i = 0
    temp = floater
    if temp < 0.001:
        return 3
    while temp < 15:
        temp *= 10
        i += 1
    # At the index i the value is above 15 so return i - 1
    # for correct decimal count.
    return i - 1


def calculate_percentages(values, rounding=2):
    """Takes a collection of values and returns the percentage of total
    sum for each value with the given rounding precision.

    Args:
        values: collection of values (must not be a generator)
        rounding: rounding precision (2 by default)

    Return:
        list of percentages
    """
    total = sum(values)

    if not total:
        return [0 for _ in values]

    return [
        round(value / total * 100, rounding)
        for value in values
    ]


def get_continuous_range(*args, a=-math.inf, b=math.inf):
    """Yields (x, y) pairs that are between a and b.

    If a is between two points, the first pair in the range will be
    (a, f(a)) where f is a linear function given by the two points.

    Args:
        args: either a single collection of (x, y) values or x values and
            y values as separate collections.
        a: lower limit of the range.
        b: upper limit of the range.

    Yield:
        (x, y) pairs.
    """
    range_points = get_elements_in_range(*args, a=a, b=b,
                                         include_before=True,
                                         include_after=True)

    p_first, p_last = None, None
    for p in range_points:
        if p[0] < a:
            p_first = p
            p = next(range_points)
            if p[0] > a:
                p_last = calculate_new_point(p_first, p, a)
                yield p_last

        if p[0] <= b:
            p_last = p
            yield p

        elif p[0] > b and p_last is not None:
            if p_last[0] < b:
                yield calculate_new_point(p, p_last, b)
            return


def calculate_new_point(p1, p2, x):
    """Calculates a new point at position x given the other two points.

    Args:
        p1: point (tuple, list or a Point object)
        p2: point (tuple, list or a Point object)
        x: x value of the new point

    Return:
        tuple consisting of x and the calculated value of y
    """
    f = get_linear_function(p1, p2)
    return x, f(x)


def get_linear_function(p1, p2):
    """Returns a linear function from the given points p1 and p2.
    """
    try:
        k = (p2[1] - p1[1]) / (p2[0] - p1[0])
    except ZeroDivisionError:
        k = math.inf

    intercept = - k * p1[0] + p1[1]

    return lambda x: k * x + intercept


def calculate_area(line1, line2=None):
    """Calculates the area between the two lines or first line and
    x-axis if second line is None.

    It is assumed that both lines are arranged by x axis.

    Args:
        line1: collection of (x, y) values
        line2: collection of (x, y) values

    Return:
        area as a float.
    """
    # If points are empty, return 0
    if not line1:
        return 0.0
    if line2 is None:
        line2 = [(line1[0][0], 0), (line1[-1][0], 0)]

    # Add the first point again to close the polygon
    polygon_points = [*line1, *reversed(line2), line1[0]]

    polygon = Polygon(polygon_points)
    return polygon.area


def split_scientific_notation(x):
    """Formulates the given number x into scientific notation and returns
    the value part and the multiplier part as separate floats.
    """
    d = float(x)
    sn = "%e" % d
    val, multi = sn.split("e")
    return float(val), float(f"1e{multi}")
