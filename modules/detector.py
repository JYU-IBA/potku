# coding=utf-8
# TODO: Add licence information
"""
Created on 23.3.2018
Updated on 26.4.2018
"""
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n " \
             "Sinikka Siironen"
__version__ = "2.0"

import os
import json
import datetime
import shutil

from modules.foil import CircularFoil, RectangularFoil
from modules.layer import Layer
from modules.calibration_parameters import CalibrationParameters
from modules.element import Element


class Detector:

    # request maybe only temporary parameter
    __slots__ = "name", "description", "date", "type", "calibration", "foils",\
                "tof_foils", "virtual_size", "tof_slope", "tof_offset",\
                "angle_slope", "angle_offset", "path", "modification_time",\
                "efficiencies", "efficiency_directory"

    def __init__(self, name="Default", description="This a default detector.",
                 modification_time=datetime.datetime.now(), type="TOF",
                 calibration=CalibrationParameters(),
                 foils=[CircularFoil("Default", 7.0, 256.0,
                                     [Layer("First", [Element("C", 12.011, 1)],
                                            0.1, 2.25)]),
                        CircularFoil("Default", 9.0, 319.0,
                                     [Layer("Second", [Element("C", 12.011, 1)],
                                            13.3, 2.25)]),
                        CircularFoil("Default", 18.0, 942.0,
                                     [Layer("Third", [Element("C", 12.011, 1)],
                                            44.4, 2.25)]),
                        RectangularFoil("Default", (14.0, 14.0), 957.0,
                                     [Layer("Fourth", [
                                         Element("N", 14.00, 0.57),
                                         Element("Si", 28.09, 0.43)],
                                            1.0, 3.44)])],
                 tof_foils=[1, 2], virtual_size=(2.0, 5.0), tof_slope=1e-11,
                 tof_offset=1e-9, angle_slope=0, angle_offset=0):
        """Initialize a detector.

        Args:
            name: Detector name.
            description: Detector description.
            modification_time: Time of modification of detector file.
            type: Type of detector.
            calibration: Calibration parameters for detector.
            foils: Detector foils.
            tof_foils: List of indexes that tell the index of tof foils in
            foils list.

        """
        # With this we get the path of the folder where the
        # .json file needs to go.
        self.path = None
        self.name = name
        self.description = description
        self.modification_time = modification_time
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
        """Get efficiency files that are in detector's efficiency
        file folder and return them as a list.

        Return:
            Returns a string list of efficiency files.
        """
        files = []
        for f in os.listdir(self.efficiency_directory):
            if f.strip().endswith(".eff"):
                files.append(f)
        return files

    def add_efficiency_file(self, file_path):
        """Copies efficiency file to detector's efficiency folder.

        Args:
            file_path: Path of the efficiency file.
        """
        shutil.copy(file_path, self.efficiency_directory)

    def remove_efficiency_file(self, file_name):
        """Removes efficiency file from detector's efficiency file folder.

        Args:
            file_name: Name of the efficiency file.
        """
        try:
            os.remove(os.path.join(self.efficiency_directory, file_name))
        except OSError as e:
            # File was not found in efficiency file folder.
            pass

    @classmethod
    def from_file(cls, file_path):
        """Initialize Detector from a JSON file.

        Args:
            file_path: A file path to JSON file containing the
            detector parameters.
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
