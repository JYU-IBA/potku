# coding=utf-8
"""
Created on 25.4.2018
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
"""
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n" \
             "Sinikka Siironen \n Juhani Sundell"
__version__ = "2.0"

import json
import logging
import numpy as np
import os
import platform
import threading
import time

from modules.element import Element
from modules.general_functions import read_espe_file
from modules.general_functions import rename_file
from modules.general_functions import uniform_espe_lists
from modules.general_functions import count_lines_in_file
from modules.get_espe import GetEspe
from modules.mcerd import MCERD
from modules.observing import Observable
from modules.point import Point
from modules.recoil_element import RecoilElement

from enum import Enum


class SimulationState(Enum):
    """This enum is used to represent the state of simulation.
    """
    # Simulations have not been run yet
    NOTRUN = 1

    # Simulation process are starting
    STARTING = 2

    # ERD files exist, MCERD running, but last ERD file is empty
    PRESIM = 3

    # MCERD is running, last ERD file is not empty
    RUNNING = 4

    # ERD files exist, MCERD not running
    DONE = 5

    def __str__(self):
        """Returns a string representation of the SimulationState.
        """
        if self == SimulationState.NOTRUN:
            return "Not run"
        if self == SimulationState.STARTING:
            return "Starting"
        if self == SimulationState.PRESIM:
            return "Pre-sim"
        if self == SimulationState.RUNNING:
            return "Running"
        return "Done"


