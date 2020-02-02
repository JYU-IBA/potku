# coding=utf-8
"""
Created on 23.3.2018
Updated on 2.5.2018

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
             "Sinikka Siironen \n Juhani Sundell"
__version__ = "2.0"

import math

# Unit conversion values for solid angle
#   sr: steradian
#   msr: millisteradian
#   usr: microsteradian ('u' is a stand-in for the lower case 'Mu')
_UNITS = {
    "sr": 1,
    "msr": 1000,
    "usr": 1000000
}


class Foil:
    """Class for detector foil.
    """

    __slots__ = "name", "distance", "layers", "transmission"

    def __init__(self, name, distance, layers, transmission):
        """ Initialize a detector foil.

        Args:
            name:         Name of the foil
            distance:     Distance from the origin of the sample.
            layers:       Layers of the foil in a single list.
            transmission: Value that takes into account possible grids that
                          may make penetration smaller.
        """
        if layers is None:
            layers = []

        self.name = name
        self.distance = distance
        self.layers = layers
        self.transmission = transmission

    def get_solid_angle(self, units="msr"):
        raise NotImplementedError


class CircularFoil(Foil):
    """ Class for circular detector foil.
    """

    __slots__ = "diameter"

    def __init__(self, name="Default", diameter=0.0, distance=0.0, layers=None,
                 transmission=1.0):
        """ Initialize a circular detector foil.

        Args:
            diameter:     Diameter of the circular foil.
            distance:     Distance from the origin of the sample.
            layers:       Layers of the foil in a single list.
            transmission: Value that takes into account possible grids that
                          may make penetration smaller.
        """

        Foil.__init__(self, name, distance, layers, transmission)
        self.diameter = diameter

    def get_radius(self):
        """Returns the radius of the circular detector foil.
        """
        return self.diameter / 2

    def get_solid_angle(self, units="msr"):
        """TODO"""
        if units not in _UNITS:
            raise ValueError("Unexpected unit for solid angle")
        return math.pi * self.get_radius()**2 / self.distance**2 \
            * _UNITS[units]


class RectangularFoil(Foil):
    """ Class for rectangular detector foil.
    """

    __slots__ = "size"

    def __init__(self, name="", size_x=0.0, size_y=0.0, distance=0.0,
                 layers=None, transmission=1.0):
        """ Initialize a rectangular detector foil.

        Args:
            name:         Nama of the foil.
            size_x:       Rectangular foil x width.
            size_y:       Rectangular foil y height.
            distance:     Distance from the origin of the sample.
            layers:       Layers of the foil in a single list.
            transmission: Value that takes into account possible grids that
                          may make penetration smaller.
        """

        Foil.__init__(self, name, distance, layers, transmission)
        self.size = (size_x, size_y)

    def get_solid_angle(self, units="msr"):
        """TODO"""
        if units not in _UNITS:
            raise ValueError("Unexpected unit for solid angle")
        return self.size[0] * self.size[1] / self.distance**2 \
            * _UNITS[units]
