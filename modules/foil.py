# coding=utf-8
"""
Created on 23.3.2018
Updated on 8.2.2020

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2018 Severi Jääskeläinen, Samuel Kaiponen, Heta Rekilä and
Sinikka Siironen, 2020 Juhani Sundell

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

from .base import MCERDParameterContainer


# Unit conversion values for solid angle
#   sr: steradian
#   msr: millisteradian
#   usr: microsteradian ('u' is a stand-in for the lower case 'Mu')
_UNITS = {
    "sr": 1,
    "msr": 1000,
    "usr": 1000000
}


class Foil(MCERDParameterContainer):
    """Class for detector foil.
    """

    __slots__ = "name", "distance", "layers", "transmission"

    TYPE = None

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
        """TODO"""
        raise NotImplementedError

    def get_mcerd_params(self):
        """Returns a list of strings that are passed as parameters for MCERD.
        """
        raise NotImplementedError

    def to_dict(self):
        """Returns the foil as a dict.
        """
        return {
            "name": self.name,
            "type": self.TYPE,
            "distance": self.distance,
            "layers": [layer.to_dict() for layer in self.layers],
            "transmission": self.transmission
        }

    @staticmethod
    def generate_foil(type, **kwargs):
        """Factory method for initializing Foil objects.

        Args:
            type: type of the foil (either 'circular' or 'rectangular'
            kwargs: keyword arguments passed down to foil

        Return:
            either a CircularFoil or RectangularFoil
        """
        if type == RectangularFoil.TYPE:
            if "size" in kwargs:
                x, y = kwargs.pop("size")
                kwargs["size_x"] = x
                kwargs["size_y"] = y
            return RectangularFoil(**kwargs)
        if type == CircularFoil.TYPE:
            return CircularFoil(**kwargs)
        raise ValueError(f"Unknown foil type: {type}")


class CircularFoil(Foil):
    """ Class for circular detector foil.
    """

    __slots__ = "diameter"
    TYPE = "circular"

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

    def get_mcerd_params(self):
        """Returns a list of strings that are passed as parameters for MCERD.
        """
        return [
            "Foil type: circular",
            f"Foil diameter: {self.diameter}",
            f"Foil distance: {self.distance}"
        ]

    def to_dict(self):
        d = super().to_dict()
        d["diameter"] = self.diameter
        return d


class RectangularFoil(Foil):
    """ Class for rectangular detector foil.
    """

    __slots__ = "size"
    TYPE = "rectangular"

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

    def get_mcerd_params(self):
        """Returns a list of strings that are passed as parameters for MCERD.
        """
        return [
            f"Foil type: {self.TYPE}",
            f"Foil size: {'%0.1f %0.1f' % self.size}",
            f"Foil distance: {self.distance}"
        ]

    def to_dict(self):
        d = super().to_dict()
        d["size"] = self.size
        return d
