# coding=utf-8
"""
Created on 15.3.2013
Updated on 29.1.2020

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
             "\n Samuli Rahkonen \n Miika Raunio \n Severi Jääskeläinen \n " \
             "Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"
__version__ = "2.0"

import hashlib
import json
import logging
import os
import shutil
import sys
import time

from modules.cut_file import CutFile
from modules.detector import Detector
from modules.general_functions import md5_for_file
from modules.general_functions import remove_file
from modules.general_functions import rename_file
from modules.run import Run
from modules.selection import Selector
from modules.target import Target
from modules.ui_log_handlers import Logger

from PyQt5 import QtCore
from PyQt5 import QtWidgets


class Measurements:
    """ Measurements class handles multiple measurements.
    """

    def __init__(self, request):
        """Inits measurements class.

        Args:
            request: Request class object.
        """
        self.request = request
        self.measurements = {}  # Dictionary<Measurement>
        self.measuring_unit_settings = None
        self.default_settings = None
        self.name_prefix = "Measurement_"

    def is_empty(self):
        """Check if there are any measurements.

        Return:
            Returns True if there are no measurements currently in the
            measurements object.
        """
        return len(self.measurements) == 0

    def get_key_value(self, key):
        """
        Get key value.

        Args:
             key: A key.

        Return:
            Measurement object corresponding to key.
        """
        if key not in self.measurements:
            return None
        return self.measurements[key]

    def add_measurement_file(self, sample, file_path, tab_id, name,
                             import_evnt_or_binary):
        """ Add a new file to measurements.

        Args:
            sample: The sample under which the measurement is put.
            file_path: Path of the .info measurement file or data file when
            creating a new measurement.
            tab_id: Integer representing identifier for measurement's tab.
            name: Name for the Measurement object.
            import_evnt_or_binary: Whether evnt or lst data is being imported
            or not.

        Return:
            Returns new measurement or None if it wasn't added
        """
        directory_prefix = "Measurement_"
        measurement = None

        if import_evnt_or_binary:
            next_serial = sample.get_running_int_measurement()
            measurement_directory = \
                os.path.join(self.request.directory, sample.directory,
                             directory_prefix + "%02d" % next_serial +
                             "-" + name)
            sample.increase_running_int_measurement_by_1()
            if not os.path.exists(measurement_directory):
                os.makedirs(measurement_directory)
            measurement = Measurement(self.request, measurement_directory,
                                      tab_id, name)
            measurement.sample = sample

            measurement.info_to_file(os.path.join(measurement_directory,
                                                  measurement.name +
                                                  ".info"))
            measurement.create_folder_structure(measurement_directory, None)
            serial_number = next_serial
            measurement.serial_number = serial_number
            self.request.samples.measurements.measurements[tab_id] = \
                measurement

        else:
            measurement_filename = os.path.split(file_path)[1]
            file_directory, file_name = os.path.split(file_path)

            profile_file_path = None
            measurement_file = None
            for file in os.listdir(file_directory):
                if file.endswith(".profile"):
                    profile_file_path = os.path.join(file_directory, file)
                elif file.endswith(".measurement"):
                    measurement_file = os.path.join(file_directory, file)

            # Create Measurement from file
            if os.path.exists(file_path) and file_path.endswith(".info"):
                measurement = Measurement.from_file(file_path,
                                                    measurement_file,
                                                    profile_file_path,
                                                    self.request)
                measurement.sample = sample
                measurement_folder_name = os.path.split(file_directory)[1]
                serial_number = int(measurement_folder_name[
                                    len(directory_prefix):len(
                                        directory_prefix) + 2])
                measurement.serial_number = serial_number
                measurement.tab_id = tab_id
                measurement.update_folders_and_selector()

                if measurement_file:
                    measurement.run = Run.from_file(os.path.join(
                        measurement.directory, measurement_file))

                # Read Detector anf Target information from file.
                for file in os.listdir(file_directory):
                    if file.endswith(".target"):
                        measurement.target = Target.from_file(os.path.join(
                            file_directory, file), os.path.join(
                            file_directory,
                            measurement_file), self.request)
                    if file.startswith("Detector"):
                        det_folder = os.path.join(file_directory,
                                                  "Detector")
                        for f in os.listdir(det_folder):
                            if f.endswith(".detector"):
                                measurement.detector = Detector.from_file(
                                    os.path.join(det_folder, f),
                                    os.path.join(measurement.directory,
                                                 measurement_file),
                                    self.request)
                                measurement.detector.update_directories(
                                    det_folder)
                self.request.samples.measurements.measurements[tab_id] = \
                    measurement

            # Create new Measurement object.
            else:
                measurement_name, extension = os.path.splitext(file_name)
                try:
                    keys = sample.measurements.measurements.keys()
                    for key in keys:
                        if sample.measurements.measurements[key].directory == \
                                measurement_name:
                            return measurement  # measurement = None
                    next_serial = sample.get_running_int_measurement()
                    measurement_directory = \
                        os.path.join(self.request.directory, sample.directory,
                                     directory_prefix + "%02d" % next_serial +
                                     "-" + name)
                    sample.increase_running_int_measurement_by_1()
                    if not os.path.exists(measurement_directory):
                        os.makedirs(measurement_directory)
                    measurement = Measurement(self.request,
                                              measurement_directory,
                                              tab_id, name)
                    measurement.sample = sample

                    measurement.info_to_file(os.path.join(measurement_directory,
                                                          measurement.name +
                                                          ".info"))

                    # Create path for measurement file used by the program and
                    # create folder structure.
                    new_measurement_file = os.path.join(measurement_directory,
                                                        "Data",
                                                        measurement_filename)
                    measurement.create_folder_structure(measurement_directory,
                                                        new_measurement_file)
                    if file_directory != os.path.join(
                            measurement_directory, measurement.directory_data) \
                                and file_directory:
                        measurement.copy_file_into_measurement(file_path)
                    serial_number = next_serial
                    measurement.serial_number = serial_number
                    self.request.samples.measurements.measurements[tab_id] = \
                        measurement
                    measurement.measurement_file = measurement_filename
                except:
                    log = "Something went wrong while adding a new measurement."
                    logging.getLogger("request").critical(log)
                    print(sys.exc_info())

        # Add Measurement to  Measurements.
        sample.measurements.measurements[tab_id] = measurement
        # self.request.samples.measurements.measurements[tab_id] = measurement
        return measurement

    def remove_obj(self, removed_obj):
        """Removes given measurement.
        """
        self.measurements.pop(removed_obj.tab_id)

    def remove_by_tab_id(self, tab_id):
        """Removes measurement from measurements by tab id
        
        Args:
            tab_id: Integer representing tab identifier.
        """

        def remove_key(d, key):
            r = dict(d)
            del r[key]
            return r

        self.measurements = remove_key(self.measurements, tab_id)


class Measurement(Logger):
    """Measurement class to handle one measurement data.
    """

    # __slots__ = "request", "tab_id", "name", "description",\
    #             "modification_time", "run", "detector", "target", \
    #             "profile_name", "profile_description", \
    #             "profile_modification_time", "reference_density", \
    #             "number_of_depth_steps", "depth_step_for_stopping",\
    #             "depth_step_for_output", "depth_for_concentration_from", \
    #             "depth_for_concentration_to", "channel_width", \
    #             "reference_cut", "number_of_splits", "normalization"

    def __init__(self, request, path, tab_id=-1, name="Default",
                 description="", modification_time=None, run=None,
                 detector=None, target=None, profile_name="Default",
                 profile_description="", profile_modification_time=None,
                 reference_density=3.0, number_of_depth_steps=150,
                 depth_step_for_stopping=10, depth_step_for_output=10,
                 depth_for_concentration_from=200,
                 depth_for_concentration_to=400, channel_width=0.025,
                 reference_cut="", number_of_splits=10, normalization="First",
                 measurement_setting_file_name="Default",
                 measurement_setting_file_description="",
                 measurement_setting_modification_time=None,
                 use_default_profile_settings=True, sample=None):
        """Initializes a measurement.

        Args:
            request: Request class object.
            path: Full path to measurement's .info file.
        """
        # Run the base class initializer to establish logging
        Logger.__init__(self, name, "Measurement")

        self.tab_id = tab_id

        self.request = request  # To which request be belong to
        self.path = path
        self.name = name
        self.description = description
        if not modification_time:
            modification_time = time.time()
        self.modification_time = modification_time

        self.sample = sample

        self.run = run
        self.detector = detector
        self.target = target

        self.measurement_setting_file_name = measurement_setting_file_name
        if not self.measurement_setting_file_name:
            self.measurement_setting_file_name = name
        self.measurement_setting_file_description = \
            measurement_setting_file_description
        if not measurement_setting_modification_time:
            measurement_setting_modification_time = time.time()
        self.measurement_setting_modification_time = \
            measurement_setting_modification_time

        self.profile_name = profile_name
        self.profile_description = profile_description
        if not profile_modification_time:
            profile_modification_time = time.time()
        self.profile_modification_time = profile_modification_time
        self.reference_density = reference_density
        self.number_of_depth_steps = number_of_depth_steps
        self.depth_step_for_stopping = depth_step_for_stopping
        self.depth_step_for_output = depth_step_for_output
        self.depth_for_concentration_from = depth_for_concentration_from
        self.depth_for_concentration_to = depth_for_concentration_to
        self.channel_width = channel_width
        self.reference_cut = reference_cut
        self.number_of_splits = number_of_splits
        self.normalization = normalization

        self.data = []

        # Main window's statusbar TODO: Remove GUI stuff.
        self.statusbar = self.request.statusbar

        # Which color scheme is selected by default
        self.color_scheme = "Default color"

        self.name_prefix = "Measurement_"
        self.serial_number = 0
        self.directory = os.path.split(self.path)[0]
        self.measurement_file = None
        self.directory_cuts = None
        self.directory_composition_changes = None
        self.directory_depth_profiles = None
        self.directory_energy_spectra = None
        self.directory_data = None

        self.selector = None

        self.use_default_profile_settings = use_default_profile_settings

    def get_detector_or_default(self):
        """
        Get measurement specific detector of default.

        Return:
            A Detector.
        """
        if self.detector is None:
            return self.request.default_detector
        else:
            return self.detector

    def update_folders_and_selector(self):
        """
        Update folders and selector.
        """
        for item in os.listdir(self.directory):
            if item.startswith("Composition_changes"):
                self.directory_composition_changes = os.path.join(
                    self.directory, "Composition_changes")
            if item.startswith("Data"):
                self.directory_data = os.path.join(self.directory, "Data")
            if item.startswith("Depth_profiles"):
                self.directory_depth_profiles = os.path.join(self.directory,
                                                             "Depth_profiles")
            if item.startswith("Energy_spectra"):
                self.directory_energy_spectra = os.path.join(self.directory,
                                                             "Energy_spectra")
        for file in os.listdir(self.directory_data):
            if file.endswith(".asc"):
                self.measurement_file = file
            if file.startswith("Cuts"):
                self.directory_cuts = os.path.join(self.directory_data, "Cuts")

        self.set_loggers(self.directory, self.request.directory)

        element_colors = self.request.global_settings.get_element_colors()
        self.selector = Selector(self, element_colors)

    def update_directory_references(self, new_dir):
        """
        Update directory references.

        Args:
            new_dir: Path to measurement folder with new name.
        """
        self.directory = new_dir
        self.directory_data = os.path.join(self.directory, "Data")
        self.directory_cuts = os.path.join(self.directory_data, "Cuts")
        self.directory_composition_changes = os.path.join(self.directory,
                                                          "Composition_changes")
        self.directory_depth_profiles = os.path.join(self.directory,
                                                     "Depth_profiles")
        self.directory_energy_spectra = os.path.join(self.directory,
                                                     "Energy_spectra")

        if self.detector:
            self.detector.update_directory_references(self)

        self.selector.update_references(self)

    @classmethod
    def from_file(cls, measurement_info_path, measurement_file_path,
                  profile_file_path,
                  request):
        """
        Read Measurement information from filea.

        Args:
            measurement_info_path: Path to .info file.
            measurement_file_path: Path to .measurement file.
            profile_file_path: Path to .profile file.

        Return:
            Measurement object.
        """

        obj_info = json.load(open(measurement_info_path))
        if measurement_file_path and os.path.exists(measurement_file_path):
            obj_measurement = json.load(open(measurement_file_path))
            measurement_settings_name = obj_measurement["general"]["name"]
            measurement_settings_description = \
                obj_measurement["general"]["description"]
            measurement_setting_modification_time = \
                obj_measurement["general"]["modification_time_unix"]
        else:
            measurement_settings_name = ""
            measurement_settings_description = ""
            measurement_setting_modification_time = time.time()

        if profile_file_path and os.path.exists(profile_file_path):
            obj_profile = json.load(open(profile_file_path))
            profile_name = obj_profile["general"]["name"]
            profile_description = obj_profile["general"]["description"]
            profile_modification_time = obj_profile["general"][
                "modification_time_unix"]

            reference_density = obj_profile["depth_profiles"][
                "reference_density"]
            number_of_depth_steps = \
                obj_profile["depth_profiles"]["number_of_depth_steps"]
            depth_step_for_stopping = \
                obj_profile["depth_profiles"]["depth_step_for_stopping"]
            depth_step_for_output = \
                obj_profile["depth_profiles"]["depth_step_for_output"]
            depth_for_concentration_from = \
                obj_profile["depth_profiles"]["depth_for_concentration_from"]
            depth_for_concentration_to = \
                obj_profile["depth_profiles"]["depth_for_concentration_to"]

            channel_width = obj_profile["energy_spectra"]["channel_width"]

            reference_cut = obj_profile["composition_changes"]["reference_cut"]
            number_of_splits = \
                obj_profile["composition_changes"]["number_of_splits"]
            normalization = obj_profile["composition_changes"]["normalization"]
            if obj_profile["general"]["use_default_settings"] == "True":
                use_default_profile_settings = True
            else:
                use_default_profile_settings = False

        else:
            measurement = request.default_measurement
            profile_name = measurement.profile_name
            profile_description = measurement.profile_description
            profile_modification_time = measurement.profile_modification_time
            number_of_depth_steps = measurement.number_of_depth_steps
            depth_step_for_stopping = measurement.depth_step_for_stopping
            depth_step_for_output = measurement.depth_step_for_output
            depth_for_concentration_from = \
                measurement.depth_for_concentration_from
            depth_for_concentration_to = measurement.depth_for_concentration_to
            channel_width = measurement.channel_width
            reference_cut = measurement.reference_cut
            number_of_splits = measurement.number_of_splits
            normalization = measurement.normalization
            reference_density = measurement.reference_density
            use_default_profile_settings = True

        name = obj_info["name"]
        description = obj_info["description"]
        modification_time = obj_info["modification_time_unix"]

        return cls(request=request, path=measurement_info_path, name=name,
                   description=description,
                   modification_time=modification_time,
                   run=None, detector=None,
                   target=None, profile_name=profile_name,
                   profile_description=profile_description,
                   profile_modification_time=profile_modification_time,
                   number_of_depth_steps=number_of_depth_steps,
                   depth_step_for_stopping=depth_step_for_stopping,
                   depth_step_for_output=depth_step_for_output,
                   depth_for_concentration_from=depth_for_concentration_from,
                   depth_for_concentration_to=depth_for_concentration_to,
                   channel_width=channel_width, reference_cut=reference_cut,
                   number_of_splits=number_of_splits,
                   normalization=normalization,
                   reference_density=reference_density,
                   measurement_setting_file_name=measurement_settings_name,
                   measurement_setting_file_description=measurement_settings_description,
                   measurement_setting_modification_time=measurement_setting_modification_time,
                   use_default_profile_settings=use_default_profile_settings)

    def measurement_to_file(self, measurement_file_path):
        """
        Write a .measurement file.

        Args:
            measurement_file_path: Path to .measurement file.
        """
        if os.path.exists(measurement_file_path):
            with open(measurement_file_path) as mesu:
                obj_measurement = json.load(mesu)
        else:
            obj_measurement = {}

        obj_measurement["general"] = {}

        obj_measurement["general"]["name"] = self.measurement_setting_file_name
        obj_measurement["general"]["description"] = \
            self.measurement_setting_file_description
        obj_measurement["general"]["modification_time"] = \
            time.strftime("%c %z %Z", time.localtime(time.time()))
        obj_measurement["general"]["modification_time_unix"] = time.time()

        with open(measurement_file_path, "w") as file:
            json.dump(obj_measurement, file, indent=4)

    def info_to_file(self, info_file_path):
        """
        Write an .info file.

        Args:
            info_file_path: Path to .info file.
        """
        obj_info = {
            "name": self.name,
            "description": self.description,
            "modification_time": time.strftime("%c %z %Z",
                                               time.localtime(time.time())),
            "modification_time_unix": time.time()
        }

        with open(info_file_path, "w") as file:
            json.dump(obj_info, file, indent=4)

    def profile_to_file(self, profile_file_path):
        """
        Write a .profile file.

        Args:
            profile_file_path: Path to .profile file.
        """
        obj_profile = {"general": {},
                       "depth_profiles": {},
                       "energy_spectra": {},
                       "composition_changes": {}}

        obj_profile["general"]["name"] = self.profile_name
        obj_profile["general"]["description"] = \
            self.profile_description
        obj_profile["general"]["modification_time"] = \
            time.strftime("%c %z %Z", time.localtime(time.time()))
        obj_profile["general"]["modification_time_unix"] = \
            self.profile_modification_time
        obj_profile["general"]["use_default_settings"] = \
            str(self.use_default_profile_settings)

        obj_profile["depth_profiles"]["reference_density"] = \
            self.reference_density
        obj_profile["depth_profiles"]["number_of_depth_steps"] = \
            self.number_of_depth_steps
        obj_profile["depth_profiles"]["depth_step_for_stopping"] = \
            self.depth_step_for_stopping
        obj_profile["depth_profiles"]["depth_step_for_output"] = \
            self.depth_step_for_output
        obj_profile["depth_profiles"]["depth_for_concentration_from"] = \
            self.depth_for_concentration_from
        obj_profile["depth_profiles"]["depth_for_concentration_to"] = \
            self.depth_for_concentration_to
        obj_profile["energy_spectra"]["channel_width"] = self.channel_width
        obj_profile["composition_changes"]["reference_cut"] = self.reference_cut
        obj_profile["composition_changes"]["number_of_splits"] = \
            self.number_of_splits
        obj_profile["composition_changes"]["normalization"] = self.normalization

        with open(profile_file_path, "w") as file:
            json.dump(obj_profile, file, indent=4)

    def create_folder_structure(self, measurement_folder, measurement_file):
        """ Creates folder structure for the measurement.

        Args:
            measurement_folder: Path of the measurement folder.
            measurement_file: Path of the measurement file. (under Data)
        """
        if measurement_file is None:
            measurement_data_folder = os.path.join(measurement_folder, "Data")
            self.measurement_file = None
        else:
            measurement_data_folder, measurement_name = \
                os.path.split(measurement_file)
            self.measurement_file = measurement_name  # With extension

        self.directory = measurement_folder
        self.directory_data = measurement_data_folder
        self.directory_cuts = os.path.join(self.directory_data, "Cuts")
        self.directory_composition_changes = os.path.join(self.directory,
                                                          "Composition_changes")
        self.directory_depth_profiles = os.path.join(self.directory,
                                                     "Depth_profiles")
        self.directory_energy_spectra = os.path.join(self.directory,
                                                     "Energy_spectra")

        self.__make_directories(self.directory)
        self.__make_directories(self.directory_data)
        self.__make_directories(self.directory_cuts)
        self.__make_directories(self.directory_composition_changes)
        self.__make_directories(os.path.join(self.directory_composition_changes,
                                             "Changes"))
        self.__make_directories(self.directory_depth_profiles)
        self.__make_directories(self.directory_energy_spectra)

        self.set_loggers(self.directory, self.request.directory)

        element_colors = self.request.global_settings.get_element_colors()
        self.selector = Selector(self, element_colors)

        # Which color scheme is selected by default
        self.color_scheme = "Default color"

    def __make_directories(self, directory):
        """
        Make directories.

        Args:
            directory: Directory to be made under measurement.
        """
        new_dir = os.path.join(self.directory, directory)
        if not os.path.exists(new_dir):
            os.makedirs(new_dir)
            log = "Created a directory {0}.".format(new_dir)
            logging.getLogger("request").info(log)

    def copy_file_into_measurement(self, file_path):
        """
         Copies the given file into the measurement's data folder

        Args:
            file_path: The file that needs to be copied.
        """
        file_name = os.path.basename(file_path)
        new_path = os.path.join(self.directory, self.directory_data, file_name)
        shutil.copyfile(file_path, new_path)

    def load_data(self):
        """Loads measurement data from filepath
        """
        # import cProfile, pstats
        # pr = cProfile.Profile()
        # pr.enable()
        n = 0
        try:
            measurement_name, extension = os.path.splitext(
                self.measurement_file)
            extension = extension.lower()
            if extension == ".asc":
                file_to_open = os.path.join(self.directory,
                                            self.directory_data,
                                            measurement_name + extension)
                # TODO this could maybe be done with CSVParser, but variable
                #      column counts are going to be a problem
                with open(file_to_open, "r") as fp:
                    for line in fp:
                        n += 1  # Event number
                        # TODO: Figure good way to split into columns.
                        # REGEX too slow.
                        split = line.split()
                        split_len = len(split)
                        if split_len == 2:  # At least two columns
                            self.data.append([int(split[0]), int(split[1]), n])
                        if split_len == 3:
                            self.data.append([int(split[0]), int(split[1]),
                                              int(split[2]), n])
            self.selector.measurement = self
        except IOError as e:
            error_log = "Error while loading the {0} {1}. {2}".format(
                "measurement date for the measurement",
                self.name,
                "The error was:")
            error_log_2 = "I/O error ({0}): {1}".format(e.errno, e.strerror)
            logging.getLogger('request').error(error_log)
            logging.getLogger('request').error(error_log_2)
        except Exception as e:
            error_log = "Unexpected error: [{0}] {1}".format(e.errno,
                                                             e.strerror)
            logging.getLogger('request').error(error_log)
        # pr.disable()
        # ps = pstats.Stats(pr)
        # ps.sort_stats("time")
        # ps.print_stats(10)

    def rename_info_file(self, new_name=None):
        """Renames the measurement data file.
        """
        if new_name is None:
            return
        info_file = None
        for file in os.listdir(self.directory):
            if file.endswith(".info"):
                info_file = file
                break
        if info_file:
            rename_file(os.path.join(self.directory, info_file),
                        new_name + ".info")

    def rename_files_in_directory(self, dir):
        if not os.path.exists(dir):
            return
        for file in os.listdir(dir):
            if file.endswith(".cut"):
                old_path = os.path.join(dir, file)
                # Get everything except old measurement name from cut file
                new_name = self.name + "." + file.split('.', 1)[1]
                rename_file(old_path, new_name)

    def set_axes(self, axes, progress_bar, start, add):
        """ Set axes information to selector within measurement.
        
        Sets axes information to selector to add selection points. Since 
        previously when creating measurement old selection could not be checked. 
        Now is time to check for it, while data is still "loading".
        
        Args:
            axes: Matplotlib FigureCanvas's subplot
            progress_bar: A progress bar used when opening a measurement.
            start: Start value for progress bar.
            add: Value added to progress bar.
        """
        self.selector.axes = axes
        # We've set axes information, check for old selection.
        self.__check_for_old_selection(progress_bar, start, add)

    def __check_for_old_selection(self, progress_bar, start, add):
        """ Use old selection file_path if exists.

        Args:
            progress_bar: A progress bar used when opening a measurement.
            start: Start value for progress bar.
            add: Value added to progress bar.
        """
        try:
            selection_file = os.path.join(self.directory, self.directory_data,
                                          "{0}.selections".format(self.name))
            with open(selection_file):
                if not add:
                    add = 10
                if not start:
                    start = 40
                self.load_selection(selection_file, progress_bar, add, start)
        except:
            # TODO: Is it necessary to inform user with this?
            log_msg = "There was no old selection file to add to this request."
            logging.getLogger(self.name).info(log_msg)

    def add_point(self, point, canvas):
        """ Add point into selection or create new selection if first or all
        closed.
        
        Args:
            point: Point (x, y) to be added to selection.
            canvas: matplotlib's FigureCanvas where selections are drawn.

        Return:
            1: When point closes open selection and allows new selection to
                be made.
            0: When point was added to open selection.
            -1: When new selection is not allowed and there are no selections.
        """
        flag = self.selector.add_point(point, canvas)
        if flag >= 0:
            self.selector.update_axes_limits()
        return flag

    def undo_point(self):
        """Undo last point in open selection.
             
        Undo last point in open (last) selection. If there are no selections, 
        do nothing.
        """
        return self.selector.undo_point()

    def purge_selection(self):
        """ Purges (removes) all open selections and allows new selection to be
        made.
        """
        self.selector.purge()

    def remove_all(self):
        """ Remove all selections in selector.
        """
        self.selector.remove_all()

    def draw_selection(self):
        """ Draw all selections in measurement.
        """
        self.selector.draw()

    def end_open_selection(self, canvas):
        """ End last open selection.
        
        Ends last open selection. If selection is open, it will show dialog to 
        select element information and draws into canvas before opening the
        dialog.
        
        Args:
            canvas: Matplotlib's FigureCanvas

        Return:
            1: If selection closed
            0: Otherwise
        """
        return self.selector.end_open_selection(canvas)

    def selection_select(self, cursorpoint, highlight=True):
        """ Select a selection based on point.
        
        Args:
            cursorpoint: Point (x, y) which is clicked on the graph to select
                         selection.
            highlight: Boolean to determine whether to highlight just this 
                       selection.

        Return:
            1: If point is within selection.
            0: If point is not within selection.
        """
        return self.selector.select(cursorpoint, highlight)

    def selection_count(self):
        """ Get count of selections.
        
        Return:
            Returns the count of selections in selector object.
        """
        return self.selector.count()

    def reset_select(self):
        """ Reset selection to None.
        
        Resets current selection to None and resets colors of all selections
        to their default values. 
        """
        self.selector.reset_select()

    def remove_selected(self):
        """ Remove selection
        
        Removes currently selected selection.
        """
        self.selector.remove_selected()

    def delete_all_cuts(self):
        """
        Delete all cuts from cut folder.

        Return:
            If something was deletd or not.
        """
        deleted = False
        for file in os.listdir(self.directory_cuts):
            file_path = os.path.join(self.directory_cuts, file)
            remove_file(file_path)
            deleted = True
        return deleted

    def save_cuts(self, progress_bar=None, percentage=None, add=None):
        """ Save cut files
        
        Saves data points within selections into cut files.
        """
        if self.selector.is_empty():
            self.__remove_old_cut_files()
            # Remove .selections file
            selection_file = os.path.join(self.directory_data, self.name +
                                          ".selections")
            if os.path.exists(selection_file):
                os.remove(selection_file)
            return 0
        if not os.path.exists(os.path.join(self.directory,
                                           self.directory_cuts)):
            self.__make_directories(self.directory_cuts)

        new_created = False
        if not progress_bar:    # TODO use ProgressReporting here
            progress_bar = QtWidgets.QProgressBar()
            self.statusbar.addWidget(progress_bar, 1)
            progress_bar.show()
            QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents)
            # Mac requires event processing to show progress bar and its
            # process.
            percentage = 0
            add = 100
            new_created = True
        first_add = add * 0.9
        second_add = add * 0.1

        starttime = time.time()

        self.__remove_old_cut_files()

        # Initializes the list size to match the number of selections.
        points_in_selection = [[] for unused_i in range(self.selector.count())]

        # Go through all points in measurement data
        data_count = len(self.data)
        for n in range(data_count):  # while n < data_count: 
            if n % 5000 == 0:
                # Do not always update UI to make it faster.
                progress_bar.setValue(percentage + (n / data_count) * first_add)
                QtCore.QCoreApplication.processEvents(
                    QtCore.QEventLoop.AllEvents)
                # Mac requires event processing to show progress bar and its
                # process.
            point = self.data[n]
            # Check if point is within selectors' limits for faster processing.
            if not self.selector.axes_limits.is_inside(point):
                continue

            dirtyinteger = 0  # Lazyway     # TODO use enumerate
            for selection in self.selector.selections:
                if selection.point_inside(point):
                    points_in_selection[dirtyinteger].append(point)
                dirtyinteger += 1

        # Save all found data points into appropriate element cut files
        # Firstly clear old cut files so those won't be accidentally
        # left there.

        dirtyinteger = 0  # Increases with for, for each selection
        content_length = len(points_in_selection)
        for points in points_in_selection:
            if points:  # If not empty selection -> save
                selection = self.selector.get_at(dirtyinteger)
                cut_file = CutFile(os.path.join(self.directory,
                                                self.directory_cuts))
                cut_file.set_info(selection, points)
                cut_file.save()
            dirtyinteger += 1
            progress_bar.setValue(percentage + first_add +
                                  (dirtyinteger / content_length) * second_add)
            QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents)
            # Mac requires event processing to show progress bar and its
            # process.

        if new_created:
            self.statusbar.removeWidget(progress_bar)
            progress_bar.hide()

        log_msg = "Saving finished in {0} seconds.".format(time.time() -
                                                           starttime)
        logging.getLogger(self.name).info(log_msg)

    def __remove_old_cut_files(self):
        """
        Remove old cut files.
        """
        self.__unlink_files(os.path.join(self.directory_cuts))
        directory_changes = os.path.join(
            self.directory_composition_changes, "Changes")
        if not os.path.exists(directory_changes):
            self.__make_directories(directory_changes)
        self.__unlink_files(directory_changes)

    def __unlink_files(self, directory):
        for the_file in os.listdir(directory):
            file_path = os.path.join(directory, the_file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception:
                log_msg = "Failed to remove the old cut files."
                logging.getLogger(self.name).error(log_msg)

    def get_cut_files(self):
        """ Get cut files from a measurement.
        
        Return:
            Returns a list of cut files in measurement.
        """
        cuts = [f for f in os.listdir(os.path.join(self.directory,
                                                   self.directory_cuts))
                if os.path.isfile(os.path.join(self.directory,
                                               self.directory_cuts, f))]
        elemloss = [f for f in os.listdir(os.path.join(
            self.directory, self.directory_composition_changes, "Changes"))
                    if os.path.isfile(os.path.join(
                        self.directory, self.directory_composition_changes,
                        "Changes",
                        f))]
        return cuts, elemloss

    def fill_cuts_treewidget(self, treewidget, use_elemloss=False,
                             checked_files=None):
        """ Fill QTreeWidget with cut files.
        
        Args:
            treewidget: A QtGui.QTreeWidget, where cut files are added to.
            use_elemloss: A boolean representing whether to add elemental
                          losses.
            checked_files: A list of previously checked files.
        """
        if checked_files is None:
            checked_files = []
        treewidget.clear()
        cuts, cuts_elemloss = self.get_cut_files()
        for cut in cuts:
            item = QtWidgets.QTreeWidgetItem([cut])
            item.directory = os.path.join(self.directory, self.directory_cuts)
            item.file_name = cut
            if not checked_files or item.file_name in checked_files:
                item.setCheckState(0, QtCore.Qt.Checked)
            else:
                item.setCheckState(0, QtCore.Qt.Unchecked)
            treewidget.addTopLevelItem(item)
        if use_elemloss and cuts_elemloss:
            elem_root = QtWidgets.QTreeWidgetItem(["Elemental Losses"])
            for elemloss in cuts_elemloss:
                item = QtWidgets.QTreeWidgetItem([elemloss])
                item.directory = os.path.join(
                    self.directory, self.directory_composition_changes,
                    "Changes")
                item.file_name = elemloss
                if item.file_name in checked_files:
                    item.setCheckState(0, QtCore.Qt.Checked)
                else:
                    item.setCheckState(0, QtCore.Qt.Unchecked)
                elem_root.addChild(item)
            treewidget.addTopLevelItem(elem_root)

    def load_selection(self, filename, progress_bar, percent_add, start=40):
        """ Load selections from a file_path.
        
        Removes all current selections and loads selections from given filename.
        
        Args:
            filename: String representing (full) directory to selection
            file_path.
            progress_bar: A progress bar used when opening a measurement.
            percent_add: How many percents are added to progress bar.
            start: Start value for progress bar.
        """
        self.selector.load(filename, progress_bar, percent_add, start)

    def generate_tof_in(self):
        """ Generate tof.in file for external programs.
        
        Generates tof.in file for measurement to be used in external programs 
        (tof_list, erd_depth).
        """
        tof_in_directory = os.path.join(os.path.realpath(os.path.curdir),
                                        "external",
                                        "Potku-bin")
        tof_in_file = os.path.join(tof_in_directory, "tof.in")

        # Get settings 
        # use_settings = self.measurement_settings.get_measurement_settings()
        global_settings = self.request.global_settings

        if self.detector is None:
            detector = self.request.default_detector
        else:
            detector = self.detector
        if self.run is None:
            run = self.request.default_run
        else:
            run = self.run
        if self.target is None:
            target = self.request.default_target
        else:
            target = self.target

        if self.use_default_profile_settings:
            reference_density = \
                self.request.default_measurement.reference_density
            number_of_depth_steps = \
                self.request.default_measurement.number_of_depth_steps
            depth_step_for_stopping = \
                self.request.default_measurement.depth_step_for_stopping
            depth_step_for_output = self.request.default_measurement. \
                depth_step_for_output
            depth_for_concentration_from = \
                self.request.default_measurement.depth_for_concentration_from
            depth_for_concentration_to = \
                self.request.default_measurement.depth_for_concentration_to
        else:
            reference_density = self.reference_density
            number_of_depth_steps = self.number_of_depth_steps
            depth_step_for_stopping = self.depth_step_for_stopping
            depth_step_for_output = self.depth_step_for_output
            depth_for_concentration_from = self.depth_for_concentration_from
            depth_for_concentration_to = self.depth_for_concentration_to
        # Measurement settings
        str_beam = "Beam: {0}\n".format(
            run.beam.ion)
        str_energy = "Energy: {0}\n".format(
            run.beam.energy)
        str_detector = "Detector angle: {0}\n".format(
            detector.detector_theta)
        str_target = "Target angle: {0}\n".format(
            target.target_theta)

        time_of_flight_length = 0
        i = len(detector.tof_foils) - 1
        while i - 1 >= 0:
            time_of_flight_length = detector.foils[
                                        detector.tof_foils[i]].distance - \
                                    detector.foils[
                                        detector.tof_foils[i - 1]].distance
            i = i - 1

        time_of_flight_length = time_of_flight_length / 1000
        str_toflen = "Toflen: {0}\n".format(time_of_flight_length)

        # Timing foil can only be carbon and have one layer!!!
        carbon_foil_thickness_in_nm = 0
        layer = detector.foils[detector.tof_foils[0]].layers[0]
        carbon_foil_thickness_in_nm += layer.thickness  # first layer only
        density_in_g_per_cm3 = layer.density
        carbon_foil_thickness = carbon_foil_thickness_in_nm * \
                                density_in_g_per_cm3 * 6.0221409e+23 * \
                                1.660548782e-27 * 100  # density in ug_per_cm2

        str_carbon = "Carbon foil thickness: {0}\n".format(
            carbon_foil_thickness)

        str_density = "Target density: {0}\n".format(reference_density)

        # Depth Profile settings
        str_depthnumber = "Number of depth steps: {0}\n".format(
            number_of_depth_steps)
        str_depthstop = "Depth step for stopping: {0}\n".format(
            depth_step_for_stopping)
        str_depthout = "Depth step for output: {0}\n".format(
            depth_step_for_output)
        str_depthscale = "Depths for concentration scaling: {0} {1}\n".format(
            depth_for_concentration_from,
            depth_for_concentration_to)

        # Cross section
        flag_cross = global_settings.get_cross_sections()
        str_cross = "Cross section: {0}\n".format(flag_cross)
        # Cross Sections: 1=Rutherford, 2=L'Ecuyer, 3=Andersen

        str_num_iterations = "Number of iterations: {0}\n".format(
            global_settings.get_num_iterations())

        # Efficiency directory
        if self.detector:
            eff_directory = self.detector.efficiency_directory
        else:
            eff_directory = self.request.default_detector.efficiency_directory

        # Add folder that has all the efficiency files in tof_list binary
        # appropriate format
        eff_directory_final = os.path.join(eff_directory, "Used_efficiencies")
        if not os.path.exists(eff_directory_final):
            os.makedirs(eff_directory_final)
        # Copy efficiencies with proper name
        # File name in format 1H.eff or 1H-example.eff

        # TODO check why incorrect efficiencies are assigned
        for eff in os.listdir(eff_directory):
            if not eff.endswith(".eff"):
                continue
            old_file = os.path.join(eff_directory, eff)
            element = eff.split('-')[0]
            if element.endswith(".eff"):
                file_to_copy = os.path.join(eff_directory_final, eff)
            else:
                file_to_copy = os.path.join(eff_directory_final, element
                                            + ".eff")
            shutil.copy(old_file, file_to_copy)
        str_eff_dir = "Efficiency directory: {0}".format(eff_directory_final)

        # Combine strings
        measurement = str_beam + str_energy + str_detector + str_target + \
            str_toflen + str_carbon + str_density
        calibration = "TOF calibration: {0} {1}\n".format(
            detector.tof_slope,
            detector.tof_offset)
        anglecalib = "Angle calibration: {0} {1}\n".format(
            detector.angle_slope,
            detector.angle_offset)
        depthprofile = str_depthnumber + str_depthstop + str_depthout + \
            str_depthscale

        tof_in = measurement + calibration + anglecalib + depthprofile + \
            str_cross + str_num_iterations + str_eff_dir

        # Get md5 of file and new settings
        md5 = hashlib.md5()
        md5.update(tof_in.encode('utf8'))
        digest = md5.digest()
        digest_file = None
        if os.path.isfile(tof_in_file):
            f = open(tof_in_file, 'r')
            digest_file = md5_for_file(f)
            f.close()

        # If different back up old tof.in and generate a new one.
        if digest_file != digest:
            # Try to back up old file.
            try:
                new_file = "{0}_{1}.bak".format(tof_in_file, time.strftime(
                    "%Y-%m-%d_%H.%M.%S"))
                shutil.copyfile(tof_in_file, new_file)
                back_up_msg = "Backed up old tof.in file to {0}".format(
                    os.path.realpath(new_file))
                logging.getLogger(self.name).info(back_up_msg)
            except:
                import traceback
                err_file = sys.exc_info()[2].tb_frame.f_code.co_filename
                str_err = ", ".join([sys.exc_info()[0].__name__ + ": " +
                                     traceback._some_str(sys.exc_info()[1]),
                                     err_file, str(sys.exc_info()[2].tb_lineno)]
                                    )
                error_msg = "Unexpected error when generating tof.in: {0}". \
                    format(str_err)
                logging.getLogger(self.name).error(error_msg)
            # Write new settings to the file.
            with open(tof_in_file, "wt+") as fp:
                fp.write(tof_in)
            str_logmsg = "Generated tof.in with params> {0}". \
                format(tof_in.replace("\n", "; "))
            logging.getLogger(self.name).info(str_logmsg)
