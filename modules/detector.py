# coding=utf-8
# TODO: Add licence information
"""
Created on 23.3.2018
Updated on 27.3.2018
"""
from enum import Enum

__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n" \
             "Sinikka Siironen"
__versio__ = "2.0"

import json
import os
import datetime

from modules.foil import CircularFoil, RectangularFoil
from modules.layer import Layer
from modules.calibration_parameters import CalibrationParameters


class DetectorType(Enum):
    ToF = 0


class Detector:

    __slots__ = "request", "name", "description", "date", "detector_type", "calibration", "foils"

    def __init__(self, request, name="", description="", date=datetime.date.today(), detector_type=DetectorType.ToF,
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
        self.name = name
        self.description = description
        self.date = date
        self.detector_type = detector_type
        self.calibration = calibration
        self.foils = foils

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

        return cls(name, angle, foils)



class ToFDetector(Detector):

    def __init__(self, name, angle, foils):
        """Initialize a Time-of-Flight detector.

        Args:
            angle: Detector angle

        """
        Detector.__init__(name, angle, foils)



# TODO: Add other detector types (GAS, SSD).
