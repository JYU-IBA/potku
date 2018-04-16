# coding=utf-8
# TODO: Add licence information
"""
Created on 23.3.2018
Updated on 13.4.2018
"""
from json import JSONEncoder

from modules.layer import Layer

__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n " \
             "Sinikka Siironen"
__versio__ = "2.0"


class FoilEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Foil):
            foil_dict = {
                "name": obj.name,
                "distance": obj.distance,
                # TODO Layer attributes
                "layers": [],
                "transmission": obj.transmission,
            }
            if isinstance(obj, CircularFoil):
                foil_dict["size"] = obj.diameter
            if isinstance(obj, RectangularFoil):
                foil_dict["size"] = obj.size
            return foil_dict
        return super(FoilEncoder, self).default(obj)


class Foil:
    """Class for detector foil.
    """

    __slots__ = "name", "distance", "layers", "transmission"

    def __init__(self, name, distance, layers, transmission):
        """Initialize a detector foil.

        Args:
            distance: Distance from the origin of the sample.
            layers: Layers of the foil in a single list.
        """
        self.name = name
        self.distance = distance
        self.layers = layers
        self.transmission = transmission


class CircularFoil(Foil):
    """Class for circular detector foil.
    """

    __slots__ = "diameter"

    def __init__(self, name, diameter=0.0, distance=0.0, layers=[], transmission=1.0):
        """Initialize a circular detector foil.

        Args:
            diameter: Diameter of the circular foil.
            distance: Distance from the origin of the sample.
            layers: Layers of the foil in a single list.
            transmission: ??
        """

        Foil.__init__(self, name, distance, layers, transmission)
        self.diameter = diameter


class RectangularFoil(Foil):
    """Class for rectangular detector foil.
    """

    __slots__ = "size"

    def __init__(self, name, size_x=0.0, size_y=0.0, distance=0.0, layers=[], transmission=1.0):
        """Initialize a rectangular detector foil.

        Args:
            size: Size of the circular foil in a tuple.
            distance: Distance from the origin of the sample.
            layers: Layers of the foil in a single list.
        """

        Foil.__init__(self, name, distance, layers, transmission)
        self.size = (size_x, size_y)
