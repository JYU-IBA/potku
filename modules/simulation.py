# coding=utf-8
"""
Created on 26.2.2018
Updated on 11.5.2018

#TODO Description of Potku and copyright
#TODO Licence

Simulation.py runs the MCERD simulation with a command file.
"""
import datetime
import json
import re
import time

from modules.element_simulation import ElementSimulation
from modules.general_functions import rename_file
from modules.target import Target
from modules.run import Run

__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä " \
             "\n Sinikka Siironen"
__version__ = "2.0"

import logging
import os
import sys
from modules.detector import Detector


class Simulations:
    """Simulations class handles multiple simulations.
    """

    def __init__(self, request):
        """Inits simulations class.
        Args:
            request: Request class object.
        """
        self.request = request
        self.simulations = {}

    def is_empty(self):
        """Check if there are any simulations.

        Return:
            Returns True if there are no simulations currently in the
            simulations object.
        """
        return len(self.simulations) == 0

    def get_key_value(self, key):
        """
        Args:
            key: Key of simulation dictionary.

        Return:
            VReturns value corresponding to key.
        """
        if key not in self.simulations:
            return None
        return self.simulations[key]

    def add_simulation_file(self, sample, simulation_path, tab_id):
        """Add a new file to simulations.

        Args:
            sample: The sample under which the simulation is put.
            simulation_path: Path of the .simulation file.
            tab_id: Integer representing identifier for simulation's tab.

        Return:
            Returns new simulation or None if it wasn't added
        """
        simulation = None

        simulation_folder_path, simulation_file = os.path.split(simulation_path)
        sample_folder, simulation_folder = os.path.split(simulation_folder_path)
        directory_prefix = "MC_simulation_"
        target_extension = ".target"
        measurement_extension = ".measurement"
        detector_extension = ".detector"
        measurement_settings_file = ""

        # Create simulation from file
        if os.path.exists(simulation_path):
            simulation = Simulation.from_file(sample.request,
                                              simulation_path)
            serial_number = int(simulation_folder[len(directory_prefix):len(
                directory_prefix) + 2])
            simulation.serial_number = serial_number

            for f in os.listdir(simulation_folder_path):
                if f.endswith(measurement_extension):
                    measurement_settings_file = f
                    simulation.run = Run.from_file(
                        os.path.join(
                            simulation.directory, measurement_settings_file))
                    obj = json.load(open(os.path.join(
                            simulation.directory, measurement_settings_file)))
                    simulation.measurement_setting_file_name = obj[
                        "general"]["name"]
                    simulation.measurement_setting_file_description = obj[
                        "general"]["description"]
                    simulation.modification_time = obj["general"][
                        "modification_time_unix"]
                    break

            # Read Detector anf Target information from file.
            for file in os.listdir(simulation_folder_path):
                if file.endswith(target_extension):
                    simulation.target = Target.from_file(os.path.join(
                        simulation_folder_path, file), os.path.join(
                        simulation_folder_path,
                        measurement_settings_file), self.request)
                if file.startswith("Detector"):
                    det_folder = os.path.join(simulation_folder_path,
                                                     "Detector")
                    for f in os.listdir(det_folder):
                        if f.endswith(detector_extension):
                            simulation.detector = Detector.from_file(
                                os.path.join(det_folder, f),
                                os.path.join(simulation.directory,
                                             measurement_settings_file),
                                self.request)

        # Create a new simulation
        else:
            # Not stripping the extension
            simulation_name, extension = os.path.splitext(simulation_file)
            try:
                keys = sample.simulations.simulations.keys()
                for key in keys:
                    if sample.simulations.simulations[key].directory == \
                            simulation_name:
                        return simulation  # simulation = None
                simulation = Simulation(simulation_path, self.request,
                                        name=simulation_name, tab_id=tab_id)
                serial_number = int(simulation_folder[len(directory_prefix):len(
                    directory_prefix) + 2])
                simulation.serial_number = serial_number
                sample.simulations.simulations[tab_id] = simulation
                self.request.samples.simulations.simulations[
                    tab_id] = simulation
            except:
                log = "Something went wrong while adding a new simulation."
                logging.getLogger("request").critical(log)
                print(sys.exc_info())
        return simulation

    def remove_by_tab_id(self, tab_id):
        """Removes simulation from simulations by tab id
        Args:
            tab_id: Integer representing tab identifier.
        """

        def remove_key(d, key):
            r = dict(d)
            del r[key]
            return r

        self.simulations = remove_key(self.simulations, tab_id)


