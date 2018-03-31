# coding=utf-8
"""
Created on 30.3.2018
Edited on 31.3.2018
"""
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"
__version__ = "2.0"

import os
from modules.measurement import Measurements
from modules.simulation import Simulations


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
        self.measurements = Measurements(self.request)
        self.simulations = Simulations(self.request)
        self.samples = []

    def add_sample_file(self, sample_path):
        """
        Create and add a Sample to the samples.

        Args:
            sample_path: The path of the sample to be added to the samples.
        """
        sample = Sample(sample_path, self.request)
        self.samples.append(sample)

    def get_samples_and_measurements(self):
        """
        Collects all the samples' paths and the measurement files under them into a dict.

        Return:
            A dictionary containing samples and their measurements.
        """
        all_samples_and_measurements = {}
        for sample in self.samples:
            all_samples_and_measurements[sample.path] = sample.get_measurements_files()
        return all_samples_and_measurements

    def get_samples_and_simulations(self):
        """
        Collects all the samples' paths and the simulation files under them into a dict.

        Return:
            A dictionary containing samples and their simulations.
        """
        all_samples_and_simulations = {}
        for sample in self.samples:
            all_samples_and_simulations[sample.path] = sample.get_simulation_files()
        return all_samples_and_simulations


class Sample:
    """
    Class for a sample.
    """

    def __init__(self, path, request):
        """
        Initialize the Sample.

        Args:
            path: Path of the sample
            request: Which request the sample belongs to.
        """
        self.path = path
        self.measurements = Measurements(request)

        if not os.path.exists(self.path):
            os.makedirs(self.path)

    def get_measurements_files(self):
        """
        Get measurements files inside sample folder.

        Return:
            A list of measurement file names.
        """
        # TODO: Possible for different formats (such as binary data .lst)
        return [f for f in os.listdir(self.path)
                if os.path.isfile(os.path.join(self.path, f)) and
                os.path.splitext(f)[1] == ".asc" and
                os.stat(os.path.join(self.path, f)).st_size]  # Do not load empty files.

    def get_simulation_files(self):
        """Get simulation files inside request folder.

        Return:
            A list of simulation file names.
        """
        return [f for f in os.listdir(self.path)
                if os.path.isfile(os.path.join(self.path, f)) and
                os.path.splitext(f)[1] == ".sim" and
                os.stat(os.path.join(self.path, f)).st_size]  # Do not load empty files.