class ElementSimulation(Observable):
    """
    Class for handling the element specific simulation. Can have multiple
    MCERD objects, but only one GetEspe object.
    """

    __slots__ = "directory", "request", "name_prefix", "modification_time", \
                "simulation_type", "number_of_ions", "number_of_preions", \
                "number_of_scaling_ions", "number_of_recoils", \
                "minimum_scattering_angle", "minimum_main_scattering_angle", \
                "minimum_energy", "simulation_mode", "seed_number", \
                "recoil_elements", "recoil_atoms", "mcerd_objects", \
                "get_espe", "channel_width", "target", "detector", \
                "__mcerd_command", "settings", "espe_settings", \
                "description", "run", "spectra", "name", \
                "use_default_settings", "sample", "controls", "simulation", \
                "simulations_done", "__full_edit_on", "y_min", "main_recoil",\
                "__erd_files", "optimization_recoils", "__previous_espe", \
                "__opt_seed", "optimization_done", "calculated_solutions", \
                "optimization_stopped", "optimization_widget", \
                "optimization_running", "optimized_fluence", \
                "optimization_mcerd_running", "last_process_count"

    def __init__(self, directory, request, recoil_elements,
                 simulation=None, name_prefix="",
                 target=None, detector=None, run=None, name="Default",
                 description="", modification_time=None,
                 simulation_type="ERD", number_of_ions=1000000,
                 number_of_preions=100000, number_of_scaling_ions=5,
                 number_of_recoils=10, minimum_scattering_angle=0.05,
                 minimum_main_scattering_angle=20, simulation_mode="narrow",
                 seed_number=101, minimum_energy=1.0, channel_width=0.025,
                 use_default_settings=True, sample=None,
                 simulations_done=False, main_recoil=None,
                 optimization_recoils=None, __opt_seed=None,
                 optimized_fluence=None):
        """ Initializes ElementSimulation.
        Args:
            directory: Folder of simulation that contains the ElementSimulation.
            request: Request object reference.
            recoil_elements: List of RecoilElement objects.
            simulation: Simulation object.
            name_prefix: Prefix of the name, e.g. 55Mn
            target: Target object reference.
            detector: Detector object reference.
            run: Run object reference.
            name: Name of the element simulation.
            description: Description of the ElementSimulation
            modification_time: Modification time in Unix time.
            simulation_type: Type of simulation
            number_of_ions: Number of ions to be simulated.
            number_of_preions: Number of ions in presimulation.
            number_of_scaling_ions: Number of scaling ions.
            number_of_recoils: Number of recoils.
            minimum_scattering_angle: Minimum angle of scattering.
            minimum_main_scattering_angle: Minimum main angle of scattering.
            simulation_mode: Mode of simulation.
            seed_number: Seed number to give unique value to one simulation.
            minimum_energy: Minimum energy.
            channel_width: Channel width.
            sample: Sample object under which Element Simualtion belongs.
            simulations_done: Whether any simulations have been run for this
            element simulation.
            main_recoil: Main recoil element.
            optimization_recoils: List or recoils that are used for
            optimization.
            optimized_fluence: Optimized fluence value.
        """
        # Call Observable's initialization to set up observer list
        super().__init__()

        self.directory = directory
        self.request = request
        self.name_prefix = name_prefix
        self.simulation = simulation
        self.name = name
        self.description = description
        if not modification_time:
            modification_time = time.time()
        self.modification_time = modification_time

        self.sample = sample    # TODO check if this is being used elsewhere
                                #      and remove if possible
        self.recoil_elements = recoil_elements

        if len(self.recoil_elements) == 1:
            self.main_recoil = self.recoil_elements[0]
        else:
            self.main_recoil = main_recoil
        self.target = target
        if detector:
            self.detector = detector
        else:
            self.detector = self.request.default_detector
        self.run = run
        self.simulation_type = simulation_type

        self.simulation_mode = simulation_mode
        self.number_of_ions = number_of_ions
        self.number_of_preions = number_of_preions
        self.number_of_scaling_ions = number_of_scaling_ions
        self.number_of_recoils = number_of_recoils
        self.minimum_scattering_angle = minimum_scattering_angle
        self.minimum_main_scattering_angle = minimum_main_scattering_angle
        self.minimum_energy = minimum_energy
        self.seed_number = seed_number
        self.channel_width = channel_width

        self.use_default_settings = use_default_settings

        if self.name_prefix != "":
            name = self.name_prefix + "-" + self.name
            prefix = self.name_prefix
        else:
            name = self.name
            if os.sep + "Default" in self.directory:
                prefix = "Default" + "_element"
                name = "Default"
            else:
                prefix = self.name_prefix
        self.mcsimu_to_file(os.path.join(self.directory,
                                         name + ".mcsimu"))
        for recoil_element in self.recoil_elements:
            self.recoil_to_file(self.directory, recoil_element)
        self.profile_to_file(os.path.join(self.directory,
                                          prefix +
                                          ".profile"))

        self.__mcerd_command = os.path.join(
            "external", "Potku-bin", "mcerd" +
            (".exe" if platform.system() == "Windows" else ""))

        # This has all the mcerd objects so get_espe knows all the element
        # simulations that belong together (with different seed numbers)
        self.mcerd_objects = {}
        self.get_espe = None
        self.spectra = []

        # Whether any simulations have been run or not
        self.simulations_done = simulations_done

        self.controls = None
        if self.simulations_done:
            self.__full_edit_on = False
            self.y_min = 0.0001
        else:
            self.__full_edit_on = True
            self.y_min = 0.0

        # Total number of processes that were run last time this simulation
        # was started
        self.last_process_count = 0
        # List for erd files to count their lines
        # TODO simulations_done and get_erd_files are somewhat redundant
        #      check who uses the first attribute and possibly remove it
        self.__erd_files = self.get_erd_files()

        # TODO check if all optimization stuff can be moved to another module
        self.optimization_recoils = optimization_recoils
        if self.optimization_recoils is None:
            self.optimization_recoils = []
        # This is needed for optimization mcerd stopping
        self.__previous_espe = None
        self.__opt_seed = None
        self.optimization_done = False
        self.calculated_solutions = 0
        self.optimization_stopped = False
        self.optimization_widget = None
        self.optimization_running = False
        self.optimization_mcerd_running = False
        # Store fluence optimization results
        self.optimized_fluence = optimized_fluence

    def unlock_edit(self):
        """
        Unlock full edit.
        """
        self.__full_edit_on = True

    def lock_edit(self):
        """
        Lock full edit.
        """
        self.__full_edit_on = False

    def get_full_edit_on(self):
        """
        Get whether full edit is on or not.

        Return:
            True of False.
        """
        return self.__full_edit_on

    # TODO remove these functions
    def get_points(self, recoil_element):
        """
        Get recoile elemnt points.

        Args:
            recoil_element: A RecoilElement object.

        Return:
            Points list.
        """
        return recoil_element.get_points()

    def get_xs(self, recoil_element):
        """
        Get x coordinates of a RecoilElement.

        Args:
            recoil_element: A RecoilElement object.

        Return:
            X coordinates in a list.
        """
        return recoil_element.get_xs()

    def get_ys(self, recoil_element):
        """
        Get y coordinates of a RecoilElement.

        Args:
            recoil_element: A RecoilElement object.

        Return:
            Y coodinates in a list.
        """
        return recoil_element.get_ys()

    def get_left_neighbor(self, recoil_element, point):
        """
        Get point's left neighbour.

        Args:
             recoil_element: A RecoilElement object.
             point: A Point object.

        Return:
            A point.
        """
        return recoil_element.get_left_neighbor(point)

    def get_right_neighbor(self, recoil_element, point):
        """
        Get point's right neighbour.

        Args:
             recoil_element: A RecoilElement object.
             point: A Point object.

        Return:
            A point.
        """
        return recoil_element.get_right_neighbor(point)

    def get_point_by_i(self, recoil_element, i):
        """
        Get a point by index.

        Args:
            recoil_element: A RecoilElement object.
            i: Index.

        Return:
            A point.
        """
        return recoil_element.get_point_by_i(i)

    def add_point(self, recoil_element, new_point):
        """
        Add a new point to recoil element.

        Args:
             recoil_element: A RecoilElement object.
             new_point: Point to be added.
        """
        recoil_element.add_point(new_point)

    def remove_point(self, recoil_element, point):
        """
        Remove a point from recoil element.

        Args:
            recoil_element: A RecoilElement object.
            point: Point to be removed.
        """
        recoil_element.remove_point(point)

    def update_recoil_element(self, recoil_element, new_values):
        """Updates RecoilElement object with new values.

        Args:
            recoil_element: RecoilElement object to update.
            new_values: New values as a dictionary.
        """
        old_name = recoil_element.name
        try:
            recoil_element.name = new_values["name"]
            recoil_element.description = new_values["description"]
            recoil_element.reference_density = new_values["reference_density"]
            recoil_element.color = new_values["color"]
            recoil_element.multiplier = new_values["multiplier"]
        except KeyError:
            raise
        # Delete possible extra rec files.
        filename_to_delete = ""
        for file in os.listdir(self.directory):
            if file.startswith(recoil_element.prefix + "-" + old_name) and \
                    (file.endswith(".rec") or file.endswith(".sct")):
                filename_to_delete = file
                break
        if filename_to_delete:
            os.remove(os.path.join(self.directory, filename_to_delete))

        self.recoil_to_file(self.directory, recoil_element)

        if old_name != recoil_element.name:
            if recoil_element.type == "rec":
                recoil_suffix = ".recoil"
            else:
                recoil_suffix = ".scatter"
            recoil_file = os.path.join(self.directory, recoil_element.prefix
                                       + "-" + old_name + recoil_suffix)
            if os.path.exists(recoil_file):
                new_name = recoil_element.prefix + "-" + recoil_element.name \
                           + recoil_suffix
                rename_file(recoil_file, new_name)

            if recoil_element is self.main_recoil:  # Only main recoil
                # updates erd file names
                for file in os.listdir(self.directory):
                    if file.startswith(recoil_element.prefix) and file.endswith(
                            ".erd"):
                        erd_file = os.path.join(self.directory, file)
                        seed = file.split('.')[1]
                        new_name = recoil_element.prefix + "-" + \
                            recoil_element.name + "." + seed + ".erd"
                        rename_file(erd_file, new_name)
                # Write mcsimu file
                self.mcsimu_to_file(os.path.join(self.directory,
                                         self.name_prefix + "-" + self.name + \
                                                          ".mcsimu"))

            simu_file = os.path.join(self.directory, recoil_element.prefix +
                                     "-" + old_name + ".simu")
            if os.path.exists(simu_file):
                new_name = recoil_element.prefix + "-" + recoil_element.name \
                           + ".simu"
                rename_file(simu_file, new_name)

    def calculate_solid(self):
        """
        Calculate the solid parameter.
        Return:
            Returns the solid parameter calculated.
        """
        transmissions = self.detector.foils[0].transmission
        for f in self.detector.foils:
            transmissions *= f.transmission

        smallest_solid_angle = self.calculate_smallest_solid_angle()

        return smallest_solid_angle * transmissions

    def calculate_smallest_solid_angle(self):
        """
        Calculate the smallest solid angle.
        Return:
            Smallest solid angle. (unit millisteradian)
        """
        # TODO this seems to be called often when optimizing. If the foil
        #      collection is not changing, result could be cached
        # TODO this could also be a function of the detector
        try:
            return min(foil.get_solid_angle(units="msr")
                       for foil in self.detector.foils)
        except ZeroDivisionError:
            return 0

    @classmethod
    def from_file(cls, request, prefix, simulation_folder, mcsimu_file_path,
                  profile_file_path):
        """Initialize ElementSimulation from JSON files.

        Args:
            request: Request that ElementSimulation belongs to.
            prefix: String that is used to prefix ".rec" files of this
            ElementSimulation.
            simulation_folder: A file path to simulation folder that contains
            files ending with ".rec".
            mcsimu_file_path: A file path to JSON file containing the
            simulation parameters.
            profile_file_path: A file path to JSON file containing the
            channel width.
        """

        obj = json.load(open(mcsimu_file_path))

        use_default_settings_str = obj["use_default_settings"]
        if use_default_settings_str == "True":
            use_default_settings = True
        else:
            use_default_settings = False
        try:
            name_prefix, name = obj["name"].split("-")
        except ValueError:
            name = obj["name"]
            name_prefix = ""

        description = obj["description"]
        modification_time = obj["modification_time_unix"]
        simulation_type = obj["simulation_type"]
        simulation_mode = obj["simulation_mode"]
        number_of_ions = obj["number_of_ions"]
        number_of_preions = obj["number_of_preions"]
        seed_number = obj["seed_number"]
        number_of_recoils = obj["number_of_recoils"]
        number_of_scaling_ions = obj["number_of_scaling_ions"]
        minimum_scattering_angle = obj["minimum_scattering_angle"]
        minimum_main_scattering_angle = obj["minimum_main_scattering_angle"]
        minimum_energy = obj["minimum_energy"]
        main_recoil_name = obj["main_recoil"]

        # Read channel width from .profile file.
        obj = json.load(open(profile_file_path))
        channel_width = obj["energy_spectra"]["channel_width"]

        # Read .rec files from simulation folder
        recoil_elements = []

        # # Read optimized (optfirst and optlast) recoil files
        optimized_recoils = []

        if simulation_type == "ERD":
            rec_type = "rec"
        else:
            rec_type = "sct"

        main_recoil = None
        optimized_fluence = None
        for file in os.listdir(simulation_folder):
            if file.startswith(prefix) and (file.endswith(".rec") or
                                            file.endswith(".sct")) and not \
                    file[file.index(prefix) + len(prefix)].isalpha():
                # Check that e.g. C and Cu are handled separately
                obj = json.load(open(os.path.join(simulation_folder, file)))
                points = []
                for dictionary_point in obj["profile"]:
                    x, y = dictionary_point["Point"].split(" ")
                    points.append(Point((float(x), float(y))))

                color = obj["color"]

                element = RecoilElement(Element.from_string(obj["element"]),
                                        points, color=color, rec_type=rec_type)
                element.name = obj["name"]

                if element.name == main_recoil_name:
                    main_recoil = element

                element.description = obj["description"]
                element.multiplier = obj["multiplier"]
                element.reference_density = obj["reference_density"]
                element.simulation_type = obj["simulation_type"]

                element.modification_time = obj["modification_time_unix"]

                element.channel_width = channel_width

                # Check whether element in regualr or part of optimized recoils
                if prefix + "-optfirst.rec" == file:
                    optimized_recoils.insert(0, element)
                elif prefix + "-optlast.rec" == file:
                    optimized_recoils.append(element)

                else:
                    is_simulated = False
                    # Find if file has a matching erd file (=has been simulated)
                    for f in os.listdir(simulation_folder):
                        if f.startswith(prefix + "-" + element.name) \
                           and f.endswith(".erd"):
                            recoil_elements.insert(0, element)
                            main_recoil = element
                            is_simulated = True
                            break
                    if not is_simulated:
                        if element is main_recoil:
                            recoil_elements.insert(0, element)
                        else:
                            recoil_elements.append(element)
            elif file.startswith(prefix) and file.endswith("optfl.result") and \
                not file[file.index(prefix) + len(prefix)].isalpha():
                # Check if fluence is optimized
                with open(os.path.join(simulation_folder, file), "r") as f:
                    optimized_fluence = float(f.readline())

        # Check if there are any files to tell that simulations have
        # been run previously
        simulations_done = False
        for f in os.listdir(simulation_folder):
            if f.startswith(name_prefix + "-" + recoil_elements[0].name) and \
                    f.endswith(
                    ".erd"):
                simulations_done = True
                break
            elif f.startswith(name_prefix + "-opt") and f.endswith(".result"):
                simulations_done = True
                break

        return cls(directory=simulation_folder, request=request,
                   recoil_elements=recoil_elements,
                   name_prefix=name_prefix,
                   description=description,
                   simulation_type=simulation_type,
                   modification_time=modification_time, name=name,
                   number_of_ions=number_of_ions,
                   number_of_preions=number_of_preions,
                   number_of_scaling_ions=number_of_scaling_ions,
                   number_of_recoils=number_of_recoils,
                   minimum_scattering_angle=minimum_scattering_angle,
                   minimum_main_scattering_angle=minimum_main_scattering_angle,
                   simulation_mode=simulation_mode,
                   seed_number=seed_number,
                   minimum_energy=minimum_energy,
                   use_default_settings=use_default_settings,
                   channel_width=channel_width,
                   simulations_done=simulations_done,
                   main_recoil=main_recoil,
                   optimization_recoils=optimized_recoils,
                   optimized_fluence=optimized_fluence)

    def mcsimu_to_file(self, file_path):
        """Save mcsimu settings to file.

        Args:
            file_path: File in which the mcsimu settings will be saved.
        """
        if self.name_prefix != "":
            name = self.name_prefix + "-" + self.name
        else:
            name = self.name
        if not self.use_default_settings:
            obj = {
                "name": name,
                "description": self.description,
                "modification_time": time.strftime("%c %z %Z", time.localtime(
                    time.time())),
                "modification_time_unix": time.time(),
                "simulation_type": self.simulation_type,
                "simulation_mode": self.simulation_mode,
                "number_of_ions": self.number_of_ions,
                "number_of_preions": self.number_of_preions,
                "seed_number": self.seed_number,
                "number_of_recoils": self.number_of_recoils,
                "number_of_scaling_ions": self.number_of_scaling_ions,
                "minimum_scattering_angle": self.minimum_scattering_angle,
                "minimum_main_scattering_angle":
                    self.minimum_main_scattering_angle,
                "minimum_energy": self.minimum_energy,
                "use_default_settings": str(self.use_default_settings),
                "main_recoil": self.main_recoil.name
            }
        else:
            elem_sim = self.request.default_element_simulation
            obj = {
                "name": name,
                "description": elem_sim.description,
                "modification_time": time.strftime("%c %z %Z", time.localtime(
                    time.time())),
                "modification_time_unix": time.time(),
                "simulation_type": elem_sim.simulation_type,
                "simulation_mode": elem_sim.simulation_mode,
                "number_of_ions": elem_sim.number_of_ions,
                "number_of_preions": elem_sim.number_of_preions,
                "seed_number": elem_sim.seed_number,
                "number_of_recoils": elem_sim.number_of_recoils,
                "number_of_scaling_ions": elem_sim.number_of_scaling_ions,
                "minimum_scattering_angle": elem_sim.minimum_scattering_angle,
                "minimum_main_scattering_angle":
                    elem_sim.minimum_main_scattering_angle,
                "minimum_energy": elem_sim.minimum_energy,
                "use_default_settings": str(self.use_default_settings),
                "main_recoil": self.main_recoil.name
            }

        with open(file_path, "w") as file:
            json.dump(obj, file, indent=4)

    def recoil_to_file(self, simulation_folder, recoil_element):
        """Save recoil settings to file.

        Args:
            simulation_folder: Path to simulation folder in which ".rec" or
            ".sct" files are stored.
            recoil_element: RecoilElement object to write to file to.
        """
        if recoil_element.type == "rec":
            suffix = ".rec"
        else:
            suffix = ".sct"
        recoil_file = os.path.join(simulation_folder,
                                   recoil_element.prefix + "-" +
                                   recoil_element.name + suffix)
        element_str = recoil_element.element.get_prefix()

        obj = {
            "name": recoil_element.name,
            "description": recoil_element.description,
            "modification_time": time.strftime("%c %z %Z", time.localtime(
                time.time())),
            "modification_time_unix": time.time(),
            "simulation_type": recoil_element.type,
            "element": element_str,
            "reference_density": recoil_element.reference_density,
            "multiplier": recoil_element.multiplier,
            "profile": [],
            "color": recoil_element.color
        }

        for point in recoil_element.get_points():
            point_obj = {
                "Point": str(round(point.get_x(), 2)) + " " + str(round(
                    point.get_y(), 4))
            }
            obj["profile"].append(point_obj)

        with open(recoil_file, "w") as file:
            json.dump(obj, file, indent=4)

    def profile_to_file(self, file_path):
        """Save profile settings (only channel width) to file.

        Args:
            file_path: File in which the channel width will be saved.
        """
        # Read .profile to obj to update only channel width
        if os.path.exists(file_path):
            obj_profile = json.load(open(file_path))
            obj_profile["modification_time"] = time.strftime("%c %z %Z",
                                                             time.localtime(
                                                                 time.time()))
            obj_profile["modification_time_unix"] = time.time()
            obj_profile["energy_spectra"]["channel_width"] = self.channel_width
        else:
            obj_profile = {"energy_spectra": {},
                           "modification_time": time.strftime("%c %z %Z",
                                                              time.localtime(
                                                                  time.time())),
                           "modification_time_unix": time.time()}
            obj_profile["energy_spectra"]["channel_width"] = self.channel_width

        with open(file_path, "w") as file:
            json.dump(obj_profile, file, indent=4)

    def start(self, number_of_processes, start_value, erd_files=None,
              optimize=False, stop_p=False, check_t=False,
              optimize_recoil=False, check_max=False, check_min=False,
              shared_ions=False):
        """
        Start the simulation.

        Args:
            number_of_processes: How many processes are started.
            start_value: Which is the first seed.
            erd_files: List of old erd files that need to be preserved.
            optimize: Whether mcerd run relates to optimization.
            stop_p: Percent for stopping the MCERD run.
            check_t: Time between checks to see whether to stop MCERD or not.
            optimize_recoil: Whether optimization concerns recoil.
            check_max: Maximum time to run simulation.
            check_min: Minimum time to run simulation.
            shared_ions: boolean that determines if the ion counts are
                divided by the number of processes
        """
        self.simulations_done = False
        if self.run is None:
            run = self.request.default_run
        else:
            run = self.run

        if self.detector is None:
            detector = self.request.default_detector
        else:
            detector = self.detector

        elem_sim = self.get_element_simulation()

        # These are the old ERD files that belong to the simulation. They are
        # stored as a dict where keys are file paths to ERD files and values are
        # seed numbers. If erd_files is None, we are starting a new simulation
        if erd_files is not None:
            self.__erd_files = erd_files
        else:
            self.__erd_files = {}

        # Set seed to either the value provided as parameter or use the one
        # stored in current element simulation.
        # TODO should this also accept 0? It does not now. Is there an
        #      acceptable range of values that should be checked for?
        if start_value:
            seed_number = start_value
        else:
            seed_number = elem_sim.seed_number

        if not optimize_recoil:
            recoil = self.recoil_elements[0]
        else:
            recoil = self.optimization_recoils[0]
        self.__opt_seed = seed_number

        if shared_ions:
            number_of_ions = elem_sim.number_of_ions // number_of_processes
            number_of_preions = \
                elem_sim.number_of_preions // number_of_processes
        else:
            number_of_ions = elem_sim.number_of_ions
            number_of_preions = elem_sim.number_of_preions

        self.last_process_count = number_of_processes

        # Notify observers that we are about to go
        self.on_next(self.get_current_status(starting=True))

        # Start as many processes as is given in number of processes
        for i in range(number_of_processes):
            settings = {
                "simulation_type": elem_sim.simulation_type,
                "number_of_ions": number_of_ions,
                "number_of_ions_in_presimu": number_of_preions,
                "number_of_scaling_ions": elem_sim.number_of_scaling_ions,
                "number_of_recoils": elem_sim.number_of_recoils,
                "minimum_scattering_angle": elem_sim.minimum_scattering_angle,
                "minimum_main_scattering_angle":
                    elem_sim.minimum_main_scattering_angle,
                "minimum_energy_of_ions": elem_sim.minimum_energy,
                "simulation_mode": elem_sim.simulation_mode,
                "seed_number": seed_number,
                "beam": run.beam,
                "target": self.target,
                "detector": detector,
                "recoil_element": recoil,
                "sim_dir": self.directory
            }
            # Delete corresponding erd file
            optimize_fluence = False
            if not optimize_recoil:
                if not optimize:
                    recoil_name = self.recoil_elements[0].name
                else:
                    recoil_name = "optfl"
                    optimize_fluence = True
                    self.optimized_fluence = 0
                new_erd_file = os.path.join(    # TODO method get_erd_file_name?
                    self.directory, self.recoil_elements[0].prefix + "-" +
                    recoil_name + "." + str(seed_number) + ".erd")
            else:
                new_erd_file = os.path.join(
                    self.directory, self.optimization_recoils[0].prefix + "-" +
                    "opt" + "." + str(seed_number) + ".erd")
            if os.path.exists(new_erd_file):
                os.remove(new_erd_file)

            self.__erd_files[new_erd_file] = seed_number

            if optimize:
                self.optimization_mcerd_running = True

            self.mcerd_objects[seed_number] = MCERD(
                settings, self, optimize_fluence=optimize_fluence)

            seed_number = seed_number + 1
            if i + 1 < number_of_processes:
                time.sleep(5)  # This is done to avoid having a mixup in mcerd
                # command file content when there are more than one process
                # (without this, Potku would crash)
                # TODO create command file for each process so they can
                #  be started at the same time?

        if self.use_default_settings and not self.simulation.detector:
            self.request.running_simulations.append(self)
        else:
            self.simulation.running_simulations.append(self)

        if not optimize:
            # Start updating observers on current progress
            thread = threading.Thread(target=self.check_status)
            thread.daemon = True
            thread.start()
        else:
            # Check the change between current and previous energy spectra (if
            # the spectra have been calculated)
            self.check_spectra_change(stop_p, check_t, optimize_recoil,
                                      check_max, check_min)

    def get_element_simulation(self):
        """Returns current element simulation to be used. Depending on the
        settings, it is either a default simulation or self.
        """
        if self.use_default_settings:
            return self.request.default_element_simulation
        return self

    def get_current_status(self, starting=False):
        """Returns the number of atoms counted, number of running processes and
        the state of simulation.

        Args:
            starting: boolean which indicates whether simulations are starting.
                      Currently get_current_status cannot tell the difference
                      between Starting and Finished simulation so this has to
                      be determined by the caller.

        Return:
            dict in the form of
                {
                    'name': 'name_prefix'-'name'
                    'atom_count': integer,
                    'running': integer,
                    'state': enum
                }
        """
        process_count = self.count_active_processes()
        atom_counts = tuple(self.get_atom_counts())
        total_count = sum(count for _, count in atom_counts)

        if starting:
            state = SimulationState.STARTING
        elif not self.__erd_files:
            # No ERD files exist so simulation has not started
            state = SimulationState.NOTRUN
        elif process_count:
            # Some processes are running, we are either in presim or running
            # state
            if not atom_counts[-1][-1]:
                # If the last ERD file contains no atoms, we are in Presim
                # TODO should get atom counts for all processes rather than
                #      just the last

                # TODO the order of atoms counts is the same as os.listdir
                #      returns so it is not guaranteed to be in alphabetical
                #      order. Furthermore, even if the files are in
                #      alphabetical order, this does not work if seeds have
                #      different number of digits as 'Li-Default.10.erd' would
                #      come before 'Li-Default.6.erd. Potential solution: store
                #      active processes in self.mcerd_objects by the ERD file
                #      name rather than seed.
                state = SimulationState.PRESIM
            else:
                # We are in full sim mode
                state = SimulationState.RUNNING
        else:
            # ERD files exist but no active simulation is in process
            state = SimulationState.DONE

        # Return status as a dict
        return {
            "name": "{0}-{1}".format(self.name_prefix, self.name),
            "atom_count": total_count,
            "running":  process_count,
            "state": state
        }

    def get_last_seed(self, erd_files):
        """Returns the last seed from given ERD files.

        Args:
            erd_files: dictionary where keys are absolute paths to ERD files
                       and values are seeds

        Return:
            last seed value used in simulation processes
        """
        # Last seed is just the maximum seed number
        # TODO do this in the ERDFileHandler class
        return max(erd_files.values(), default=0)

    def get_erd_files(self):
        """Finds ERD files in ElementSimulation's directory and returns them.

        Return:
             dict where keys are file names and values are seeds
        """
        # TODO do this in the ERDFileHandler class
        erd_files = {}

        start_part = "{0}-{1}.".format(self.recoil_elements[0].prefix,
                                       self.recoil_elements[0].name)
        end = ".erd"

        for file in os.listdir(self.directory):
            if file.startswith(start_part) and file.endswith(end):
                try:
                    file_path = os.path.join(self.directory,
                                             file)
                    seed = int(file.rsplit('.', 2)[1])
                    erd_files[file_path] = seed
                except ValueError:
                    # Seed was not an int, file won't be used
                    pass
        return erd_files

    def check_status(self):
        """Periodically checks the status of simulation and reports the status
        to observers.
        """
        while True:
            time.sleep(1)
            status = self.get_current_status()
            self.on_next(status)
            if status["state"] == SimulationState.DONE:
                break

    def count_active_processes(self):
        """Returns the number of active processes.
        """
        return len(self.mcerd_objects)

    def get_atom_counts(self):
        """Calculates the number of atoms in each ERD file.

        Yield:
            tuple where first element is an ERD file path and second
            value is the number of atoms in that file
        """
        # TODO do this in the ERDFileHandler class
        for erd_file in self.__erd_files:
            yield erd_file, count_lines_in_file(erd_file,
                                                check_file_exists=True)

    def check_spectra_change(self, stop_percent, check_time, optimize_recoil,
                             check_max, check_min):
        """
        If there are previous and current energy spectra, check the change in
        distance between them. When this is smaller than the threshold,
        mcerd can be stopped.

        Args:
            stop_percent: Percent at which to stop.
            check_time: Time between the percentage checks.
            optimize_recoil: Whether recoil is being optimized.
            check_max: Maximum time until simulation is stopped.
            check_min: Minimum time to run simulation.
        """
        previous_avg = None
        sleep_beginning = True
        check_start = time.time()
        while True:
            if not self.mcerd_objects:
                self.optimization_mcerd_running = False
                self.simulations_done = True
                break
            if sleep_beginning:
                time.sleep(check_min)  # Sleep for user-defined time to
                # ensure bigger results than just few percents
                sleep_beginning = False
            else:
                time.sleep(check_time)  # Sleep for specified time
            # Check if erd file can be found (presimulation has been
            # finished)
            if optimize_recoil:
                recoils = self.optimization_recoils
                opt = True
                optfl = False
                recoil_name = self.optimization_recoils[0].name
            else:
                recoils = self.recoil_elements
                opt = False
                optfl = True
                recoil_name = "optfl"

            # Check if maximum time has been used for simulation
            current_time = time.time()
            if current_time - check_start >= check_max:  # Max time
                self.stop(optimize_recoil=opt)

            erd_file = os.path.join(
                self.directory, recoils[0].prefix + "-" + recoil_name +
                "." + str(self.__opt_seed) + ".erd")
            if os.path.exists(erd_file):
                # Calculate new energy spectrum
                self.calculate_espe(recoils[0], optimize_recoil=opt,
                                    optimize_fluence=optfl)
                espe_file = os.path.join(self.directory, recoils[0].prefix +
                                         "-" + recoil_name + ".simu")
                espe = read_espe_file(espe_file)
                if espe:
                    # Change items to float types
                    espe = list(np.float_(espe))
                    if self.__previous_espe:
                        espe, self.__previous_espe = uniform_espe_lists([
                            espe, self.__previous_espe], self.channel_width)
                        # Calculate distance between energy spectra
                        sum_diff = 0
                        i = 0
                        amount = 0
                        for point in espe:
                            prev_point = self.__previous_espe[i]
                            p_y = float(point[1])
                            pr_y = float(prev_point[1])
                            if p_y != 0 or pr_y != 0:
                                amount += 1
                            diff = abs(p_y - pr_y)
                            sum_diff += diff
                            i += 1
                        # Take average of sum_diff (non-zero diffs)
                        avg = sum_diff/amount
                        if previous_avg:
                            avg_ratio = avg/previous_avg
                            if avg_ratio < stop_percent:
                                self.stop(optimize_recoil=opt)
                                break
                        previous_avg = avg
                    self.__previous_espe = espe

    def notify(self, sim):
        """
        Remove MCERD object from list that has finished.
        If no there are no more MCERD objects, show the end of the simulation
        in the controls.
        """
        key_to_delete = None
        for seed, value in self.mcerd_objects.items():
            if value == sim:
                key_to_delete = seed

        if key_to_delete:
            self.mcerd_objects[key_to_delete].delete_unneeded_files()
            del self.mcerd_objects[key_to_delete]

        if not self.mcerd_objects:
            processes = "N/a"
            if self.controls:   # TODO try to get rid of controls references
                processes = self.last_process_count
            if self.use_default_settings:
                self.request.running_simulations.remove(self)
            else:
                self.simulation.running_simulations.remove(self)

            # Calculate erd lines for log
            atom_count = sum(count for _, count in self.get_atom_counts())

            simulation_name = self.simulation.name
            element = self.recoil_elements[0].element

            msg = "Simulation finished. Element {0}, processes: {1}, observed" \
                  " atoms: {2}".format(str(element), processes, atom_count)
            logging.getLogger(simulation_name).info(msg)

        self.simulations_done = True
        self.on_complete(self.get_current_status())

    def stop(self, optimize_recoil=False):
        """ Stop the simulation."""
        # TODO check if this and notify can be refactored
        process_count = self.count_active_processes()
        ref_key = None

        for seed, sim in self.mcerd_objects.items():
            if ref_key is None:
                ref_key = seed
            sim.stop_process()
        try:
            # TODO why delete files for only 'ref_key'? Or does this delete
            #      all files anyway?
            # self.mcerd_objects[sim].copy_results(self.directory)
            self.mcerd_objects[ref_key].delete_unneeded_files()
        except (FileNotFoundError, KeyError):
            pass
        for sim in list(self.mcerd_objects.keys()):
            del self.mcerd_objects[sim]
        try:
            self.request.running_simulations.remove(self)
        except ValueError:
            self.simulation.running_simulations.remove(self)
        if self.optimization_mcerd_running:
            self.optimization_mcerd_running = False

        # Calculate erd lines for log
        atom_count = sum(count for _, count in self.get_atom_counts())

        simulation_name = self.simulation.name
        if not optimize_recoil:
            element = self.recoil_elements[0].element
        else:
            element = self.optimization_recoils[0].element

        element_name = element.get_prefix()

        self.simulations_done = True

        msg = f"Simulation stopped. Element: {element_name}, processes: " \
              f"{process_count}, Number of observed atoms: {atom_count}"

        logging.getLogger(simulation_name).info(msg)
        self.on_complete(self.get_current_status())

    def calculate_espe(self, recoil_element, optimize_recoil=False, ch=None,
                       fluence=None, optimize_fluence=False):
        """
        Calculate the energy spectrum from the MCERD result file.

        Args:
            recoil_element: Recoil element.
            optimize_recoil: Whether recoil is optimized.
            ch: Channel width to use.
            fluence: Fluence to use.
        """
        if self.simulation_type == "ERD":
            suffix = ".recoil"
        else:
            suffix = ".scatter"

        if not optimize_recoil:
            recoil_elements = self.recoil_elements
            if optimize_fluence:
                erd_recoil_name = "optfl"
                recoil_name = "optfl"
            else:
                erd_recoil_name = self.recoil_elements[0].name
                recoil_name = recoil_element.name
        else:
            recoil_elements = self.optimization_recoils
            recoil_name = recoil_element.name
            erd_recoil_name = "opt"

        recoil_file = os.path.join(self.directory,
                                   recoil_element.prefix + "-" +
                                   recoil_name + suffix)
        recoil_element.write_recoil_file(recoil_file)

        erd_file = os.path.join(self.directory, recoil_elements[0].prefix +
                                "-" + erd_recoil_name + ".*.erd")
        spectrum_file = os.path.join(self.directory, recoil_element.prefix +
                                     "-" + recoil_name + ".simu")
        if ch:
            channel_width = ch
        else:
            channel_width = self.channel_width

        if self.run is None:
            run = self.request.default_run
        else:
            run = self.run
        if self.detector is None:
            detector = self.request.default_detector
        else:
            detector = self.detector

        if fluence is not None:
            used_fluence = fluence
        else:
            used_fluence = run.fluence
        espe_settings = {
            "beam": run.beam,
            "detector": detector,
            "target": self.target,
            "ch": channel_width,
            "reference_density": recoil_element.reference_density,
            "multiplier": recoil_element.multiplier,
            "fluence": used_fluence,
            "timeres": detector.timeres,
            "solid": self.calculate_solid(),
            "erd_file": erd_file,
            "spectrum_file": spectrum_file,
            "recoil_file": recoil_file
        }
        self.get_espe = GetEspe(espe_settings)


