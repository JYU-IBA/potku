# coding=utf-8
"""
Created on 26.2.2018
Updated on 27.4.2018

#TODO Description of Potku and copyright
#TODO Licence

Simulation.py runs the MCERD simulation with a command file.
"""
import re

from modules.element_simulation import ElementSimulation
from modules.target import Target

__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä " \
             "\n Sinikka Siironen"
__version__ = "2.0"

import logging
import os
import sys


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
        if key not in self.simulations:
            return None
        return self.simulations[key]

    def add_simulation_file(self, sample, simulation_name, tab_id):
        """Add a new file to simulations.

        Args:
            sample: The sample under which the simulation is put.
            simulation_name: Name of the simulation (not a path)
            tab_id: Integer representing identifier for simulation's tab.

        Return:
            Returns new simulation or None if it wasn't added
        """
        simulation = None
        name_prefix = "MC_simulation_"
        if name_prefix in simulation_name:
            plain_name = re.sub('^MC_simulation_\d\d-', '', simulation_name)
            serial_number = int(simulation_name[len(name_prefix):len(
                name_prefix)+2])
        else:
            plain_name = simulation_name
            serial_number = sample.get_running_int_simulation()
            sample.increase_running_int_simulation_by_1()
        simulation_folder = os.path.join(
            sample.request.directory, sample.directory, name_prefix +
                                                        "%02d" % serial_number + "-"
                                                        + plain_name)
        try:
            keys = sample.simulations.simulations.keys()
            for key in keys:
                if sample.simulations.simulations[key].directory == \
                        plain_name:
                    return simulation  # simulation = None
            simulation = Simulation(self.request, plain_name,
                                    run=self.request.default_run,
                                    detector=self.request.default_detector)
            simulation.create_folder_structure(simulation_folder)
            simulation.serial_number = serial_number
            sample.simulations.simulations[tab_id] = simulation
            self.request.samples.simulations.simulations[tab_id] = simulation
        except:
            log = "Something went wrong while adding a new simulation."
            logging.getLogger("request").critical(log)
            print(sys.exc_info())  # TODO: Remove this.
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

    def __init__(self, request, name, tab_id=-1, description="", run=None,
                 detector=None):
        self.request = request
        self.tab_id = tab_id
        self.name = name
        self.description = description
        self.element_simulations = []

        self.run = run
        self.target = Target()
        self.detector = detector

        self.name_prefix = "MC_simulation_"
        self.serial_number = 0
        self.directory = None

    def create_folder_structure(self, simulation_folder_path):
        self.directory = simulation_folder_path
        self.__make_directories(self.directory)

    def create_directory(self, simulation_folder):
        """ Creates folder structure for the simulation.

        Args:
            simulation_folder: Path of the simulation folder.
        """
        self.directory = os.path.join(simulation_folder, self.name)
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
        # Rename any simulation related files.
        pass

    def add_element_simulation(self, recoil_element):
        """Adds ElementSimulation to Simulation.

        Args:
            recoil_element: RecoilElement that is simulated.
        """
        element_simulation = ElementSimulation(recoil_element, self.run.beam,
                                               self.target,
                                               self.detector, self.run)
        self.element_simulations.append(element_simulation)
        return element_simulation
