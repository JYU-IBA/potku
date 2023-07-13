# coding=utf-8
"""
Created on 25.4.2018
Updated on 13.4.2023
Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2018 Severi Jääskeläinen, Samuel Kaiponen, Heta Rekilä and
Sinikka Siironen, 2020 Juhani Sundell, Tuomas Pitkänen
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
             "Sinikka Siironen \n Juhani Sundell \n Tuomas Pitkänen"
__version__ = "2.0"

import functools
import itertools
import json
import os
import time
from collections import deque
from pathlib import Path
from threading import Event
from typing import Any
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple
from typing import Union

import reactivex as rx
from reactivex import operators as ops

from . import file_paths as fp
from . import general_functions as gf
from .base import AdjustableSettings
from .base import MCERDParameterContainer
from .base import Serializable
from .concurrency import CancellationToken
from .detector import Detector
from .element import Element
from .enums import IonDivision
from .enums import OptimizationType
from .enums import SimulationMode
from .enums import SimulationState
from .enums import SimulationType
from .get_espe import GetEspe
from .mcerd import MCERD
from .observing import Observable
from .recoil_element import RecoilElement
from .run import Run
from .config_manager import ConfigManager

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
    """Class for handling the element specific simulation. Can have multiple
    MCERD objects.
    """
    # Keys that are added to MCERD output
    FINISHED = "finished_processes"
    TOTAL = "total_processes"
    STATE = "status"
    ATOMS = "atom_count"
    OPTIMIZING = "optimizing"

    __slots__ = "directory", "request", "name_prefix", "modification_time", \
                "simulation_type", "number_of_ions", "number_of_preions", \
                "number_of_scaling_ions", "number_of_recoils", \
                "minimum_scattering_angle", "minimum_main_scattering_angle", \
                "minimum_energy", "simulation_mode", "seed_number", \
                "recoil_elements", "recoil_atoms", \
                "channel_width", "_erd_filehandler", \
                "description", "name", \
                "use_default_settings", "simulation", "__full_edit_on", \
                "optimization_recoils", "optimization_widget", \
                "_optimization_running", "optimized_fluence", \
                "_cts", "_simulation_running", "_running_event"

    def __init__(self, directory: Path, request: "Request",
                 recoil_elements: List[RecoilElement],
                 simulation: Optional["Simulation"] = None,
                 name_prefix="", name="Default",
                 description="", modification_time=None,
                 simulation_type=SimulationType.ERD, number_of_ions=1_000_000,
                 number_of_preions=100_000, number_of_scaling_ions=5,
                 number_of_recoils=10, minimum_scattering_angle=0.05,
                 minimum_main_scattering_angle=20,
                 simulation_mode=SimulationMode.NARROW,
                 seed_number=101, minimum_energy=1.0, channel_width=0.025,
                 use_default_settings=True, optimization_recoils=None,
                 optimized_fluence=None, save_on_creation=True, recoils=None):
        """Initializes ElementSimulation. Most arguments are ignored if
        use_default_settings is True.
        Args:
            directory: Folder of simulation that contains the ElementSimulation.
            request: Request object reference.
            recoil_elements: List of RecoilElement objects.
            simulation: Simulation object.
            name_prefix: Prefix of the name, e.g. 55Mn
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
            optimization_recoils: List of recoils that are used for
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
        # TODO: Rename to use_request_settings
        self.use_default_settings = use_default_settings
        if self.use_default_settings:
            # Initialize fields to prevent KeyErrors during
            # self.clone_request_settings()
            self.simulation_type = None
            self.simulation_mode = None

            self.number_of_ions = None
            self.number_of_preions = None
            self.number_of_scaling_ions = None
            self.number_of_recoils = None
            self.minimum_scattering_angle = None
            self.minimum_main_scattering_angle = None
            self.minimum_energy = None
            self.seed_number = None
            self.channel_width = None

            self.clone_request_settings()
        else:
            self.simulation_type = SimulationType.fromStr(simulation_type)
            self.simulation_mode = SimulationMode(simulation_mode.lower())

            self.number_of_ions = number_of_ions
            self.number_of_preions = number_of_preions
            self.number_of_scaling_ions = number_of_scaling_ions
            self.number_of_recoils = number_of_recoils
            self.minimum_scattering_angle = minimum_scattering_angle
            self.minimum_main_scattering_angle = minimum_main_scattering_angle
            self.minimum_energy = minimum_energy
            self.seed_number = seed_number
            self.channel_width = channel_width

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

        #if save_on_creation: -TL
        if False:
            # Write .mcsimu file, recoil file and .profile file
            #self.to_file(Path(self.directory, f"{name}.mcsimu")) #TL

            for recoil_element in self.recoil_elements:
                recoil_element.to_file(self.directory)

            #print(f'type: {recoil_element.type}, sim_type: {self.simulation_type}')
            #self.simulation_type = SimulationType.fromStr(recoil_element.get_simulation_type())
            #print(f'sim_type: {self.simulation_type}')

            self.profile_to_file(Path(self.directory, f"{prefix}.profile"))

        # Collection of CancellationTokens
        self._cts: Set[CancellationToken] = set()

        self._erd_filehandler = ERDFileHandler.from_directory(
            self.directory, self.get_main_recoil())

        # TODO there should be a clearer boundary between optimization stuff
        #   and simulation stuff. Everything should not just be contained in
        #   this one class.
        if optimization_recoils is None:
            self.optimization_recoils = []
        else:
            self.optimization_recoils = optimization_recoils

        self._simulation_running = False
        self._optimization_running = False
        # Also set up an Event that will be locked during simulation
        self._running_event = Event()
        self._running_event.set()

        # TODO get rid of this GUI reference
        self.optimization_widget = None
        # Store fluence optimization results
        self.optimized_fluence = optimized_fluence

        if self.is_simulation_finished():
            self.__full_edit_on = False
        else:
            self.__full_edit_on = True

    def unlock_edit(self):
        """Unlock full edit.
        """
        self.__full_edit_on = True

    def lock_edit(self):
        """Lock full edit.
        """
        self.__full_edit_on = False

    def get_full_edit_on(self):
        """Get whether full edit is on or not.
        Return:
            True of False.
        """
        return self.__full_edit_on

    def move_optimized_recoil_to_regular_recoils(self):
        """Moves optimized recoils to the collection that holds regular
        recoils.
        """
        for recoil in self.optimization_recoils:
            # Find a unique name
            new_name = self._get_next_available_recoil_name(
                recoil.name.replace("opt", "", 1))

            values = {
                "name": new_name,
                "description": recoil.description,
                "reference_density": self.simulation.target.reference_density.get_value(),
                "color": recoil.color
            }
            self.update_recoil_element(recoil, values)
        self.recoil_elements.extend(self.optimization_recoils)
        self.optimization_recoils = []

    def _get_next_available_recoil_name(self, candidate_name: str) -> str:
        """Helper function for finding next recoil name that does not already
        exist.
        """
        def recoil_name_generator():
            yield candidate_name
            for i in itertools.count(start=1):
                yield f"{candidate_name}-{i}"

        recoil_names = {r.name for r in self.recoil_elements}
        return gf.find_next(
            recoil_name_generator(), lambda s: s not in recoil_names)

    def update_recoil_element(self, recoil_element: RecoilElement, new_values):
        """Updates RecoilElement object with new values.
        Args:
            recoil_element: RecoilElement object to update.
            new_values: New values as a dictionary.
        """
        old_name = recoil_element.get_full_name_without_simtype()

        recoil_element.update(new_values)

        # Delete possible extra rec files.
        # TODO use name instead of startswith
        gf.remove_matching_files(
            self.directory, exts={".rec", ".sct", ".prof"},
            filter_func=lambda x: x.startswith(old_name))

        recoil_element.to_file(self.directory)

        if old_name != recoil_element.get_full_name():
            recoil_suffix = recoil_element.get_recoil_suffix()
            recoil_file = Path(self.directory, f"{old_name}.{recoil_suffix}")
            if recoil_file.exists():
                new_name = recoil_element.get_full_name() + recoil_suffix
                gf.rename_file(recoil_file, new_name)

            if recoil_element is self.get_main_recoil():  # Only main recoil
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
                self._erd_filehandler.update()

            simu_file = Path(self.directory, f"{old_name}.simu")
            if simu_file.exists():
                new_name = recoil_element.get_full_name() + ".simu"
                gf.rename_file(simu_file, new_name)

    @classmethod
    def from_file(cls, request: "Request", prefix: str, simulation_folder: Path,
                  mcsimu_file: Path, profile_file: Path,
                  simulation: Optional["Simulation"] = None,
                  save_on_creation=True) -> "ElementSimulation":
        """Initialize ElementSimulation from JSON files.
        Args:
            request: Request that ElementSimulation belongs to.
            prefix: String that is used to prefix ".rec" files of this
                ElementSimulation.
            simulation_folder: A file path to simulation folder that contains
                files ending with ".rec".
            mcsimu_file: A file path to JSON file containing the
                simulation parameters.
            profile_file: A file path to JSON file containing the
                channel width.
            simulation: parent Simulation object of this ElementSimulation
            save_on_creation: whether ElementSimulation object is saved after
                it has been initialized
        Return:
            ElementSimulation object
        """
        with mcsimu_file.open("r") as mcsimu_file:
            mcsimu = json.load(mcsimu_file)

        # Pop the recoil name so it can be converted to a RecoilElement
        main_recoil_name = mcsimu.pop("main_recoil")

        # Convert modification_time and use_default_settings to correct
        # types
        mcsimu["modification_time"] = mcsimu.pop("modification_time_unix")
        mcsimu["use_default_settings"] = \
            mcsimu["use_default_settings"] == "True"
        mcsimu["simulation_type"] = SimulationType.fromStr(
            mcsimu["simulation_type"])
        mcsimu["simulation_mode"] = SimulationMode(
            mcsimu["simulation_mode"].lower())

        full_name = mcsimu.pop("name")
        try:
            name_prefix, name = full_name.split("-")
        except ValueError:
            name = full_name
            name_prefix = ""

        # Read channel width from .profile file.
        # TODO: element simulations use a simplified .profile format.
        #       Because of this, they cannot be loaded with
        #       Profile.from_file. Unify them?
        try:
            with profile_file.open("r") as prof_file:
                prof = json.load(prof_file)
            kwargs = {
                "channel_width": prof["energy_spectra"]["channel_width"]
            }
        except (json.JSONDecodeError, OSError, KeyError, AttributeError) as e:
            msg = f"Failed to read data from element simulation .profile " \
                  f"file {profile_file}: {e}."
            request.log_error(msg)
            kwargs = {}

        rec_type = mcsimu["simulation_type"].get_recoil_type()

        main_recoil = None
        recoil_elements = deque()
        optimized_recoils_dict = {}

        files = gf.find_files_by_extension(
            simulation_folder, ".recoil", ".erd", ".result", ".rec", ".sct")

        for r in (*files[".rec"], *files[".sct"]):
            if fp.is_recoil_file(prefix, r):
                recoil = RecoilElement.from_file(r, rec_type=rec_type, **kwargs)
                if SimulationType.fromStr(recoil.get_simulation_type()) == SimulationType.fromStr(rec_type):
                    # Check if main recoil
                    if recoil.name == main_recoil_name:
                        main_recoil = recoil

                    # Sort out optimization results
                    # TODO main recoil cannot be opt_first? could change this
                    #   to elif
                    if fp.is_optfirst(prefix, r):
                        optimized_recoils_dict[0] = recoil
                    elif fp.is_optmed(prefix, r):
                        optimized_recoils_dict[1] = recoil
                    elif fp.is_optlast(prefix, r):
                        optimized_recoils_dict[2] = recoil

                    else:
                        # Find if file has a matching erd file
                        # (=has been simulated)
                        for erd_file in files[".erd"]:
                            if fp.is_erd_file(recoil, erd_file):
                                recoil_elements.appendleft(recoil)
                                main_recoil = recoil
                                break
                        else:
                            # No matching erd file was found
                            if recoil is main_recoil:
                                recoil_elements.appendleft(recoil)
                            else:
                                recoil_elements.append(recoil)

        # Sort optimized recoils into proper order
        optimized_recoils = [
            val for key, val
            in sorted(optimized_recoils_dict.items())
        ]

        # Check if fluence has been optimized
        optimized_fluence = None
        for file in files[".result"]:
            if fp.is_optfl_result(prefix, file):
                with file.open("r") as f:
                    optimized_fluence = float(f.readline())
                break


        return cls(
            directory=simulation_folder, request=request,
            recoil_elements=list(recoil_elements), name_prefix=name_prefix,
            name=name, optimization_recoils=optimized_recoils,
            optimized_fluence=optimized_fluence, **kwargs, **mcsimu,
            simulation = simulation, save_on_creation = save_on_creation)

    @classmethod
    def from_json(cls, request: "Request", prefix: str, simulation_folder: Path,
                  mcsimu, profile_file: Path,
                  simulation: Optional["Simulation"] = None,
                  save_on_creation=True) -> "ElementSimulation":
        """Initialize ElementSimulation from JSON files.
        Args:
            request: Request that ElementSimulation belongs to.
            prefix: String that is used to prefix ".rec" files of this
                ElementSimulation.
            simulation_folder: A file path to simulation folder that contains
                files ending with ".rec".
            mcsimu_file: A file path to JSON file containing the
                simulation parameters.
            profile_file: A file path to JSON file containing the
                channel width.
            simulation: parent Simulation object of this ElementSimulation
            save_on_creation: whether ElementSimulation object is saved after
                it has been initialized
        Return:
            ElementSimulation object
        """

        # Pop the recoil name so it can be converted to a RecoilElement
        main_recoil_name = mcsimu.pop("main_recoil")

        # Convert modification_time and use_default_settings to correct
        # types
        mcsimu["modification_time"] = mcsimu.pop("modification_time_unix")
        mcsimu["use_default_settings"] = \
            mcsimu["use_default_settings"] == "True"
        mcsimu["simulation_type"] = SimulationType.fromStr(
            mcsimu["simulation_type"])
        mcsimu["simulation_mode"] = SimulationMode(
            mcsimu["simulation_mode"].lower())

        full_name = mcsimu.pop("name")
        try:
            name_prefix, name = full_name.split("-")
        except ValueError:
            name = full_name
            name_prefix = ""

        # Read channel width from .profile file.
        # TODO: element simulations use a simplified .profile format.
        #       Because of this, they cannot be loaded with
        #       Profile.from_file. Unify them?
        try:
            with profile_file.open("r") as prof_file:
                prof = json.load(prof_file)
            kwargs = {
                "channel_width": prof["energy_spectra"]["channel_width"]
            }
        except (json.JSONDecodeError, OSError, KeyError, AttributeError) as e:
            msg = f"Failed to read data from element simulation .profile " \
                  f"file {profile_file}: {e}."
            request.log_error(msg)
            kwargs = {}

        rec_type = mcsimu["simulation_type"].get_recoil_type()

        main_recoil = None
        recoil_elements = deque()
        optimized_recoils_dict = {}

        files = gf.find_files_by_extension(
            simulation_folder, ".recoil", ".erd", ".result", ".rec", ".sct")


        for r in mcsimu["recoils"]:
            recoil = RecoilElement.from_json(r, **kwargs)
            #if SimulationType.fromStr(recoil.get_simulation_type()) == SimulationType.fromStr(rec_type):
            # Check if main recoil
            if recoil.name == main_recoil_name:
                main_recoil = recoil
                recoil_elements.appendleft(recoil)
            else:
                recoil_elements.append(recoil)

            # Sort out optimization results
            # TODO main recoil cannot be opt_first? could change this
            #   to elif
            # if fp.is_optfirst(prefix, r["name"]):
            #     optimized_recoils_dict[0] = recoil
            # elif fp.is_optmed(prefix, r["name"]):
            #     optimized_recoils_dict[1] = recoil
            # elif fp.is_optlast(prefix, r["name"]):
            #     optimized_recoils_dict[2] = recoil
            # if False:
            #     pass
            # else:
            #     # Find if file has a matching erd file
            #     # (=has been simulated)
            #     for erd_file in files[".erd"]:
            #         if fp.is_erd_file(recoil, erd_file):
            #             recoil_elements.appendleft(recoil)
            #             main_recoil = recoil
            #             break
            #         else:
            #             # No matching erd file was found
            #             if recoil is main_recoil:
            #                 recoil_elements.appendleft(recoil)
            #             else:
            #                 recoil_elements.append(recoil)



        # Sort optimized recoils into proper order
        optimized_recoils = [
            val for key, val
            in sorted(optimized_recoils_dict.items())
        ]

        # Check if fluence has been optimized
        optimized_fluence = None
        for file in files[".result"]:
            if fp.is_optfl_result(prefix, file):
                with file.open("r") as f:
                    optimized_fluence = float(f.readline())
                break

        #No save_on_creation -TL
        return cls(
            directory=simulation_folder, request=request,
            recoil_elements=list(recoil_elements), name_prefix=name_prefix,
            name=name, optimization_recoils=optimized_recoils,
            optimized_fluence=optimized_fluence, **kwargs, **mcsimu,
            simulation = simulation, save_on_creation = False)

    def get_full_name(self):
        """Returns the full name of the ElementSimulation object.
        """
        if self.name_prefix:
            return f"{self.name_prefix}-{self.name}"
        return self.name

    def get_json_content(self) -> Dict:
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
            "main_recoil": self.get_main_recoil().get_name()
        }

    def get_new_json_content(self) -> Dict:
        """Returns a dictionary that represents the values of the
        ElementSimulation in json format.
        """
        timestamp = time.time()

        self.optimization_results_to_file()

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
            "main_recoil": self.get_main_recoil().get_name(),
            "recoils": [
                    recoil.get_json_content()
                for recoil in self.recoil_elements
            ]
        }


    def get_default_file_path(self) -> Path:
        """Returns a default file path that to_file uses.
        """
        return Path(self.directory, f"{self.get_full_name()}.mcsimu")

    def to_file(self, file_path: Optional[Path] = None,
                save_optim_results=False):
        """Save mcsimu settings to file.
        Args:
            file_path: File in which the mcsimu settings will be saved.
            save_optim_results: whether to save optimization results or not (
                nothing is saved if no results exist)
        """

        config_manager = ConfigManager()
        config_manager.save()

        # # TODO call profile_to_file and recoil.to_file in here instead of having
        # #   the caller call each function separately
        # if file_path is None:
        #     file_path = self.get_default_file_path()
        if save_optim_results:
            self.optimization_results_to_file()
        # with file_path.open("w") as file:
        #     json.dump(self.get_json_content(), file, indent=4)

    def profile_to_file(self, file_path: Path):
        """Save profile settings (only channel width) to file.
        Args:
            file_path: File in which the channel width will be saved.
        """
        # Read .profile to obj to update only channel width
        time_stamp = time.time()
        try:
            with file_path.open("r") as file:
                obj_profile = json.load(file)

            obj_profile["modification_time"] = time.strftime(
                "%c %z %Z", time.localtime(time_stamp))
            obj_profile["modification_time_unix"] = time_stamp
            obj_profile["energy_spectra"]["channel_width"] = self.channel_width
        except (OSError, json.JSONDecodeError):
            obj_profile = {
                "energy_spectra": {},
                "modification_time": time.strftime(
                    "%c %z %Z", time.localtime(time_stamp)),
                "modification_time_unix": time_stamp}
            obj_profile["energy_spectra"]["channel_width"] = self.channel_width

        with file_path.open("w") as file:
            json.dump(obj_profile, file, indent=4)

    def start(self, number_of_processes: int, start_value=None,
              use_old_erd_files=True, optimization_type=None,
              ion_division=IonDivision.NONE,
              ct: Optional[CancellationToken] = None,
              start_interval=1, status_check_interval=1,
              **kwargs) -> Optional[rx.Observable]:
        """
        Start the simulation.
        Args:
            number_of_processes: How many processes are started.
            start_value: Which is the first seed.
            use_old_erd_files: whether the simulation continues using old erd
                files or not
            optimization_type: either recoil, fluence or None
            ion_division: ion division mode that determines how ions are
                divided per process
            ct: CancellationToken that can be used to stop
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
            self._erd_filehandler.clear()
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
            recoil = self.get_main_recoil()

        if number_of_processes < 1:
            number_of_processes = 1

        # Update ion counts depending on the ion_division mode
        presim_ions, sim_ions = ion_division.get_ion_counts(
            settings["number_of_ions_in_presimu"], settings["number_of_ions"],
            number_of_processes)

        settings.update({
            "number_of_ions_in_presimu": presim_ions,
            "number_of_ions": sim_ions,
            "beam": run.beam,
            "target": self.simulation.target,
            "detector": detector,
            "recoil_element": recoil,
            "sim_dir": self.directory
        })

        if ct is None:
            ct = CancellationToken()

        self._cts.add(ct)

        # New MCERD process is started every second until number of
        # processes is reached or cancellation has been requested.
        # Seed is incremented for each new process.
        return rx.timer(0, start_interval).pipe(
            ops.take_while(
                lambda _: not ct.is_cancellation_requested()),
            ops.take(number_of_processes),
            ops.scan(lambda acc, _: acc + 1, seed=seed_number - 1),
            ops.map(lambda next_seed: self._start(
                recoil, next_seed, optimization_type, dict(settings),
                ct, **kwargs)),
            ops.flat_map(lambda x: x),
            ops.scan(lambda acc, x: {
                **x,
                ElementSimulation.TOTAL: number_of_processes,
                ElementSimulation.FINISHED:
                    acc[ElementSimulation.FINISHED] + int(
                        not x[MCERD.IS_RUNNING])
            }, seed={ElementSimulation.FINISHED: 0}),
            ops.combine_latest(rx.timer(0, status_check_interval).pipe(
                ops.map(lambda x: self.get_current_status()),
                ops.take_while(
                    lambda _: not ct.is_cancellation_requested(),
                    inclusive=True),
            )),
            ops.starmap(lambda x, y: {**x, **y}),
            ops.take_while(
                lambda x: x[ElementSimulation.FINISHED] < x[
                    ElementSimulation.TOTAL] and
                not x[MCERD.MSG] in (MCERD.SIM_STOPPED, MCERD.SIM_TIMEOUT),
                inclusive=True),
            ops.do_action(
                on_error=lambda _: self._clean_up(ct),
                on_completed=lambda: self._clean_up(ct)
            )
        )

    def _start(self, recoil, seed_number, optimization_type, settings, ct,
               **kwargs) -> rx.Observable:
        """Inner method that creates an MCERD instance and runs it.
        Returns an observable stream of MCERD output.
        """
        new_erd_file = fp.get_erd_file_name(
            recoil, seed_number, optim_mode=optimization_type)

        new_erd_file = Path(self.directory, new_erd_file)
        try:
            # remove file if it exists previously
            new_erd_file.unlink()
        except OSError:
            pass

        if optimization_type is None:
            self._erd_filehandler.add_active_file(new_erd_file)

        mcerd = MCERD(
            seed_number, settings, self.get_full_name(),
            optimize_fluence=optimization_type is OptimizationType.FLUENCE)

        return mcerd.run(ct=ct, **kwargs)

    def _set_flags(self, b: bool, optim_mode=None):
        """Sets the boolean flags that indicate the state of
        simulation accordingly.
        """
        # TODO could just replace the boolean flags with the Event
        if b:
            self._running_event.clear()
        else:
            self._running_event.set()
        self._simulation_running = b and optim_mode is None
        self._optimization_running = b and optim_mode is not None

    def _get_setting_value(self, attr) -> Any:
        """Overrides base class function."""
        value = getattr(self, _SETTINGS_MAP[attr])
        if isinstance(value, AdjustableSettings):
            return value.get_settings()
        return value

    def _set_setting_value(self, attr, value) -> None:
        """Overrides base class function."""
        attr_val = getattr(self, _SETTINGS_MAP[attr])
        if isinstance(attr_val, AdjustableSettings):
            attr_val.set_settings(**value)
        else:
            setattr(self, _SETTINGS_MAP[attr], value)

    def _get_attrs(self) -> Set[str]:
        """Returns MCERD names of attributes that can be adjusted."""
        return {
            attr for attr in _SETTINGS_MAP.keys()
        }

    def get_atom_count(self) -> int:
        """Returns the total number of observed atoms.
        """
        return self._erd_filehandler.get_total_atom_count()

    def get_current_status(self) -> Dict:
        """Returns the number of atoms counted, number of running processes and
        the state of simulation.
        Return:
            dictionary
        """
        atom_count = self.get_atom_count()

        if self.is_simulation_running():
            state = SimulationState.RUNNING
        elif self.is_simulation_finished():
            state = SimulationState.DONE
        else:
            state = SimulationState.NOTRUN

        # Return status as a dict
        return {
            ElementSimulation.ATOMS: atom_count,
            ElementSimulation.STATE: state,
            ElementSimulation.OPTIMIZING: self.is_optimization_running()
        }

    def get_main_recoil(self) -> Optional[RecoilElement]:
        """Returns the main recoil of this ElementSimulation.
        """
        if self.recoil_elements:
            return self.recoil_elements[0]
        else:
            return None

    def has_element(self, element: Element) -> bool:
        """Checks whether the this ELementSimulation's collection of
        RecoilElements contains the given element.
        """
        # TODO can't ElementSimulation only have one type of element anyway?
        t = element.symbol, element.isotope, element.RRectype
        return t in ((r.element.symbol, r.element.isotope, r.element.RRectype)
                     for r in self.recoil_elements)

    def is_simulation_running(self) -> bool:
        """Whether simulation is currently running and optimization is not
        running.
        """
        return self._simulation_running

    def is_simulation_finished(self) -> bool:
        """Whether simulation is finished.
        """
        return not self.is_simulation_running() and \
            self._erd_filehandler.results_exist()

    def is_optimization_running(self) -> bool:
        """Whether optimization is running.
        """
        return self._optimization_running

    def is_optimization_finished(self) -> bool:
        """Whether optimization has finished.
        """
        return not self.is_optimization_running() and (any(
            self.optimization_recoils) or self.optimized_fluence is not None)

    def get_max_seed(self) -> int:
        """Returns maximum seed that has been used in simulations.
        Return:
            maximum seed value used in simulation processes
        """
        return self._erd_filehandler.get_max_seed()

    def get_erd_files(self) -> List[Path]:
        """Returns both active and already simulated ERD files.
        """
        return list(f for f, _, _ in self._erd_filehandler)

    def _clean_up(self, ct: CancellationToken):
        """Performs clean up after all of the simulation process have ended.
        """
        self._set_flags(False)
        self._erd_filehandler.update()
        self._cts.remove(ct)
        if self.simulation is not None:
            atom_count = self._erd_filehandler.get_total_atom_count()
            msg = f"Simulation finished. Element " \
                  f"{self.get_main_recoil().get_full_name()}, " \
                  f"observed atoms: {atom_count}."
            self.simulation.log(msg)

        self.on_completed(self.get_current_status())

    def stop(self) -> Event:
        """Stops all running simulation processes for this ElementSimulation.
        Returns an Event that can be waited for until all processes have
        stopped.
        """
        cts = list(self._cts)
        for ct in cts:
            ct.request_cancellation()

        return self._running_event

    def calculate_espe(
            self,
            recoil_element: RecoilElement,
            verbose: bool = False,
            ch: Optional[float] = None,
            fluence: Optional[float] = None,
            optimization_type: Optional[OptimizationType] = None,
            write_to_file: bool = True,
            remove_recoil_file: bool = False) -> Tuple[List, Optional[Path]]:
        """Calculate the energy spectrum from the MCERD result file.

        Args:
            recoil_element: Recoil element.
            verbose: In terminal (disabled by default).
            ch: Channel width to use.
            fluence: Fluence to use.
            optimization_type: Either recoil, fluence or None
            write_to_file: Whether spectrum is written to file
            remove_recoil_file: Whether to remove temporary .recoil file
                after getting the energy spectrum.

        Return:
            tuple consisting of spectrum data and espe file
        """
        suffix = self.simulation_type.get_recoil_suffix()

        if optimization_type is OptimizationType.RECOIL:
            recoil = self.optimization_recoils[0]
        else:
            recoil = self.get_main_recoil()

        if optimization_type is OptimizationType.FLUENCE:
            output_file = f"{recoil_element.prefix}-optfl.simu"
            recoil_file = f"{recoil_element.prefix}-optfl.{suffix}"
        else:
            output_file = f"{recoil_element.get_full_name()}.simu"
            recoil_file = f"{recoil_element.get_full_name()}.{suffix}"

        erd_file = Path(
            self.directory,
            fp.get_erd_file_name(recoil, "*", optim_mode=optimization_type))

        if write_to_file:
            output_file = Path(self.directory, output_file)
        else:
            output_file = None
        recoil_file = Path(self.directory, recoil_file)

        with recoil_file.open("w") as rec_file:
            rec_file.write("\n".join(recoil_element.get_mcerd_params()))

        ch = ch or self.channel_width

        _, run, detector = self.get_mcerd_params()

        if fluence is not None:
            used_fluence = fluence
        else:
            used_fluence = run.fluence

        spectrum = GetEspe.calculate_simulated_spectrum(
            beam=run.beam,
            detector=detector,
            target=self.simulation.target,
            ch=ch,
            reference_density=self.simulation.target.reference_density.get_value(),
            fluence=used_fluence,
            erd_file=erd_file,
            output_file=output_file,
            recoil_file=recoil_file,
            verbose=verbose
        )

        if remove_recoil_file:
            recoil_file.unlink()

        # TODO returning espe_file is a bit pointless if write_to_file is
        #   False
        return spectrum, output_file

    def get_mcerd_params(self) -> Tuple[Dict, Run, Detector]:
        """Returns the parameters for MCERD simulations.
        """
        settings = self.get_settings()
        run = self.simulation.run
        detector = self.simulation.detector

        return settings, run, detector

    def clone_request_settings(self) -> None:
        """Clone settings from request."""
        settings = self.request.default_element_simulation.get_settings()
        self.set_settings(**settings)

        self.channel_width = \
            self.request.default_element_simulation.channel_width

    def optimization_results_to_file(self, cut_file: Optional[Path] = None):
        """Saves optimizations results to file if they exist.
        """
        if self.optimization_recoils:
            # Save recoils
            for recoil in self.optimization_recoils:
                recoil.to_file(self.directory)
            if cut_file is not None:
                save_file_name = f"{self.name_prefix}-opt.measured"
                with (self.directory / save_file_name).open("w") as f:
                    f.write(cut_file.stem)
        if self.optimized_fluence:
            # save found fluence value
            file_name = f"{self.name_prefix}-optfl.result"
            with (self.directory / file_name).open("w") as f:
                f.write(str(self.optimized_fluence))

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
        # TODO check for file name rather than startswith

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

        gf.remove_matching_files(
            self.directory,
            exts={".recoil", ".erd", ".simu", ".scatter", ".rec"},
            filter_func=filter_func)

        self.optimization_recoils = []

    def delete_simulation_results(self):
        """Deletes all simulation results for this ElementSimulation.
        """
        prefixes = {recoil.get_full_name() for recoil in self.recoil_elements}

        def filter_func(file):
            # TODO check for file name rather than startswith
            return any(file.startswith(pre) for pre in prefixes) and \
                "opt" not in file

        gf.remove_matching_files(
            self.directory,
            exts={".recoil", ".erd", ".simu", ".scatter", ".prof"},
            filter_func=filter_func)

    def delete_all_files(self):
        """Stops simulation and removes all simulation files.
        """
        self.reset(remove_result_files=True)
        # FIXME also removes files that have the same prefix
        gf.remove_matching_files(
            self.directory, exts={".mcsimu", ".rec", ".profile", ".sct", ".prof"},
            filter_func=lambda fn: fn.startswith(self.name_prefix)
        )

    def reset(self, remove_result_files=True):
        """Function that resets the state of ElementSimulation.
        Args:
            remove_result_files: whether simulation result files are also
                removed
        """
        self.stop().wait(1)

        if remove_result_files:
            self.delete_simulation_results()
            self.delete_optimization_results()
            self._erd_filehandler.clear()
        self.unlock_edit()

        self.on_completed(self.get_current_status())


class ERDFileHandler:
    """Helper class to handle ERD files that belong to the ElementSimulation
    Handles counting atoms and getting seeds.
    """
    def __init__(self, files: Iterable[Union[Path, str]],
                 recoil_element: RecoilElement):
        """Initializes a new ERDFileHandler that tracks old and new .erd files
        belonging to the given recoil element
        Args:
            files: list of absolute paths to .erd files that contain data
                that has already been simulated
            recoil_element: recoil element for which the .erd files belong to.
        """
        self.recoil_element = recoil_element
        self.__active_files = {}

        self.__old_files = {
            file: seed
            for file, seed in fp.validate_erd_file_names(
                files, self.recoil_element)
        }

    @classmethod
    def from_directory(cls, directory: Path, recoil_element: RecoilElement) \
            -> "ERDFileHandler":
        """Initializes a new ERDFileHandler by reading ERD files
        from a directory.
        Args:
            directory: path to a directory
            recoil_element: recoil element for which the ERD files belong
                            to
        Return:
            new ERDFileHandler.
        """
        try:
            full_paths = gf.find_files_by_extension(directory, ".erd")[".erd"]
        except OSError:
            full_paths = []
        return cls(full_paths, recoil_element)

    def __iter__(self):
        """Iterates over all of the ERD files, both active and old ones.
        Yield:
            tuple consisting of absolute file path, seed value and boolean
            that tells if the ERD file is used in a running simulation or
            not.
        """
        for file, seed in itertools.chain(
                self.__active_files.items(), self.__old_files.items()):
            yield file, seed, file in self.__active_files

    def __len__(self):
        """Returns the number of active files and already simulated files.
        """
        return len(self.__active_files) + len(self.__old_files)

    def add_active_file(self, erd_file: Union[Path, str]):
        """Adds an active ERD file to the handler.
        File must not already exist in active or old files, otherwise
        ValueError is raised.
        Args:
            erd_file: file name of an .erd file
        """
        erd_file = Path(erd_file)
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

    def get_max_seed(self) -> Optional[int]:
        """Returns the largest seed in current .erd file collection or None
        if no .erd files are stored in the handler.
        """
        return max((seed for _, seed, _ in self), default=None)

    def get_active_atom_count(self) -> int:
        """Returns the number of atoms in currently active .erd files.
        """
        return sum(self.__get_atom_count(file)
                   for file in self.__active_files)

    def get_old_atom_count(self) -> int:
        """Returns the number of atoms in already simulated .erd files.
        """
        return sum(self.__get_atom_count_cached(file)
                   for file in self.__old_files)

    def get_total_atom_count(self) -> int:
        """Returns the total number of observed atoms.
        """
        return self.get_active_atom_count() + self.get_old_atom_count()

    @staticmethod
    def __get_atom_count(erd_file: Path):
        """Returns the number of counted atoms in given ERD file.
        """
        return gf.count_lines_in_file(erd_file, check_file_exists=True)

    @functools.lru_cache(128)
    def __get_atom_count_cached(self, erd_file: Path):
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

    def results_exist(self) -> bool:
        """Returns True if ERD files exist.
        """
        return any(self.__old_files) or any(self.__active_files)

    @classmethod
    def from_json(cls, mcsimu,
                  simulation: Optional["Simulation"] = None,
                  save_on_creation=True) -> "ElementSimulation":
        """Initialize ElementSimulation from JSON files.
        Args:
            request: Request that ElementSimulation belongs to.
            prefix: String that is used to prefix ".rec" files of this
                ElementSimulation.
            simulation_folder: A file path to simulation folder that contains
                files ending with ".rec".
            mcsimu_file: A file path to JSON file containing the
                simulation parameters.
            profile_file: A file path to JSON file containing the
                channel width.
            simulation: parent Simulation object of this ElementSimulation
            save_on_creation: whether ElementSimulation object is saved after
                it has been initialized
        Return:
            ElementSimulation object
        """
        # Pop the recoil name so it can be converted to a RecoilElement
        main_recoil_name = mcsimu.pop("main_recoil")

        # Convert modification_time and use_default_settings to correct
        # types
        mcsimu["modification_time"] = mcsimu.pop("modification_time_unix")
        mcsimu["use_default_settings"] = \
            mcsimu["use_default_settings"] == "True"
        mcsimu["simulation_type"] = SimulationType.fromStr(
            mcsimu["simulation_type"])
        mcsimu["simulation_mode"] = SimulationMode(
            mcsimu["simulation_mode"].lower())

        full_name = mcsimu.pop("name")
        try:
            name_prefix, name = full_name.split("-")
        except ValueError:
            name = full_name
            name_prefix = ""

        # Read channel width from .profile file.
        # TODO: element simulations use a simplified .profile format.
        #       Because of this, they cannot be loaded with
        #       Profile.from_file. Unify them?
        try:
            with profile_file.open("r") as prof_file:
                prof = json.load(prof_file)
            kwargs = {
                "channel_width": prof["energy_spectra"]["channel_width"]
            }
        except (json.JSONDecodeError, OSError, KeyError, AttributeError) as e:
            msg = f"Failed to read data from element simulation .profile " \
                  f"file {profile_file}: {e}."
            request.log_error(msg)
            kwargs = {}

        rec_type = mcsimu["simulation_type"].get_recoil_type()

        main_recoil = None
        recoil_elements = deque()
        optimized_recoils_dict = {}

        return cls(
            directory=simulation_folder, request=request,
            recoil_elements=list(recoil_elements), name_prefix=name_prefix,
            name=name, optimization_recoils=optimized_recoils,
            optimized_fluence=optimized_fluence, **kwargs, **mcsimu,
            simulation = simulation, save_on_creation = save_on_creation)

    @classmethod
    def from_json_only(cls, mcsimu,
                  simulation: Optional["Simulation"] = None,
                  save_on_creation=True) -> "ElementSimulation":
        """Initialize ElementSimulation from JSON files.
        Args:
            request: Request that ElementSimulation belongs to.
            prefix: String that is used to prefix ".rec" files of this
                ElementSimulation.
            simulation_folder: A file path to simulation folder that contains
                files ending with ".rec".
            mcsimu_file: A file path to JSON file containing the
                simulation parameters.
            profile_file: A file path to JSON file containing the
                channel width.
            simulation: parent Simulation object of this ElementSimulation
            save_on_creation: whether ElementSimulation object is saved after
                it has been initialized
        Return:
            ElementSimulation object
        """
        # Pop the recoil name so it can be converted to a RecoilElement
        main_recoil_name = mcsimu.pop("main_recoil")

        # Convert modification_time and use_default_settings to correct
        # types
        mcsimu["modification_time"] = mcsimu.pop("modification_time_unix")
        mcsimu["use_default_settings"] = \
            mcsimu["use_default_settings"] == "True"
        mcsimu["simulation_type"] = SimulationType.fromStr(
            mcsimu["simulation_type"])
        mcsimu["simulation_mode"] = SimulationMode(
            mcsimu["simulation_mode"].lower())

        full_name = mcsimu.pop("name")
        try:
            name_prefix, name = full_name.split("-")
        except ValueError:
            name = full_name
            name_prefix = ""

        # Read channel width from .profile file.
        # TODO: element simulations use a simplified .profile format.
        #       Because of this, they cannot be loaded with
        #       Profile.from_file. Unify them?
        try:
            with profile_file.open("r") as prof_file:
                prof = json.load(prof_file)
            kwargs = {
                "channel_width": prof["energy_spectra"]["channel_width"]
            }
        except (json.JSONDecodeError, OSError, KeyError, AttributeError) as e:
            msg = f"Failed to read data from element simulation .profile " \
                  f"file {profile_file}: {e}."
            request.log_error(msg)
            kwargs = {}

        rec_type = mcsimu["simulation_type"].get_recoil_type()

        main_recoil = None
        recoil_elements = (recoil_element.from_json(r, **kwargs) for r in mcsimu["recoils"])
        optimized_recoils_dict = {}

        return cls(
            directory=simulation_folder, request=request,
            recoil_elements=list(recoil_elements), name_prefix=name_prefix,
            name=name, optimization_recoils=optimized_recoils,
            optimized_fluence=optimized_fluence, **kwargs, **mcsimu,
            simulation = simulation, save_on_creation = save_on_creation)
