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

__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen " \
             "\n Samuli Rahkonen \n Miika Raunio \n Severi Jääskeläinen " \
             "\n Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"
__version__ = "2.0"

import configparser
import logging
import os
import re
import time

from pathlib import Path
from typing import Tuple

from .base import ElementSimulationContainer
from .detector import Detector
from .element import Element
from .element_simulation import ElementSimulation
from .measurement import Measurement
from .run import Run
from .sample import Samples
from .simulation import Simulation
from .target import Target
from .recoil_element import RecoilElement


class Request(ElementSimulationContainer):
    """Request class to handle all measurements.
    """

    def __init__(self, directory: Path, name, global_settings, tabs=None,
                 save_on_creation=True, enable_logging=True):
        """ Initializes Request class.
        
        Args:
            directory: A String representing request directory.
            name: Name of the request.
            global_settings: A GlobalSettings class object (of the program).
            tabs: A dictionary of MeasurementTabWidgets and SimulationTabWidgets
                  of the request.
        """
        self.directory = Path(directory)
        self.default_folder = Path(self.directory, "Default")

        self.request_name = name
        self.global_settings = global_settings
        self.samples = Samples(self)

        self.default_run = Run()
        # self.default_target = Target()

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
        self.default_detector = self._create_default_detector(
            self.default_detector_folder, save_on_creation=save_on_creation
        )
        self.default_measurement = self._create_default_measurement(
            save_on_creation=save_on_creation
        )
        self.default_target = self._create_default_target(
            save_on_creation=save_on_creation
        )
        self.default_simulation, self.default_element_simulation = \
            self._create_default_simulation(
                save_on_creation=save_on_creation)

        # Set default Run, Detector and Target objects to Measurement
        self.default_measurement.run = self.default_run
        self.default_measurement.detector = self.default_detector
        self.default_measurement.target = self.default_target

        # Set default Run, Detector and Target objects to Simulation
        self.default_simulation.run = self.default_run
        self.default_simulation.detector = self.default_detector
        self.default_simulation.target = self.default_target

        if enable_logging:
            self.__set_request_logger()

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
            self.load()
        elif save_on_creation:
            self.save()

    def create_folder_structure(self):
        self.directory.mkdir(exist_ok=True)
        self.default_folder.mkdir(exist_ok=True)

    @classmethod
    def from_file(cls, file, settings, tab_widgets):
        """Returns a new Request from an existing .request file and folder
        structure.

        Args:
        """
        # TODO better error checking
        file_path = Path(file).resolve()
        if not file_path.exists():
            raise ValueError("Request file does not exist.")
        if not file_path.is_file():
            raise ValueError("Expected file, got a directory")
        if file_path.suffix != ".request":
            raise ValueError("Expected request file")
        return cls(file_path.parent, file_path.stem, settings, tab_widgets)

    def _create_default_detector(self, folder: Path, save_on_creation) -> \
            Detector:
        """Returns default detector.
        """
        detector_path = folder / "Default.detector"
        if detector_path.exists():
            # Read detector from file
            detector = Detector.from_file(
                detector_path, self.default_measurement_file_path, self,
                save_on_creation=save_on_creation)
        else:
            # Create Detector folder under Default folder
            if save_on_creation:
                self.default_detector_folder.mkdir(exist_ok=True)
            # Create default detector for request
            detector = Detector(
                Path(self.default_detector_folder, "Default.detector"),
                self.default_measurement_file_path, name="Default-detector",
                description="These are default detector settings.",
                save_on_creation=save_on_creation)

        if save_on_creation:
            detector.update_directories(self.default_detector_folder)

            detector.to_file(
                Path(self.default_detector_folder, "Default.detector"),
                self.default_measurement_file_path)

        return detector

    def _create_default_measurement(self, save_on_creation) -> Measurement:
        """Returns default measurement.
        """
        info_path = Path(self.default_folder, "Default.info")
        if info_path.exists():
            # Read measurement from file
            measurement = Measurement.from_file(
                info_path,
                Path(self.default_folder, "Default.measurement"),
                Path(self.default_folder, "Default.profile"),
                self)
            self.default_run = Run.from_file(self.default_measurement_file_path)
        else:
            # Create default measurement for request
            measurement = Measurement(
                self, path=info_path, run=self.default_run,
                detector=self.default_detector,
                description="This is a default measurement.",
                profile_description="These are default profile parameters.",
                measurement_setting_file_description="These are default "
                                                     "measurement "
                                                     "parameters.",
                use_default_profile_settings=False,
                save_on_creation=save_on_creation)

        return measurement

    def _create_default_target(self, save_on_creation) -> Target:
        """Returns default target.
        """
        target_path = Path(self.default_folder, "Default.target")
        if target_path.exists():
            # Read target from file
            target = Target.from_file(
                target_path, self.default_measurement_file_path, self)
        else:
            # Create default target for request
            target = Target(
                description="These are default target parameters.")

        if save_on_creation:
            target.to_file(
                Path(self.default_folder, target.name + ".target"),
                self.default_measurement_file_path)

        return target

    def _create_default_run(self):
        """
        Create default run.
        """
        # TODO this is not used currently
        try:
            # Try reading Run parameters from .measurement file.
            self.default_run = Run.from_file(self.default_measurement_file_path)
        except KeyError:
            # Save new Run parameters to file.
            self.default_run.to_file(Path(
                self.default_folder,
                self.default_measurement.measurement_setting_file_name +
                ".measurement"))

    def _create_default_simulation(
            self, save_on_creation) -> Tuple[Simulation, ElementSimulation]:
        """Create default simulation.
        """
        simulation_path = Path(self.default_folder, "Default.simulation")
        if simulation_path.exists():
            # Read default simulation from file
            sim = Simulation.from_file(
                self, simulation_path, save_on_creation=save_on_creation)
        else:
            # Create default simulation for request
            sim = Simulation(
                Path(self.default_folder, "Default.simulation"), self,
                save_on_creation=save_on_creation,
                detector=self.default_detector,
                description="This is a default simulation.",
                measurement_setting_file_description="These are default "
                                                     "simulation "
                                                     "parameters.")

        mcsimu_path = Path(self.default_folder, "Default.mcsimu")
        if mcsimu_path.exists():
            # Read default element simulation from file
            elem_sim = ElementSimulation.from_file(
                self, "4He", self.default_folder, mcsimu_path,
                Path(self.default_folder, "Default.profile"), sim)
            # TODO should this be added to sim's element sims?
        else:
            # Create default element simulation for request
            elem_sim = ElementSimulation(
                self.default_folder, self,
                [RecoilElement(Element.from_string("4He 3.0"), [],
                               "#0000ff")],
                simulation=sim,
                description="These are default simulation parameters.",
                use_default_settings=False,
                save_on_creation=save_on_creation)
            sim.element_simulations.append(elem_sim)
        return sim, elem_sim

    def exclude_slave(self, measurement):
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
        self.save()

    def include_slave(self, measurement):
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
        self.save()

    def get_name(self):
        """ Get the request's name.
        
        Return:
            Returns the request's name.
        """
        return self.__request_information["meta"]["request_name"]

    def get_master(self) -> Measurement:
        """ Get master measurement of the request.
        """
        return self.__master_measurement

    def get_samples_files(self):
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
                        self._running_int = int(item[match_object.start() + 1])
                    else:
                        self._running_int = int(item[match_object.start():
                                                     match_object.start() + 2])
        return samples

    def get_running_int(self):
        """
        Get the running int needed for numbering the samples.
        """
        return self._running_int

    def increase_running_int_by_1(self):
        """
        Increase running int by one.
        """
        self._running_int = self._running_int + 1

    def get_measurement_tabs(self, exclude_id=-1):
        """ Get measurement tabs of a request.
        """
        list_m = []
        for tab in self.__tabs.values():
            if type(tab.obj) is Measurement:
                if not tab.tab_id == exclude_id:
                    list_m.append(tab)
        return list_m

    def get_nonslaves(self):
        """ Get measurement names that will be excluded from slave category.
        """
        paths = self.__request_information["meta"]["nonslave"] \
            .split("|")
        for measurement in self.samples.measurements.measurements.values():
            for path in paths:
                if path == measurement.path:
                    if measurement in self.__non_slaves:
                        continue
                    self.__non_slaves.append(measurement)
        return self.__non_slaves

    def has_master(self):
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
        for measurement in self.samples.measurements.measurements.values():
            if measurement.path == path:
                return measurement
        return ""

    def load(self):
        """ Load request.
        """
        self.__request_information.read(self.request_file)
        paths = self.__request_information["meta"]["nonslave"] \
            .split("|")
        for measurement in self.samples.measurements.measurements.values():
            for path in paths:
                if path == measurement.path:
                    self.__non_slaves.append(measurement)

    def save(self):
        """ Save request.
        """
        # TODO: Saving properly.
        with open(self.request_file, "wt+") as configfile:
            self.__request_information.write(configfile)

    def save_cuts(self, measurement, progress=None):
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

    def save_selection(self, measurement, progress=None):
        """ Save selection for all measurements except for master.
        
        Args:
            measurement: A measurement class object that issued save cuts.
            progress: ProgressReporter object.
        """
        directory = measurement.directory_data
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

    def set_master(self, measurement=None):
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
        self.save()

    def __set_request_logger(self):
        """ Sets the logger which is used to log everything that doesn't happen
        in measurements.
        """
        logger = logging.getLogger("request")
        logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S")
        requestlog = logging.FileHandler(Path(self.directory, "request.log"))
        requestlog.setLevel(logging.INFO)
        requestlog.setFormatter(formatter)

        logger.addHandler(requestlog)

    def _get_simulations(self):
        return (
            sim for sample in self.samples.samples
            for sim in sample.simulations.simulations.values()
        )

    def get_running_simulations(self):
        return list(
            elem_sim for sim in self._get_simulations()
            for elem_sim in sim.get_running_simulations()
        )

    def get_running_optimizations(self):
        return list(
            elem_sim for sim in self._get_simulations()
            for elem_sim in sim.get_running_optimizations()
        )

    def get_finished_simulations(self):
        return list(
            elem_sim for sim in self._get_simulations()
            for elem_sim in sim.get_finished_simulations()
        )

    def get_finished_optimizations(self):
        return list(
            elem_sim for sim in self._get_simulations()
            for elem_sim in sim.get_finished_optimizations()
        )
