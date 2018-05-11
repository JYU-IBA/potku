# coding=utf-8
"""
Created on 23.3.2018
Updated on 11.5.2018

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2018 Severi Jääskeläinen, Samuel Kaiponen, Heta Rekilä and
Sinikka Siironen

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program (file named 'LICENCE').
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
                "detector_theta", "__measurement_settings_file_path"

    def __init__(self, path, measurement_settings_file_path, name="Default",
                 description="This a default detector setting file.",
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
                 timeres=250.0, detector_theta=40):
        """Initialize a detector.

        Args:
            name: Detector name.
            measurement_settings_file_path: Path to measurement settings file
                                            which has detector angles.
            description: Detector description.
            modification_time: Modification time of detector file in Unix time.
            type: Type of detector.
            calibration: Calibration parameters for detector.
            foils: Detector foils.
            tof_foils: List of indexes of ToF foils in foils list.
            virtual_size: Virtual size of the detector.
            tof_slope: Tof slope.
            tof_offset: Tof offset.
            angle_slope: Angle slope.
            angle_offset: Angle offset.
            timeres: Time resolution.
            detector_theta: Angle of the detector.
        """
        # With this we get the path of the folder where the
        # .json file needs to go.
        self.path = path

        self.name = name
        self.__measurement_settings_file_path = measurement_settings_file_path
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
        self.detector_theta = detector_theta
        self.foils = foils
        self.tof_foils = tof_foils

        self.efficiencies = []
        self.efficiency_directory = None

        self.to_file(os.path.join(self.path),
                     self.__measurement_settings_file_path)

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
    def from_file(cls, detector_file_path, measurement_file_path, request):
        """Initialize Detector from a JSON file.

        Args:
            detector_file_path: A file path to JSON file containing the
                                detector parameters.
            measurement_file_path: A file path to measurement settings file
                                   which has detector angles.
            request: Request object which has default detector angles.
        """
        obj = json.load(open(detector_file_path))

        # Below we do conversion from dictionary to Detector object
        name = obj["name"]
        description = obj["description"]
        modification_time = obj["modification_time_unix"]
        detector_type = obj["detector_type"]
        calibration = None  # TODO
        timeres = obj["timeres"]
        virtual_size = tuple(obj["virtual_size"])
        tof_slope = obj["tof_slope"]
        tof_offset = obj["tof_offset"]
        angle_slope = obj["angle_slope"]
        angle_offset = obj["angle_offset"]
        tof_foils = obj["tof_foils"]
        foils = []

        for foil in obj["foils"]:

            distance = foil["distance"]
            layers = []

            for layer in foil["layers"]:
                elements = []
                elements_str = layer["elements"]
                for element_str in elements_str:
                    elements.append(Element.from_string(element_str))

                layers.append(Layer(layer["name"],
                                    elements,
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

        if measurement_file_path.endswith(".measurement"):
            mes_obj = json.load(open(measurement_file_path))
            detector_theta = mes_obj["geometry"]["detector_theta"]
        else:
            detector_theta = request.default_detector.detector_theta

        return cls(path=detector_file_path,
                   measurement_settings_file_path=measurement_file_path,
                   name=name,
                   description=description,
                   modification_time=modification_time,
                   type=detector_type, calibration=calibration, foils=foils,
                   tof_foils=tof_foils,
                   virtual_size=virtual_size, tof_slope=tof_slope,
                   tof_offset=tof_offset, angle_slope=angle_slope,
                   angle_offset=angle_offset,
                   timeres=timeres, detector_theta=detector_theta)

    def to_file(self, detector_file_path, measurement_file_path):
        """Save detector settings to a file.

        Args:
            detector_file_path: File in which the detector settings will be
                                saved.
            measurement_file_path: File in which the detector_theta angle is
                                   saved.
        """

        #  Delete possible extra .detector files
        det_folder = os.path.split(detector_file_path)[0]
        filename_to_remove = ""
        for file in os.listdir(det_folder):
            if file.endswith(".detector"):
                filename_to_remove = file
                break
        if filename_to_remove:
            os.remove(os.path.join(det_folder, filename_to_remove))

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
            "angle_offset": self.angle_offset
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

        with open(detector_file_path, "w") as file:
            json.dump(obj, file, indent=4)

        # Read .measurement to obj to update only detector angles
        if os.path.exists(measurement_file_path):
            obj = json.load(open(measurement_file_path))
            try:
                obj["geometry"]["detector_theta"] = self.detector_theta
            except KeyError:
                obj["geometry"] = {
                    "detector_theta": self.detector_theta
                }
        else:
            obj = {
                "geometry": {
                    "detector_theta": self.detector_theta
                }
            }

        with open(measurement_file_path, "w") as file:
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
