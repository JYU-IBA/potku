# coding=utf-8
"""
Created on 26.2.2018
Updated on 8.4.2018

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
from modules.settings import Settings
import shutil


class Simulations:
    """Simulations class handles multiple simulations.
    """
    def __init__(self, request):
        """Inits simulations class.
        Args:
            request: Request class object.
        """
        # self._directory = os.path.join(sample_directory, "Simulations")
        # self.simulations = []
        self.request = request
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
        simulation_folder = os.path.join(sample.path, name_prefix + sample.get_running_int_simulation() + "-"
                                         + simulation_name)
        sample.increase_running_int_simulation_by_1()
        try:
            # if file_directory != self.request.directory and file_directory:
            #     dirtyinteger = 2  # Begin from 2, since 0 and 1 would be confusing.
            #     while os.path.exists(new_file):
            #         file_name = "{0}_{1}{2}".format(simulation_name[0],
            #                                         dirtyinteger,
            #                                         simulation_name[1])
            #         new_file = os.path.join(sample.path, file_name)
            #         dirtyinteger += 1
            #     shutil.copyfile(simulation_name, new_file)
            #     file_directory, file_name = os.path.split(new_file)
            #
            #     log = "Added new simulation {0} to the request.".format(file_name)
            #     logging.getLogger("request").info(log)
            keys = sample.simulations.simulations.keys()
            for key in keys:
                if sample.simulations.simulations[key].simulation_folder == simulation_name:
                    return simulation  # sismulation = None
            simulation = Simulation(simulation_folder, self.request, tab_id)
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

#     def load_simulation(self, simulation_name):
#         """Loads a single simulation
#         """
#
#         simulation_directory = os.path.join(self._directory, simulation_name)
#
#     def load_simulations(self):
#         """Loads all of the simulations in Simulations directory
#         """
#
#         simulations_directory_content = os.listdir(self._directory)
#         # TODO: Remove non-directories from list
#         for simulation_directory in simulations_directory_content:
#             simulation = Simulation(os.path.join(self._directory, simulation_directory))
#             simulation.load_settings()
#             self.simulations.append(simulation)
#
#     def new_simulation(self, simulation_name):
#         """Adds a new simulation to request.
#
#         Args:
#             simulation_name: Name of the simulation
#
#         Return:
#             Returns new simulation or None if it wasn't added
#         """
#         simulation_directory = os.path.join(self._directory, simulation_name)
#
#         # Check if simulation already exists. In case of exception we should
#         # inform the user that another simulation name should be used.
#         if os.path.exists(simulation_directory): raise EEXIST; return
#
#         # Create a directory for new simulation.
#         try:
#             os.makedirs(simulation_directory)
#         except:
#             log_msg = "Failed creating directory for simulation" + simulation_name
#             logging.getLogger("request").critical(log_msg)
#             # TODO: Inform user also with a pop up window.
#             return
#
#         # Add a new simulation by making a Simulation object and adding it to
#         # list of simulations.
#         try:
#             self.simulations.append(Simulation(simulation_directory))
#             log_msg =  "Added simulation " + simulation_name + " to the request."
#             logging.getLogger("request").info(log_msg)
#         except:
#             log_msg = "Something went wrong while adding simulation" + simulation_name
#             logging.getLogger("request").critical(log_msg)
#             # TODO: Inform user also with a pop up window.
#
#     # TODO: Function for removing simulation


