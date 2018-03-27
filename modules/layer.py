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

    def __init__(self, elements, thickness, ion_stopping, recoil_stopping,
                 density):
        """Initializes a target or foil layer.

        Args:
            elements:        A list of tuples that contain the element, the
                             isotope and amount, eg. ("O", 16.00, 0.13).
            thickness:       Thickness of the layer in nanometers.
            ion_stopping:    Stopping model for the primary ion.
            recoil_stopping: Stopping model for the recoils.
            density:         Layer density.
        """

        self.elements = elements
        self.thickness = thickness
        self.ion_stopping = ion_stopping
        self.recoil_stopping = recoil_stopping
        self.density = density

