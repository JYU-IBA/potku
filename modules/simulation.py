# coding=utf-8
"""
Created on 26.2.2018
Updated on 11.4.2018

#TODO Description of Potku and copyright
#TODO Licence

Simulation.py runs the MCERD simulation with a command file.
"""
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"
__version__ = "2.0"

import os
import platform
import subprocess
import logging
import sys
import shutil
import datetime
from enum import Enum
from json import JSONEncoder

from modules.general_functions import save_settings
from modules.beam import Beam
from modules.detector import Detector
from modules.target import Target


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
        simulation_folder = os.path.join(sample.directory, name_prefix +
                              "%02d" % sample.get_running_int_simulation() + "-"
                              + simulation_name)
        sample.increase_running_int_simulation_by_1()
        try:
            # if file_directory != self.request.directory and file_directory:
            #     dirtyinteger = 2  # Begin from 2, since 0 and 1 would be confusing.
            #     while os.path.exists(new_file):
            #         file_name = "{0}_{1}{2}".format(name[0],
            #                                         dirtyinteger,
            #                                         name[1])
            #         new_file = os.path.join(sample.path, file_name)
            #         dirtyinteger += 1
            #     shutil.copyfile(name, new_file)
            #     file_directory, file_name = os.path.split(new_file)
            #
            #     log = "Added new simulation {0} to the request.".format(file_name)
            #     logging.getLogger("request").info(log)
            keys = sample.simulations.simulations.keys()
            for key in keys:
                if sample.simulations.simulations[key].directory == \
                        simulation_name:
                    return simulation  # simulation = None
            simulation = Simulation(self.request, simulation_name)
            simulation.create_folder_structure(simulation_folder)
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

    def __init__(self, request, tab_id, name="", description=""):
        self.request = request
        self.tab_id = tab_id
        self.name = name
        self.description = description

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


class ElementSimulationEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ElementSimulation):
            return {
                "name": obj.name,
                "date": obj.modification_time.isoformat(),
                "simulation_type": obj.simulation_type,
                "scatter": obj.minimum_scattering_angle,
                "main_scatter": obj.minimum_main_scattering_angle,
                "energy": obj.minimum_energy,
                "mode": obj.simulation_mode,
                "no_of_ions": obj.number_of_ions,
                "no_of_preions": obj.number_of_preions,
                "seed": obj.seed_number,
                "no_of_recoils": obj.number_of_recoils,
                "no_of_scaling": obj.number_of_scaling_ions
            }
        return super(ElementSimulationEncoder, self).default(obj)


class ElementSimulation:
    """ElementSimulation class handles the simulation parameters and data."""

    __slots__ = "name", \
                "modification_time", \
                "simulation_type", "number_of_ions", "number_of_preions", \
                "number_of_scaling_ions", "number_of_recoils", \
                "minimum_scattering_angle", \
                "minimum_main_scattering_angle", "minimum_energy", \
                "simulation_mode", "seed_number", \
                "element", "recoil_atoms", "mcerd", "get_espe", \
                "channel_width", "reference_density", "beam", "target", \
                "detector",

    def __init__(self, name="",
                 modification_time=datetime.datetime.now(),
                 simulation_type="rec",
                 number_of_ions=1000000, number_of_preions=100000,
                 number_of_scaling_ions=5, number_of_recoils=10,
                 minimum_main_scattering_angle=20,
                 simulation_mode="narrow", seed_number=101,
                 minimum_energy=1.0, channel_width=0.1,
                 reference_density=4.98e22):
        """Inits Simulation.
        Args:
            request: Request class object.
        """
        self.name = name
        self.modification_time = modification_time

        self.simulation_type = simulation_type
        self.simulation_mode = simulation_mode
        self.number_of_ions = number_of_ions
        self.number_of_preions = number_of_preions
        self.number_of_scaling_ions = number_of_scaling_ions
        self.number_of_recoils = number_of_recoils
        self.minimum_main_scattering_angle = minimum_main_scattering_angle
        self.minimum_energy = minimum_energy
        self.seed_number = seed_number
        self.channel_width = channel_width
        self.reference_density = reference_density

        self.beam = Beam()
        self.target = Target()
        self.detector = Detector()

        settings = {
            "simulation_type": self.simulation_type,
            "number_of_ions": self.number_of_ions,
            "number_of_preions_in_presimu": self.number_of_preions,
            "number_of_scaling_ions": self.number_of_scaling_ions,
            "number_of_recoils": self.number_of_recoils,
            "minimum_main_scattering_angle": self.minimum_main_scattering_angle,
            "minimum_energy_of_ions": self.minimum_energy,
            "simulation_mode": self.simulation_mode,
            "seed_number": self.seed_number,
            "beam": self.beam,
            "target": self.target,
            "detector": self.detector,
            "recoil": None
        }

    def save_settings(self, filepath=None):
        """Saves parameters from Simulation object in JSON format in .mc_simu file.

        Args:
            filepath: Filepath including name of the file.
        """
        save_settings(self, ".mc_simu", ElementSimulationEncoder, filepath)

    def add_command_file(self, command_file):
        """ Adds command file to Simulation object.

        Args:
            command_file: Command file to add.
        """
        simulation_folder, name = os.path.split(command_file)
        self.simulation_file = name  # With extension
        self.name = os.path.splitext(name)[0]
        self.create_directory(simulation_folder)


