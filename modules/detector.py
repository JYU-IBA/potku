# coding=utf-8
"""
Created on 23.3.2018
Updated on 27.8.2018

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

import json
import os
import shutil
import time

from modules.element import Element
from modules.foil import CircularFoil
from modules.foil import RectangularFoil
from modules.layer import Layer


class Detector:
    """
    Detector class that handles all the information about a detector.
    It also can convert itself to and from JSON file.
    """
    __slots__ = "name", "description", "date", "type", "foils",\
                "tof_foils", "virtual_size", "tof_slope", "tof_offset",\
                "angle_slope", "angle_offset", "path", "modification_time",\
                "efficiencies", "efficiency_directory", "timeres", \
                "detector_theta", "__measurement_settings_file_path", \
                "efficiencies_to_remove", "save_in_creation"

    def __init__(self, path, measurement_settings_file_path, name="Default",
                 description="", modification_time=None,
                 detector_type="TOF",
                 foils=None, tof_foils=None, virtual_size=(2.0, 5.0),
                 tof_slope=1e-11, tof_offset=1e-9, angle_slope=0,
                 angle_offset=0, timeres=250.0, detector_theta=40,
                 save_in_creation=True):
        """Initialize a detector.

        Args:
            path: Path to .detector file.
            name: Detector name.
            measurement_settings_file_path: Path to measurement settings file
                                            which has detector angles.
            description: Detector parameters description.
            modification_time: Modification time of detector file in Unix time.
            detector_type: Type of detector.
            foils: List of detector foils.
            tof_foils: List of indexes of ToF foils in foils list.
            virtual_size: Virtual size of the detector.
            tof_slope: ToF slope.
            tof_offset: ToF offset.
            angle_slope: Angle slope.
            angle_offset: Angle offset.
            timeres: Time resolution.
            detector_theta: Angle of the detector.
            save_in_creation: Whether to save created detector into a file.
        """
        self.path = path

        self.name = name
        self.__measurement_settings_file_path = measurement_settings_file_path
        self.description = description
        if not modification_time:
            modification_time = time.time()
        self.modification_time = modification_time
        self.type = detector_type
        self.foils = foils
        if not self.foils:
            # Create default foils
            self.foils = [CircularFoil("Foil1", 7.0, 256.0,
                                       [Layer("Layer_12C",
                                              [Element("C", 12.011, 1)],
                                              0.1, 2.25, 0.0)]),
                          CircularFoil("Foil2", 10.0, 356.0,
                                       [Layer("Layer_12C",
                                              [Element("C", 12.011, 1)],
                                              13.0, 2.25, 0.0)]),
                          CircularFoil("Foil3", 18.0, 979.0,
                                       [Layer("Layer_12C",
                                              [Element("C", 12.011, 1)],
                                              44.4, 2.25, 0.0)]),
                          RectangularFoil("Foil4", 14.0, 14.0, 1042.0,
                                          [Layer("Layer_28Si",
                                                 [Element("N", 14.00, 0.57),
                                                  Element("Si", 28.09, 0.43)],
                                                 100.0, 3.44, 0.0)])]
        self.tof_foils = tof_foils
        if not self.tof_foils:
            # Set default ToF foils
            self.tof_foils = [1, 2]
        self.timeres = timeres
        self.virtual_size = virtual_size
        self.tof_slope = tof_slope
        self.tof_offset = tof_offset
        self.angle_slope = angle_slope
        self.angle_offset = angle_offset
        self.detector_theta = detector_theta

        # Efficiency file paths and directory
        self.efficiencies = []
        self.efficiencies_to_remove = []
        self.efficiency_directory = None

        if save_in_creation:
            self.to_file(os.path.join(self.path),
                         self.__measurement_settings_file_path)

    def update_directories(self, directory):
        """Creates directories if they do not exist and updates paths.
        Args:
            directory: Path to where all the detector information goes.
        """
        self.path = directory

        if not os.path.exists(self.path):
            os.makedirs(self.path)

        self.efficiency_directory = os.path.join(self.path, "Efficiency_files")
        if not os.path.exists(self.efficiency_directory):
            os.makedirs(self.efficiency_directory)

    def update_directory_references(self, obj):
        """
        Update detector's path and efficiency folder path and efficiencies'
        paths.
        """
        old_path_to_det, det_file = os.path.split(self.path)
        old_path_to_obj, det_folder = os.path.split(old_path_to_det)
        new_path = os.path.join(obj.directory, det_folder)

        self.path = os.path.join(new_path, det_file)

        self.efficiency_directory = os.path.join(new_path, "Efficiency_files")

    def get_efficiency_files(self):
        """Get efficiency files that are in detector's efficiency file folder
        and return them as a list.

        Return:
            Returns a string list of efficiency files.
        """
        files = []
        for f in os.listdir(self.efficiency_directory):
            if f.strip().endswith(".eff"):
                files.append(f)
        return files

    def get_efficiency_files_from_list(self):
        """Get efficiency files that are stored in detector's efficiency list,
        i.e. that are not yet moved under any detector's efficiency folder.

        Return:
            List of efficiency files.
        """
        files = []
        for path in self.efficiencies:
            file = os.path.split(path)[1]
            files.append(file)
        return files

    def save_efficiency_file_path(self, file_path):
        """Add the efficiency file path to detector's efficiencies list.
        """
        self.efficiencies.append(file_path)

    def add_efficiency_file(self, file_path):
        """Copies efficiency file to detector's efficiency folder.

        Args:
            file_path: Path of the efficiency file.
        """
        try:
            shutil.copy(file_path, self.efficiency_directory)
        except shutil.SameFileError:
            pass

    def remove_efficiency_file_path(self, file_name):
        """
        Add efficiency file to remove to the list of to be removed efficiency
        file paths and remove it from the efficiencies list.

        Args:
            file_name: Name of the efficiency file.
        """
        file_path = ""
        folder_and_file = os.path.join("Efficiency_files", file_name)
        for f in self.efficiencies:
            if f.endswith(folder_and_file):
                file_path = f
            if f.endswith(file_name):
                self.efficiencies.remove(f)

        if file_path:
            self.efficiencies_to_remove.append(file_path)

    def remove_efficiency_file(self, file_name):
        """Removes efficiency file from detector's efficiency file folder.

        Args:
            file_name: Name of the efficiency file.
        """
        try:
            os.remove(os.path.join(self.efficiency_directory, file_name))
            # Remove file from used efficiencies if it exists
            element = file_name.split('-')[0]
            if os.sep in element:
                element = os.path.split(element)[1]
            if element.endswith(".eff"):
                file_to_remove = element
            else:
                file_to_remove = os.path.join(self.efficiency_directory,
                                              "Used_efficiencies", element +
                                              ".eff")
            if os.path.exists(file_to_remove):
                os.remove(file_to_remove)
        except OSError:
            # File was not found in efficiency file folder.
            pass

    @classmethod
    def from_file(cls, detector_file_path, measurement_file_path, request,
                  save=True):
        """Initialize Detector from a JSON file.

        Args:
            detector_file_path: A file path to JSON file containing the
                                detector parameters.
            measurement_file_path: A file path to measurement settings file
                                   which has detector angles.
            request: Request object which has default detector angles.
            save: Whether to save created detector or not.

        Return:
            Detector object.
        """
        obj = json.load(open(detector_file_path))

        name = obj["name"]
        description = obj["description"]
        modification_time = obj["modification_time_unix"]
        detector_type = obj["detector_type"]
        timeres = obj["timeres"]
        virtual_size = tuple(obj["virtual_size"])
        tof_slope = obj["tof_slope"]
        tof_offset = obj["tof_offset"]
        angle_slope = obj["angle_slope"]
        angle_offset = obj["angle_offset"]
        tof_foils = obj["tof_foils"]
        foils = []

        # Read foils
        for foil in obj["foils"]:

            distance = foil["distance"]
            layers = []

            # Read layers of the foil
            for layer in foil["layers"]:
                elements = []
                elements_str = layer["elements"]
                # Read elements of the layer
                for element_str in elements_str:
                    elements.append(Element.from_string(element_str))

                layers.append(Layer(layer["name"],
                                    elements,
                                    float(layer["thickness"]),
                                    float(layer["density"]),
                                    float(layer["start_depth"])))

            if foil["type"] == "circular":
                foils.append(
                    CircularFoil(foil["name"], foil["diameter"], distance,
                                 layers, foil["transmission"]))
            else:
                foils.append(
                    RectangularFoil(foil["name"], (foil["size"])[0],
                                    (foil["size"])[1],
                                    distance, layers, foil["transmission"]))

        try:
            # Read .measurement file and update detector angle
            measurement_obj = json.load(open(measurement_file_path))
            detector_theta = measurement_obj["geometry"]["detector_theta"]
        except KeyError:
            # Get default detector angle from default detector
            detector_theta = request.default_detector.detector_theta

        return cls(path=detector_file_path,
                   measurement_settings_file_path=measurement_file_path,
                   name=name, description=description,
                   modification_time=modification_time,
                   detector_type=detector_type,
                   foils=foils, tof_foils=tof_foils, virtual_size=virtual_size,
                   tof_slope=tof_slope, tof_offset=tof_offset,
                   angle_slope=angle_slope, angle_offset=angle_offset,
                   timeres=timeres, detector_theta=detector_theta,
                   save_in_creation=save)

    def to_file(self, detector_file_path, measurement_file_path):
        """Save detector settings to a file.

        Args:
            detector_file_path: File in which the detector settings will be
                                saved.
            measurement_file_path: File in which the detector_theta angle is
                                   saved.
        """
        # Delete possible extra .detector files
        det_folder = os.path.split(detector_file_path)[0]
        filename_to_remove = ""
        for file in os.listdir(det_folder):
            if file.endswith(".detector"):
                filename_to_remove = file
                break
        if filename_to_remove:
            os.remove(os.path.join(det_folder, filename_to_remove))

        # Read Detector parameters to dictionary
        obj = {
            "name": self.name,
            "description": self.description,
            "modification_time": time.strftime("%c %z %Z", time.localtime(
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
                    "density": layer.density,
                    "start_depth": layer.start_depth
                }
                foil_obj["layers"].append(layer_obj)

            obj["foils"].append(foil_obj)

        with open(detector_file_path, "w") as file:
            json.dump(obj, file, indent=4)

        # Read .measurement to obj to update only detector angles
        try:
            obj = json.load(open(measurement_file_path))
            try:
                # Change existing detector theta
                obj["geometry"]["detector_theta"] = self.detector_theta
            except KeyError:
                # Add detector theta
                obj["geometry"] = {"detector_theta": self.detector_theta}
        except FileNotFoundError:
            # Write new .measurement file
            obj = {"geometry": {"detector_theta": self.detector_theta}}

        with open(measurement_file_path, "w") as file:
            json.dump(obj, file, indent=4)
