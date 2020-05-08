# coding=utf-8
"""
Created on 23.3.2018
Updated on 17.12.2018

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

import modules.general_functions as gf

from pathlib import Path

from modules.base import Serializable
from modules.base import AdjustableSettings
from modules.base import MCERDParameterContainer
from modules.element import Element
from modules.foil import Foil
from modules.foil import CircularFoil
from modules.foil import RectangularFoil
from modules.layer import Layer


class Detector(MCERDParameterContainer, Serializable, AdjustableSettings):
    """
    Detector class that handles all the information about a detector.
    It also can convert itself to and from JSON file.
    """
    __slots__ = "name", "description", "date", "type", "foils",\
                "tof_foils", "virtual_size", "tof_slope", "tof_offset",\
                "angle_slope", "angle_offset", "path", "modification_time",\
                "efficiency_directory", "timeres", \
                "detector_theta", "_measurement_settings_file_path",

    EFFICIENCY_DIR = "Efficiency_files"
    USED_EFFICIENCIES_DIR = "Used_efficiencies"

    def __init__(self, path, measurement_settings_file_path, name="Default",
                 description="", modification_time=None, detector_type="TOF",
                 foils=None, tof_foils=None, virtual_size=(2.0, 5.0),
                 tof_slope=5.8e-11, tof_offset=-1.0e-9, angle_slope=0,
                 angle_offset=0, timeres=250.0, detector_theta=41,
                 save_on_creation=True):
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
            save_on_creation: Whether to save created detector into a file.
        """
        self.path = Path(path)

        self.name = name
        self._measurement_settings_file_path = Path(
            measurement_settings_file_path)
        self.description = description
        if modification_time is None:
            self.modification_time = time.time()
        else:
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
            # TODO make being a timing foil an attribute of a foil
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
        self.efficiency_directory = None

        if save_on_creation:
            self.to_file(self.path, self._measurement_settings_file_path)

    def update_directories(self, directory):
        """Creates directories if they do not exist and updates paths.
        Args:
            directory: Path to where all the detector information goes.
        """
        self.path = Path(directory)
        os.makedirs(self.path, exist_ok=True)

        self.efficiency_directory = Path(self.path, Detector.EFFICIENCY_DIR)
        os.makedirs(self.efficiency_directory, exist_ok=True)

    def update_directory_references(self, obj):
        """
        Update detector's path and efficiency folder path and efficiencies'
        paths.
        """
        old_path_to_det, det_file = self.path.parent, self.path.name
        old_path_to_obj, det_folder = \
            old_path_to_det.parent, old_path_to_det.name
        new_path = Path(obj.directory, det_folder)

        self.path = Path(new_path, det_file)

        self.efficiency_directory = Path(new_path, Detector.EFFICIENCY_DIR)

    def get_efficiency_files(self, full_path=False):
        """Returns efficiency files that are in detector's efficiency file
        folder, either with full path or just the file name.

        Return:
            Returns a string list of efficiency files.
        """
        def filter_func(dir_entry):
            fp = Path(dir_entry)
            if fp.is_file() and fp.suffix == ".eff":
                if full_path:
                    return fp
                return Path(fp.name)
            return None
        return [
            *filter(
                lambda f: f is not None,
                (filter_func(file) for file in os.scandir(
                    self.efficiency_directory)))
        ]

    def add_efficiency_file(self, file_path: Path):
        """Copies efficiency file to detector's efficiency folder. Existing
        files are overwritten.

        Raises OSError if the file_path points to a directory.

        Args:
            file_path: Path of the efficiency file.
        """
        fp = Path(file_path)
        if fp.suffix == ".eff":
            try:
                shutil.copy(fp, self.efficiency_directory)
            except shutil.SameFileError:
                pass

    def get_settings(self) -> dict:
        """Returns a dictionary of settings that can be adjusted.
        """
        return {
            "name": self.name,
            "modification_time": self.modification_time,
            "description": self.description,
            "detector_type": self.type,
            "angle_slope": self.angle_slope,
            "angle_offset": self.angle_offset,
            "tof_slope": self.tof_slope,
            "tof_offset": self.tof_offset,
            "timeres": self.timeres,
            "virtual_size": self.virtual_size
        }

    def set_settings(self, detector_type=None, **kwargs):
        """Adjusts this Detector's settings with given keyword arguments.
        """
        allowed = self.get_settings()
        if detector_type is not None:
            self.type = detector_type
        for key, value in kwargs.items():
            if key in allowed:
                setattr(self, key, value)

    def remove_efficiency_file(self, file_name: Path):
        """Removes efficiency file from detector's efficiency file folder as
        well as the used efficiencies folder.

        Args:
            file_name: Name of the efficiency file.
        """
        file_name = Path(file_name)
        try:
            Path(self.efficiency_directory, file_name).unlink()
        except OSError:
            pass
        try:
            used_eff_file = \
                self.get_used_efficiencies_dir() / \
                Detector.get_used_efficiency_file_name(file_name)
            os.remove(used_eff_file)
        except (OSError, ValueError):
            # File was not found in efficiency file folder or the file extension
            # was wrong.
            pass

    @classmethod
    def from_file(cls, detector_file_path: Path, measurement_file_path: Path,
                  request, save=True):
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
        with open(detector_file_path) as dfp:
            detector = json.load(dfp)

        detector["modification_time"] = detector.pop("modification_time_unix")
        detector["virtual_size"] = tuple(detector["virtual_size"])

        foils = []

        # Read foils
        for foil in detector.pop("foils"):
            layers = []

            # Read layers of the foil
            for layer in foil.pop("layers"):
                elements = []
                elements_str = layer.pop("elements")
                # Read elements of the layer
                for element_str in elements_str:
                    elements.append(Element.from_string(element_str))

                layers.append(Layer(**layer, elements=elements))

            foils.append(Foil.generate_foil(**foil, layers=layers))

        try:
            # Read .measurement file and update detector angle
            with open(measurement_file_path) as mesu_file:
                measurement_obj = json.load(mesu_file)
            detector_theta = measurement_obj["geometry"]["detector_theta"]
        except KeyError:
            # Get default detector angle from default detector
            detector_theta = request.default_detector.detector_theta

        return cls(path=detector_file_path,
                   measurement_settings_file_path=measurement_file_path,
                   foils=foils, detector_theta=detector_theta,
                   save_on_creation=save, **detector)

    def to_file(self, detector_file_path, measurement_file_path):
        """Save detector settings to a file.

        Args:
            detector_file_path: File in which the detector settings will be
                                saved.
            measurement_file_path: File in which the detector_theta angle is
                                   saved.
        """
        # Delete possible extra .detector files
        det_folder = Path(detector_file_path).parent
        os.makedirs(det_folder, exist_ok=True)
        gf.remove_files(det_folder, exts={".detector"})

        timestamp = time.time()

        # Read Detector parameters to dictionary
        obj = {
            **self.get_settings(),
            "foils": [
                foil.to_dict() for foil in self.foils
            ],
            "tof_foils": self.tof_foils,
            "modification_time": time.strftime(
                "%c %z %Z", time.localtime(timestamp)),
            "modification_time_unix": timestamp
        }

        with open(detector_file_path, "w") as file:
            json.dump(obj, file, indent=4)

        if measurement_file_path is None:
            return
        # Read .measurement to obj to update only detector angles
        try:
            with open(measurement_file_path) as mesu:
                obj = json.load(mesu)
            try:
                # Change existing detector theta
                obj["geometry"]["detector_theta"] = self.detector_theta
            except KeyError:
                # Add detector theta
                obj["geometry"] = {"detector_theta": self.detector_theta}
        except OSError:
            # Write new .measurement file
            obj = {"geometry": {"detector_theta": self.detector_theta}}

        with open(measurement_file_path, "w") as file:
            json.dump(obj, file, indent=4)

    def get_mcerd_params(self):
        """Returns a list of strings that are passed as parameters for MCERD.
        """
        return [
            f"Detector type: {self.type}",
            f"Detector angle: {self.detector_theta}",
            f"Virtual detector size: {'%0.1f %0.1f' % self.virtual_size}",
            f"Timing detector numbers: {self.tof_foils[0]} {self.tof_foils[1]}"
        ]

    def calculate_solid(self):
        """
        Calculate the solid parameter.
        Return:
            Returns the solid parameter calculated.
        """
        try:
            transmissions = self.foils[0].transmission
        except IndexError:
            return 0

        for f in self.foils:
            transmissions *= f.transmission

        smallest_solid_angle = self.calculate_smallest_solid_angle()

        return smallest_solid_angle * transmissions

    def calculate_smallest_solid_angle(self):
        """
        Calculate the smallest solid angle.
        Return:
            Smallest solid angle. (unit millisteradian)
        """
        try:
            return min(foil.get_solid_angle(units="msr")
                       for foil in self.foils)
        except (ZeroDivisionError, ValueError):
            return 0

    @staticmethod
    def get_used_efficiency_file_name(file_name) -> Path:
        """Returns an efficiency file name that can be used by tof_list.

        File name should end in '.eff', otherwise ValueError is raised.
        If the file name includes comments (indicated by a '-'), they will be
        stripped from the output. A file named '1He-autumn2019.eff' becomes
        '1He.eff'.

        Args:
            file_name: either a file name or path to a file

        Return:
            Path object that is only the file name.
        """
        file_name = Path(file_name)
        if file_name.suffix != ".eff":
            raise ValueError(
                f"Efficiency file should have the extension '.eff'."
                f"Given file was named '{file_name}'.")
        first_part = file_name.name.split("-")[0]
        if first_part.endswith(".eff"):
            return Path(first_part)
        return Path(f"{first_part}.eff")

    def get_used_efficiencies_dir(self):
        """Returns the path to efficiency folder where the files used when
        running tof_list are located.
        """
        try:
            return Path(
                self.efficiency_directory, Detector.USED_EFFICIENCIES_DIR)
        except TypeError:
            # efficiency directory is None, this should also return None
            return None

    def copy_efficiency_files(self):
        """Copies efficiency files to the directory where tof_list will be
        looking for them. Additional comments are stripped from the files.
        (i.e. 1H-example.eff becomes 1H.eff).
        """
        destination = self.get_used_efficiencies_dir()
        destination.mkdir(exist_ok=True)
        # Remove previous files
        gf.remove_files(destination, {".eff"})

        for eff in self.get_efficiency_files(full_path=True):
            try:
                used_file = Detector.get_used_efficiency_file_name(eff)
            except ValueError:
                continue
            old_file = Path(self.efficiency_directory, eff)
            shutil.copy(old_file, destination / used_file)
