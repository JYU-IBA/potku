# coding=utf-8
"""
Created on 30.3.2018
Edited on 21.6.2018

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
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä " \
             "\n Sinikka Siironen"
__version__ = "2.0"

import os
import re

from pathlib import Path
from typing import Optional
from typing import Union
from typing import Dict
from typing import List
from typing import Iterable

from .measurement import Measurements
from .measurement import Measurement
from .simulation import Simulations
from .simulation import Simulation


class Samples:
    """Class for handling multiple samples.
    """

    def __init__(self, request: "Request"):
        """
        Initialize the Samples.

        Args:
            request: Which request the samples belong to.
        """
        self.request = request
        self.samples = []

        # These attributes are needed for handling tabs
        self.measurements = Measurements(self.request)
        self.simulations = Simulations(self.request)

    def add_sample(self, sample_path: Optional[Path] = None,
                   name: str = "") -> Optional["Sample"]:
        """Create and add a Sample to the samples.

        Args:
            sample_path: The path of the sample to be added to the samples.
            name: Optional name for the sample.
        """
        if sample_path is not None:
            if name == "":
                name = sample_path.name.split("-", 1)[1]
            sample = Sample(Sample.get_number_from_directory_name(sample_path), self.request, sample_path.name, name)
        else:
            self.request.increase_running_int_by_1()
            next_serial = self.request.get_running_int()
            sample_dir = Sample.DIRECTORY_PREFIX + f"{next_serial:02d}-{name}"
            new_path = Path(self.request.directory, sample_dir)
            sample = Sample(next_serial, self.request, sample_dir, name)
            new_path.mkdir(exist_ok=True)
        self.samples.append(sample)
        self.request._running_int = max(self.request._running_int, sample.serial_number)
        return sample

    def get_samples_and_measurements(self) -> Dict["Sample", List[Path]]:
        """Collects all the samples and the measurement files under them into a
        dictionary.

        Return:
            A dictionary containing samples and their measurements.
        """
        all_samples_and_measurements = {}
        for sample in self.samples:
            all_samples_and_measurements[sample] = \
                sample.get_measurements_files()
        return all_samples_and_measurements

    def get_samples_and_simulations(self) -> Dict["Sample", List[Path]]:
        """Collects all the samples and the simulation files under them into a
        dictionary.

        Return:
            A dictionary containing samples and their simulations.
        """
        all_samples_and_simulations = {}
        for sample in self.samples:
            all_samples_and_simulations[sample] = sample.get_simulation_files()
        return all_samples_and_simulations

class Sample:
    """Class for a sample.
    """
    DIRECTORY_PREFIX = "Sample_"

    def __init__(self, serial_number: int, request: "Request", dir_name: str,
                 name: str = ""):
        """
        Initialize the Sample.

        Args:
            serial_number: Serial number for sample.
            request: Which request the sample belongs to.
            dir_name: name of the sample directory
            name: Optional name for the sample.
        """
        self.name = name
        self.serial_number = serial_number
        self.request = request

        self.directory = dir_name

        self.measurements = Measurements(request)
        self.simulations = Simulations(request)

        self._running_int_measurement = 1
        self._running_int_simulation = 1

    def long_name(self):
        return f"Sample {self.serial_number:02d} {self.name}"

    def get_running_int_measurement(self) -> int:
        """Get running int for measurements,

        Return:
            Integer.
        """
        return self._running_int_measurement

    def increase_running_int_measurement_by_1(self):
        """Increase running int for measurement by one.
        """
        self._running_int_measurement += 1

    def get_running_int_simulation(self) -> int:
        """Get running int for simulations,

        Return:
            Integer.
        """
        return self._running_int_simulation

    def increase_running_int_simulation_by_1(self):
        """Increase running int for simulation by one.
        """
        self._running_int_simulation += 1

    def get_measurements_files(self) -> List[Path]:
        """
        Get measurements files inside sample folder.

        Return:
            A list of full paths to measurement files.
        """
        all_measurements = []   # TODO refactor
        name_prefix = Measurement.DIRECTORY_PREFIX
        all_dirs = os.listdir(Path(self.request.directory, self.directory))
        all_dirs.sort()

        for directory in all_dirs:
            # Only handle directories that start with name_prefix
            if directory.startswith(name_prefix):
                try:
                    # Read measurment number from directory name
                    self._running_int_measurement = int(
                        directory[len(name_prefix):len(name_prefix) + 2])
                    for file in os.listdir(Path(
                            self.request.directory, self.directory, directory)):
                        if file.endswith(".info"):  # TODO break?
                            all_measurements.append(Path(
                                self.request.directory, self.directory,
                                directory, file))
                except ValueError:
                    # Couldn't add measurement directory because the number
                    # could not be read
                    continue
        if all_measurements:
            # Increment running int so it's ready to use when creating new
            # measurement under this sample
            self.increase_running_int_measurement_by_1()
        return all_measurements

    def get_simulation_files(self) -> List[Path]:
        """Get .simulation or .mccfg files inside simulation directories.

        Return:
            A list of full paths to .simulation or .mccfg files.
        """
        all_simulations = []    # TODO refactor
        name_prefix = Simulation.DIRECTORY_PREFIX
        all_dirs = os.listdir(Path(self.request.directory, self.directory))
        all_dirs.sort()     # TODO why sort here?

        for directory in all_dirs:
            # Only handle directories that start with name_prefix
            if directory.startswith(name_prefix):
                try:
                    # Read simulation number from directory name
                    self._running_int_simulation = int(
                        directory[len(name_prefix):len(name_prefix) + 2])
                    for file in os.listdir(Path(
                            self.request.directory, self.directory, directory)):
                        if file.endswith(".mccfg") or file.endswith(".simulation"):
                            all_simulations.append(Path(
                                self.request.directory, self.directory,
                                directory, file))
                            break
                except ValueError:
                    # Couldn't add simulation directory because the number
                    # could not be read
                    continue
        if all_simulations:
            # Increment running int so it's ready to use when creating new
            # simulation under this sample
            self.increase_running_int_simulation_by_1()
        return all_simulations

    def remove_obj(self, obj_removed: Union[Measurement, Simulation]):
        """Removes given object from sample.

        Args:
            obj_removed: Object to remove.
        """
        if isinstance(obj_removed, Measurement):
            self.measurements.remove_obj(obj_removed)
        elif isinstance(obj_removed, Simulation):
            self.simulations.remove_obj(obj_removed)

    def get_measurements(self) -> Iterable[Measurement]:
        for measurement in self.measurements.measurements.values():
            yield measurement

    @classmethod
    def get_number_from_directory_name(cls, dir_name: Path) -> int:
        """Returns sample number from a directory path.
        Sample directories are expected to be e.g. "Sample_02-Something".

        Args:
            dir_name: Path to sample directory, can be full path.
        Return:
                Sample number. Zero if directory name is not appropriate.
        """
        m = re.search(r"^"+ Sample.DIRECTORY_PREFIX + r"(\d*)-", dir_name.name)

        if m:
            return int(m.group(1))
        else:
            return 0
