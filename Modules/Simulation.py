# coding=utf-8
"""
Created on 26.2.2018
Updated on 28.2.2018

#TODO Description of Potku and copyright
#TODO Lisence

Simulation.py runs the MCERD simulation with a command file.
"""
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"
__versio__ = "2.0"

import os
import platform
import subprocess
import logging
import sys
from Modules.Functions import md5_for_file
from Modules.Settings import Settings
import shutil
from Modules.Null import Null

class Simulations:
    """Simulations class handles multiple simulations.
    """

    def __init__(self, project):
        """Inits simulations class.

        Args:
            project: Project class object.
        """
        self.project = project
        self.simulations = {}  # Dictionary<Simulation>
        # self.measuring_unit_settings = None
        # self.default_settings = None

    def is_empty(self):
        """Check if there are any simulations.

        Return:
            Returns True if there are no simulations currently in the
            simulations object.
        """
        return len(self.simulations) == 0

    def get_key_value(self, key):
        if not key in self.simulations:
            return None
        return self.simulations[key]

    def add_simulation_file(self, simulation_file, tab_id):
        """Add a new file to simulations.

        Args:
            simulation_file: String representing file containing simulation data.
            tab_id: Integer representing identifier for simulation's tab.

        Return:
            Returns new simulation or None if it wasn't added
        """
        print(simulation_file)
        simulation = None
        simulation_filename = os.path.split(simulation_file)[1]
        simulation_name = os.path.splitext(simulation_filename)
        new_file = os.path.join(self.project.directory, simulation_filename)

        file_directory, file_name = os.path.split(simulation_file)
        try:
            if file_directory != self.project.directory and file_directory:
                dirtyinteger = 2  # Begin from 2, since 0 and 1 would be confusing.
                while os.path.exists(new_file):
                    file_name = "{0}_{1}{2}".format(simulation_name[0],
                                                    dirtyinteger,
                                                    simulation_name[1])
                    new_file = os.path.join(self.project.directory, file_name)
                    dirtyinteger += 1
                shutil.copyfile(simulation_file, new_file)
                file_directory, file_name = os.path.split(new_file)

                log = "Added new simulation {0} to the project.".format(
                    file_name)
                logging.getLogger("project").info(log)
            keys = self.simulations.keys()
            for key in keys:
                if self.simulations[key].simulation_file == file_name:
                    return simulation  # measurement = None
            simulation = Simulation(new_file, self.project, tab_id)
            # measurement.load_data()
            self.simulations[tab_id] = simulation
        except:
            log = "Something went wrong while adding a new simulation."
            logging.getLogger("project").critical(log)
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
    """Simulation class handles the simulation data."""

    def __init__(self, command_file, project, tab_id):
        """Inits Simulation.

        Args:
            project: Project class object.
        """

        simulation_folder, simulation_name = os.path.split(command_file)
        self.simulation_file = simulation_name  # With extension
        self.simulation_name = os.path.splitext(simulation_name)[0]

        self.project = project
        self.directory = os.path.join(simulation_folder, self.simulation_name)

        self.data = []
        self.tab_id = tab_id

        self.__make_directories(self.directory)
        # self.set_loggers()

        # The settings that come from the project
        self.__project_settings = self.project.settings
        # The settings that are individually set for this measurement
        self.simulation_settings = Settings(self.directory, self.__project_settings)

        # Main window's statusbar TODO: Remove GUI stuff.
        self.statusbar = self.project.statusbar

        element_colors = self.project.global_settings.get_element_colors()

        # Which color scheme is selected by default
        self.color_scheme = "Default color"

        self.callMCERD = Null()
        self.call_get_espe = Null()


    def remove_by_tab_id(self, tab_id):
        """Removes simulation from tabs by tab id

        Args:
            tab_id: Integer representing tab identifier.
        """

        def remove_key(d, key):
            r = dict(d)
            del r[key]
            return r

        self.simulations = remove_key(self.simulations, tab_id)


    def __make_directories(self, directory):
        if not os.path.exists(directory):
            os.makedirs(directory)
            # log = "Created a directory {0}.".format(directory)
            # logging.getLogger("project").info(log)

    def load_data(self):
        """Loads measurement data from filepath
        """
        # import cProfile, pstats
        # pr = cProfile.Profile()
        # pr.enable()
        n=0
        try:
            extension = os.path.splitext(self.simulation_file)[1]
            extension = extension.lower()
            if extension == ".asc":
                with open("{0}{1}".format(self.directory, extension)) as fp:
                    for line in fp:
                        n += 1 #Event number
                        # TODO: Figure good way to split into columns. REGEX too slow.
                        split = line.split()
                        split_len = len(split)
                        if split_len == 2:  # At least two columns
                            self.data.append([int(split[0]), int(split[1]), n])
                        if split_len == 3:
                            self.data.append([int(split[0]), int(split[1]), int(split[2]), n])
        except IOError as e:
            error_log = "Error while loading the {0} {1}. {2}".format(
                        "measurement date for the measurement",
                        self.measurement_name,
                        "The error was:")
            error_log_2 = "I/O error ({0}): {1}".format(e.errno, e.strerror)
            logging.getLogger("project").error(error_log)
            logging.getLogger("project").error(error_log_2)
        except Exception as e:
            error_log = "Unexpected error: [{0}] {1}".format(e.errno, e.strerror)
            logging.getLogger("project").error(error_log)
        # pr.disable()
        # ps = pstats.Stats(pr)
        # ps.sort_stats("time")
        # ps.print_stats(10)


