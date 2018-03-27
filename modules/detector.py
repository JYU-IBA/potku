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

        def __object_hook(obj):
            """This function is needed for converting the parsed dictionary
            to Detector object.

            Args:
                obj: A JSON object (has been parsed, so this is a dictionary).
            """
            directory = os.path.dirname(file_path)
            name = obj["name"]
            angle = obj["angle"]
            foils = []

            for foil in obj["foils"]:
                distance = foil["distance"]
                layers = []

                for layer in foil["layers"]:
                    layers.append(Layer(layer["elements"],
                                        layer["thickness"],
                                        layer["ion_stopping"],
                                        layer["recoil_stopping"],
                                        layer["density"]))

                if foil["type"] == "circular":
                    foils.append(
                        CircularFoil(foil["diameter"], distance, layers))
                elif foil["type"] == "rectangular":
                    foils.append(
                        RectangularFoil(foil["size"], distance, layers))
                else:
                    raise json.JSONDecodeError

            return Detector(directory, name, angle, foils)

        return json.load(file_path, object_hook=__object_hook)



class ToFDetector(Detector):

    def __init__(self, directory, name, angle, foils):
        """Initialize a Time-of-Flight detector.

        Args:
            angle: Detector angle

        """
        Detector.__init__(directory, name, angle, foils)



# TODO: Add other detector types (GAS, SSD).
