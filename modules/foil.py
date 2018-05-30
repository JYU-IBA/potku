# coding=utf-8
# TODO: Add licence information
"""
Created on 23.3.2018
Updated on 2.5.2018
"""
from json import JSONEncoder

from modules.layer import Layer

__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n " \
             "Sinikka Siironen"
__version__ = "2.0"


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
        self.name = name
        self.distance = distance
        self.layers = layers
        self.transmission = transmission


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

        if layers is None:
            layers = []
        Foil.__init__(self, name, distance, layers, transmission)
        self.diameter = diameter


class RectangularFoil(Foil):
    """ Class for rectangular detector foil.
    """

    __slots__ = "size"

    def __init__(self, name="", size_x=0.0, size_y=0.0, distance=0.0, layers=None,
                 transmission=1.0):
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

        if layers is None:
            layers = []
        Foil.__init__(self, name, distance, layers, transmission)
        self.size = (size_x, size_y)