def __get_atom_count(self, file):
    return count_lines_in_file(file, check_file_exists=True)

# TODO move import to top of the file
import functools

@functools.lru_cache(32)
def __get_atom_count_cached(self, file):
        return __get_atom_count(file)


def get_seed(erd_file):
    try:
        return int(erd_file.rsplit('.', 2)[1])
    except ValueError:
        return None


def get_valid_erd_file_names(directory, recoil_element):
    start_part = "{0}-{1}.".format(recoil_element.prefix,
                                   recoil_element.name)
    end = ".erd"

    for file in os.listdir(directory):
        if file.startswith(start_part) and file.endswith(end):
            try:
                file_path = os.path.join(directory,
                                         file)
                seed = get_seed(file_path)
                yield file_path, recoil_element, seed
            except ValueError:
                # Seed was not an int, file won't be used
                pass


class ERDFileHandler:
    """Helper class to handle ERD files that belong to the ElementSimulation

    Handles counting atoms and getting seeds.
    """
    def __init__(self, *args):
        self.__active_files = {}
        self.__old_files = {
            str(f): {
                "rec_elem": r,
                "seed": int(s)
            }
            for f, r, s in args
        }

    @classmethod
    def from_directory(cls, directory, recoil_element):
        return cls(get_valid_erd_file_names(directory, recoil_element))

    def add_active_file(self, file):
        if file in self.__active_files:
            raise ValueError("Already in active files")
        if file in self.__old_files:
            raise ValueError("Already in old files")

        seed = get_seed(file)
        if seed is None:
            raise ValueError("ERD file did not contain a valid seed.")

        self.__active_files[file] = seed

    def get_max_seed(self):
        return max(seed for _, seed, _ in self)

    def get_active_atom_counts(self):
        return sum(self.__get_atom_count(file)
                   for file in self.__active_files)

    def get_old_atom_counts(self):
        return sum(self.__get_atom_count_cached(file)
                   for file in self.__old_files)

    def update(self):
        self.__old_files.update(self.__active_files)
        self.__active_files.clear()


def get_erd_file_path(directory, elem_prefix, rec_name):
    """Returns the file path that corresponds to given
    directory, recoil element prefix and recoil name.

    Args:
        directory: absolute path to a directory
        elem_prefix: prefix of the recoil element
        rec_name: name of the recoil

    Return:
        absolute path to an ERD file
    """
    # TODO check for path traversal
    # TODO implement all possible naming options that an ERD file can have
    #      before using this function
    return os.path.join(directory,
                        f"{elem_prefix}-{rec_name}.*.erd")