class CallGetEspe(object):
    """Handles calling the external program get_espe to generate energy spectra coordinates."""

    def __init__(self, command_file_path):
        """Inits CallGetEspe.

tash list

   ssArgs:
            command_file_path: Full path of where simulation command file is located.
        """

        # Options for get_espe, here only temporarily:
        #
        # get_espe - Calculate an energy spectrum from simulated ERD data
        #
        # Options:
        #         -real    only real events are handled
        #         -ch      channel width in the output (MeV)
        #         -depth   depth range of the events (nm, two values)
        #         -dist    file name for depth distribution
        #         -m2      average mass of the secondary particles (u)
        #         -avemass use average mass for calculating energy from TOF
        #         -scale   scale the total intensity to value
        #         -err     give statistics in the third column
        #         -detsize limit in the size of the detector foil (mm)
        #         -erange  energy range in the output spectrum (MeV)
        #         -timeres time resolution of the TOF-detector (ps, FWHM)
        #         -eres    energy resolution (keV, FWHM) of the SSD, (energy signal used!)
        #         -toflen  time-of-flight length (m)
        #         -beam    mass number and the chemical symbol of the primary ion
        #         -dose    dose of the beam (particle-┬╡C)
        #         -energy  beam energy (MeV)
        #         -theta   scattering angle (deg)
        #         -tangle  angle between target surface and beam (deg)
        #         -solid   solid angle of the detector (msr)
        #         -density surface atomic density of the first 10 nm layer (at/cm^2)

        # TODO When the directory structure for simulation settings has been decided, update this
        # self.bin_dir = "%s%s%s" % ("external", os.sep, "Examples")
        # TODO Read the parameters from the program

        # Example parameters:
        input_file = "35Cl-85-LiMnO_Li.*.erd"
        params = ["-beam 35Cl", "-energy 8.515", "-theta 41.12", "-tangle 20.6",
                  "-timeres 250.0",
                  "-toflen 0.623", "-solid 0.2", "-dose 8.1e12", "-avemass",
                  "-density 4.98e16", "-dist " + command_file_path + os.sep +
                  "recoiling.LiMnO_Li",
                  "-ch 0.02"]  # recoiling file needs to be a parameter
        params_string = " ".join(params)
        self.output_file = "LiMnO_Li.simu"

        self.command_win = "type " + command_file_path + os.sep + input_file + " | " + "external\Potku-bin\get_espe " \
                           + params_string + " > " + command_file_path + os.sep + self.output_file
        self.command_linux = "cat " + command_file_path + os.sep + input_file + " | " + "external/Potku-bin/get_espe_linux " \
                             + params_string + " > " + command_file_path + os.sep + self.output_file
        self.command_mac = "cat " + command_file_path + os.sep + input_file + " | " + "external/Potku-bin/get_espe_mac " \
                           + params_string + " > " + command_file_path + os.sep + self.output_file

    def run_get_espe(self):
        """Runs get_espe. It generates an energy spectrum coordinate file from the result of MCERD.
        """
        used_os = platform.system()
        if used_os == "Windows":
            subprocess.call(self.command_win, shell=True)
        elif used_os == "Linux":
            subprocess.call(self.command_linux, shell=True)
        elif used_os == "Darwin":
            subprocess.call(self.command_mac, shell=True)
        else:
            print("It appears we do not support your OS.")

# For testing the CallMCERD class:
# CallMCERD(r"C:\Users\localadmin\potku\requests\testi7\35Cl-85-LiMnO_Li").run_simulation()
# MCERD tries to read the input files from the path specified in the command file
# CallMCERD(r"..\Examples\35Cl-85-LiMnO_Li").run_simulation()

# For testing the CallGetEspe class:
# test_espe = CallGetEspe("")
# test_espe.run_get_espe()
