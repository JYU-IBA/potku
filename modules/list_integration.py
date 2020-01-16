# coding=utf-8
"""
Created on 15.1.2020

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2018 TODO

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


def integrate(x_axis, y_axis, lim_a=-math.inf, lim_b=math.inf, t="concentrations"):
    """Integrates over a list.

    Args:
        x_axis: values on the x-axis
        y_axis: values on the y-axis
        lim_a: first value of the integration interval
        lim_b: last value of the integration interval
    """
    if t == "concentrations":
        return __integrate_concentrations(x_axis, y_axis, lim_a, lim_b)
    if t == "running_avgs":
        return __integrate_running_avgs(x_axis, y_axis, lim_a, lim_b)
    if t == "sums":
        return __sum_elements(x_axis, y_axis, lim_a, lim_b)
    raise NotImplemented("integration of type '{0}' not implemented".format(
        type))


def __integrate_concentrations(x_axis, y_axis, lim_a, lim_b):
    if len(x_axis) != len(y_axis):
        raise ValueError("x axis and y axis must have the same size.")

    # Need at least two x-values to calculate width
    if len(x_axis) <= 1:
        return 0.0

    total_sum = 0.0
    # For now, just assume that step_size is constant
    step_size = abs(x_axis[1] - x_axis[0])

    # TODO should iteration here start from first depth value or second?
    # TODO make sure that this is what we actually want to calculate
    # TODO test that floating point accuracy is good enough (maybe use
    #      Decimal
    # TODO maybe check that x_axis is in order
    for x_i, y_i in zip(x_axis, y_axis):
        if lim_a <= x_i < lim_b:
            total_sum += y_i
        elif x_i > lim_b > lim_a:
            total_sum += y_i
            break

    return total_sum * step_size


def __integrate_running_avgs(x_axis, y_axis, lim_a, lim_b):
    if len(x_axis) != len(y_axis):
        raise ValueError("x axis and y axis must have the same size.")

    if len(x_axis) == 0:
        return 0.0

    total_sum = 0.0
    prev_x = x_axis[0]
    prev_y = y_axis[0]

    for x_i, y_i in zip(x_axis, y_axis):
        if prev_x == x_i:
            continue

        if lim_a <= x_i <= lim_b:
            total_sum += (prev_y + y_i) / 2
        elif x_i > lim_b:
            total_sum += (prev_y + y_i) / 2
            break
        prev_x = x_i
        prev_y = y_i

    return total_sum


def __sum_elements(x_axis, y_axis, lim_a, lim_b):
    if len(x_axis) != len(y_axis):
        raise ValueError("x axis and y axis must have the same size.")

    total_sum = 0.0

    for x_i, y_i in zip(x_axis, y_axis):
        if lim_a <= x_i <= lim_b:
            total_sum += y_i
        elif x_i > lim_b:
            total_sum += y_i
            break

    return total_sum
