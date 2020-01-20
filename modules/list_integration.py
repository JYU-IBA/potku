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
    return sum_y_values(x_axis, y_axis, a, b) * step_size


def sum_running_avgs(x_axis, y_axis, a=-math.inf, b=math.inf):
    """Sums together 2-step running averages for y axis values over
    the range [a, b] on the x axis.

    Args:
        x_axis: values on the x axis
        y_axis: values on the y axis
        a: minimum x value in the range
        b: maximum x value in the range

    Return:
        sum of running averages on the y axis
    """
    return sum(y for (_, y) in calculate_running_avgs(x_axis, y_axis, a, b))


def sum_y_values(x_axis, y_axis, a=-math.inf, b=math.inf):
    """Sums the values on y axis over the range [a, b] on the x axis.

    Args:
        x_axis: values on the x axis
        y_axis: values on the y axis
        a: minimum x value in the range
        b: maximum x value in the range

    Return:
        sum of y values within range
    """
    return sum(y for (_, y) in get_elements_in_range(x_axis, y_axis, a, b))


def calculate_running_avgs(x_axis, y_axis, a=-math.inf, b=math.inf):
    """Generates 2-step running averages of y axis value over the
    range [a, b] on the x axis.

    Args:
        x_axis: values on the x axis
        y_axis: values on the y axis
        a: minimum x value in the range
        b: maximum x value in the range

    Yield:
        (x, y) tuples where y is the running average of current
        and previous y value
    """
    # TODO currently prev_y is always 0 for the first element in range,
    #      even though data can contain y values before it. This may need
    #      to be fixed
    prev_y = 0
    for x, y in get_elements_in_range(x_axis, y_axis, a, b):
        yield x, (prev_y + y) / 2
        prev_y = y


def get_elements_in_range(x_axis, y_axis, a=-math.inf, b=math.inf):
    """Generates (x, y) tuples from the given x and y values where the
    x value is in within the range defined by a and b.

    It is assumed that x axis is sorted in ascending order.

    Args:
        x_axis: values on the x axis
        y_axis: values on the y axis
        a: minimum x value in the range
        b: maximum x value in the range

    Yield:
        (x, y) tuple where x is within the range and y is the corresponding
        value on the y axis
    """
    # TODO maybe add parameters such as inclusive/exclusive range
    # TODO instead of separate x and y axis, values could be provided
    #      as a single tuple
    if a > b:
        # If a is bigger than b, there are no values to yield
        return

    for x, y in zip(x_axis, y_axis):
        if a <= x <= b:
            # Yield (x, y) when x is between a and b
            yield x, y
        elif x > b:
            # Also yield the first (x, y) where x is bigger
            # than b. Then stop.
            # TODO this follows the original logic that was used
            #      in depth profile calculations. Check if this
            #      needs to be revised
            yield x, y
            return
