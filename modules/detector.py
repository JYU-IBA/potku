# coding=utf-8
# TODO: Add licence information
"""
Created on 23.3.2018
Updated on 24.3.2018
"""

__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n" \
             "Sinikka Siironen"
__versio__ = "2.0"

import json
import os
from types import SimpleNamespace as Namespace

from modules.foil import CircularFoil, RectangularFoil
from modules.layer import Layer

class Detector:

    def __init__(self, directory, name, angle, foils):
        """Initialize a detector.

        Args:
            directory: The directory where the detector settings file is saved.
            angle: Detector angle.
            foils: Detector foils.

        """

        self.__directory = directory
        self.__name = name
        self.__angle = angle
        self.__foils = foils

    @classmethod
    def fromJSON(cls, file_path):
        """Initialize Detector from a JSON file.

        Args:
            file_path: A file path to JSON file containing the detector
                       parameters.
        """

        return json.load(open(file_path), object_hook=lambda d: Namespace(**d))



class ToFDetector(Detector):

    def __init__(self, directory, name, angle, foils):
        """Initialize a Time-of-Flight detector.

        Args:
            angle: Detector angle

        """
        Detector.__init__(directory, name, angle, foils)



# TODO: Add other detector types (GAS, SSD).
