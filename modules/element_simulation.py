# coding=utf-8
"""
Created on 25.4.2018
Updated on 8.2.2020

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
import threading
import time
import functools
import itertools

import modules.file_paths as fp
import modules.general_functions as gf

from enum import Enum
from pathlib import Path
from collections import deque

from modules.get_espe import GetEspe
from modules.mcerd import MCERD
from modules.observing import Observable
from modules.recoil_element import RecoilElement


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
                "settings", "espe_settings", "__erd_filehandler", \
                "description", "run", "spectra", "name", \
                "use_default_settings", "controls", "simulation", \
                "simulations_done", "__full_edit_on", "y_min", "main_recoil",\
                "optimization_recoils", "__previous_espe", \
                "__opt_seed", "optimization_done", "calculated_solutions", \
                "optimization_stopped", "optimization_widget", \
                "optimization_running", "optimized_fluence", \
                "optimization_mcerd_running", "last_process_count", "sample", \
                "__cancellation_token"

    def __init__(self, directory, request, recoil_elements,
                 simulation=None, name_prefix="", sample=None,
                 target=None, detector=None, run=None, name="Default",
                 description="", modification_time=None,
                 simulation_type="ERD", number_of_ions=1000000,
                 number_of_preions=100000, number_of_scaling_ions=5,
                 number_of_recoils=10, minimum_scattering_angle=0.05,
                 minimum_main_scattering_angle=20, simulation_mode="narrow",
                 seed_number=101, minimum_energy=1.0, channel_width=0.025,
                 use_default_settings=True, main_recoil=None,
                 optimization_recoils=None, __opt_seed=None,
                 optimized_fluence=None, save_on_creation=True, **kwargs):
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
            save_on_creation: Determines if the element simulation is saved to
                              a file when initialized
        """
        # Call Observable's initialization to set up observer list
        super().__init__()

        self.directory = directory
        self.request = request
        self.name_prefix = name_prefix
        self.simulation = simulation
        self.name = name
        self.description = description
        if modification_time is None:
            self.modification_time = time.time()
        else:
            self.modification_time = modification_time

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
        self.sample = sample
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

        if save_on_creation:
            # Write .mcsimu file, recoil file and .profile file
            self.to_file(Path(self.directory, f"{name}.mcsimu"))

            for recoil_element in self.recoil_elements:
                recoil_element.to_file(self.directory)

            self.profile_to_file(Path(self.directory, f"{prefix}.profile"))

        # This has all the mcerd objects so get_espe knows all the element
        # simulations that belong together (with different seed numbers)
        self.mcerd_objects = {}
        self.get_espe = None
        self.spectra = []

        # TODO get rid of this reference to GUI element. Currently there are
        #      some other objects that modify controls via this reference so
        #      that needs to be sorted out before removing this. (Also this
        #      should be removed from __slots__)
        self.controls = None

        # Total number of processes that were run last time this simulation
        # was started
        self.last_process_count = 0

        self.__erd_filehandler = ERDFileHandler.from_directory(
            self.directory, self.main_recoil)

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

        # Check if there are any files to tell that simulations have
        # been run previously
        self.simulations_done = len(self.__erd_filehandler) != 0

        if self.simulations_done:
            self.__full_edit_on = False
            self.y_min = 0.0001
        else:
            self.__full_edit_on = True
            self.y_min = 0.0

        self.__cancellation_token = None

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

    def update_recoil_element(self, recoil_element, new_values):
        """Updates RecoilElement object with new values.

        Args:
            recoil_element: RecoilElement object to update.
            new_values: New values as a dictionary.
        """
        # TODO this should affect erd file handler too
        # TODO make this a function of RecoilElement
        old_name = recoil_element.name

        recoil_element.update(new_values)

        # Delete possible extra rec files.
        filename_to_delete = ""
        for file in os.listdir(self.directory):
            if file.startswith(recoil_element.prefix + "-" + old_name) and \
                    (file.endswith(".rec") or file.endswith(".sct")):
                filename_to_delete = file
                break
        if filename_to_delete:
            os.remove(os.path.join(self.directory, filename_to_delete))

        recoil_element.to_file(self.directory)

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
                gf.rename_file(recoil_file, new_name)

            if recoil_element is self.main_recoil:  # Only main recoil
                # updates erd file names
                for file in os.listdir(self.directory):
                    if file.startswith(recoil_element.prefix) and file.endswith(
                            ".erd"):
                        erd_file = os.path.join(self.directory, file)
                        seed = file.split('.')[1]
                        new_name = recoil_element.prefix + "-" + \
                            recoil_element.name + "." + seed + ".erd"
                        gf.rename_file(erd_file, new_name)
                # Write mcsimu file
                self.to_file(os.path.join(
                    self.directory,
                    self.name_prefix + "-" + self.name + ".mcsimu"))

            simu_file = os.path.join(self.directory, recoil_element.prefix +
                                     "-" + old_name + ".simu")
            if os.path.exists(simu_file):
                new_name = recoil_element.prefix + "-" + recoil_element.name \
                           + ".simu"
                gf.rename_file(simu_file, new_name)

    @classmethod
    def from_file(cls, request, prefix, simulation_folder, mcsimu_file_path,
                  profile_file_path, sample=None):
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
        with open(mcsimu_file_path) as mcsimu_file:
            mcsimu = json.load(mcsimu_file)

        # Pop the values that need to be converted (name and
        # use_def_settings) from the dict
        use_default_settings = mcsimu.pop("use_default_settings") == "True"
        main_recoil_name = mcsimu.pop("main_recoil")
        modification_time = mcsimu.pop("modification_time_unix")

        # This is the time in 'human readable' form. It is not being used
        # apart from saving to file so it can just be removed
        mcsimu.pop("modification_time")

        full_name = mcsimu.pop("name")
        try:
            name_prefix, name = full_name.split("-")
        except ValueError:
            name = full_name
            name_prefix = ""

        # Read channel width from .profile file.
        with open(profile_file_path) as prof_file:
            prof = json.load(prof_file)

        channel_width = prof["energy_spectra"]["channel_width"]

        if mcsimu["simulation_type"] == "ERD":
            # TODO can this be determined from the file extension?
            rec_type = "rec"
        else:
            rec_type = "sct"

        main_recoil = None
        optimized_fluence = None
        recoil_elements = deque()
        optimized_recoils = deque()

        for file in os.listdir(simulation_folder):
            if fp.is_recoil_file(prefix, file):
                # Initialize a recoil element
                rec_elem = RecoilElement.from_file(
                    Path(simulation_folder, file),
                    channel_width=channel_width,
                    rec_type=rec_type
                )

                if rec_elem.name == main_recoil_name:
                    main_recoil = rec_elem

                # Check whether element in regular or part of optimized recoils
                if fp.is_optfirst(prefix, file):
                    optimized_recoils.appendleft(rec_elem)
                elif fp.is_optlast(prefix, file):
                    optimized_recoils.append(rec_elem)
                else:
                    # Find if file has a matching erd file (=has been simulated)
                    for f in os.listdir(simulation_folder):
                        if fp.is_erd_file(rec_elem, f):
                            recoil_elements.appendleft(rec_elem)
                            main_recoil = rec_elem
                            break
                    else:
                        # No matching erd file was found
                        if rec_elem is main_recoil:
                            recoil_elements.appendleft(rec_elem)
                        else:
                            recoil_elements.append(rec_elem)

            # Check if fluence has been optimized
            elif fp.is_optfl_result(prefix, file):
                with open(Path(simulation_folder, file), "r") as f:
                    optimized_fluence = float(f.readline())

        return cls(directory=simulation_folder,
                   request=request,
                   recoil_elements=recoil_elements,
                   name_prefix=name_prefix,
                   name=name,
                   use_default_settings=use_default_settings,
                   channel_width=channel_width,
                   optimization_recoils=optimized_recoils,
                   optimized_fluence=optimized_fluence,
                   main_recoil=main_recoil,
                   modification_time=modification_time,
                   sample=sample,
                   **mcsimu)

    def get_full_name(self):
        """Returns the full name of the ElementSimulation object."""
        # TODO if either the name or the prefix contains a '-', this naming
        #      scheme becomes ambiguous
        # TODO check the difference between this and recoil element
        #  get_full_name
        if self.name_prefix:
            return f"{self.name_prefix}-{self.name}"
        return self.name

    def to_dict(self):
        """Returns a dictionary representation of the element simulation
        object.
        """
        elem_sim = self.get_element_simulation()

        # TODO maybe declare __dict__ in __slots__ so we get to use vars
        # d = vars(elem_sim)

        return {
            # TODO should this have the name of the elem_sim instead?
            "name": self.get_full_name(),
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

    def copy_settings_from(self, other):
        """Copies settings from another ElementSimulation object.

        Args:
            other: ElementSimulation object
        """
        if not isinstance(other, ElementSimulation):
            raise TypeError("ElementSimulation can only copy settings from "
                            "another ElementSimulation object.")

        self.name = other.name  # TODO not prefix also?
        self.description = other.description
        self.simulation_mode = other.simulation_mode
        self.simulation_type = other.simulation_type
        self.number_of_ions = other.number_of_ions
        self.number_of_preions = other.number_of_preions
        self.seed_number = other.seed_number
        self.number_of_recoils = other.number_of_recoils
        self.number_of_scaling_ions = other.number_of_scaling_ions
        self.minimum_scattering_angle = other.minimum_scattering_angle
        self.minimum_main_scattering_angle = \
            other.minimum_main_scattering_angle
        self.minimum_energy = other.minimum_energy

    def to_file(self, file_path):
        """Save mcsimu settings to file.

        Args:
            file_path: File in which the mcsimu settings will be saved.
        """
        # TODO maybe it is not necessary to call this every time a request
        #      is opened
        with open(file_path, "w") as file:
            json.dump(self.to_dict(), file, indent=4)

    def profile_to_file(self, file_path):
        """Save profile settings (only channel width) to file.

        Args:
            file_path: File in which the channel width will be saved.
        """
        # Read .profile to obj to update only channel width
        if os.path.exists(file_path):
            with open(file_path) as file:
                obj_profile = json.load(file)

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

    def start(self, number_of_processes, start_value, use_old_erd_files=True,
              optimize=False, stop_p=False, check_t=False,
              optimize_recoil=False, check_max=False, check_min=False,
              shared_ions=False, cancellation_token=None):
        """
        Start the simulation.

        Args:
            number_of_processes: How many processes are started.
            start_value: Which is the first seed.
            use_old_erd_files: whether the simulation continues using old erd
                files or not
            optimize: Whether mcerd run relates to optimization.
            stop_p: Percent for stopping the MCERD run.
            check_t: Time between checks to see whether to stop MCERD or not.
            optimize_recoil: Whether optimization concerns recoil.
            check_max: Maximum time to run simulation.
            check_min: Minimum time to run simulation.
            shared_ions: boolean that determines if the ion counts are
                divided by the number of processes
            cancellation_token: CancellationToken that can be used to stop
                                the start process
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

        if not use_old_erd_files:
            self.__erd_filehandler.clear()

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
            # ATM user can also enter value 0 to process count
            # so lets make a quick check first
            if number_of_processes < 1:
                number_of_processes = 1
            number_of_ions = elem_sim.number_of_ions // number_of_processes
            number_of_preions = \
                elem_sim.number_of_preions // number_of_processes
        else:
            number_of_ions = elem_sim.number_of_ions
            number_of_preions = elem_sim.number_of_preions

        self.last_process_count = number_of_processes

        # Notify observers that we are about to go
        self.on_next(self.get_current_status(starting=True))

        self.__cancellation_token = cancellation_token

        # Start as many processes as is given in number of processes
        for i in range(number_of_processes):
            if self.__cancellation_token is not None:
                self.__cancellation_token.raise_if_cancelled()

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

            # TODO create an optimization_mode enum {None, "rec", "flu"} instead
            #      of using three different booleans
            if not optimize_recoil:
                if not optimize:
                    new_erd_file = fp.get_erd_file_name(recoil, seed_number)
                    # TODO check if erdfilehandler should have optim files too
                    self.__erd_filehandler.add_active_file(
                        Path(self.directory, new_erd_file))
                else:
                    optimize_fluence = True
                    self.optimized_fluence = 0
                    new_erd_file = fp.get_erd_file_name(recoil, seed_number,
                                                        optim_mode="fluence")

            else:
                new_erd_file = fp.get_erd_file_name(recoil, seed_number,
                                                    optim_mode="recoil")

            new_erd_file = Path(self.directory, new_erd_file)

            if os.path.exists(new_erd_file):
                # TODO maybe this file should be kept when optimizing
                os.remove(new_erd_file)

            self.optimization_mcerd_running = optimize

            mcerd = MCERD(settings,
                          self,
                          optimize_fluence=optimize_fluence)
            mcerd.run()
            self.mcerd_objects[seed_number] = mcerd

            seed_number += 1
            if i + 1 < number_of_processes:
                time.sleep(5)
                # This is done to avoid having a mixup in mcerd
                # command file content when there are more than one process
                # (without this, Potku would crash)
                # TODO create command file for each process so they can
                #  be started at the same time?

        if not optimize:
            # Start updating observers on current progress
            thread = threading.Thread(target=self.check_status)
            thread.daemon = True
            thread.start()

            if self.use_default_settings and not self.simulation.detector:
                # TODO instead of having these lists of running simulations
                #      simulation object could just iterate over its element
                #      simulations and check the boolean values to determine
                #      which simulations are running when needed
                self.request.running_simulations.append(self)
            else:
                self.simulation.running_simulations.append(self)
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
        active_count = self.__erd_filehandler.get_active_atom_counts()
        old_count = self.__erd_filehandler.get_old_atom_counts()
        total_count = active_count + old_count
        erd_file_count = len(self.__erd_filehandler)

        if starting:
            state = SimulationState.STARTING
        elif not erd_file_count:
            # No ERD files exist so simulation has not started
            state = SimulationState.NOTRUN
        elif process_count:
            # Some processes are running, we are either in presim or running
            # state
            if not active_count:
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

    def get_max_seed(self):
        """Returns maximum seed that has been used in simulations.

        Return:
            maximum seed value used in simulation processes
        """
        return self.__erd_filehandler.get_max_seed()

    def get_erd_files(self):
        """Returns both active and already simulated ERD files.
        """
        return list(f for f, _, _ in self.__erd_filehandler)

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
                opt_mode = "recoil"
            else:
                recoils = self.recoil_elements
                opt = False
                optfl = True
                recoil_name = "optfl"
                opt_mode = "fluence"

            # Check if maximum time has been used for simulation
            current_time = time.time()
            if current_time - check_start >= check_max:  # Max time
                self.stop()

            erd_file = Path(self.directory,
                            fp.get_erd_file_name(recoils[0],
                                                 self.__opt_seed,
                                                 optim_mode=opt_mode))
            if os.path.exists(erd_file):
                # Calculate new energy spectrum
                self.calculate_espe(recoils[0], optimize_recoil=opt,
                                    optimize_fluence=optfl)
                espe_file = os.path.join(self.directory, recoils[0].prefix +
                                         "-" + recoil_name + ".simu")
                espe = gf.read_espe_file(espe_file)
                if espe:
                    # Change items to float types
                    espe = list(np.float_(espe))
                    if self.__previous_espe:
                        espe, self.__previous_espe = gf.uniform_espe_lists([
                            espe, self.__previous_espe], self.channel_width)
                        # Calculate distance between energy spectra
                        # TODO move this to math_functions
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
                                self.stop()
                                break
                        previous_avg = avg
                    self.__previous_espe = espe

    def __remove(self):
        """Removes the simulation from running simulations."""
        # We do not particularly care in which list the simulation is, just
        # get it removed (from both if necessary)
        try:
            self.request.running_simulations.remove(self)
        except ValueError:
            # simulation was not here, nothing to do
            # TODO what type of Error might happen in race condition?
            pass
        try:
            self.simulation.running_simulations.remove(self)
        except ValueError:
            # simulation was not here, nothing to do
            pass

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

        status = self.get_current_status()

        if status["state"] == SimulationState.DONE:
            self.__remove()

            # FIXME ATM, logging from another thread than main thread will
            #       cause an error:
            #   QObject::connect: Cannot queue arguments of type
            #       'QTextCursor'
            #   (Make sure 'QTextCursor' is registered using
            #       qRegisterMetaType().)
            # GUI has a log box that is updated on each log message,
            # so updating it from another thread leads to errors and possibly
            # (albeit rarely) crashes. A thread safe GUI logging should
            # nevertheless be implemented.

            # msg = "Simulation finished. Element {0}, processes: {1},
            # observed" \
            #      " atoms: {2}".format(str(element),
            #                           self.last_process_count,
            #                           status["atom_count"])

            # logging.getLogger(simulation_name).info(msg)

            self.simulations_done = True
            self.__erd_filehandler.update()
            self.on_complete(self.get_current_status())

    def stop(self):
        """ Stop the simulation."""
        # TODO check if this and notify can be refactored
        if self.__cancellation_token is not None:
            self.__cancellation_token.request_cancellation()

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

        self.__remove()

        self.optimization_mcerd_running = False
        self.simulations_done = True

        # Calculate erd lines for log
        status = self.get_current_status()

        if not self.optimization_recoils:
            element = self.recoil_elements[0].element
        else:
            element = self.optimization_recoils[0].element

        msg = f"Simulation stopped. Element: {element.get_prefix()}, " \
              f"processes: {self.last_process_count}, Number of observed " \
              f"atoms: {status['atom_count']}"

        logging.getLogger(self.simulation.name).info(msg)
        self.__erd_filehandler.update()
        self.on_complete(status)

    def calculate_espe(self, recoil_element, optimize_recoil=False, ch=None,
                       fluence=None, optimize_fluence=False):
        """
        Calculate the energy spectrum from the MCERD result file.

        Args:
            recoil_element: Recoil element.
            optimize_recoil: Whether recoil is optimized.
            ch: Channel width to use.
            fluence: Fluence to use.
            optimize_fluence: TODO
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
            "solid": detector.calculate_solid(),
            "erd_file": erd_file,
            "spectrum_file": spectrum_file,
            "recoil_file": recoil_file
        }
        self.get_espe = GetEspe(espe_settings)
        self.get_espe.run_get_espe()

    def reset(self, remove_files=True):
        """Function that resets the state of ElementSimulation.

        Args:
            remove_files: whether simulation result files are also removed
        """
        self.stop()

        self.simulations_done = False
        if self.optimization_running:
            self.optimization_stopped = True
        self.optimization_running = False

        if remove_files:
            for recoil in self.recoil_elements:
                gf.delete_simulation_results(self, recoil)

        self.__erd_filehandler.clear()

        self.on_complete(self.get_current_status())


