# coding=utf-8
# TODO: Add licence information
"""
Created on 23.3.2018
Updated on 24.3.2018
"""

__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n" \
             "Sinikka Siironen"
__versio__ = "2.0"

class Detector:

    def __init__(self, angle, foils):
        """Initialize a Time-of-Flight detector.

        Args:
            angle: Detector angle

        """

        self.angle = angle
        self.foils = foils

class ToFDetector(Detector):

    def __init__(self, angle, foils):
        """Initialize a Time-of-Flight detector.

        Args:
            angle: Detector angle

        """

        self.angle = angle
        self.foils = foils

# TODO: Add other detector types (GAS, SSD).