class Simulation:
    __slots__ = "path", "request", "simulation_file", "name", "tab_id", \
                "description", "modification_time", "run", "detector", \
                "target", "element_simulations", "name_prefix", \
                "serial_number", "directory", "measurement_setting_file_name", \
                "measurement_setting_file_description"

    def __init__(self, path, request, name="Default",
                 description="This is a default simulation setting file.",
                 modification_time=time.time(), tab_id=-1, run=None,
                 detector=None, target=Target(),
                 measurement_setting_file_name=None,
                 measurement_setting_file_description=""):
        """Initializes Simulation object.

        Args:
            path: Path to .simulation file.
            """
        self.tab_id = tab_id
        self.path = path
        self.request = request
        self.name = name
        self.description = description
        if not measurement_setting_file_name:
            self.measurement_setting_file_name = name
        self.measurement_setting_file_name = measurement_setting_file_name
        self.measurement_setting_file_description = \
            measurement_setting_file_description
        self.modification_time = modification_time
        self.element_simulations = []

        self.run = run
        self.target = target
        self.detector = detector

        self.name_prefix = "MC_simulation_"
        self.serial_number = 0

        self.directory, self.simulation_file = os.path.split(self.path)
        self.create_folder_structure()

        self.to_file(self.path)

    def create_folder_structure(self):
        self.__make_directories(self.directory)

    def __make_directories(self, directory):
        if not os.path.exists(directory):
            os.makedirs(directory)
            # log = "Created a directory {0}.".format(directory)
            # logging.getLogger("request").info(log)

    def rename_data_file(self, new_name=None):
        """Renames the simulation files.
        """
        if new_name is None:
            return
        rename_file(os.path.join(self.directory, self.simulation_file),
                    new_name + ".simulation")
        self.simulation_file = new_name + ".simulation"
        self.path = os.path.join(self.directory, self.simulation_file)
        self.to_file(self.path)

    def add_element_simulation(self, recoil_element):
        """Adds ElementSimulation to Simulation.

        Args:
            recoil_element: RecoilElement that is simulated.
        """
        element = recoil_element.element
        if element.isotope:
            element_str = "{0}{1}".format(element.isotope, element.symbol)
        else:
            element_str = element.symbol

        element_simulation = ElementSimulation(directory=self.directory,
                                               request=self.request,
                                               name=element_str,
                                               recoil_element=recoil_element,
                                               target=self.target,
                                               detector=self.detector)
        self.element_simulations.append(element_simulation)
        return element_simulation

    @classmethod
    def from_file(cls, request, file_path):
        """Initialize Simulation from a JSON file.

        Args:
            request: Request which the Simulation belongs to.
            file_path: A file path to JSON file containing the
            simulation information.
        """
        obj = json.load(open(file_path))

        # Below we do conversion from dictionary to Simulation object
        name = obj["name"]
        description = obj["description"]
        modification_time = obj["modification_time_unix"]

        return cls(request=request, path=file_path, name=name,
                   description=description, modification_time=modification_time)

    def to_file(self, file_path):
        """Save simulation settings to a file.

        Args:
            file_path: File in which the simulation settings will be saved."""

        obj = {
            "name": self.name,
            "description": self.description,
            "modification_time": time.strftime("%c %z %Z", time.localtime(
                time.time())),
            "modification_time_unix": time.time(),
        }

        with open(file_path, "w") as file:
            json.dump(obj, file, indent=4)
