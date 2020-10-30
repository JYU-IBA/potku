# coding=utf-8
"""
Created on 23.3.2018
Updated on 17.12.2018

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2018 Severi Jääskeläinen, Samuel Kaiponen, Heta Rekilä and
Sinikka Siironen, 2020 Juhani Sundell

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
             "Sinikka Siironen \n Juhani Sundell \n Tuomas Pitkänen"
__version__ = "2.0"

import json
import shutil
import time
from typing import Iterable
from typing import Set
from typing import List
from pathlib import Path

from . import general_functions as gf

from .base import Serializable
from .base import AdjustableSettings
from .base import MCERDParameterContainer
from .element import Element
from .foil import Foil
from .foil import CircularFoil
from .foil import RectangularFoil
from .layer import Layer
from .enums import DetectorType


class Detector(MCERDParameterContainer, Serializable, AdjustableSettings):
    """
    Detector class that handles all the information about a detector.
    It also can convert itself to and from JSON file.
    """
    __slots__ = "name", "description", "date", "detector_type", "foils",\
                "tof_foils", "virtual_size", "tof_slope", "tof_offset",\
                "angle_slope", "angle_offset", "path", "modification_time",\
                "timeres", "detector_theta"

    EFFICIENCY_DIR = "Efficiency_files"
    USED_EFFICIENCIES_DIR = "Used_efficiencies"

    def __init__(self, path: Path, name="Default",
                 description="", modification_time=None,
                 detector_type=DetectorType.TOF,
                 foils=None, tof_foils=None, virtual_size=(2.0, 5.0),
                 tof_slope=5.8e-11, tof_offset=-1.0e-9, angle_slope=0,
                 angle_offset=0, timeres=250.0, detector_theta=41,
                 save_on_creation=True):
        """Initialize a detector.

        Args:
            path: Path to .detector file.
            name: Detector name.
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
        self.description = description
        if modification_time is None:
            self.modification_time = time.time()
        else:
            self.modification_time = modification_time

        # TODO: This should be called type, but renaming it solved issues with
        #       initialization and backwards incompatibility (deserialization)
        self.detector_type = DetectorType(detector_type.upper())
        self.foils = foils

        if not self.foils:
            # Create default foils
            self.foils = [CircularFoil("Foil1", 7.0, 256.0,
                                       [Layer("Layer_12C",
                                              [Element("C", 12, 1)],
                                              0.1, 2.25, 0.0)]),
                          CircularFoil("Foil2", 10.0, 356.0,
                                       [Layer("Layer_12C",
                                              [Element("C", 12, 1)],
                                              13.0, 2.25, 0.0)]),
                          CircularFoil("Foil3", 18.0, 979.0,
                                       [Layer("Layer_12C",
                                              [Element("C", 12, 1)],
                                              44.4, 2.25, 0.0)]),
                          RectangularFoil("Foil4", 14.0, 14.0, 1042.0,
                                          [Layer("Layer_28Si",
                                                 [Element("N", 14, 0.57),
                                                  Element("Si", 28, 0.43)],
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

        if save_on_creation:
            self.to_file(self.path)

    def update_directories(self, directory: Path):
        """Creates directories if they do not exist and updates paths.
        Args:
            directory: Path to where all the detector information goes.
        """
        self.path = directory / self.path.name
        directory.mkdir(exist_ok=True)

        self.get_efficiency_dir().mkdir(exist_ok=True)

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

    def get_efficiency_files(self, return_full_paths: bool = False) ->  \
            List[Path]:
        """Returns efficiency files that are in detector's efficiency file
        folder, either with full path or just the file name.

        Args:
            return_full_paths: whether full paths are returned or not

        Return:
            Paths to efficiency files either as full paths or just file names
        """
        try:
            return [
                fp if return_full_paths else Path(fp.name)
                for fp in gf.find_files_by_extension(
                    self.get_efficiency_dir(), ".eff")[".eff"]
            ]
        except OSError:
            return []

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
                shutil.copy(fp, self.get_efficiency_dir())
            except shutil.SameFileError:
                pass

    def _get_attrs(self) -> Set[str]:
        return {
                "name", "modification_time", "description", "detector_type",
                "angle_slope", "angle_offset", "tof_slope", "tof_offset",
                "timeres", "virtual_size", "detector_theta"
            }

    def remove_efficiency_file(self, file_name: Path):
        """Removes efficiency file from detector's efficiency file folder as
        well as the used efficiencies folder.

        Args:
            file_name: Name of the efficiency file.
        """
        file_name = Path(file_name)

        try:
            used_path = self.get_used_efficiencies_dir() / \
                Detector.get_used_efficiency_file_name(file_name),
        except ValueError:
            used_path = tuple()

        gf.remove_files(
            self.get_efficiency_dir() / file_name, *used_path
        )

    @classmethod
    def from_file(cls, detector_file: Path, request, save_on_creation=True):
        """Initialize Detector from a JSON file.

        Args:
            detector_file: A file path to JSON file containing the
                                detector parameters.
            request: Request object which has default detector angles.
            save_on_creation: Whether to save created detector or not.

        Return:
            Detector object.
        """
        with detector_file.open("r") as dfp:
            detector = json.load(dfp)

        detector["modification_time"] = detector.pop("modification_time_unix")
        detector["virtual_size"] = tuple(detector["virtual_size"])

        foils = [Foil.generate_foil(**foil) for foil in detector.pop("foils")]

        return cls(path=detector_file, foils=foils,
                   save_on_creation=save_on_creation, **detector)

    def to_file(self, detector_file: Path):
        """Save detector settings to a file.

        Args:
            detector_file: File in which the detector settings will be
                saved.
        """
        # Delete possible extra .detector files
        det_folder = detector_file.parent
        det_folder.mkdir(parents=True, exist_ok=True)

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
            "modification_time_unix": timestamp,
            "detector_theta": self.detector_theta
        }

        with detector_file.open("w") as file:
            json.dump(obj, file, indent=4)

    def get_mcerd_params(self):
        """Returns a list of strings that are passed as parameters for MCERD.
        """
        return [
            f"Detector type: {self.detector_type}",
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

    def get_efficiency_dir(self) -> Path:
        """Returns the path to efficiency directory.
        """
        return self.path.parent / Detector.EFFICIENCY_DIR

    def get_used_efficiencies_dir(self) -> Path:
        """Returns the path to efficiency folder where the files used when
        running tof_list are located.
        """
        return self.get_efficiency_dir() / Detector.USED_EFFICIENCIES_DIR

    def copy_efficiency_files(self):
        """Copies efficiency files to the directory where tof_list will be
        looking for them. Additional comments are stripped from the files.
        (i.e. 1H-example.eff becomes 1H.eff).
        """
        destination = self.get_used_efficiencies_dir()
        destination.mkdir(exist_ok=True)
        # Remove previous files
        gf.remove_matching_files(destination, {".eff"})

        for eff in self.get_efficiency_files(return_full_paths=True):
            try:
                used_file = Detector.get_used_efficiency_file_name(eff)
            except ValueError:
                continue
            old_file = Path(self.get_efficiency_dir(), eff)
            shutil.copy(old_file, destination / used_file)

    def get_matching_efficiency_files(self, cut_files: Iterable[Path]) \
            -> Set[Path]:
        """Returns a set of efficiency files whose elements match those
        of given cut files.
        """
        matched_efficiencies = set()

        eff_elems = {
            Detector.get_used_efficiency_file_name(eff_file).stem: eff_file
            for eff_file in self.get_efficiency_files()
        }

        for cut in cut_files:
            # TODO check for RBS selection too
            cut_element_str = cut.name.split(".")[1]

            if cut_element_str in eff_elems:
                matched_efficiencies.add(eff_elems[cut_element_str])

        return matched_efficiencies

    def copy_foils(self) -> List[Foil]:
        """Returns a copy of foils in detector."""
        return [Foil.generate_foil(**foil.to_dict()) for foil in self.foils]

    def copy_tof_foils(self) -> List[int]:
        """Returns a copy of ToF foils in detector."""
        return [tof_foil for tof_foil in self.tof_foils]
