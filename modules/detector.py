# coding=utf-8
# TODO: Add licence information
"""
Created on 23.3.2018
Updated on 9.4.2018
"""
from enum import Enum

__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"
__version__ = "2.0"

import json
import os
import datetime

from modules.foil import CircularFoil, RectangularFoil
from modules.layer import Layer
from modules.calibration_parameters import CalibrationParameters


class DetectorType(Enum):
    ToF = 0


class Detector:

    # request maybe only temporary parameter
    __slots__ = "request", "description", "path", "name", "date", "angle", "detector_type", "foils", "calibration", "efficiencies", "efficiencies_path"

    def __init__(self, request, path, name="", description="", date=datetime.date.today(), detector_type=DetectorType.ToF,
                 calibration=CalibrationParameters(), foils=[]):
        """Initialize a detector.

        Args:
            request: Request in which this detector is used.
            name: Detector name.
            description: Detector description.
            date: Date of modification of detector file.
            detector_type: Type of detector.
            calibration: Calibration parameters for detector.
            foils: Detector foils.

        """
        self.request = request
        self.path = path  # With this we get the path of the folder where the .json file needs to go.
        self.name = name
        self.description = description
        self.date = date
        self.detector_type = detector_type
        self.calibration = calibration
        self.foils = foils

        # This is here only for testing that when creating a request and detector, a file is created that should contain
        # some information about the detector, if there is not one yet.
        # TODO: This needs to be more specific.
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

    def __init__(self, path, name, angle, foils):
        """Initialize a Time-of-Flight detector.

        Args:
            angle: Detector angle

        """
        Detector.__init__(self, path, name, angle, foils)


# TODO: Add other detector types (GAS, SSD).
