# coding=utf-8
"""
Created on 26.2.2018
Updated on 29.1.2020

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2018 Severi Jääskeläinen, Samuel Kaiponen, Heta Rekilä and
Sinikka Siironen, 2020 Juhani Sundell

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
             "\n Sinikka Siironen \n Juhani Sundell \n Tuomas Pitkänen"
__version__ = "2.0"

import json
import time

from collections import namedtuple
from pathlib import Path
from typing import Optional
from typing import List

from . import general_functions as gf

from .recoil_element import RecoilElement
from .element import Element
from .base import ElementSimulationContainer
from .base import Serializable
from .enums import SimulationType
from .detector import Detector
from .element_simulation import ElementSimulation
from .run import Run
from .target import Target
from .ui_log_handlers import SimulationLogger
from .config_manager import ConfigManager


class Simulations:
    """Simulations class handles multiple simulations.
    """

    def __init__(self, request: "Request"):
        """Inits simulations class.
        Args:
            request: Request class object.
        """
        self.request = request
        self.simulations = {}
        self.sim_config = ConfigManager()

    def is_empty(self) -> bool:
        """Check if there are any simulations.

        Return:
            Returns True if there are no simulations currently in the
            simulations object.
        """
        return len(self.simulations) == 0

    def get_key_value(self, key: int) -> Optional["Simulation"]:
        """
        Args:
            key: Key of simulation dictionary.

        Return:
            Returns value corresponding to key.
        """
        if key not in self.simulations:
            return None
        return self.simulations[key]

    def add_simulation_file(self, sample: "Sample", simulation_file: Path,
                            tab_id: int) -> Optional["Simulation"]:
        """Add a new file to simulations.

        Args:
            sample: The sample under which the simulation is put.
            simulation_file: Path of the .simulation file.
            tab_id: Integer representing identifier for simulation's tab.

        Return:
            Returns new simulation or None if it wasn't added
        """
        simulation = None

        simulation_folder = simulation_file.parent
        directory_prefix = Simulation.DIRECTORY_PREFIX

        # Create simulation from file
        if simulation_file.exists():
            (target_file, mesu_file,
             elem_sim_files, profile_files,
             detector_file) = Simulation.find_simulation_files(
                simulation_folder)

            if target_file is not None:
                target = Target.from_file(
                    target_file, sample.request)
            else:
                target = None

            if detector_file is not None:
                detector = Detector.from_file(
                    detector_file, sample.request, save_on_creation=False)
                detector.update_directories(detector_file.parent)
            else:
                detector = None

            simulation = Simulation.from_file(
                sample.request, simulation_file, measurement_file=mesu_file,
                sample=sample, target=target, detector=detector)

            serial_number = int(
                simulation_folder.name[
                    len(directory_prefix):len(directory_prefix) + 2])
            simulation.serial_number = serial_number
            simulation.tab_id = tab_id

            for mcsimu_file in elem_sim_files:
                element_str_with_name = mcsimu_file.stem

                prefix, name = element_str_with_name.split("-")

                profile_file = next(
                    p for p in profile_files if p.name.startswith(prefix)
                )

                if profile_file is not None:
                    # Create ElementSimulation from files
                    element_simulation = ElementSimulation.from_file(
                        self.request, prefix, simulation_folder,
                        mcsimu_file, profile_file, simulation=simulation
                    )
                    # TODO need to check that element simulation can be added
                    simulation.element_simulations.append(
                        element_simulation)

        # Create a new simulation
        else:
            # Not stripping the extension
            simulation_name = simulation_file.stem
            try:
                keys = sample.simulations.simulations.keys()
                for key in keys:
                    if sample.simulations.simulations[key].directory == \
                            simulation_name:
                        return simulation  # simulation = None
                simulation = Simulation(
                    simulation_file, self.request, name=simulation_name,
                    tab_id=tab_id, sample=sample)
                serial_number = int(simulation_folder.name[len(
                    directory_prefix):len(directory_prefix) + 2])
                simulation.serial_number = serial_number
                self.request.samples.simulations.simulations[tab_id] = \
                    simulation
            except Exception as e:
                log = f"Something went wrong while adding a new simulation: {e}"
                self.request.log_error(log)
        if simulation is not None:
            sample.simulations.simulations[tab_id] = simulation
        self.sim_config.set_simulation(simulation)
        self.sim_config.read_simulation()
        self.sim_config.save()
        return simulation

    def remove_obj(self, removed_obj: "Simulation"):
        """Removes given simulation.

        Args:
            removed_obj: Simulation to remove.
        """
        self.simulations.pop(removed_obj.tab_id)

    def remove_by_tab_id(self, tab_id: int):
        """Removes simulation from simulations by tab id
        Args:
            tab_id: Integer representing tab identifier.
        """

        def remove_key(d, key):
            r = dict(d)
            del r[key]
            return r

        self.simulations = remove_key(self.simulations, tab_id)

    def add_simulation_json(self, sample: "Sample", simulation_json,
                            tab_id: int) -> Optional["Simulation"]:
        """Add a new file to simulations.

        Args:
            sample: The sample under which the simulation is put.
            simulation_file: Path of the .simulation file.
            tab_id: Integer representing identifier for simulation's tab.

        Return:
            Returns new simulation or None if it wasn't added
        """
        simulation = None

        simulation_folder = simulation_json.parent
        directory_prefix = Simulation.DIRECTORY_PREFIX

        with simulation_json.open("r") as file:
            simu_obj = json.load(file)

        self.sim_config.set_config_file(simulation_json)

        # Create simulation from file
        if simulation_json:
            (target_file, mesu_file,
             elem_sim_files, profile_files,
             detector_file) = Simulation.find_simulation_files(
                simulation_folder)

            if target_file is not None:
                target = Target.from_file(
                    target_file, sample.request)
            else:
                target = None

            if detector_file is not None:
                detector = Detector.from_file(
                    detector_file, sample.request, save_on_creation=False)
                detector.update_directories(detector_file.parent)
            else:
                detector = None

            simulation = Simulation.from_json(
                sample.request, simulation_json, simu_obj, measurement_file=mesu_file,
                sample=sample, target=target, detector=detector)

            serial_number = int(
                simulation_folder.name[
                    len(directory_prefix):len(directory_prefix) + 2])
            simulation.serial_number = serial_number
            simulation.tab_id = tab_id

            for mcsimu in simu_obj['element_simulations']:
                element_str_with_name = mcsimu['name']

                prefix, name = element_str_with_name.split("-")

                try:
                    profile_file = next(
                        p for p in profile_files if p.name.startswith(prefix)
                    )
                except StopIteration:
                    profile_file = None

                if profile_file is not None:
                    # Create ElementSimulation from files
                    element_simulation = ElementSimulation.from_json(
                        self.request, prefix, simulation_folder,
                        mcsimu, profile_file, simulation=simulation
                    )
                    # TODO need to check that element simulation can be added
                    simulation.element_simulations.append(
                        element_simulation)

        # Create a new simulation
        else:
            # Not stripping the extension
            simulation_name = simulation_file.stem
            try:
                keys = sample.simulations.simulations.keys()
                for key in keys:
                    if sample.simulations.simulations[key].directory == \
                            simulation_name:
                        return simulation  # simulation = None
                simulation = Simulation(
                    simulation_file, self.request, name=simulation_name,
                    tab_id=tab_id, sample=sample)
                serial_number = int(simulation_folder.name[len(
                    directory_prefix):len(directory_prefix) + 2])
                simulation.serial_number = serial_number
                self.request.samples.simulations.simulations[tab_id] = \
                    simulation
            except Exception as e:
                log = f"Something went wrong while adding a new simulation: {e}"
                self.request.log_error(log)
        if simulation is not None:
            sample.simulations.simulations[tab_id] = simulation
        #self.sim_config.read_simulation(simulation)
        #self.sim_config.save()
        self.sim_config.set_simulation(simulation)
        return simulation



class Simulation(SimulationLogger, ElementSimulationContainer, Serializable):
    """
    A Simulation class that handles information about one Simulation.
    """
    __slots__ = "path", "request", "simulation_file", "name", "tab_id", \
                "description", "modification_time", "run", "detector", \
                "target", "element_simulations", \
                "serial_number", "directory", "measurement_setting_file_name", \
                "measurement_setting_file_description", \
                "sample", "use_request_settings"

    DIRECTORY_PREFIX = "MC_simulation_"

    def __init__(self, path: Path, request, name="Default",
                 description="",
                 modification_time=None, tab_id=-1,
                 run: Optional[Run] = None,
                 detector: Optional[Detector] = None,
                 target: Optional[Target] = None,
                 measurement_setting_file_name="",
                 measurement_setting_file_description="", sample=None,
                 use_request_settings=True,
                 save_on_creation=True, enable_logging=True,
                 element_simulations = None):
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
            enable_logging: whether logging is enabled
        """
        # Run the base class initializer to establish logging
        SimulationLogger.__init__(
            self, name, enable_logging=enable_logging, parent=request)

        self.tab_id = tab_id
        self.path = Path(path)
        self.directory, self.simulation_file = self.path.parent, self.path.name
        self.request = request
        self.sample = sample

        self.name = name
        self.description = description
        if not modification_time:
            self.modification_time = time.time()
        else:
            self.modification_time = modification_time

        if measurement_setting_file_name:
            self.measurement_setting_file_name = measurement_setting_file_name
        else:
            self.measurement_setting_file_name = name
        self.measurement_setting_file_description = \
            measurement_setting_file_description

        self.element_simulations: List[ElementSimulation] = []

        self.use_request_settings = use_request_settings

        if run is None:
            self.run = self.request.copy_default_run()
        else:
            self.run = run

        if detector is None:
            self.detector = self.request.copy_default_detector(
                self.directory, save_on_creation=False)
        else:
            self.detector = detector

        if target is None:
            self.target = self.request.copy_default_target()
        else:
            self.target = target

        self.serial_number = 0

        if save_on_creation:
            self.create_folder_structure()
            self.to_file(self.path)

    def create_folder_structure(self):
        """Create folder structure for simulation.
        """
        if not self.directory.exists():
            self.directory.mkdir(exist_ok=True)
            self.request.log(f"Created a directory {self.directory}.")
        self.set_up_log_files(self.directory)

    def get_measurement_file(self) -> Path:
        """Returns the path to .measurement file that contains the settings
        of this Simulation.
        """
        # TODO this method should be defined in a common base class
        return Path(self.path.parent,
                    f"{self.measurement_setting_file_name}.measurement")

    def rename(self, new_name: str):
        """Renames Simulation with the given name and updates folders and
        saved files.
        """
        # TODO should .measurement file also be renamed?
        old_file_name = self.simulation_file
        gf.rename_entity(self, new_name)
        # self.name is updated during gf.rename_entity, so no need to
        # update simulation file here
        # TODO add function get_simulation_file to dynamically
        #   get the right file name
        # TODO too confusing to have separate attributes for path
        #   and simulation_file
        old_file_path = self.directory / old_file_name
        try:
            gf.rename_file(old_file_path, self.simulation_file)
            self.to_file()
        except OSError as e:
            e.args = f"Failed to rename .simulation file: {e}",
            raise

    def rename_simulation_file(self):
        """Renames the simulation file with self.simulation_file.
        """
        files = gf.find_files_by_extension(self.directory, ".simulation")
        for file in files[".simulation"]:
            gf.rename_file(Path(self.directory, file), self.simulation_file)
            break

    @staticmethod
    def find_simulation_files(simulation_dir: Path) -> namedtuple:
        """Returns a tuple of all simulation files.
        """
        res = gf.find_files_by_extension(
            simulation_dir, ".mcsimu", ".target", ".measurement", ".profile")
        try:
            det_res = gf.find_files_by_extension(
                simulation_dir / "Detector", ".detector")
        except OSError:
            det_res = {".detector": []}

        if res[".target"]:
            target_file = res[".target"][0]
        else:
            target_file = None
        if res[".measurement"]:
            mesu_file = res[".measurement"][0]
        else:
            mesu_file = None

        if det_res[".detector"]:
            detector_file = det_res[".detector"][0]
        else:
            detector_file = None

        sim_files = namedtuple(
            "Simulation_files",
            ("target", "measurement", "element_simulations", "profiles",
             "detector"))
        return sim_files(
            target_file, mesu_file, res[".mcsimu"], res[".profile"],
            detector_file)

    def has_element(self, element: Element) -> bool:
        return any((elem_sim.has_element(element)
                   for elem_sim in self.element_simulations))

    def can_add_recoil(self, recoil_element: RecoilElement) -> bool:
        """Checks whether RecoilElement can be added.
        """
        # Note: currently Potku cannot properly differentiate recoils with exact
        # same Element that are used within the same simulation, so return
        # False if an Element already exists.
        return not self.has_element(recoil_element.element)

    def add_element_simulation(self, recoil_element: RecoilElement,
                               save_on_creation=True) -> ElementSimulation:
        """Adds ElementSimulation to Simulation. Raises ValueError if
        RecoilElement cannot be added.

        Args:
            recoil_element: RecoilElement that is simulated.
            save_on_creation: whether ElementSimulation is saved upon
                initialization.
        """
        if not self.can_add_recoil(recoil_element):
            raise ValueError("Cannot add RecoilElement to Simulation")
        element_str = recoil_element.element.get_prefix()
        name = self.request.default_element_simulation.name

        use_default_settings = True
        request_simulation_type = self.request.default_element_simulation.simulation_type
        recoil_simulation_type = SimulationType.fromStr(recoil_element.type)
        if request_simulation_type is not recoil_simulation_type:
            use_default_settings = False

        element_simulation = ElementSimulation(
            directory=self.directory, request=self.request, simulation=self,
            name_prefix=element_str, name=name,
            recoil_elements=[recoil_element], simulation_type=recoil_simulation_type,
            save_on_creation=save_on_creation, use_default_settings=use_default_settings)

        self.element_simulations.append(element_simulation)
        return element_simulation

    @classmethod
    def from_file(cls, request: "Request", simulation_file: Path,
                  measurement_file: Optional[Path] = None,
                  detector=None, target=None, run=None, sample=None,
                  save_on_creation=True, enable_logging=True) -> "Simulation":
        """Initialize Simulation from a JSON file.

        Args:
            request: Request which the Simulation belongs to.
            simulation_file: path to .simulation file
            measurement_file: path to .measurement file
            detector: Detector used by this simulation
            target: Target used by this simulation
            run: Run used by this simulation
            sample: Sample under which this simulation belongs to
            save_on_creation: whether Simulation object is saved to file
                after initialization
            enable_logging: whether logging is enabled
        """
        with simulation_file.open("r") as file:
            simu_obj = json.load(file)

        # Overwrite the human readable time stamp with unix time stamp, as
        # that is what the Simulation object uses internally
        simu_obj["modification_time"] = simu_obj.pop("modification_time_unix")

        if measurement_file is not None:
            run = Run.from_file(measurement_file)
            with measurement_file.open("r") as mesu_f:
                mesu_settings = json.load(mesu_f)

            try:
                general = {
                    "measurement_setting_file_name": mesu_settings["name"],
                    "measurement_setting_file_description": mesu_settings[
                        "description"]
                }
            except KeyError:
                general = {}
        else:
            general = {}

        return cls(
            simulation_file, request, detector=detector, target=target, run=run,
            sample=sample, **simu_obj, save_on_creation=save_on_creation,
            enable_logging=enable_logging, **general)

    def to_file(self, simulation_file: Optional[Path] = None,
                measurement_file: Optional[Path] = None):
        """Save simulation settings to a file.

        Settings will not be saved if self.use_request_settings is True.

        Args:
            simulation_file: path to a .simulation file
            measurement_file: path to a .measurement_file
        """

    #    if simulation_file is None:
    #        simulation_file = self.path
    #
        time_stamp = time.time()
        sim_config = ConfigManager()
        sim_config.set_simulation(self)
        if self.path.name.split('.')[-1] != 'simulation':
            sim_config.set_config_file(self.path)
        sim_config.save()
    #    obj = {
    #        "name": self.name,
    #        "description": self.description,
    #        "modification_time": time.strftime("%c %z %Z", time.localtime(
    #            time_stamp)),
    #        "modification_time_unix": time_stamp,
    #        "use_request_settings": self.use_request_settings
    #    }
    #    with simulation_file.open("w") as file:
    #        json.dump(obj, file, indent=4)
    #
        if not self.use_request_settings:
            # Save measurement settings parameters.
            if measurement_file is None:
                measurement_file = self.get_measurement_file()

            general_obj = {
                "name": self.measurement_setting_file_name,
                "description":
                    self.measurement_setting_file_description,
                "modification_time":
                    time.strftime("%c %z %Z", time.localtime(time_stamp)),
                "modification_time_unix": time_stamp,
            }

            if measurement_file.exists():
                with measurement_file.open("r") as mesu:
                    obj = json.load(mesu)
                obj["general"] = general_obj
            else:
                obj = {
                    "general": general_obj
                }

            # Write measurement settings to file
            with measurement_file.open("w") as file:
                json.dump(obj, file, indent=4)

            # Save Run object to file
            self.run.to_file(measurement_file)
            # Save Detector object to file
            self.detector.to_file(self.detector.path)

            # Save Target object to file
            target_file = Path(self.directory, f"{self.target.name}.target")
            self.target.to_file(target_file)

    def update_directory_references(self, new_dir: Path):
        """Update simulation's directory references.

        Args:
            new_dir: Path to simulation folder with new name.
        """
        self.directory = new_dir
        self.simulation_file = self.name + ".simulation"

        self.path = Path(self.directory, self.simulation_file)
        if self.detector:
            self.detector.update_directory_references(self)

        for elem_sim in self.element_simulations:
            elem_sim.directory = new_dir

        self.set_up_log_files(self.directory)

    def get_running_simulations(self) -> List[ElementSimulation]:
        """Returns a list of currently running simulations.
        """
        return list(
            elem_sim for elem_sim in self.element_simulations
            if elem_sim.is_simulation_running()
        )

    def get_finished_simulations(self) -> List[ElementSimulation]:
        """Returns a list of simulations that are finished.
        """
        return list(
            elem_sim for elem_sim in self.element_simulations
            if elem_sim.is_simulation_finished()
        )

    def get_running_optimizations(self) -> List[ElementSimulation]:
        """Returns a list of simulations currently involved in a running
        optimization.
        """
        return list(
            elem_sim for elem_sim in self.element_simulations
            if elem_sim.is_optimization_running()
        )

    def get_finished_optimizations(self) -> List[ElementSimulation]:
        """Returns a list of simulations that have optimizations results.
        """
        return list(
            elem_sim for elem_sim in self.element_simulations
            if elem_sim.is_optimization_finished()
        )

    def get_recoil_elements(self) -> List[RecoilElement]:
        """Returns a combined list of RecoilElements from all
        ElementSimulations that this Simulation has.
        """
        return [
            recoil for elem_sim in self.element_simulations
            for recoil in elem_sim.recoil_elements
        ]

    def clone_request_settings(self, save_on_creation=False) -> None:
        """Clone settings from request. For target, only target_theta
        is copied.
        """
        self.run = self.request.copy_default_run()
        self.detector = self.request.copy_default_detector(
            self.directory, save_on_creation=save_on_creation)
        # The simulation's layers (main content) are saved in target.
        # Overwriting them with request's values is not acceptable.
        self.target.target_theta = self.request.default_target.target_theta

    def get_json_content(self):
        time_stamp = time.time()
        obj = {
            "name": self.name,
            "description": self.description,
            "modification_time": time.strftime("%c %z %Z", time.localtime(
                time_stamp)),
            "modification_time_unix": time_stamp,
            "use_request_settings": self.use_request_settings,
            "element_simulations": [
                                simulation.get_new_json_content()
                                for simulation in self.element_simulations
            ],
        }
        return obj

    @classmethod
    def from_json(cls, request: "Request", simulation_json_file, simu_obj,
                  measurement_file: Optional[Path] = None,
                  detector=None, target=None, run=None, sample=None,
                  save_on_creation=True, enable_logging=True) -> "Simulation":
        """Initialize Simulation from a JSON.

        Args:
            request: Request which the Simulation belongs to.
            simu_ocj: simulation json
            measurement_file: path to .measurement file
            detector: Detector used by this simulation
            target: Target used by this simulation
            run: Run used by this simulation
            sample: Sample under which this simulation belongs to
            save_on_creation: whether Simulation object is saved to file
                after initialization
            enable_logging: whether logging is enabled
        """

        # Overwrite the human readable time stamp with unix time stamp, as
        # that is what the Simulation object uses internally
        simu_obj["modification_time"] = simu_obj.pop("modification_time_unix")

        if measurement_file is not None:
            run = Run.from_file(measurement_file)
            with measurement_file.open("r") as mesu_f:
                mesu_settings = json.load(mesu_f)

            try:
                general = {
                    "measurement_setting_file_name": mesu_settings["name"],
                    "measurement_setting_file_description": mesu_settings[
                        "description"]
                }
            except KeyError:
                general = {}
        else:
            general = {}

        #not saving on creation -TL
        return cls(
            simulation_json_file, request, detector=detector, target=target, run=run,
            sample=sample, **simu_obj, save_on_creation=False,
            enable_logging=enable_logging, **general)

    @classmethod
    def from_manager(cls, request: "Request", simulation_json_file, simu_obj,
                  measurement_file: Optional[Path] = None,
                  detector=None, target=None, run=None, sample=None,
                  save_on_creation=True, enable_logging=True) -> "Simulation":
        """Initialize Simulation from a JSON.

        Args:
            request: Request which the Simulation belongs to.
            simu_ocj: simulation json
            measurement_file: path to .measurement file
            detector: Detector used by this simulation
            target: Target used by this simulation
            run: Run used by this simulation
            sample: Sample under which this simulation belongs to
            save_on_creation: whether Simulation object is saved to file
                after initialization
            enable_logging: whether logging is enabled
        """

        # Overwrite the human readable time stamp with unix time stamp, as
        # that is what the Simulation object uses internally
        simu_obj["modification_time"] = simu_obj.pop("modification_time_unix")

        if measurement_file is not None:
            run = Run.from_file(measurement_file)
            with measurement_file.open("r") as mesu_f:
                mesu_settings = json.load(mesu_f)

            try:
                general = {
                    "measurement_setting_file_name": mesu_settings["name"],
                    "measurement_setting_file_description": mesu_settings[
                        "description"]
                }
            except KeyError:
                general = {}
        else:
            general = {}

        # not saving on creation -TL
        return cls(
            simulation_json_file, request, detector=detector, target=target, run=run,
            sample=sample, **simu_obj, save_on_creation=False,
            enable_logging=enable_logging, **general)
