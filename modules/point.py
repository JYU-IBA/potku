# coding=utf-8
"""
Created on 1.3.2018
Updated on 24.8.2018

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2018 Severi Jääskeläinen, Samuel Kaiponen, Heta Rekilä and
Sinikka Siironen

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
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n " \
             "Sinikka Siironen"
__version__ = "2.0"

import modules.math_functions as mf


class Point:
    """A 2D point with x and y coordinates."""
    def __init__(self, *xy):
        """Inits point.

        Args:
            xy: The x and y coordinates of the point. An ordered data structure
             whose first element is the x coordinate and second element
             the y coordinate. Or x and y as separate parameters.
        """
        # TODO: Precision
        if len(xy) == 1:
            xy = xy[0]
        self._x = xy[0]
        self._y = xy[1]

    def __lt__(self, other):
        """
        Return if other's x is bigger.

        Args:
            other: Other point.

        Return:
            True or False.
        """
        if not isinstance(other, Point):
            return NotImplemented

        return self.get_x() < other.get_x()

    def __eq__(self, other):
        """Compares the Point to another Point and returns True if they
        are the same, False otherwise.
        """
        if not isinstance(other, Point):
            return NotImplemented

        return vars(self) == vars(other)

    def __repr__(self):
        """Returns a string representation of the Point object.
        """
        return f"Point{repr(self.get_coordinates())}"

    def __str__(self):
        """Returns a string representation of a point with rounded decimals.
        """
        return f"{round(self.get_x(), 2)} {round(self.get_y(), 4)}"

    def __iter__(self):
        """Iterable interface for Point.
        """
        return iter(self.get_coordinates())

    def __getitem__(self, item):
        """Makes the Point object subscriptable, meaning that x and y values can
        be looked up in similar way as values in a list or dict (i.e. p[0]
        or p["x"]).
        """
        if item == 0 or item == "x":
            return self.get_x()
        if item == 1 or item == "y":
            return self.get_y()

        raise ValueError("Unknown key or index")

    def __len__(self):
        """This is a 2D point so always return 2.
        """
        return 2

    def get_coordinates(self):
        """
        Get point coordinates.

        Return:
             Coordinates.
        """
        return self._x, self._y

    def get_x(self):
        """
        Get point's x coordinate.

        Return:
            X coordinate.
        """
        return self._x

    def get_y(self):
        """
         Get point's y coordinate.

        Return:
             Y coordinate.
        """
        return self._y

    def set_x(self, x):
        """
        Set point's x coordinate.

        Args:
             x: X coordinate.
        """
        self._x = x

    def set_y(self, y):
        """
        Set point's y coordinate.

        Args:
             y: Y coordinate.
        """
        self._y = y

    def set_coordinates(self, xy):
        """
        Set point's coordinates.

        Args:
            xy: Point's x and y coordinates.
        """
        self._x = xy[0]
        self._y = xy[1]

    def calculate_new_point(self, other, x):
        """Returns a new point at position x on a line that goes trough
        self and other point.

        Args:
            other: Point object.
            x: position on x axis

        Return:
            Point object.
        """
        if not isinstance(other, Point):
            return NotImplemented

        return Point(mf.calculate_new_point(self, other, x))

    def get_mcerd_params(self):
        """Returns a string representation of the point as used in MCERD
        simulation.
        """
        return f"{round(self.get_x(), 2)} {round(self.get_y(), 4)}"
