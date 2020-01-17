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

__author__ = ""     # TODO
__version__ = ""    # TODO

import math


def integrate_bins(x_axis, y_axis, a=-math.inf, b=math.inf):
    """Calculates the closed integral between a and b for series
    of bins.

    Assumes that x_axis is in order and that step size between
    bins is constant.

    Args:
        x_axis: values on the x-axis
        y_axis: values on the y-axis
        a: first x value of the integration interval
        b: last x value of the integration interval

    Return:
        integral between a and b
    """
    # TODO make sure that this is what we actually want to calculate
    # TODO test that floating point accuracy is good enough (maybe use
    #      Decimal)
    # TODO maybe change separate x- and y-axes into single list of
    #      (x, y) tuples
    total_sum = sum_elements(x_axis, y_axis, a, b)

    # Need at least two x-values to calculate width
    if len(x_axis) <= 1:
        return 0.0

    # For now, just assume that step_size is constant
    step_size = abs(x_axis[1] - x_axis[0])

    return total_sum * step_size


def sum_running_avgs(x_axis, y_axis, a=-math.inf, b=math.inf):
    """TODO"""
    if len(x_axis) != len(y_axis):
        raise ValueError("x axis and y axis must have the same size.")

    if len(x_axis) == 0:
        return 0.0

    total_sum = 0.0
    prev_x = x_axis[0]
    prev_y = y_axis[0]

    for x, y in zip(x_axis, y_axis):
        if prev_x == x:
            continue

        if a <= x <= b:
            total_sum += (prev_y + y) / 2
        elif x > b > a:
            total_sum += (prev_y + y) / 2
            break
        prev_x = x
        prev_y = y

    return total_sum


def sum_elements(x_axis, y_axis, a=-math.inf, b=math.inf):
    """TODO"""
    if len(x_axis) != len(y_axis):
        raise ValueError("x axis and y axis must have the same size.")

    if a > b:
        return 0.0

    total_sum = 0.0

    for x, y in zip(x_axis, y_axis):
        if a <= x <= b:
            total_sum += y
        elif x > b > a:
            total_sum += y
            break

    return total_sum
