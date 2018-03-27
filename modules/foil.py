# coding=utf-8
# TODO: Add licence information
"""
Created on 23.3.2018
Updated on 24.3.2018
"""

__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n " \
             "Sinikka Siironen"
__versio__ = "2.0"

class Foil:
    """Class for detector foil.
    """

    __slots__ = "distance", "layers"

    def __init__(self, distance, layers):
        """Initialize a detector foil.

        Args:
            distance: Distance from the origin of the sample.
            layers: Layers of the foil in a single list.
        """

        self.distance = distance
        self.layers = layers



class CircularFoil(Foil):
    """Class for circular detector foil.
    """

    __slots__ = "diameter"

    def __init__(self, diameter, distance, layers):
        """Initialize a circular detector foil.

        Args:
            diameter: Diameter of the circular foil.
            distance: Distance from the origin of the sample.
            layers: Layers of the foil in a single list.
        """

        Foil.__init__(self, distance, layers)
        self.diameter = diameter



class RectangularFoil(Foil):
    """Class for rectangular detector foil.
    """

    __slots__ = "size"

    def __init__(self, size, distance, layers):
        """Initialize a rectangular detector foil.

        Args:
            size: Size of the circular foil in a tuple.
            distance: Distance from the origin of the sample.
            layers: Layers of the foil in a single list.
        """

        Foil.__init__(self, distance, layers)
        self.size = size