class CallMCERD(object):
    """Handles calling the external program MCERD to run the simulation."""

    def __init__(self, command_file_path):
        """Inits CallMCERD.

        Args:
            command_file_path: Full path of where simulation command file is located.
        """
        # TODO When the directory structure for simulation settings has been decided, update this
        self.bin_dir = "%s%s%s" % ("external", os.sep, "Potku-bin")

        self.command_win = "cd " + self.bin_dir + " && mcerd.exe " + command_file_path
        self.command_unix = "cd " + self.bin_dir + " && ./mcerd " + command_file_path

    def run_simulation(self):
        """Runs the simulation.

        """
        used_os = platform.system()
        if used_os == "Windows":
            subprocess.call(self.command_win, shell=True)
        elif used_os == "Linux":
            subprocess.call(self.command_unix, shell=True)
        elif used_os == "Darwin":
            subprocess.call(self.command_unix, shell=True)
        else:
            print("It appears we do not support your OS.")


class CallGetEspe(object):
    """Handles calling the external program get_espe to generate energy spectra coordinates."""

    def __init__(self, command_file_path):
        """Inits CallGetEspe.

        Args:
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
        self.bin_dir = command_file_path
        # self.bin_dir = "%s%s%s" % ("external", os.sep, "Examples")
        # TODO Read the parameters from the program

        # Example parameters:
        input_file = "35Cl-85-LiMnO_Li.*.erd"
        params = {"-beam 35Cl", "-energy 8.515", "-theta 41.12", "-tangle 20.6", "-timeres 250.0",
                  "-toflen 0.623", "-solid 0.2", "-dose 8.1e12", "-avemass",
                  "-density 4.98e16", "-dist " + command_file_path + os.sep +
                  "recoiling.LiMnO_Li", "-ch 0.02"}  # recoiling file needs to be a parameter
        params_string = " ".join(params)
        self.output_file = "LiMnO_Li.simu"

        # TODO: This doesn't work in Windows because the comand_file_path has slashes, not dashes
        self.command_win = "type " + command_file_path + os.sep + input_file + " | " + "external\Potku-bin\get_espe " \
                           + params_string + " > " + command_file_path + os.sep + self.output_file
        self.command_unix = "cat " + command_file_path + os.sep + input_file + " | " + "external/Potku-bin/get_espe" \
                            + params_string + " > " + command_file_path + os.sep + self.output_file

    def run_get_espe(self):
        """Runs get_espe. It generates an energy spectrum coordinate file from the result of MCERD.
        """
        used_os = platform.system()
        if used_os == "Windows":
            subprocess.call(self.command_win, shell=True)
        elif used_os == "Linux":
            subprocess.call(self.command_unix, shell=True)
        elif used_os == "Darwin":
            subprocess.call(self.command_unix, shell=True)
        else:
            print("It appears we do not support your OS.")


# For testing the CallMCERD class:
# CallMCERD(r"C:\Users\localadmin\potku\projects\testi7\35Cl-85-LiMnO_Li").run_simulation()
# MCERD tries to read the input files from the path specified in the command file
# CallMCERD(r"..\Examples\35Cl-85-LiMnO_Li").run_simulation()

# For testing the CallGetEspe class:
# test_espe = CallGetEspe("")
# test_espe.run_get_espe()
