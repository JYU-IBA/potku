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
import os
import time
import itertools
import functools
import rx

import modules.file_paths as fp
import modules.general_functions as gf

from typing import Optional
from rx import operators as ops
from pathlib import Path
from collections import deque

from modules.concurrency import CancellationToken
from modules.base import Serializable
from modules.base import AdjustableSettings
from modules.base import MCERDParameterContainer
from modules.get_espe import GetEspe
from modules.mcerd import MCERD
from modules.observing import Observable
from modules.recoil_element import RecoilElement
from modules.enums import OptimizationType
from modules.enums import SimulationState


# Mappings between the names of the MCERD parameters (keys) and
# ElementSimulation attributes (values)
_SETTINGS_MAP = {
    "simulation_type": "simulation_type",
    "simulation_mode": "simulation_mode",
    "number_of_ions": "number_of_ions",
    "number_of_ions_in_presimu": "number_of_preions",
    "number_of_scaling_ions": "number_of_scaling_ions",
    "number_of_recoils": "number_of_recoils",
    "minimum_scattering_angle": "minimum_scattering_angle",
    "minimum_main_scattering_angle": "minimum_main_scattering_angle",
    "minimum_energy_of_ions": "minimum_energy",
    "seed_number": "seed_number"
}


class ElementSimulation(Observable, Serializable, AdjustableSettings,
                        MCERDParameterContainer):
    """
    Class for handling the element specific simulation. Can have multiple
    MCERD objects.
    """

    __slots__ = "directory", "request", "name_prefix", "modification_time", \
                "simulation_type", "number_of_ions", "number_of_preions", \
                "number_of_scaling_ions", "number_of_recoils", \
                "minimum_scattering_angle", "minimum_main_scattering_angle", \
                "minimum_energy", "simulation_mode", "seed_number", \
                "recoil_elements", "recoil_atoms", \
                "channel_width", "detector", "__erd_filehandler", \
                "description", "run", "name", \
                "use_default_settings", "simulation", \
                "__full_edit_on", "y_min", "main_recoil",\
                "optimization_recoils", "optimization_widget", \
                "_optimization_running", "optimized_fluence", \
                "sample", "__cts", "_simulation_running"

    def __init__(self, directory, request, recoil_elements,
                 simulation=None, name_prefix="", sample=None,
                 detector=None, run=None, name="Default",
                 description="", modification_time=None,
                 simulation_type="ERD", number_of_ions=1000000,
                 number_of_preions=100000, number_of_scaling_ions=5,
                 number_of_recoils=10, minimum_scattering_angle=0.05,
                 minimum_main_scattering_angle=20, simulation_mode="narrow",
                 seed_number=101, minimum_energy=1.0, channel_width=0.025,
                 use_default_settings=True, main_recoil=None,
                 optimization_recoils=None, optimized_fluence=None,
                 save_on_creation=True):
        """ Initializes ElementSimulation.
        Args:
            directory: Folder of simulation that contains the ElementSimulation.
            request: Request object reference.
            recoil_elements: List of RecoilElement objects.
            simulation: Simulation object.
            name_prefix: Prefix of the name, e.g. 55Mn
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
            sample: Sample object under which ElementSimulation belongs.
            element simulation.
            main_recoil: Main recoil element.
            optimization_recoils: List or recoils that are used for
                optimization.
            optimized_fluence: Optimized fluence value.
            save_on_creation: Determines if the element simulation is saved to
                    a file when initialized
        """
        # FIXME there is an inconsistency when it comes to the return value
        #  is_simulation_finished method. If the user starts a new simulation,
        #  but stops it before pre-sim ends, the method will return True,
        #  However, when the program is restarted, and the ElementSimulation is
        #  initialized again, the method will once again return False.
        # Call Observable's initialization to set up observer list
        Observable.__init__(self)

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

        if detector:
            self.detector = detector
        else:
            self.detector = self.request.default_detector

        self.run = run
        self.sample = sample

        # TODO raise errors if the type and mode are wrong
        # TODO make these into enums
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
            if os.sep + "Default" in str(self.directory):
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

        # Collection of CancellationTokens
        self.__cts = set()

        self.__erd_filehandler = ERDFileHandler.from_directory(
            self.directory, self.main_recoil)

        # TODO check if all optimization stuff can be moved to another module
        if optimization_recoils is None:
            self.optimization_recoils = []
        else:
            self.optimization_recoils = optimization_recoils

        self._simulation_running = False
        self._optimization_running = False
        self.optimization_widget = None
        # Store fluence optimization results
        self.optimized_fluence = optimized_fluence

        if self.is_simulation_finished():
            self.__full_edit_on = False
            self.y_min = 0.0001
        else:
            self.__full_edit_on = True
            self.y_min = 0.0

    def unlock_edit(self):
        """
        Unlock full edit.

        Also resets ElementSimulation
        """
        self.y_min = 0.0
        self.__full_edit_on = True

    def lock_edit(self):
        """
        Lock full edit.
        """
        self.y_min = 0.0001
        self.__full_edit_on = False

    def get_full_edit_on(self):
        """
        Get whether full edit is on or not.

        Return:
            True of False.
        """
        return self.__full_edit_on

    def move_optimized_recoil_to_regular_recoils(self):
        """Moves optimized recoils to the collection that holds regular
        recoils.
        """
        for recoil in self.optimization_recoils:
            # Ensure that the name is unique
            new_name = recoil.name.replace("opt", "", 1)
            full_name = new_name
            recoil_names = {r.name for r in self.recoil_elements}
            suffix = 1
            while full_name in recoil_names:
                full_name = f"{new_name}-{suffix}"
                suffix += 1

            values = {
                "name": full_name,
                "description": recoil.description,
                "reference_density": recoil.reference_density,
                "color": recoil.color,
                "multiplier": recoil.multiplier
            }
            self.update_recoil_element(recoil, values)
        self.recoil_elements.extend(self.optimization_recoils)
        self.optimization_recoils = []

    def update_recoil_element(self, recoil_element, new_values):
        """Updates RecoilElement object with new values.

        Args:
            recoil_element: RecoilElement object to update.
            new_values: New values as a dictionary.
        """
        old_name = recoil_element.get_full_name()

        recoil_element.update(new_values)

        # Delete possible extra rec files.
        for file in os.listdir(self.directory):
            if file.startswith(old_name) and \
                    (file.endswith(".rec") or file.endswith(".sct")):
                try:
                    os.remove(Path(self.directory, file))
                except OSError:
                    pass
                break

        recoil_element.to_file(self.directory)

        if old_name != recoil_element.get_full_name():
            if recoil_element.type == "rec":
                recoil_suffix = ".recoil"
            else:
                recoil_suffix = ".scatter"
            recoil_file = Path(self.directory, old_name + recoil_suffix)
            if recoil_file.exists():
                new_name = recoil_element.get_full_name() + recoil_suffix
                gf.rename_file(recoil_file, new_name)

            if recoil_element is self.main_recoil:  # Only main recoil
                # updates erd file names
                for file in os.listdir(self.directory):
                    if file.startswith(recoil_element.prefix) and file.endswith(
                            ".erd"):
                        erd_file = Path(self.directory, file)
                        seed = file.split('.')[1]
                        new_name = f"{recoil_element.get_full_name()}." \
                                   f"{seed}.erd"
                        gf.rename_file(erd_file, new_name)
                # Write mcsimu file
                self.to_file()
                self.__erd_filehandler.update()

            simu_file = Path(self.directory, old_name + ".simu")
            if simu_file.exists():
                new_name = recoil_element.get_full_name() + ".simu"
                gf.rename_file(simu_file, new_name)

    @classmethod
    def from_file(cls, request, prefix, simulation_folder, mcsimu_file_path,
                  profile_file_path, sample=None, detector=None):
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
            sample: sample under which the parent simulation belongs to
            detector: detector that is used when simulation is not run with
                request settings.
        """
        with open(mcsimu_file_path) as mcsimu_file:
            mcsimu = json.load(mcsimu_file)

        # Pop the recoil name so it can be converted to a RecoilElement
        main_recoil_name = mcsimu.pop("main_recoil")

        # Convert modification_time and use_default_settings to correct
        # types
        mcsimu["modification_time"] = mcsimu.pop("modification_time_unix")
        mcsimu["use_default_settings"] = \
            mcsimu["use_default_settings"] == "True"

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
        optimized_recoils_dict = {}

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
                    optimized_recoils_dict[0] = rec_elem
                elif fp.is_optmed(prefix, file):
                    optimized_recoils_dict[1] = rec_elem
                elif fp.is_optlast(prefix, file):
                    optimized_recoils_dict[2] = rec_elem
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
        optimized_recoils = [val
                             for key, val
                             in sorted(optimized_recoils_dict.items())]
        return cls(directory=simulation_folder,
                   request=request,
                   recoil_elements=recoil_elements,
                   name_prefix=name_prefix,
                   name=name,
                   channel_width=channel_width,
                   optimization_recoils=optimized_recoils,
                   optimized_fluence=optimized_fluence,
                   main_recoil=main_recoil,
                   sample=sample,
                   detector=detector,
                   **mcsimu)

    def get_full_name(self):
        """Returns the full name of the ElementSimulation object.
        """
        if self.name_prefix:
            return f"{self.name_prefix}-{self.name}"
        return self.name

    def get_json_content(self):
        """Returns a dictionary that represents the values of the
        ElementSimulation in json format.
        """
        timestamp = time.time()

        return {
            "name": self.get_full_name(),
            "description": self.description,
            "modification_time": time.strftime("%c %z %Z", time.localtime(
                timestamp)),
            "modification_time_unix": timestamp,
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

    def get_default_file_path(self):
        """Returns a default file path that to_file uses.
        """
        return Path(self.directory, f"{self.get_full_name()}.mcsimu")

    def to_file(self, file_path=None):
        """Save mcsimu settings to file.

        Args:
            file_path: File in which the mcsimu settings will be saved.
        """
        # TODO maybe it is not necessary to call this every time a request
        #      is opened
        if file_path is None:
            file_path = self.get_default_file_path()
        with open(file_path, "w") as file:
            json.dump(self.get_json_content(), file, indent=4)

    def remove_file(self, file_path=None):
        """Removes the .mcsimu file.

        Args:
            file_path: path to the .mcsimu file
        """
        try:
            if file_path is None:
                file_path = self.get_default_file_path()
            os.remove(file_path)
        except (OSError, IsADirectoryError, PermissionError):
            pass

    def profile_to_file(self, file_path):
        """Save profile settings (only channel width) to file.

        Args:
            file_path: File in which the channel width will be saved.
        """
        # Read .profile to obj to update only channel width
        time_stamp = time.time()
        if Path(file_path).exists():
            with open(file_path) as file:
                obj_profile = json.load(file)

            obj_profile["modification_time"] = time.strftime(
                "%c %z %Z", time.localtime(time_stamp))
            obj_profile["modification_time_unix"] = time_stamp
            obj_profile["energy_spectra"]["channel_width"] = self.channel_width
        else:
            obj_profile = {"energy_spectra": {},
                           "modification_time": time.strftime(
                               "%c %z %Z", time.localtime(time_stamp)),
                           "modification_time_unix": time_stamp}
            obj_profile["energy_spectra"]["channel_width"] = self.channel_width

        with open(file_path, "w") as file:
            json.dump(obj_profile, file, indent=4)

    def start(self, number_of_processes, start_value=None,
              use_old_erd_files=True, optimization_type=None,
              shared_ions=False, cancellation_token=None, start_interval=5,
              status_check_interval=1, **kwargs) -> Optional[rx.Observable]:
        """
        Start the simulation.

        Args:
            number_of_processes: How many processes are started.
            start_value: Which is the first seed.
            use_old_erd_files: whether the simulation continues using old erd
                files or not
            optimization_type: either recoil, fluence or None
            shared_ions: boolean that determines if the ion counts are
                divided by the number of processes
            cancellation_token: CancellationToken that can be used to stop
                the start process
            start_interval: seconds between the start of each simulation
                (ensures that MCERD's startup files are not being
                overwritten by later processes)
            status_check_interval: seconds between each observed atoms count.
            kwargs: keyword arguments passed down to MCERD's run method

        Return:
            observable stream
        """
        if self.is_simulation_running() or self.is_optimization_running():
            return None
        self._set_flags(True, optimization_type)
        if self.is_optimization_running():
            # This is done to inform the controls about optimization starting
            # so the GUI elements can be disabled.
            self.on_completed(self.get_current_status())

        if not use_old_erd_files:
            self.__erd_filehandler.clear()
            self.delete_simulation_results()

        settings, run, detector = self.get_mcerd_params()

        # Set seed to either the value provided as parameter or use the one
        # stored in current element simulation.
        max_seed = self.get_max_seed()
        seed_number = settings.pop("seed_number")
        if start_value is not None:
            seed_number = start_value
        if max_seed is not None and seed_number <= max_seed:
            seed_number = max_seed + 1

        if optimization_type is OptimizationType.RECOIL:
            recoil = self.optimization_recoils[0]
        else:
            recoil = self.recoil_elements[0]

        if number_of_processes < 1:
            number_of_processes = 1

        if shared_ions:
            settings["number_of_ions"] //= number_of_processes
            settings["number_of_ions_in_presimu"] //= number_of_processes

        settings.update({
            "beam": run.beam,
            "target": self.simulation.target,
            "detector": detector,
            "recoil_element": recoil,
            "sim_dir": self.directory
        })

        if cancellation_token is None:
            cancellation_token = CancellationToken()

        self.__cts.add(cancellation_token)

        # New MCERD process is started every five seconds until number of
        # processes is reached or cancellation has been requested.
        # Seed is incremented for each new process.
        return rx.timer(0, start_interval).pipe(
            ops.take_while(
                lambda _: not cancellation_token.is_cancellation_requested()),
            ops.take(number_of_processes),
            ops.scan(lambda acc, _: acc + 1, seed=seed_number - 1),
            ops.map(lambda next_seed: self._start(
                recoil, next_seed, optimization_type, dict(settings),
                cancellation_token, **kwargs)),
            ops.flat_map(lambda x: x),
            ops.scan(lambda acc, x: {
                **x,
                "total_processes": number_of_processes,
                "finished_processes": acc["finished_processes"] + int(
                    not x["is_running"])
            }, seed={"finished_processes": 0}),
            ops.combine_latest(rx.timer(0, status_check_interval).pipe(
                ops.map(lambda x: self.get_current_status()),
                ops.take_while(
                    lambda _:
                    not cancellation_token.is_cancellation_requested(),
                    inclusive=True),
            )),
            ops.map(lambda x: {**x[0], **x[1]}),
            ops.take_while(
                lambda x: x["finished_processes"] < x["total_processes"] and
                not x["msg"].startswith("Simulation "),
                inclusive=True),
            ops.do_action(
                on_error=lambda _: self._clean_up(cancellation_token),
                on_completed=lambda: self._clean_up(cancellation_token)
            )
        )

    def _start(self, recoil, seed_number, optimization_type, settings,
               cancellation_token, **kwargs) -> rx.Observable:
        """Inner method that creates an MCERD instance and runs it.

        Returns an observable stream of MCERD output.
        """
        new_erd_file = fp.get_erd_file_name(
            recoil, seed_number, optim_mode=optimization_type)

        new_erd_file = Path(self.directory, new_erd_file)
        try:
            # remove file if it exists previously
            os.remove(new_erd_file)
        except OSError:
            pass

        if optimization_type is None:
            self.__erd_filehandler.add_active_file(new_erd_file)

        mcerd = MCERD(
            seed_number, settings, self.get_full_name(),
            optimize_fluence=optimization_type is OptimizationType.FLUENCE)

        return mcerd.run(cancellation_token=cancellation_token, **kwargs)

    def _set_flags(self, b, optim_mode=None):
        """Sets the boolean flags that indicate the state of
        simulation accordingly.
        """
        self._simulation_running = b and optim_mode is None
        self._optimization_running = b and optim_mode is not None

    def get_settings(self):
        """Returns simulation settings as a dict. Overrides base class function.
        """
        return {
            key: getattr(self, value)
            for key, value in _SETTINGS_MAP.items()
        }

    def set_settings(self, **kwargs):
        """Sets simulation settings based on the keyword arguments. Overrides
        base class function.

        Note that the keywords must be the ones used by MCERD, rather than
        the attribute names of the ElementSimulation object.
        """
        for key, value in kwargs.items():
            try:
                setattr(self, _SETTINGS_MAP[key], value)
            except KeyError:
                # keyword does not have a known mapping, nothing to do
                pass

    def get_current_status(self):
        """Returns the number of atoms counted, number of running processes and
        the state of simulation.

        Return:
            dictionary
        """
        atom_count = self.__erd_filehandler.get_total_atom_count()

        if self.is_simulation_running():
            state = SimulationState.RUNNING
        elif self.is_simulation_finished():
            state = SimulationState.DONE
        else:
            state = SimulationState.NOTRUN

        # Return status as a dict
        return {
            "atom_count": atom_count,
            "state": state,
            "optimizing": self.is_optimization_running()
        }

    def get_main_recoil(self) -> Optional[RecoilElement]:
        # TODO replace the main_recoil attribute as well as all references to
        #   recoil_elements[0] with this function
        if self.recoil_elements:
            return self.recoil_elements[0]
        else:
            return None

    def is_simulation_running(self) -> bool:
        """Whether simulation is currently running and optimization is not
        running.
        """
        return self._simulation_running

    def is_simulation_finished(self) -> bool:
        """Whether simulation is finished.
        """
        return not self.is_simulation_running() and \
            self.__erd_filehandler.results_exist()

    def is_optimization_running(self) -> bool:
        """Whether optimization is running.
        """
        return self._optimization_running

    def is_optimization_finished(self) -> bool:
        """Whether optimization has finished.
        """
        # TODO better way to determine this
        return not self.is_optimization_running() and (any(
            self.optimization_recoils) or self.optimized_fluence is not None)

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

    def _clean_up(self, cancellation_token):
        """Performs clean up after all of the simulation process have ended.
        """
        self._set_flags(False)
        self.__erd_filehandler.update()
        self.__cts.remove(cancellation_token)
        if self.simulation is not None:
            atom_count = self.__erd_filehandler.get_total_atom_count()
            msg = f"Simulation finished. Element " \
                  f"{self.get_main_recoil().get_full_name()}, " \
                  f"observed atoms: {atom_count}."
            logging.getLogger(self.simulation.name).info(msg)

        self.on_completed(self.get_current_status())

    def stop(self):
        """ Stop the simulation.
        """
        cts = list(self.__cts)
        for ct in cts:
            ct.request_cancellation()

    def calculate_espe(self, recoil_element, ch=None, fluence=None,
                       optimization_type=None):
        """
        Calculate the energy spectrum from the MCERD result file.

        Args:
            recoil_element: Recoil element.
            ch: Channel width to use.
            fluence: Fluence to use.
            optimization_type: either recoil, fluence or None

        Return:
            path to the espe file
        """
        if self.simulation_type == "ERD":
            suffix = "recoil"
        else:
            suffix = "scatter"

        if optimization_type is OptimizationType.RECOIL:
            recoil = self.optimization_recoils[0]
        else:
            recoil = self.recoil_elements[0]

        if optimization_type is OptimizationType.FLUENCE:
            espe_file = f"{recoil_element.prefix}-optfl.simu"
            recoil_file = f"{recoil_element.prefix}-optfl.{suffix}"
        else:
            espe_file = f"{recoil_element.get_full_name()}.simu"
            recoil_file = f"{recoil_element.get_full_name()}.{suffix}"

        erd_file = Path(
            self.directory,
            fp.get_erd_file_name(recoil, "*", optim_mode=optimization_type))
        espe_file = Path(self.directory, espe_file)
        recoil_file = Path(self.directory, recoil_file)

        with open(recoil_file, "w") as rec_file:
            rec_file.write("\n".join(recoil_element.get_mcerd_params()))

        if ch:
            channel_width = ch
        else:
            channel_width = self.channel_width

        _, run, detector = self.get_mcerd_params()

        if fluence is not None:
            used_fluence = fluence
        else:
            used_fluence = run.fluence

        espe_settings = {
            "beam": run.beam,
            "detector": detector,
            "target": self.simulation.target,
            "ch": channel_width,
            "reference_density": recoil_element.reference_density,
            "multiplier": recoil_element.multiplier,
            "fluence": used_fluence,
            "timeres": detector.timeres,
            "solid": detector.calculate_solid(),
            "erd_file": erd_file,
            "spectrum_file": espe_file,
            "recoil_file": recoil_file
        }
        get_espe = GetEspe(espe_settings)
        get_espe.run_get_espe()

        # TODO could also return the contents of the espe_file
        return Path(espe_file)

    def get_mcerd_params(self):
        """Returns the parameters for MCERD simulations.
        """
        if self.use_default_settings:
            settings = self.request.default_element_simulation.get_settings()
        else:
            settings = self.get_settings()

        if self.simulation.use_request_settings:
            run = self.request.default_run
            detector = self.request.default_detector
        else:
            run = self.run
            detector = self.detector

        return settings, run, detector

    def delete_optimization_results(self, optim_mode=None):
        """Deletes optimization results. Also stops the optimization if
        it is running.

        Args:
            optim_mode: OptimizationType
        """
        if self.is_optimization_running():
            self.stop()

        # FIXME ensure that these files are actually optimization results and
        #   not just simulations with names like <something>-opt or
        #   <something>-optfl.
        #   Would perhaps be better if the optimization files are in their
        #   own folder.

        if optim_mode is OptimizationType.RECOIL:
            def filter_func(file):
                return file.startswith(f"{self.name_prefix}-opt") and not \
                    file.startswith(f"{self.name_prefix}-optfl")
        elif optim_mode is OptimizationType.FLUENCE:
            def filter_func(file):
                return file.startswith(f"{self.name_prefix}-optfl")
            self.optimized_fluence = None
        elif optim_mode is None:
            def filter_func(file):
                return file.startswith(f"{self.name_prefix}-opt") or \
                    file.startswith(f"{self.name_prefix}-optfl")
            self.optimized_fluence = None
        else:
            raise ValueError(f"Unknown optimization type: {optim_mode}.")

        gf.remove_files(
            self.directory,
            exts={".recoil", ".erd", ".simu", ".scatter", ".rec"},
            filter_func=filter_func)

        self.optimization_recoils = []

    def delete_simulation_results(self):
        """Deletes all simulation results for this ElementSimulation.
        """
        prefixes = {recoil.get_full_name() for recoil in self.recoil_elements}

        def filter_func(file):
            return any(file.startswith(pre) for pre in prefixes) and \
                "opt" not in file

        gf.remove_files(
            self.directory,
            exts={".recoil", ".erd", ".simu", ".scatter"},
            filter_func=filter_func)

    def reset(self, remove_files=True):
        """Function that resets the state of ElementSimulation.

        Args:
            remove_files: whether simulation result files are also removed
        """
        self.stop()
        # TODO should wait here until the simulation fully stops

        self._set_flags(False)

        if remove_files:
            self.delete_simulation_results()
            self.delete_optimization_results()
            self.__erd_filehandler.clear()
        self.unlock_edit()


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
            for file, seed in fp.validate_erd_file_names(
                old_files, self.recoil_element)
        }

    @classmethod
    def from_directory(cls, directory, recoil_element):
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
                      for file in os.scandir(directory))
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
        tpl = next(fp.validate_erd_file_names(
            [erd_file], self.recoil_element), None)

        if tpl is not None:
            self.__active_files = {
                **self.__active_files,
                tpl[0]: tpl[1]
            }
        else:
            raise ValueError("Given file was not a valid .erd file")

    def get_max_seed(self):
        """Returns the largest seed in current .erd file collection or None
        if no .erd files are stored in the handler.
        """
        return max((seed for _, seed, _ in self), default=None)

    def get_active_atom_count(self):
        """Returns the number of atoms in currently active .erd files.
        """
        return sum(self.__get_atom_count(file)
                   for file in self.__active_files)

    def get_old_atom_count(self):
        """Returns the number of atoms in already simulated .erd files.
        """
        return sum(self.__get_atom_count_cached(file)
                   for file in self.__old_files)

    def get_total_atom_count(self):
        """Returns the total number of observed atoms.
        """
        return self.get_active_atom_count() + self.get_old_atom_count()

    @staticmethod
    def __get_atom_count(erd_file):
        """Returns the number of counted atoms in given ERD file.
        """
        return gf.count_lines_in_file(erd_file, check_file_exists=True)

    @functools.lru_cache(128)
    def __get_atom_count_cached(self, erd_file):
        """Cached version of the atom counter. If the atoms in the
        ERD file have already been counted, a cached result is returned.
        """
        return self.__get_atom_count(erd_file)

    def update(self):
        """Moves all files from active file collection to already simulated
        files.
        """
        # TODO check if the name of the RecoilElement has changed and update
        #   file references if necessary
        self.__old_files = {
            **self.__old_files,
            **self.__active_files
        }
        self.__active_files = {}

    def clear(self):
        """Removes existing ERD files from handler.
        """
        self.__active_files = {}
        self.__old_files = {}
        self.__get_atom_count_cached.cache_clear()

    def results_exist(self):
        """Returns True if ERD files exist.
        """
        return any(self.__old_files) or any(self.__active_files)

    def __len__(self):
        """Returns the number of active files and already simulated files.
        """
        return len(self.__active_files) + len(self.__old_files)
