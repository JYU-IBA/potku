# coding=utf-8
"""
Created on 23.3.2018
Updated on 5.6.2018

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

__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n" \
             "Sinikka Siironen"
__version__ = "2.0"


class Layer:
    """Class for a target or foil layer.
    """

    __slots__ = "name", "elements", "thickness", "density", "start_depth"

    def __init__(self, name, elements, thickness, density, start_depth=-1):
        """Initializes a target or foil layer.

        Args:
            name:            Name of the layer.
            elements:        A list of Element objects.
            thickness:       Thickness of the layer in nanometers.
            density:         Layer density.
            start_depth:     Depth where the layer starts.
        """
        self.name = name
        self.elements = elements
        self.thickness = thickness
        self.density = density
        self.start_depth = start_depth

    def click_is_inside(self, coordinate):
        """
        Check if given coordinate is inside layer.

        Args:
            coordinate: Coordinate to check.

        Return:
            True or False.
        """
        return self.start_depth < coordinate <= self.start_depth + \
        self.thickness
