# coding=utf-8
"""
Created on 30.3.2018
Edited on 6.4.2018
"""
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"
__version__ = "2.0"

import os
from modules.measurement import Measurements, Measurement
from modules.simulation import Simulations, Simulation
import re


class Samples:
    """
    Class for handling multiple samples.
    """

    def __init__(self, request):
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

    def add_sample(self, sample_path=None, name=""):
        """
        Create and add a Sample to the samples.

        Args:
            sample_path: The path of the sample to be added to the samples.
            name: Optional name for the sample.
        """
        if sample_path:
            sample_path, sample_dir = os.path.split(sample_path)
            dir_split = sample_dir.split("-")
            prefix = dir_split[0].split("_")
            serial_string = prefix[1]
            try:
                serial_number = int(serial_string)
                sample = Sample(serial_number, self.request, sample_dir, name)
            except Exception as e:
                # Couldn't read sample's serial number from file path.
                print("Couldn't read sample's serial number from path. " + e)
                return
        else:
            next_serial = self.request.get_running_int()
            sample_dir = "Sample_" + "%02d" % next_serial + "-" + name
            new_path = os.path.join(self.request.directory, sample_dir)
            sample = Sample(next_serial, self.request, sample_dir, name)
            self.request.increase_running_int_by_1()
            if not os.path.exists(new_path):
                os.makedirs(new_path)
        self.samples.append(sample)
        return sample

    def get_samples_and_measurements(self):
        """
        Collects all the samples and the measurement files under them into a dictionary.

        Return:
            A dictionary containing samples and their measurements.
        """
        all_samples_and_measurements = {}
        for sample in self.samples:
            all_samples_and_measurements[sample] = sample.get_measurements_files()
        return all_samples_and_measurements

    def get_samples_and_simulations(self):
        """
        Collects all the samples and the simulation files under them into a dictionary.

        Return:
            A dictionary containing samples and their simulations.
        """
        all_samples_and_simulations = {}
        for sample in self.samples:
            all_samples_and_simulations[sample] = sample.get_simulation_files()
        return all_samples_and_simulations


class Sample:
    """
    Class for a sample.
    """

    def __init__(self, serial_number, request, directory, name=""):
        """
        Initialize the Sample.

        Args:
            serial_number: Serial number for sample.
            request: Which request the sample belongs to.
            name: Optional name for the sample.
        """
        self.name = name
        self.serial_number = serial_number
        self.request = request

        self.directory = directory

        self.measurements = Measurements(request)
        self.simulations = Simulations(request)

        self._running_int_measurement = 1
        self._running_int_simulation = 1

    def get_running_int_measurement(self):
        return self._running_int_measurement

    def increase_running_int_measurement_by_1(self):
        self._running_int_measurement = self._running_int_measurement + 1

    def get_running_int_simulation(self):
        return self._running_int_simulation

    def increase_running_int_simulation_by_1(self):
        self._running_int_simulation = self._running_int_simulation + 1

    def get_measurements_files(self):
        """
        Get measurements files inside sample folder.

        Return:
            A list of measurement file names.
        """
        # TODO: Possible for different formats (such as binary data .lst)
        all_measurements = []
        for item in os.listdir(os.path.join(self.request.directory, self.directory)):
            if item.startswith("Measurement_"):
                measurement_name_start = item.find('-')
                if measurement_name_start == -1:  # measurement needs to have a name.
                    return []
                number_str = item[measurement_name_start - 2]
                if number_str == "0":
                    self._running_int_measurement = int(item[measurement_name_start - 1])
                else:
                    self._running_int_measurement = int(item[measurement_name_start - 2:measurement_name_start - 1])
                measurement_name = item[measurement_name_start+1:]
                if os.path.isfile(os.path.join(self.request.directory, self.directory, item, "Data", measurement_name + ".asc")):
                    all_measurements.append(measurement_name + ".asc")
        return all_measurements

    def get_simulation_files(self):
        """Get simulation files inside request folder.

        Return:
            A list of simulation file names.
        """
        return [f for f in os.listdir(os.path.join(self.request.directory, self.directory))
                if os.path.isfile(os.path.join(self.request.directory, self.directory, f)) and
                os.path.splitext(f)[1] == ".sim" and
                os.stat(os.path.join(self.request.directory, self.directory, f)).st_size]  # Do not load empty files.

    def remove_obj(self, obj_removed):
        """Removes given object from sample.
        Args:
            obj_removed: Object to remove.
        """
        if isinstance(obj_removed, Measurement):
            self.measurements.remove_obj(obj_removed)
        elif isinstance(obj_removed, Simulation):
            self.simulations.remove_obj(obj_removed)
