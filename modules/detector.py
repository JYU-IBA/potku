# coding=utf-8
# TODO: Add licence information
"""
Created on 23.3.2018
Updated on 3.5.2018
"""
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n " \
             "Sinikka Siironen"
__version__ = "2.0"

import os
import json
import datetime
import shutil
import time

from modules.foil import CircularFoil, RectangularFoil
from modules.layer import Layer
from modules.calibration_parameters import CalibrationParameters
from modules.element import Element


class Detector:
    """
    Detector class that handles all the information about a detector.
    It also can convert itself to and from file.
    """
    __slots__ = "name", "description", "date", "type", "calibration", "foils",\
                "tof_foils", "virtual_size", "tof_slope", "tof_offset",\
                "angle_slope", "angle_offset", "path", "modification_time",\
                "efficiencies", "efficiency_directory", "timeres", \
                "detector_theta", "detector_fii"

    def __init__(self, path, name="Default", description="This a default "
                                                         "detector.",
                 modification_time=time.time(), type="ToF",
                 calibration=CalibrationParameters(), foils=[CircularFoil(
                "Default", 7.0, 256.0, [Layer("First", [Element("C", 12.011,
                                                                1)], 0.1,
                                              2.25)]), CircularFoil(
                "Default", 9.0, 319.0, [Layer("Second", [Element("C", 12.011,
                                                                 1)], 13.3,
                                              2.25)]), CircularFoil(
                "Default", 18.0, 942.0, [Layer("Third", [Element("C", 12.011,
                                                                 1)], 44.4,
                                               2.25)]), RectangularFoil(
                "Default", 14.0, 14.0, 957.0, [Layer("Fourth", [Element(
                    "N", 14.00, 0.57), Element("Si", 28.09, 0.43)], 1.0,
                                                     3.44)])], tof_foils=[
                1, 2], virtual_size=(2.0, 5.0), tof_slope=1e-11,
                 tof_offset=1e-9, angle_slope=0, angle_offset=0,
                 timeres=250.0, detector_fii=0, detector_theta=40):
        """Initialize a detector.

        Args:
            name: Detector name.
            description: Detector description.
            modification_time: Modification time of detector file in Unix time.
            type: Type of detector.
            calibration: Calibration parameters for detector.
            foils: Detector foils.
            tof_foils: List of indexes of ToF foils in foils list.
            timeres: Time resolution.

        """
        # With this we get the path of the folder where the
        # .json file needs to go.
        self.path = path

        self.name = name
        self.description = description
        self.modification_time = modification_time
        self.type = type
        self.calibration = calibration
        self.timeres = timeres
        self.virtual_size = virtual_size
        self.tof_slope = tof_slope
        self.tof_offset = tof_offset
        self.angle_slope = angle_slope
        self.angle_offset = angle_offset
        self.detector_fii = detector_fii
        self.detector_theta = detector_theta
        self.foils = foils
        self.tof_foils = tof_foils

        self.efficiencies = []
        self.efficiency_directory = None

        self.to_file(os.path.join(self.path))

    def create_folder_structure(self, directory):
        """

        Args:
            directory: Path to where all the detector information goes.
        """
        self.path = directory

        if not os.path.exists(self.path):
            os.makedirs(self.path)

        self.efficiency_directory = os.path.join(self.path, "Efficiency_files")
        if not os.path.exists(self.efficiency_directory):
            os.makedirs(self.efficiency_directory)

    def get_efficiency_files(self):
        """ Get efficiency files that are in detector's efficiency
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
        name = obj["name"]
        description = obj["description"]
        modification_time = obj["modification_time_unix"]
        detector_type = obj["detector_type"]
        calibration = None  # TODO
        timeres = obj["timeres"]
        virtual_size = obj["virtual_size"]
        tof_slope = obj["tof_slope"]
        tof_offset = obj["tof_offset"]
        angle_slope = obj["angle_slope"]
        angle_offset = obj["angle_offset"]
        detector_fii = obj["detector_fii"]
        detector_theta = obj["detector_theta"]
        tof_foils = obj["tof_foils"]
        foils = []

        for foil in obj["foils"]:

            distance = foil["distance"]
            layers = []

            for layer in foil["layers"]:
                layers.append(Layer(layer["name"],
                                    layer["elements"],
                                    float(layer["thickness"]),
                                    float(layer["density"])))

            if foil["type"] == "circular":
                foils.append(
                    CircularFoil(foil["name"], foil["diameter"], distance,
                                 layers, foil["transmission"]))
            else:
                foils.append(
                    RectangularFoil(foil["name"], (foil["size"])[0],
                                    (foil["size"])[1],
                                    distance, layers, foil["transmission"]))

        return cls(file_path, name, description, modification_time,
                   detector_type, calibration, foils, tof_foils,
                   virtual_size, tof_slope,
                   tof_offset, angle_slope, angle_offset,
                   timeres, detector_fii, detector_theta)

    def to_file(self, file_path):
        """Save detector settings to a file.

        Args:
            file_path: File in which the detector settings will be saved."""

        obj = {
            "name": self.name,
            "description": self.description,
            "modification_time": str(datetime.datetime.fromtimestamp(
                time.time())),
            "modification_time_unix": time.time(),
            "detector_type": self.type,
            "foils": [],
            "tof_foils": self.tof_foils,
            "timeres": self.timeres,
            "virtual_size": self.virtual_size,
            "tof_slope": self.tof_slope,
            "tof_offset": self.tof_offset,
            "angle_slope": self.angle_slope,
            "angle_offset": self.angle_offset,
            "detector_fii": self.detector_fii,
            "detector_theta": self.detector_theta
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
                foil_obj["diameter"] = foil.diameter
            else:
                foil_obj["type"] = "rectangular"
                foil_obj["size"] = foil.size

            for layer in foil.layers:
                layer_obj = {
                    "name": layer.name,
                    "elements": [element.__str__() for element in
                                 layer.elements],
                    "thickness": layer.thickness,
                    "density": layer.density
                }
                foil_obj["layers"].append(layer_obj)

            obj["foils"].append(foil_obj)

        with open(file_path, "w") as file:
            json.dump(obj, file, indent=4)

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