class Simulation:
    """Simulation class handles the simulation data."""

    def __init__(self, simulation_folder, request, tab_id):
        """Inits Simulation.
        Args:
            simulation_folder: The path of the simulation folder
            request: Request class object.
        """

        sim_folder, simulation_name = os.path.split(simulation_folder)
        self.simulation_folder = simulation_name
        name_start_index = simulation_folder.index('-')
        self.simulation_name = simulation_folder[name_start_index + 1:]

        self.request = request
        self.directory = simulation_folder

        self.data = []
        self.tab_id = tab_id

        self.__make_directories(self.directory)
        # self.set_loggers()

        # The settings that come from the request
        self.__request_settings = self.request.settings
        # The settings that are individually set for this measurement
        self.simulation_settings = Settings(self.directory, self.__request_settings)

        # Main window's statusbar TODO: Remove GUI stuff.
        self.statusbar = self.request.statusbar

        element_colors = self.request.global_settings.get_element_colors()

        # Which color scheme is selected by default
        self.color_scheme = "Default color"

        self.callMCERD = None
        self.call_get_espe = None

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
            # logging.getLogger("request").info(log)

    # TODO: Fix this according to simulation (now copied from measurement).
    def load_data(self):
        """Loads measurement data from filepath
        """
        # import cProfile, pstats
        # pr = cProfile.Profile()
        # pr.enable()
        n=0
        try:
            extension = os.path.splitext(self.simulation_folder)[1]
            extension = extension.lower()
            if extension == ".asc":
                with open("{0}{1}".format(self.directory, extension)) as fp:
                    for line in fp:
                        n += 1  # Event number
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
            logging.getLogger("request").error(error_log)
            logging.getLogger("request").error(error_log_2)
        except Exception as e:
            error_log = "Unexpected error: [{0}] {1}".format(e.errno, e.strerror)
            logging.getLogger("request").error(error_log)
        # pr.disable()
        # ps = pstats.Stats(pr)
        # ps.sort_stats("time")
        # ps.print_stats(10)

#     def load_settings(self):
#         """Loads simulation settings from file path. If, for example, no settings
#         file is found for target, then request settings are used.
#         """
#
#
#         params = " ".join(["-beam 35Cl", "-energy 8.515", "-theta 41.12",
#                            "-tangle 20.6", "-timeres 250.0", "-toflen 0.623",
#                            "-solid 0.2", "-dose 8.1e12", "-avemass",
#                            "-density 4.98e16", "-dist recoiling.LiMnO_Li",
#                            "-ch 0.02"])  # recoiling file needs to be a parameter
#         # params_string = " ".join(params)
#         output_file = "LiMnO_Li.simu"
#
#         # TODO: No cd-ing, do this with absolute paths
#         self.command_win = "cd " + self.bin_dir + " && type " + input_file + \
#                            " | " + os.getcwd() + "\external\Potku-bin\get_espe " + params_string + \
#                            " > " + output_file
#         input_file = request.directory +"35Cl-85-LiMnO_Li.*.erd"
#         self.command_win = BIN_DIR + "get_espe " + params
#
#         self.command_unix = "cd " + self.bin_dir + " && cat " + input_file + \
#                             " | " + os.getcwd() + "/external/Potku-bin/get_espe " + params_string + \
#                             " > " + output_file


class CallMCERD(object):
    """Handles calling the external program MCERD to run the simulation."""

    def __init__(self, command_file):
        """Inits CallMCERD.

        Args:
            command_file: Full path to the command file.
        """
        # TODO When the directory structure for simulation settings has been decided, update this
        # self.bin_dir = "%s%s%s" % ("external", os.sep, "Potku-bin")

        self.command_win = "external\Potku-bin\mcerd.exe " + command_file
        self.command_unix = "external/Potku-bin/mcerd " + command_file

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
        # self.bin_dir = "%s%s%s" % ("external", os.sep, "Examples")
        # TODO Read the parameters from the program

        # Example parameters:
        input_file = "35Cl-85-LiMnO_Li.*.erd"
        params = ["-beam 35Cl", "-energy 8.515", "-theta 41.12", "-tangle 20.6", "-timeres 250.0",
                  "-toflen 0.623", "-solid 0.2", "-dose 8.1e12", "-avemass",
                  "-density 4.98e16", "-dist " + command_file_path + os.sep +
                  "recoiling.LiMnO_Li", "-ch 0.02"]  # recoiling file needs to be a parameter
        params_string = " ".join(params)
        self.output_file = "LiMnO_Li.simu"

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
# CallMCERD(r"C:\Users\localadmin\potku\requests\testi7\35Cl-85-LiMnO_Li").run_simulation()
# MCERD tries to read the input files from the path specified in the command file
# CallMCERD(r"..\Examples\35Cl-85-LiMnO_Li").run_simulation()

# For testing the CallGetEspe class:
# test_espe = CallGetEspe("")
# test_espe.run_get_espe()
