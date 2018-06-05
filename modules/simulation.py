# coding=utf-8
"""
Created on 26.2.2018
Updated on 5.6.2018

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
            Returns value corresponding to key.
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
        element_simulation_extension = ".mcsimu"
        profile_extension = ".profile"

        # Create simulation from file
        if os.path.exists(simulation_path):
            simulation = Simulation.from_file(sample.request,
                                              simulation_path)
            serial_number = int(simulation_folder[len(directory_prefix):len(
                directory_prefix) + 2])
            simulation.serial_number = serial_number
            simulation.tab_id = tab_id

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

            for file in os.listdir(simulation_folder_path):
                # Read Target information from file.
                if file.endswith(target_extension):
                    simulation.target = Target.from_file(os.path.join(
                        simulation_folder_path, file), os.path.join(
                        simulation_folder_path,
                        measurement_settings_file), self.request)

                # Read Detector information from file.
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

                # Read read ElementSimulation information from files.
                if file.endswith(element_simulation_extension):
                    # .mcsimu file
                    mcsimu_file_path = os.path.join(simulation.directory, file)

                    element_str_with_name = file.split(".")[0]

                    prefix, name = element_str_with_name.split("-")
                    target_file_path = None
                    measurement_file_path = None
                    profile_file_path = ""

                    for f in os.listdir(simulation.directory):
                        if f.endswith(".target"):
                            target_file_path = os.path.join(
                                simulation.directory, f)
                        if f.endswith(measurement_extension):
                            measurement_file_path = os.path.join(
                                simulation.directory, f)
                        if f.endswith(profile_extension) and f.startswith(
                                prefix):
                            profile_file_path = os.path.join(
                                simulation.directory, f)

                    if os.path.exists(profile_file_path):
                        # Create ElementSimulation from files
                        element_simulation = ElementSimulation.from_file(
                            self.request, prefix, simulation_folder_path,
                            mcsimu_file_path, profile_file_path)
                        simulation.element_simulations.append(
                            element_simulation)
                        element_simulation.run = simulation.run
                        element_simulation.target = Target.from_file(
                            target_file_path, measurement_file_path,
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
                self.request.samples.simulations.simulations[
                    tab_id] = simulation
            except:
                log = "Something went wrong while adding a new simulation."
                logging.getLogger("request").critical(log)
                print(sys.exc_info())
        sample.simulations.simulations[tab_id] = simulation
        return simulation

    def remove_obj(self, removed_obj):
        """Removes given simulation.

        Args:
            removed_obj: Simulation to remove.
        """
        self.simulations.pop(removed_obj.tab_id)

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
    """
    A Simulation class that handles information about one Simulation.
    """
    __slots__ = "path", "request", "simulation_file", "name", "tab_id", \
                "description", "modification_time", "run", "detector", \
                "target", "element_simulations", "name_prefix", \
                "serial_number", "directory", "measurement_setting_file_name", \
                "measurement_setting_file_description", "defaultlog", "errorlog"

    def __init__(self, path, request, name="Default",
                 description="",
                 modification_time=None, tab_id=-1, run=None,
                 detector=None, target=None,
                 measurement_setting_file_name="",
                 measurement_setting_file_description=""):
        """Initializes Simulation object.

        Args:
            path: Path to .simulation file.
            request: Request object.
            name: Simulation name.
            description: Simulation description.
            modification_time: Modification time.
            tab_id: Tab id.
            detector: Detector object.
            target: Target object.
            measurement_setting_file_name: Measurement settings file name.
            measurement_setting_file_description: Measurement settings file
            description.
            """
        self.tab_id = tab_id
        self.path = path
        self.request = request

        self.name = name
        self.description = description
        if not modification_time:
            modification_time = time.time()
        self.modification_time = modification_time

        self.measurement_setting_file_name = measurement_setting_file_name
        if not self.measurement_setting_file_name:
            self.measurement_setting_file_name = name
        self.measurement_setting_file_description = \
            measurement_setting_file_description

        self.element_simulations = []

        self.run = run
        self.detector = detector
        self.target = target
        if not self.target:
            self.target = Target()

        self.name_prefix = "MC_simulation_"
        self.serial_number = 0

        self.directory, self.simulation_file = os.path.split(self.path)
        self.create_folder_structure()

        self.to_file(self.path)

    def create_folder_structure(self):
        """
        Create folder structure for simulation.
        """
        self.__make_directories(self.directory)
        self.set_loggers()

    def __make_directories(self, directory):
        """
        Makes a directory and adds the event to log.

        Args:
             directory: Directory to create.
        """
        if not os.path.exists(directory):
            os.makedirs(directory)
            log = "Created a directory {0}.".format(directory)
            logging.getLogger("request").info(log)

    def rename_data_file(self, new_name=None):
        """Renames the simulation files.

        Args:
            new_name: New name of the file.
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

        Return:
            Created element simulation.
        """
        element = recoil_element.element
        if element.isotope:
            element_str = "{0}{1}".format(element.isotope, element.symbol)
        else:
            element_str = element.symbol

        element_simulation = ElementSimulation(directory=self.directory,
                                               request=self.request,
                                               name_prefix=element_str,
                                               target=self.target,
                                               detector=self.detector,
                                               recoil_elements=[
                                                   recoil_element],
                                               run=self.run)
        element_simulation.recoil_elements.append(recoil_element)
        self.element_simulations.append(element_simulation)
        return element_simulation

    def set_loggers(self):
        """Sets the loggers for this specified simulation.

        The logs will be displayed in the simulations folder.
        After this, the simulation logger can be called from anywhere of the
        program, using logging.getLogger([simulation_name]).
        """

        # Initializes the logger for this simulation.
        logger = logging.getLogger(self.name)
        logger.setLevel(logging.DEBUG)

        # Adds two loghandlers. The other one will be used to log info (and up)
        # messages to a default.log file. The other one will log errors and
        # criticals to the errors.log file.
        self.defaultlog = logging.FileHandler(os.path.join(self.directory,
                                                           'default.log'))
        self.defaultlog.setLevel(logging.INFO)
        self.errorlog = logging.FileHandler(os.path.join(self.directory,
                                                         'errors.log'))
        self.errorlog.setLevel(logging.ERROR)

        # Set the formatter which will be used to log messages. Here you can
        # edit the format so it will be deprived to all log messages.
        defaultformat = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S')

        requestlog = logging.FileHandler(os.path.join(self.request.directory,
                                                      'request.log'))
        requestlogformat = logging.Formatter(
            '%(asctime)s - %(levelname)s - [Measurement : '
            '%(name)s] - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

        # Set the formatters to the logs.
        requestlog.setFormatter(requestlogformat)
        self.defaultlog.setFormatter(defaultformat)
        self.errorlog.setFormatter(defaultformat)

        # Add handlers to this simulation's logger.
        logger.addHandler(self.defaultlog)
        logger.addHandler(self.errorlog)
        logger.addHandler(requestlog)

    @classmethod
    def from_file(cls, request, file_path):
        """Initialize Simulation from a JSON file.

        Args:
            request: Request which the Simulation belongs to.
            file_path: A file path to JSON file containing the
            simulation information.

        Return:
            Simulation object.
        """
        obj = json.load(open(file_path))

        # Below we do conversion from dictionary to Simulation object
        name = obj["name"]
        description = obj["description"]
        modification_time = obj["modification_time_unix"]

        return cls(request=request, path=file_path, name=name,
                   description=description, modification_time=modification_time)

    def to_file(self, file_path):
        """Save simulation info to a file.

        Args:
            file_path: File in which the simulation info will be saved."""

        obj = {
            "name": self.name,
            "description": self.description,
            "modification_time": time.strftime("%c %z %Z", time.localtime(
                time.time())),
            "modification_time_unix": time.time(),
        }

        with open(file_path, "w") as file:
            json.dump(obj, file, indent=4)
