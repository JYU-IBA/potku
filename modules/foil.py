# coding=utf-8
# TODO: Add licence information
"""
Created on 23.3.2018
Updated on ... 
"""

__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"
__versio__ = "2.0"

class Foil:
    """Class for detector foil.
    """

    __slots__ = "foil_type", "diameter", "size", "distance", "layers"

    def __init__(self, type):
        """Initialized a detector foil.

        Args:
            foil_type:     Type of the foil (either circular or rectangular)
            diameter: If type of the foil is 'circular', a single double
                      value should be used to describe the diameter of the foil.
                      Otherwise this should be None.
            size:     If the type of the foil is 'rectangular', a tuple of two
                      doubles should be used to describe the size of the foil.
                      Otherwise this should be None.
            distance: Distance from the origin of the sample.

        """

        self.foil_type = foil_type
        if diameter == None and size == None:
        if diameter != None and size != None:
        self.di
