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
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n " \
             "Sinikka Siironen"
__version__ = "2.0"


class Foil:
    """Class for detector foil and its information.
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
        self.name = name
        self.distance = distance
        self.layers = layers
        self.transmission = transmission


class CircularFoil(Foil):
    """ Class for circular detector foil and its information.
    """

    __slots__ = "diameter"

    def __init__(self, name="Default", diameter=0.0, distance=0.0, layers=None,
                 transmission=1.0):
        """ Initialize a circular detector foil.

        Args:
            name:         Name of the foil.
            diameter:     Diameter of the circular foil.
            distance:     Distance from the origin of the sample.
            layers:       Layers of the foil in a single list.
            transmission: Value that takes into account possible grids that
                          may make penetration smaller.
        """

        if layers is None:
            layers = []
        Foil.__init__(self, name, distance, layers, transmission)
        self.diameter = diameter


class RectangularFoil(Foil):
    """ Class for rectangular detector foil and its information.
    """

    __slots__ = "size"

    def __init__(self, name="", size_x=0.0, size_y=0.0, distance=0.0,
                 layers=None, transmission=1.0):
        """ Initialize a rectangular detector foil.

        Args:
            name:         Name of the foil.
            size_x:       Rectangular foil x width.
            size_y:       Rectangular foil y height.
            distance:     Distance from the origin of the sample.
            layers:       Layers of the foil in a single list.
            transmission: Value that takes into account possible grids that
                          may make penetration smaller.
        """

        if layers is None:
            layers = []
        Foil.__init__(self, name, distance, layers, transmission)
        self.size = (size_x, size_y)
