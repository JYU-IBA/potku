# coding=utf-8
# TODO: Add licence information
"""
Created on 23.3.2018
Updated on 24.3.2018
"""

__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n" \
             "Sinikka Siironen"
__versio__ = "2.0"

class Layer:
    """Class for a target or foil layer.
    """

    __slots__ = "elements", "thickness", "ion_stopping", "recoil_stopping",\
                "density"

    def __init__(self, name, elements, thickness, density):
        """Initializes a target or foil layer.

        Args:
            name:            Name of the layer.
            elements:        A list of Element objects.
            thickness:       Thickness of the layer in nanometers.
            density:         Layer density.
        """
        self.name = name
        self.elements = elements
        self.thickness = thickness
        self.density = density

