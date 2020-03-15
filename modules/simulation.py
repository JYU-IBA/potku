# coding=utf-8
"""
Created on 26.2.2018
Updated on 29.1.2020

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

__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä " \
             "\n Sinikka Siironen"
__version__ = "2.0"

import json
import logging
import os
import sys
import time
import itertools
import collections

import modules.general_functions as gf

from modules.detector import Detector
from modules.element_simulation import ElementSimulation
from modules.run import Run
from modules.target import Target
from modules.ui_log_handlers import Logger


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
        directory_prefix = Simulation.DIRECTORY_PREFIX
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
            simulation.sample = sample
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
                    with open(
                            os.path.join(simulation.directory,
                                         measurement_settings_file)) as mesu_f:
                        mesu_settings = json.load(mesu_f)

                    simulation.measurement_setting_file_name = \
                        mesu_settings["general"]["name"]
                    simulation.measurement_setting_file_description = \
                        mesu_settings["general"]["description"]
                    simulation.modification_time = \
                        mesu_settings["general"]["modification_time_unix"]
                    break

            # Read Detector information from file.
            det_folder = os.path.join(simulation_folder_path,
                                      "Detector")
            if os.path.isdir(det_folder):
                for file in os.listdir(det_folder):
                    if file.endswith(detector_extension):
                        simulation.detector = Detector.from_file(
                            os.path.join(det_folder, file),
                            os.path.join(simulation.directory,
                                         measurement_settings_file),
                            self.request)
                        simulation.detector.update_directories(det_folder)
                        break

            for file in os.listdir(simulation_folder_path):
                # Read Target information from file.
                if file.endswith(target_extension):
                    simulation.target = Target.from_file(os.path.join(
                        simulation_folder_path, file), os.path.join(
                        simulation_folder_path,
                        measurement_settings_file), self.request)

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
                            mcsimu_file_path, profile_file_path,
                            sample=simulation.sample,
                            detector=simulation.detector
                        )
                        simulation.element_simulations.append(
                            element_simulation)
                        element_simulation.run = simulation.run
                        element_simulation.target = Target.from_file(
                            target_file_path, measurement_file_path,
                            self.request)
                        element_simulation.simulation = simulation

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
                                        name=simulation_name, tab_id=tab_id,
                                        sample=sample)
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


class Simulation(Logger):
    """
    A Simulation class that handles information about one Simulation.
    """
    __slots__ = "path", "request", "simulation_file", "name", "tab_id", \
                "description", "modification_time", "run", "detector", \
                "target", "element_simulations", \
                "serial_number", "directory", "measurement_setting_file_name", \
                "measurement_setting_file_description", \
                "sample", "running_simulations", "use_request_settings"

    DIRECTORY_PREFIX = "MC_simulation_"

    def __init__(self, path, request, name="Default",
                 description="",
                 modification_time=None, tab_id=-1, run=None,
                 detector=None, target=None,
                 measurement_setting_file_name="",
                 measurement_setting_file_description="", sample=None,
                 use_request_settings=True,
                 save_on_creation=True):
        """Initializes Simulation object.

        Args:
            path: Path to .simulation file.
            request: Request object.
            name: Name of the simulation.
            description: Description of the simulation.
            modification_time: Modification time of the .simulation file.
            tab_id: Tab id.
            run: Run object.
            detector: Detector object.
            target: Target object.
            measurement_setting_file_name: Measurement settings file name.
            measurement_setting_file_description: Measurement settings file
            description.
            sample: Sample object under which Simulation belongs.
            use_request_settings: whether ElementSimulations under this
                simulation use request settings or simulation settings
            save_on_creation: whether the Simulation is written to file when
                              initialized.
        """
        # Run the base class initializer to establish logging
        Logger.__init__(self, name, "Simulation")

        self.tab_id = tab_id
        self.path = path
        self.request = request
        self.sample = sample

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
        self.use_request_settings = use_request_settings
        if not self.target:
            self.target = Target()

        self.serial_number = 0

        self.defaultlog = None
        self.errorlog = None

        self.directory, self.simulation_file = os.path.split(self.path)
        self.create_folder_structure()
        self.running_simulations = []

        if save_on_creation:
            self.to_file(self.path)

    def create_folder_structure(self):
        """
        Create folder structure for simulation.
        """
        self.__make_directories(self.directory)
        self.set_loggers(self.directory, self.request.directory)

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

    def rename_simulation_file(self):
        """Renames the simulation files with self.simulatio_file.
        """
        simulation_file = None
        for file in os.listdir(self.directory):
            if file.endswith(".simulation"):
                simulation_file = file
                break
        if simulation_file:
            gf.rename_file(os.path.join(self.directory, simulation_file),
                           self.simulation_file)

    def add_element_simulation(self, recoil_element):
        """Adds ElementSimulation to Simulation.

        Args:
            recoil_element: RecoilElement that is simulated.
        """
        element_str = recoil_element.element.get_prefix()
        name = self.request.default_element_simulation.name

        if recoil_element.type == "rec":
            simulation_type = "ERD"
        else:
            simulation_type = "RBS"

        element_simulation = ElementSimulation(directory=self.directory,
                                               request=self.request,
                                               simulation=self,
                                               name_prefix=element_str,
                                               name=name,
                                               target=self.target,
                                               detector=self.detector,
                                               recoil_elements=[recoil_element],
                                               run=self.run,
                                               sample=self.sample,
                                               simulation_type=simulation_type)
        # element_simulation.recoil_elements.append(recoil_element)
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
        with open(file_path) as file:
            simu_obj = json.load(file)

        # Overwrite the human readable time stamp with unix time stamp, as
        # that is what the Simulation object uses internally
        simu_obj["modification_time"] = simu_obj.pop("modification_time_unix")

        return cls(request=request, path=file_path, **simu_obj)

    def to_file(self, file_path):
        """Save simulation settings to a file.

        Args:
            file_path: File in which the simulation settings will be saved.
        """

        # TODO could add file paths to detector and run files here too
        obj = {
            "name": self.name,
            "description": self.description,
            "modification_time": time.strftime("%c %z %Z", time.localtime(
                time.time())),
            "modification_time_unix": time.time(),
            "use_request_settings": self.use_request_settings
        }

        with open(file_path, "w") as file:
            json.dump(obj, file, indent=4)

    def update_directory_references(self, new_dir):
        """
        Update simualtion's directory references.

        Args:
            new_dir: Path to simulation folder with new name.
        """
        self.directory = new_dir
        self.simulation_file = self.name + ".simulation"

        self.path = os.path.join(self.directory, self.simulation_file)
        if self.detector:
            self.detector.update_directory_references(self)

        for elem_sim in self.element_simulations:
            elem_sim.directory = new_dir

        self.set_loggers(self.directory, self.request.directory)

    def get_running_simulations(self):
        """Returns a shallow copy of ElementSimulations that are running on
        either simulation specific settings or request specific settings.
        """
        request_sims = (elem_sim for elem_sim in self.element_simulations
                        if elem_sim in self.request.running_simulations)
        return list(itertools.chain(request_sims, self.running_simulations))

    def get_finished_simulations(self):
        """Returns a list of ElementSimulations that have finished.
        """
        return list(
            elem_sim for elem_sim in self.element_simulations
            if elem_sim.simulations_done
        )

    def get_running_optimizations(self):
        """Returns a list of ElementSimulations that have a running
        optimization.
        """
        return list(
            elem_sim for elem_sim in self.element_simulations
            if elem_sim.optimization_running
        )

    def get_finished_optimizations(self):
        """Returns a list of finished optimizations.
        """
        return list(
            elem_sim for elem_sim in self.element_simulations
            # TODO better way to determine if an optimization has been
            #      done. ElementSimulation should not have a direct
            #      reference to a widget
            if elem_sim.optimization_widget is not None and
            not elem_sim.optimization_running
        )

    def get_active_simulations(self):
        """Returns a named tuple of all simulations that are either running
        or have results.
        """
        simulations = collections.namedtuple(
            "Simulations",
            ("running_simulations", "finished_simulations",
             "running_optimizations", "finished_optimizations"),
        )
        return simulations(
            self.get_running_simulations(),
            self.get_finished_simulations(),
            self.get_running_optimizations(),
            self.get_finished_optimizations()
        )
