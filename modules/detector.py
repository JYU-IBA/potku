# coding=utf-8
# TODO: Add licence information
"""
Created on 23.3.2018
Updated on 20.4.2018
"""
import re

from modules.general_functions import save_settings

__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"
__version__ = "2.0"

import os
import json
import datetime

from modules.foil import CircularFoil, RectangularFoil
from modules.layer import Layer
from modules.calibration_parameters import CalibrationParameters
from modules.element import Element

class Detector:

    # request maybe only temporary parameter
    __slots__ = "name", "description", "path", "date",\
                "type", "foils", "calibration", "efficiencies", \
                "efficiency_directory", "tof_foils"

    def __init__(self, name="Default", description="", date=datetime.date.today(),
                 detector_type="TOF", calibration=CalibrationParameters(), foils=[], tof_foils=[1, 2]):
        """Initialize a detector.

        Args:
            name: Detector name.
            description: Detector description.
            date: Date of modification of detector file.
            type: Type of detector.
            calibration: Calibration parameters for detector.
            foils: Detector foils.
            tof_foils: List of indexes that tell the index of tof foils in foils list.

        """
        self.path = None  # With this we get the path of the folder where the .json file needs to go.
        self.name = name
        self.description = description
        self.date = date
        self.type = type
        self.calibration = calibration
        self.foils = foils
        self.tof_foils = tof_foils

        self.efficiencies = []
        self.efficiency_directory = None

    def create_folder_structure(self, path):
        self.path = path

        if not os.path.exists(self.path):
            os.makedirs(self.path)

        self.efficiency_directory = os.path.join(self.path, "Efficiency_files")
        if not os.path.exists(self.efficiency_directory):
            os.makedirs(self.efficiency_directory)

    def get_efficiency_files(self):
        """Get efficiency files that are in detector's efficiency file folder and return
        them as a list.

        Return:
            Returns a string list of efficiency files.
        """
        files = []
        for f in os.listdir(self.efficiency_directory):
            if f.strip().endswith(".eff"):
                files.append(f)
        return files

    @classmethod
    def from_file(cls, file_path):
        """Initialize Detector from a JSON file.

        Args:
            file_path: A file path to JSON file containing the detector parameters.
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
                layers.append(Layer(layer["name"],
                                    Element.from_string(layer["elements"]),
                                    float(layer["thickness"]),
                                    float(layer["density"])))

            if foil["type"] == "circular":
                foils.append(
                    CircularFoil(foil["diameter"], distance, layers))
            else:
                foils.append(
                    RectangularFoil(foil["size"], distance, layers))


        return cls(file_path, name, angle, foils)

    def to_file(self, file_path):
        """Save detector settings to a file.

        Args:
            file_path: File in which the detector settings will be saved."""

        obj = {
            "name": self.name,
            "description": self.description,
            "date": self.date,
            "type": self.type,
            "foils": [],
            "tof_foils": self.tof_foils
        }

        for foil in self.foils:
            foil_obj = {
                "name": foil.name,
                "distance": foil.distance,
                "layers": [],
                "transmission": foil.transmission,
            }
            if isinstance(foil, CircularFoil):
                foil_obj["type"] = "circular"
                foil_obj["diameter"] = str(foil.diameter)
            else:
                foil_obj["type"] = "rectangular"
                foil_obj["size"] = str(foil.size)

            for layer in foil.layers:
                layer_obj = {
                    "name": layer.name,
                    "elements": [str(element) for element in layer.elements],
                    "thickness": layer.thickness,
                    "density": layer.density
                }
                foil_obj["layers"].append(layer_obj)

            obj["foils"].append(foil_obj)

        with open(file_path, "w") as file:
            json.dump(obj, file)


# class ToFDetector(Detector):
#
#     def __init__(self, path, name, angle, foils):
#         """Initialize a Time-of-Flight detector.
#
#         Args:
#             angle: Detector angle
#
#         """
#         Detector.__init__(self, path, name, angle, foils)


# TODO: Add other detector types (GAS, SSD).
