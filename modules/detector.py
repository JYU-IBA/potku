# coding=utf-8
# TODO: Add licence information
"""
Created on 23.3.2018
Updated on 4.4.2018
"""

__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"
__version__ = "2.0"

import json
import os

from modules.foil import CircularFoil, RectangularFoil
from modules.layer import Layer


class Detector:

    # request maybe only temporary parameter
    __slots__ = "path", "name", "angle", "foils", "efficiencies", "efficiencies_path"

    def __init__(self, path, name, angle, foils):
        """Initialize a detector.

        Args:
            path: Request in which the detector belongs to.
            name: Name of the detector.
            angle: Detector angle.
            foils: Detector foils.

        """
        self.path = path  # With this we get the path of the folder where the .json file needs to go.
        self.name = name
        self.angle = angle
        self.foils = foils

        # This is here only for testing that when creating a request and detector, a file is created that should contain
        # some information about the detector, if there is not one yet.
        # TODO: This needs to be more specific.
        # TODO: In the future, when opening a request, this should check whether there is a .json file in the directory
        file_name = os.path.join(self.path, self.name) + ".detector"
        try:
            file = open(file_name, "r")
            print(file.readlines())
        except IOError:
            file = open(file_name, "w")
            file.write("This is a detector in json format.")

        self.efficiencies = []
        self.efficiencies_path = os.path.join(self.path, "Efficiency_files")

        if not os.path.exists(self.efficiencies_path):
            os.makedirs(self.efficiencies_path)

    @classmethod
    def from_file(cls, file_path):
        """Initialize Detector from a JSON file.

        Args:
            file_path: A file path to JSON file containing the detector
                       parameters.
        """

        obj = json.load(open(file_path))

        # Below we do conversion from dictionary to Detector object
        name = os.path.splitext(os.path.split(file_path)[1])[0]
        angle = obj["angle"]
        foils = []

        for foil in obj["foils"]:

            distance = foil["distance"]
            layers = []

            for layer in foil["layers"]:
                layers.append(Layer(tuple(layer["elements"]),
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

        return cls(file_path, name, angle, foils)


class ToFDetector(Detector):

    def __init__(self, name, angle, foils):
        """Initialize a Time-of-Flight detector.

        Args:
            angle: Detector angle

        """
        Detector.__init__(name, angle, foils)


# TODO: Add other detector types (GAS, SSD).