class ERDFileHandler:
    """Helper class to handle ERD files that belong to the ElementSimulation

    Handles counting atoms and getting seeds.
    """
    def __init__(self, old_files, recoil_element):
        """Initializes a new ERDFileHandler that tracks old and new .erd files
        belonging to the given recoil element

        Args:
            old_files: list of absolute paths to .erd files that contain data
                       that has already been simulated
            recoil_element: recoil element for which the .erd files belong to.
        """
        self.recoil_element = recoil_element
        self.__active_files = {}

        self.__old_files = {
            file: seed
            for file, seed in fp.validate_erd_file_names(old_files,
                                                         self.recoil_element)
        }

    @classmethod
    def from_directory(cls, directory, recoil_element, optim=None):
        """Initializes a new ERDFileHandler by reading ERD files
        from a directory.

        Args:
            directory: path to a directory
            recoil_element: recoil element for which the ERD files belong
                            to

        Return:
            new ERDFileHandler.
        """
        full_paths = (Path(directory, file)
                      for file in os.listdir(directory))
        return cls(full_paths, recoil_element)

    def __iter__(self):
        """Iterates over all of the ERD files, both active and old ones.

        Yield:
            tuple consisting of absolute file path, seed value and boolean
            that tells if the ERD file is used in a running simulation or
            not.
        """
        for file, seed in itertools.chain(self.__active_files.items(),
                                          self.__old_files.items()):
            yield file, seed, file in self.__active_files

    def add_active_file(self, erd_file):
        """Adds an active ERD file to the handler.

        File must not already exist in active or old files, otherwise
        ValueError is raised.

        Args:
            erd_file: file name of an .erd file
        """
        if erd_file in self.__active_files:
            raise ValueError("Given .erd file is an already active file")
        if erd_file in self.__old_files:
            raise ValueError("Given .erd file is an already simulated file")

        # Check that the file is valid
        tpl = next(fp.validate_erd_file_names([erd_file],
                                              self.recoil_element),
                   None)

        if tpl is not None:
            self.__active_files[tpl[0]] = tpl[1]
        else:
            raise ValueError("Given file was not a valid .erd file")

    def get_max_seed(self):
        """Returns the largest seed in current .erd file collection or None
        if no .erd files are stored in the handler.
        """
        return max((seed for _, seed, _ in self), default=None)

    def get_active_atom_counts(self):
        """Returns the number of atoms in currently active .erd files.
        """
        return sum(self.__get_atom_count(file)
                   for file in self.__active_files)

    def get_old_atom_counts(self):
        """Returns the number of atoms in already simulated .erd files.
        """
        return sum(self.__get_atom_count_cached(file)
                   for file in self.__old_files)

    def __get_atom_count(self, erd_file):
        """Returns the number of counted atoms in given ERD file.
        """
        return gf.count_lines_in_file(erd_file, check_file_exists=True)

    @functools.lru_cache(32)
    def __get_atom_count_cached(self, erd_file):
        """Cached version of the atom counter. If the atoms in the
        ERD file have already been counted, a cached result is returned.

        Cache is never cleared during the run time of the program so only
        use this when you are sure that the atom count in a file does not
        change anymore.
        """
        return self.__get_atom_count(erd_file)

    def update(self):
        """Moves all files from active file collection to already simulated
        files.
        """
        self.__old_files.update(self.__active_files)
        self.__active_files.clear()

    def clear(self):
        """Removes existing ERD files from handler.
        """
        self.__active_files.clear()
        self.__old_files.clear()
        self.__get_atom_count_cached.cache_clear()

    def __len__(self):
        """Returns the number of active files and already simulated files.
        """
        return len(self.__active_files) + len(self.__old_files)
