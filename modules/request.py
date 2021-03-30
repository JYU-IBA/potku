# coding=utf-8
"""
Created on 11.4.2013
Updated on 23.5.2019

Potku is a graphical user interface for analyzation and 
visualization of measurement data collected from a ToF-ERD 
telescope. For physics calculations Potku uses external 
analyzation components.  
Copyright (C) 2013-2018 Jarkko Aalto, Severi Jääskeläinen, Samuel Kaiponen,
Timo Konu, Samuli Kärkkäinen, Samuli Rahkonen, Miika Raunio, Heta Rekilä and
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
"""

__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen " \
             "\n Samuli Rahkonen \n Miika Raunio \n Severi Jääskeläinen " \
             "\n Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"
__version__ = "2.0"

import configparser
import os
import re
import time

from pathlib import Path
from typing import Tuple, List, Union, Optional, Iterable

from .ui_log_handlers import RequestLogger
from .base import ElementSimulationContainer
from .detector import Detector
from .element import Element
from .element_simulation import ElementSimulation
from .measurement import Measurement
from .profile import Profile
from .run import Run
from .sample import Samples
from .simulation import Simulation
from .target import Target
from .recoil_element import RecoilElement
from .global_settings import GlobalSettings
from .observing import ProgressReporter


class Request(ElementSimulationContainer, RequestLogger):
    """Request class to handle all measurements.
    """

    def __init__(self, directory: Path, name: str,
                 global_settings: GlobalSettings, tabs=None,
                 save_on_creation: bool = True, enable_logging: bool = True):
        """ Initializes Request class.
        
        Args:
            directory: A String representing request directory.
            name: Name of the request.
            global_settings: A GlobalSettings class object (of the program).
            tabs: A dictionary of MeasurementTabWidgets and SimulationTabWidgets
                of the request.
        """
        RequestLogger.__init__(self, enable_logging)
        self.directory = Path(directory).resolve()
        self.default_folder = Path(self.directory, "Default")

        self.request_name = name
        self.global_settings = global_settings
        self.samples = Samples(self)

        self.__tabs = tabs
        self.__master_measurement = None
        self.__non_slaves = []  # List of measurements that aren't slaves,
        # easier.
        # This is used to number all the samples
        # e.g. Sample-01, Sample-02.optional_name,...
        self._running_int = 1  # TODO: Maybe be saved into .request file?

        # Check folder exists and make request file there.
        if save_on_creation:
            self.create_folder_structure()

        # Try reading default objects from Default folder.
        self.default_measurement_file_path = Path(
            self.default_folder, "Default.measurement")

        self.default_detector_folder = Path(self.default_folder, "Detector")

        self.default_run = self._create_default_run()
        self.default_target = self._create_default_target(
            save_on_creation=save_on_creation
        )
        self.default_detector = self._create_default_detector(
            self.default_detector_folder, save_on_creation=save_on_creation
        )
        self.default_profile = self._create_default_profile(
            save_on_creation=save_on_creation)
        self.default_measurement = self._create_default_measurement(
            save_on_creation=save_on_creation,
            detector=self.default_detector,
            target=self.default_target,
            run=self.default_run,
            profile=self.default_profile
        )
        self.default_simulation, self.default_element_simulation = \
            self._create_default_simulation(
                save_on_creation=save_on_creation,
                detector=self.default_detector,
                target=self.default_target,
                run=self.default_run)

        self.set_up_log_files(self.directory)

        # Request file containing necessary information of the request.
        # If it exists, we assume old request is loaded.
        self.__request_information = configparser.ConfigParser()

        # directory name has extra .potku in it, need to remove it for the
        # .request file name
        self.request_file = Path(
            self.directory, f"{self.directory.stem}.request")

        # Defaults
        self.__request_information.add_section("meta")
        self.__request_information.add_section("open_measurements")
        self.__request_information["meta"]["request_name"] = self.request_name
        self.__request_information["meta"]["created"] = \
            time.strftime("%c %z %Z", time.localtime(time.time()))
        self.__request_information["meta"]["master"] = ""
        self.__request_information["meta"]["nonslave"] = ""
        if self.request_file.exists():
            self._load()
        elif save_on_creation:
            self._save()

    def create_folder_structure(self) -> None:
        self.directory.mkdir(exist_ok=True)
        self.default_folder.mkdir(exist_ok=True)

    def to_file(self) -> None:
        self.create_folder_structure()
        self._save()
        self.default_measurement.to_file()
        self.default_simulation.to_file()

    @classmethod
    def from_file(
            cls, file: Path, settings: GlobalSettings,
            tab_widgets=None, enable_logging: bool = True) -> "Request":
        """Returns a new Request from an existing .request file and folder
        structure.

        Args:
            file: path to a .request file
            settings: GlobalSettings object
            tab_widgets: A dictionary of MeasurementTabWidgets and
                SimulationTabWidgets of the request.
            enable_logging: whether logging is enabled or not

        Return:
            Request object
        """
        # TODO better error checking
        file_path = Path(file).resolve()
        if not file_path.exists():
            raise ValueError("Request file does not exist.")
        if not file_path.is_file():
            raise ValueError("Expected file, got a directory")
        if file_path.suffix != ".request":
            raise ValueError("Expected request file")
        return cls(
            file_path.parent, file_path.stem, settings, tab_widgets,
            enable_logging=enable_logging)

    def _create_default_detector(
            self, folder: Path, save_on_creation: bool) -> Detector:
        """Returns default detector.
        """
        detector_path = folder / "Default.detector"
        if detector_path.exists():
            # Read detector from file
            detector = Detector.from_file(
                detector_path, self, save_on_creation=save_on_creation)
        else:
            # Create Detector folder under Default folder
            if save_on_creation:
                self.default_detector_folder.mkdir(exist_ok=True)
            # Create default detector for request
            detector = Detector(
                Path(self.default_detector_folder, "Default.detector"),
                name="Default",
                description="These are default detector settings.",
                save_on_creation=save_on_creation)

        if save_on_creation:
            detector.update_directories(self.default_detector_folder)

            detector.to_file(
                Path(self.default_detector_folder, "Default.detector"))

        return detector

    def _create_default_measurement(
            self, save_on_creation: bool, **kwargs) -> Measurement:
        """Returns default measurement.
        """
        info_path = Path(self.default_folder, "Default.info")
        if info_path.exists():
            # Read measurement from file
            measurement_file = Path(self.default_folder, "Default.measurement")
            measurement = Measurement.from_file(
                info_path, measurement_file, self, **kwargs,
                enable_logging=False)

            # Ensure that use_request_settings flag is False. Otherwise
            # measurement settings would not be saved when calling
            # measurement.to_file (this was change was introduced in commit
            # fc68f07)
            measurement.use_request_settings = False
        else:
            # Create default measurement for request
            measurement = Measurement(
                self, path=info_path, **kwargs,
                description="This is a default measurement.",
                measurement_setting_file_description="These are default "
                                                     "measurement "
                                                     "parameters.",
                use_request_settings=False,
                save_on_creation=save_on_creation,
                enable_logging=False)

        return measurement

    def _create_default_target(self, save_on_creation: bool) -> Target:
        """Returns default target.
        """
        target_path = Path(self.default_folder, "Default.target")
        if target_path.exists():
            # Read target from file
            target = Target.from_file(target_path, self)
        else:
            # Create default target for request
            target = Target(
                description="These are default target parameters.")

        if save_on_creation:
            target.to_file(Path(self.default_folder, target.name + ".target"))

        return target

    def _create_default_run(self) -> Run:
        """Create default run.
        """
        try:
            # Try reading Run parameters from .measurement file.
            return Run.from_file(self.default_measurement_file_path)
        except (KeyError, OSError):
            return Run()

    def _create_default_profile(self, save_on_creation: bool) -> Profile:
        """Returns default profile.
        """
        profile_path = Path(self.default_folder, "Default.profile")
        if profile_path.exists():
            profile = Profile.from_file(profile_path, logger=self)
        else:
            profile = Profile(
                description="These are default profile parameters.")

        if save_on_creation:
            profile.to_file(
                Path(self.default_folder, profile.name + ".profile"))

        return profile

    def _create_default_simulation(
            self,
            save_on_creation: bool,
            target: Optional[Target] = None,
            detector: Optional[Detector] = None,
            run: Optional[Run] = None,
            **kwargs) -> Tuple[Simulation, ElementSimulation]:
        """Create default simulation and ElementSimulation
        """
        simulation_path = Path(self.default_folder, "Default.simulation")
        if simulation_path.exists():
            # Read default simulation from file
            sim = Simulation.from_file(
                self, simulation_path, save_on_creation=save_on_creation,
                target=target, detector=detector, run=run, **kwargs,
                enable_logging=False)
            sim.use_request_settings = False
        else:
            # Create default simulation for request
            sim = Simulation(
                Path(self.default_folder, "Default.simulation"), self,
                save_on_creation=save_on_creation, target=target,
                detector=detector, run=run, **kwargs,
                description="This is a default simulation.",
                measurement_setting_file_description="These are default "
                                                     "simulation "
                                                     "parameters.",
                use_request_settings=False,
                enable_logging=False)

        mcsimu_path = Path(self.default_folder, "Default.mcsimu")
        if mcsimu_path.exists():
            # Read default element simulation from file
            elem_sim = ElementSimulation.from_file(
                self, "4He", self.default_folder, mcsimu_path,
                Path(self.default_folder, "Default.profile"), simulation=sim)
        else:
            # Create default element simulation for request
            elem_sim = ElementSimulation(
                self.default_folder, self,
                [RecoilElement(Element.from_string("4He 3.0"), [],
                               "#0000ff")],
                simulation=sim,
                description="These are default simulation parameters.",
                use_default_settings=False,
                save_on_creation=save_on_creation, **kwargs)
        # TODO need to check that elem sim can be added
        sim.element_simulations.append(elem_sim)
        return sim, elem_sim

    def copy_default_detector(self, root_path: Path,
                              save_on_creation=False) -> Detector:
        """Returns a copy of default detector."""
        detector_path = root_path / "Detector" / "Default.detector"
        detector = Detector(
            detector_path,
            foils=self.default_detector.copy_foils(),
            tof_foils=self.default_detector.copy_tof_foils(),
            detector_theta=self.default_detector.detector_theta,
            save_on_creation=save_on_creation)
        detector_defaults = self.default_detector.get_settings()
        detector.set_settings(**detector_defaults)
        return detector

    def copy_default_profile(self) -> Profile:
        """Returns a copy of default profile."""
        profile = Profile()
        profile_defaults = self.default_profile.get_settings()
        profile.set_settings(**profile_defaults)
        return profile

    def copy_default_run(self) -> Run:
        """Returns a copy of default run."""
        run = Run()
        run_defaults = self.default_run.get_settings()
        # TODO: Is there a better way to create a copy of ion?
        run_defaults["beam"]["ion"] = \
            run_defaults["beam"]["ion"].create_copy()
        run.set_settings(**run_defaults)
        return run

    def copy_default_target(self) -> Target:
        """Returns a copy of default target."""
        target = Target()
        target_defaults = self.default_target.get_settings()
        target_defaults["layers"] = self.default_target.copy_layers()
        target.set_settings(**target_defaults)
        return target

    def exclude_slave(self, measurement: Measurement):
        """ Exclude measurement from slave category under master.
        
        Args:
            measurement: A measurement class object.
        """
        # Check if measurement is already excluded.
        if measurement in self.__non_slaves:
            return
        self.__non_slaves.append(measurement)
        paths = [m.path for m in self.__non_slaves]
        self.__request_information["meta"]["nonslave"] = "|".join(
            paths)
        self._save()

    def include_slave(self, measurement: Measurement) -> None:
        """ Include measurement to slave category under master.
        
        Args:
            measurement: A measurement class object.
        """
        # Check if measurement is in the list.
        if measurement not in self.__non_slaves:
            return
        self.__non_slaves.remove(measurement)
        paths = [m.path for m in self.__non_slaves]
        self.__request_information["meta"]["nonslave"] = "|".join(
            paths)
        self._save()

    def get_name(self) -> str:
        """ Get the request's name.
        
        Return:
            Returns the request's name.
        """
        return self.__request_information["meta"]["request_name"]

    def get_master(self) -> Measurement:
        """ Get master measurement of the request.
        """
        return self.__master_measurement

    def get_samples_files(self) -> List[Path]:
        """
        Searches the directory for folders beginning with "Sample".

        Return:
            Returns all the paths for these samples.
        """
        samples = []
        for item in os.listdir(self.directory):
            if os.path.isdir(Path(self.directory, item)) and \
                    item.startswith("Sample_"):
                samples.append(Path(self.directory, item))
                # It is presumed that the sample numbers are of format
                # '01', '02',...,'10', '11',...

                # Python 3.6 gives DeprecationWarning for using just "\d" as
                # regex pattern. To avoid potential future issues, the pattern
                # is declared as a raw  string (see https://stackoverflow.com/
                # questions/50504500/deprecationwarning-invalid-escape-sequence
                # -what-to-use-instead-of-d
                match_object = re.search(r"\d", item)

                if match_object:
                    number_str = item[match_object.start()]
                    if number_str == "0":
                        n = int(item[match_object.start() + 1])
                    else:
                        n = int(
                            item[match_object.start():match_object.start() + 2])
                    self._running_int = max(self._running_int, n)
        return samples

    def get_running_int(self) -> int:
        """
        Get the running int needed for numbering the samples.
        """
        return self._running_int

    def increase_running_int_by_1(self) -> None:
        """
        Increase running int by one.
        """
        self._running_int = self._running_int + 1

    def get_measurement_tabs(self, exclude_id=-1) -> List:
        """ Get measurement tabs of a request.
        """
        list_m = []
        for tab in self.__tabs.values():
            if type(tab.obj) is Measurement:
                if not tab.tab_id == exclude_id:
                    list_m.append(tab)
        return list_m

    def get_nonslaves(self) -> List[Measurement]:
        """ Get measurement names that will be excluded from slave category.
        """
        paths = self.__request_information["meta"]["nonslave"].split("|")
        for measurement in self._get_measurements():
            for path in paths:
                if path == measurement.path:
                    if measurement in self.__non_slaves:
                        continue
                    self.__non_slaves.append(measurement)
        return self.__non_slaves

    def has_master(self) -> Union[str, Measurement]:
        """ Does request have master measurement? Check from config file as
        it is not loaded yet.
        
        This is used when loading request. As request has no measurement in it
        when inited so check is made in potku.py after loading all measurements
        via this method. The corresponding master title in treewidget is then
        set.

        Return:
            Measurement object.
        """
        path = self.__request_information["meta"]["master"]
        for measurement in self._get_measurements():
            if measurement.path == path:
                return measurement
        return ""

    def _load(self) -> None:
        """ Load request.
        """
        self.__request_information.read(self.request_file)
        paths = self.__request_information["meta"]["nonslave"] \
            .split("|")
        for measurement in self._get_measurements():
            for path in paths:
                if path == measurement.path:
                    self.__non_slaves.append(measurement)

    def _save(self) -> None:
        """ Save request.
        """
        # TODO: Saving properly.
        with self.request_file.open("w") as configfile:
            self.__request_information.write(configfile)

    def save_cuts(
            self,
            measurement: Measurement,
            progress: Optional[ProgressReporter] = None) -> None:
        """ Save cuts for all measurements except for master.
        
        Args:
            measurement: A measurement class object that issued save cuts.
            progress: ProgressReporter object.
        """
        name = measurement.name
        master = self.has_master()
        if master != "" and name == master.name:
            nonslaves = self.get_nonslaves()
            tabs = self.get_measurement_tabs(measurement.tab_id)
            for i, tab in enumerate(tabs):
                if progress is not None:
                    sub_progress = progress.get_sub_reporter(
                        lambda x: (100 * i + x) / len(tabs)
                    )
                else:
                    sub_progress = None

                tab_name = tab.obj.name
                if tab.data_loaded and tab.obj not in nonslaves and \
                        tab_name != name:
                    # No need to save same measurement twice.
                    tab.obj.save_cuts(progress=sub_progress)

        if progress is not None:
            progress.report(100)

    def save_selection(
            self,
            measurement: Measurement,
            progress: Optional[ProgressReporter] = None) -> None:
        """ Save selection for all measurements except for master.
        
        Args:
            measurement: A measurement class object that issued save cuts.
            progress: ProgressReporter object.
        """
        directory = measurement.get_data_dir()
        name = measurement.name
        selection_file = "{0}.selections".format(Path(directory, name))
        master = self.has_master()
        if master != "" and name == master.name:
            nonslaves = self.get_nonslaves()
            tabs = self.get_measurement_tabs(measurement.tab_id)

            for i, tab in enumerate(tabs):
                tab_name = tab.obj.name
                if tab.data_loaded and tab.obj not in nonslaves and \
                        tab_name != name:

                    if progress is not None:
                        sub_progress = progress.get_sub_reporter(
                            lambda x: (100 * i + x) / len(tabs))
                    else:
                        sub_progress = None

                    tab.obj.selector.load(selection_file, progress=sub_progress)
                    tab.histogram.matplotlib.on_draw()

        if progress is not None:
            progress.report(100)

    def set_master(self, measurement: Optional[Measurement] = None) -> None:
        """ Set master measurement for the request.
        
        Args:
            measurement: A measurement class object.
        """
        self.__master_measurement = measurement
        if not measurement:
            self.__request_information["meta"]["master"] = ""
        else:
            # name = measurement.name
            path = measurement.path
            self.__request_information["meta"]["master"] = path
        self._save()

    def get_imported_files_folder(self) -> Path:
        return self.directory / "Imported_files"

    def get_imported_files(self) -> List[Path]:
        """Returns a list of file paths from imported files directory.
        """
        files = []
        try:
            with os.scandir(self.get_imported_files_folder()) as scdir:
                for entry in scdir:
                    path = Path(entry)
                    if path.is_file():
                        files.append(path)
        except OSError:
            pass
        return files

    def _get_simulations(self) -> Iterable[Simulation]:
        return (
            sim for sample in self.samples.samples
            for sim in sample.simulations.simulations.values()
        )

    def _get_measurements(self) -> Iterable[Measurement]:
        return (
            measurement for sample in self.samples.samples
            for measurement in sample.measurements.measurements.values()
        )

    def get_running_simulations(self) -> List[ElementSimulation]:
        return list(
            elem_sim for sim in self._get_simulations()
            for elem_sim in sim.get_running_simulations()
        )

    def get_running_optimizations(self) -> List[ElementSimulation]:
        return list(
            elem_sim for sim in self._get_simulations()
            for elem_sim in sim.get_running_optimizations()
        )

    def get_finished_simulations(self) -> List[ElementSimulation]:
        return list(
            elem_sim for sim in self._get_simulations()
            for elem_sim in sim.get_finished_simulations()
        )

    def get_finished_optimizations(self) -> List[ElementSimulation]:
        return list(
            elem_sim for sim in self._get_simulations()
            for elem_sim in sim.get_finished_optimizations()
        )

    def close_log_files(self) -> None:
        """Closes the log file of this Request as well as log files of
        all Measurements and Simulations belonging to this Request.
        """
        # default_simulation and default_measurement should not have open log
        # files to begin with, but close them anyway just in case
        self.default_simulation.close_log_files()
        self.default_measurement.close_log_files()

        for sim in self._get_simulations():
            sim.close_log_files()
        for measurement in self._get_measurements():
            measurement.close_log_files()
        RequestLogger.close_log_files(self)
