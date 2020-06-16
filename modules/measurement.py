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
             "Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen \n " \
             "Juhani Sundell"
__version__ = "2.0"

import hashlib
import json
import logging
import os
import shutil
import time

from pathlib import Path
from collections import namedtuple
from typing import Optional

from . import general_functions as gf
from .cut_file import CutFile
from .detector import Detector
from .run import Run
from .target import Target
from .ui_log_handlers import Logger
from .base import Serializable
from .base import AdjustableSettings


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

    def add_measurement_file(self, sample, file_path: Path, tab_id, name,
                             import_evnt_or_binary, selector_cls=None):
        """Add a new file to measurements. If selector_cls is given,
        selector will be initialized as an object of that class.

        Args:
            sample: The sample under which the measurement is put.
            file_path: Path of the .info measurement file or data file when
                creating a new measurement.
            tab_id: Integer representing identifier for measurement's tab.
            name: Name for the Measurement object.
            import_evnt_or_binary: Whether evnt or lst data is being imported
                or not.
            selector_cls: class of the selector.

        Return:
            Returns new measurement or None if it wasn't added
        """
        directory_prefix = "Measurement_"
        measurement = None

        if import_evnt_or_binary:
            # TODO remove duplicate code when creating new Measurement
            next_serial = sample.get_running_int_measurement()
            measurement_directory = \
                Path(self.request.directory, sample.directory,
                     directory_prefix + "%02d" % next_serial + "-" + name)
            sample.increase_running_int_measurement_by_1()
            measurement_directory.mkdir(exist_ok=True)
            measurement = Measurement(
                self.request, measurement_directory, tab_id, name,
                sample=sample)

            measurement.create_folder_structure(
                measurement_directory, None, selector_cls=selector_cls)
            serial_number = next_serial
            measurement.serial_number = serial_number
            self.request.samples.measurements.measurements[tab_id] = \
                measurement

        else:
            file_name = file_path.name
            file_directory = file_path.parent

            profile_file, mesu_file, tgt_file, det_file = \
                Measurement.find_measurement_files(file_directory)

            if tgt_file is not None:
                target = Target.from_file(tgt_file, mesu_file, self.request)
            else:
                target = None

            if det_file is not None:
                detector = Detector.from_file(det_file, mesu_file, self.request)
                detector.update_directories(det_file.parent)
            else:
                detector = None

            if mesu_file is not None:
                run = Run.from_file(mesu_file)
            else:
                run = None

            # Create Measurement from file
            if file_path.exists() and file_path.suffix == ".info":
                measurement = Measurement.from_file(
                    file_path, mesu_file, profile_file,
                    self.request, sample=sample, target=target,
                    detector=detector, run=run)

                measurement_folder_name = file_directory.name
                serial_number = int(measurement_folder_name[
                                    len(directory_prefix):len(
                                        directory_prefix) + 2])
                measurement.serial_number = serial_number
                measurement.tab_id = tab_id
                measurement.update_folders_and_selector(
                    selector_cls=selector_cls)

                self.request.samples.measurements.measurements[tab_id] = \
                    measurement

            # Create new Measurement object.
            else:
                measurement_name, extension = file_path.stem, file_path.suffix
                try:
                    keys = sample.measurements.measurements.keys()
                    for key in keys:
                        if sample.measurements.measurements[key].directory == \
                                measurement_name:
                            return measurement  # measurement = None
                    next_serial = sample.get_running_int_measurement()
                    measurement_directory = \
                        Path(self.request.directory, sample.directory,
                             directory_prefix + "%02d" % next_serial + "-" +
                             name)
                    mesu_file = measurement_directory / f"{name}.info"
                    sample.increase_running_int_measurement_by_1()
                    measurement_directory.mkdir(exist_ok=True)
                    measurement = Measurement(
                        self.request, mesu_file, tab_id, name, sample=sample)

                    # Create path for measurement file used by the program and
                    # create folder structure.
                    new_data_file = Path(
                        measurement_directory, "Data", file_name)
                    measurement.create_folder_structure(
                        measurement_directory, new_data_file,
                        selector_cls=selector_cls)
                    if file_directory != Path(
                            measurement_directory, measurement.directory_data) \
                            and file_directory:
                        measurement.copy_file_into_measurement(file_path)
                    serial_number = next_serial
                    measurement.serial_number = serial_number
                    self.request.samples.measurements.measurements[tab_id] = \
                        measurement
                    measurement.measurement_file = file_name
                except Exception as e:
                    log = f"Something went wrong while adding a new " \
                          f"measurement: {e}"
                    logging.getLogger("request").critical(log)

        # Add Measurement to Measurements.
        if measurement is not None:
            sample.measurements.measurements[tab_id] = measurement
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


class Measurement(Logger, AdjustableSettings, Serializable):
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
    DIRECTORY_PREFIX = "Measurement_"

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
                 use_default_profile_settings=True, sample=None,
                 save_on_creation=True):
        """Initializes a measurement.

        Args:
            request: Request class object.
            path: Full path to measurement's .info file.
        """
        # Run the base class initializer to establish logging
        Logger.__init__(self, name, "Measurement")
        # FIXME path should be to info file
        self.tab_id = tab_id

        self.request = request  # To which request be belong to
        self.sample = sample

        self.path = Path(path)  # TODO rename this to info_file
        self.name = name
        self.description = description
        if modification_time is None:
            self.modification_time = time.time()
        else:
            self.modification_time = modification_time

        # TODO rename 'measurement_setting_file_name' to 'measurement_file_name'
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
        if profile_modification_time is None:
            self.profile_modification_time = time.time()
        else:
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

        self.serial_number = 0
        self.directory = self.path.parent
        self.measurement_file = None
        self.directory_cuts = None
        self.directory_data = None

        if run is None:
            self.run = Run()
        else:
            self.run = run

        if detector is None:
            # Detector will be saved when self.to_file is called so
            # save_on_creation is false here
            self.detector = Detector(
                self.directory / "Detector" / "measurement.detector",
                self.get_measurement_file(),
                save_on_creation=False)
        else:
            self.detector = detector

        if target is None:
            self.target = Target()
        else:
            self.target = target

        self.selector = None

        self.use_default_profile_settings = use_default_profile_settings

        if save_on_creation:
            self.to_file()

    def get_detector_or_default(self) -> Detector:
        """Get measurement specific detector of default.

        Return:
            A Detector.
        """
        detector, *_ = self._get_used_settings()
        return detector

    def get_measurement_file(self) -> Path:
        """Returns the path to .measurement file that contains the settings
        of this Measurement.
        """
        return Path(self.path.parent,
                    f"{self.measurement_setting_file_name}.measurement")

    def update_folders_and_selector(self, selector_cls=None):
        """Update folders and selector. Initializes a new selector if
        selector_cls argument is given.

        Args:
            selector_cls: class of the selector.
        """
        for entry in os.scandir(self.directory):
            # TODO if the directory we are looking for does not exist (for
            #  example "Energy_spectra", this will cause a crash later on
            #  as self.directory_energy_spectra remains None. Maybe initialize
            #  some default values for each folder
            # TODO it makes little sense to just iterate all these
            path = Path(entry.path)
            if path.name == "Data":
                self.directory_data = path
                for e in os.scandir(path):
                    p = Path(e.path)
                    if p.suffix == ".asc":
                        self.measurement_file = p
                    elif p.name == "Cuts":
                        self.directory_cuts = p

        self.set_loggers(self.directory, self.request.directory)

        element_colors = self.request.global_settings.get_element_colors()
        if selector_cls is not None:
            self.selector = selector_cls(self, element_colors)

    def update_directory_references(self, new_dir: Path):
        """Update directory references.

        Args:
            new_dir: Path to measurement folder with new name.
        """
        self.directory = new_dir
        self.directory_data = Path(self.directory, "Data")
        self.directory_cuts = Path(self.directory_data, "Cuts")

        self.detector.update_directory_references(self)

        self.selector.update_references(self)

        self.set_loggers(self.directory, self.request.directory)

    @staticmethod
    def find_measurement_files(directory: Path):
        res = gf.find_files_by_extension(
            directory, ".profile", ".measurement", ".target")
        try:
            det_res = gf.find_files_by_extension(
                directory / "Detector", ".detector")
        except OSError:
            det_res = {".detector": []}

        if res[".profile"]:
            profile_file = res[".profile"][0]
        else:
            profile_file = None

        if res[".measurement"]:
            measurement_file = res[".measurement"][0]
        else:
            measurement_file = None

        if res[".target"]:
            target_file = res[".target"][0]
        else:
            target_file = None

        if det_res[".detector"]:
            detector_file = det_res[".detector"][0]
        else:
            detector_file = None

        mesu_files = namedtuple(
            "Measurement_files",
            ("profile", "measurement", "target", "detector"))
        return mesu_files(
            profile_file, measurement_file, target_file, detector_file)

    @classmethod
    def from_file(cls, info_file: Path, measurement_file: Path,
                  profile_file: Path, request, detector=None, run=None,
                  target=None, sample=None):
        """Read Measurement information from file.

        Args:
            info_file: Path to .info file.
            measurement_file: Path to .measurement file.
            profile_file: Path to .profile file.
            request: Request that the Measurement belongs to.
            detector: Measurement's Detector object.
            run: Measurement's Run object.
            target: Measurement's Target object.
            sample: Sample under which this Measurement belongs to.

        Return:
            Measurement object.
        """
        with info_file.open("r") as mesu_info:
            obj_info = json.load(mesu_info)
        obj_info["modification_time"] = obj_info.pop("modification_time_unix")

        try:
            with measurement_file.open("r") as mesu_file:
                obj_gen = json.load(mesu_file)["general"]

            mesu_general = {
                "measurement_setting_file_name": obj_gen["name"],
                "measurement_setting_file_description": obj_gen["description"],
                "measurement_setting_modification_time": obj_gen[
                    "modification_time_unix"
                ]
            }
        except (OSError, KeyError, AttributeError) as e:
            logging.getLogger("request").error(
                f"Failed to read settings from file {measurement_file}: "
                f"{e}"
            )
            mesu_general = {}

        try:
            with profile_file.open("r") as prof_file:
                obj_prof = json.load(prof_file)

            prof_gen = {
                "profile_name": obj_prof["general"]["name"],
                "profile_description": obj_prof["general"]["description"],
                "profile_modification_time": obj_prof["general"][
                    "modification_time_unix"]
            }

            depth = obj_prof["depth_profiles"]

            channel_width = obj_prof["energy_spectra"]["channel_width"]

            comp = obj_prof["composition_changes"]

            if obj_prof["general"]["use_default_settings"] == "True":
                use_default_profile_settings = True
            else:
                use_default_profile_settings = False

        except (OSError, KeyError, AttributeError, json.JSONDecodeError) as e:
            logging.getLogger("request").error(
                f"Failed to read settings from file {profile_file}: {e}"
            )
            measurement = request.default_measurement
            if measurement is None:
                return cls(request=request, path=info_file,
                           **mesu_general, use_default_profile_settings=True)
            prof_gen = {
                "profile_name": measurement.profile_name,
                "profile_description": measurement.profile_description,
                "profile_modification_time":
                    measurement.profile_modification_time,
            }

            depth = {
                "number_of_depth_steps": measurement.number_of_depth_steps,
                "depth_step_for_stopping": measurement.depth_step_for_stopping,
                "depth_step_for_output": measurement.depth_step_for_output,
                "depth_for_concentration_from":
                    measurement.depth_for_concentration_from,
                "depth_for_concentration_to":
                    measurement.depth_for_concentration_to
            }
            channel_width = measurement.channel_width
            comp = {
                "reference_cut": measurement.reference_cut,
                "number_of_splits": measurement.number_of_splits,
                "normalization": measurement.normalization,
                "reference_density": measurement.reference_density,
            }

            use_default_profile_settings = True

        return cls(
            request=request, path=info_file, run=run,
            detector=detector, target=target, channel_width=channel_width,
            **obj_info, **prof_gen, **depth, **comp, **mesu_general,
            use_default_profile_settings=use_default_profile_settings,
            sample=sample)

    def get_energy_spectra_dir(self) -> Path:
        """Returns the path to energy spectra directory.
        """
        return self.directory / "Energy_spectra"

    def get_depth_profile_dir(self) -> Path:
        """Returns the path to depth profile directory.
        """
        return self.directory / "Depth_profiles"

    def get_composition_changes_dir(self) -> Path:
        """Returns the path to composition changes directory.
        """
        return self.directory / "Composition_changes"

    def get_changes_dir(self):
        """Returns the path to 'Composition_changes/Changes directory.
        """
        return self.get_composition_changes_dir() / "Changes"

    def _get_measurement_file(self) -> Path:
        """Returns the path to .measuremnent file.
        """
        return Path(
            self.directory, f"{self.measurement_setting_file_name}.measurement")

    def _get_profile_file(self) -> Path:
        """Returns the path to .profile file
        """
        return self.directory / f"{self.profile_name}.profile"

    def _get_tof_in_dir(self) -> Path:
        """Returns the directory where tof.in is located.
        """
        return self.directory / "tof_in"

    def _get_info_file(self) -> Path:
        return self.directory / f"{self.name}.info"

    def to_file(self, measurement_file: Optional[Path] = None,
                profile_file: Optional[Path] = None,
                info_file: Optional[Path] = None):
        """Writes measurement to file. If optional path arguments are 'None',
        default values will be used as file names.

        Args:
            measurement_file: path to .measurement file
            profile_file: path to .profile file
            info_file: path to .info file
        """
        # Save general measurement settings parameters.
        if measurement_file is None:
            measurement_file = self._get_measurement_file()

        self._measurement_to_file(measurement_file)
        self._profile_to_file(profile_file)
        self._info_to_file(info_file)

        # Save run, detector and target parameters

        self.run.to_file(measurement_file)
        self.detector.to_file(self.detector.path, measurement_file)
        target_file = Path(self.directory, f"{self.target.name}.target")
        self.target.to_file(target_file, measurement_file)

    def _measurement_to_file(self, measurement_file: Optional[Path] = None):
        """Write a .measurement file.

        Args:
            measurement_file: Path to .measurement file.
        """
        if measurement_file is None:
            measurement_file = self._get_measurement_file()

        if measurement_file.exists():
            with measurement_file.open("r") as mesu:
                obj_measurement = json.load(mesu)
        else:
            obj_measurement = {}

        time_stamp = time.time()
        obj_measurement["general"] = {}

        obj_measurement["general"]["name"] = self.measurement_setting_file_name
        obj_measurement["general"]["description"] = \
            self.measurement_setting_file_description
        obj_measurement["general"]["modification_time"] = \
            time.strftime("%c %z %Z", time.localtime(time_stamp))
        obj_measurement["general"]["modification_time_unix"] = time_stamp

        with measurement_file.open("w") as file:
            json.dump(obj_measurement, file, indent=4)

    def _info_to_file(self, info_file: Optional[Path] = None):
        """Write an .info file.

        Args:
            info_file: Path to .info file.
        """
        if info_file is None:
            info_file = self._get_info_file()

        time_stamp = time.time()

        obj_info = {
            "name": self.name,
            "description": self.description,
            "modification_time": time.strftime("%c %z %Z",
                                               time.localtime(time_stamp)),
            "modification_time_unix": time_stamp
        }

        with info_file.open("w") as file:
            json.dump(obj_info, file, indent=4)

    def _profile_to_file(self, profile_file: Optional[Path] = None):
        """Write a .profile file.

        Args:
            profile_file: Path to .profile file.
        """
        if profile_file is None:
            profile_file = self._get_profile_file()

        obj_profile = {
            "general": {},
            "depth_profiles": {},
            "energy_spectra": {},
            "composition_changes": {}
        }

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

        with profile_file.open("w") as file:
            json.dump(obj_profile, file, indent=4)

    def create_folder_structure(self, measurement_folder: Path,
                                measurement_file: Path = None,
                                selector_cls=None):
        """ Creates folder structure for the measurement. If selector_cls is
        given, selector will be initialized as an object of that class.

        Args:
            measurement_folder: Path of the measurement folder.
            measurement_file: Path of the measurement file. (under Data)
            selector_cls: class of the selector.
        """
        # TODO refactor this and update_directory references
        if measurement_file is None:
            measurement_data_folder = measurement_folder / "Data"
            self.measurement_file = None
        else:
            measurement_data_folder = measurement_file.parent
            self.measurement_file = measurement_file.name  # With extension

        self.directory = measurement_folder
        self.directory_data = measurement_data_folder
        self.directory_cuts = self.directory_data / "Cuts"

        self.__make_directories(self.directory)
        self.__make_directories(self.directory_data)
        self.__make_directories(self.directory_cuts)
        self.__make_directories(self.get_composition_changes_dir())
        self.__make_directories(self.get_changes_dir())
        self.__make_directories(self.get_depth_profile_dir())
        self.__make_directories(self.get_energy_spectra_dir())
        self.__make_directories(self._get_tof_in_dir())

        self.set_loggers(self.directory, self.request.directory)

        element_colors = self.request.global_settings.get_element_colors()
        if selector_cls is not None:
            self.selector = selector_cls(self, element_colors)

    def __make_directories(self, directory):
        """Make directories.

        Args:
            directory: Directory to be made under measurement.
        """
        new_dir = Path(self.directory, directory)
        if not new_dir.exists():
            try:
                new_dir.mkdir()
                log = f"Created a directory {new_dir}."
                logging.getLogger("request").info(log)
            except OSError as e:
                logging.getLogger("request").error(
                    f"Failed to create a directory: {e}."
                )

    def copy_file_into_measurement(self, file_path):
        """Copies the given file into the measurement's data folder

        Args:
            file_path: The file that needs to be copied.
        """
        file_name = os.path.basename(file_path)
        new_path = Path(self.directory, self.directory_data, file_name)
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
                file_to_open = Path(
                    self.directory, self.directory_data,
                    f"{measurement_name}.asc")
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
            error_log = "Unexpected error: {0}".format(e)
            logging.getLogger('request').error(error_log)
        # pr.disable()
        # ps = pstats.Stats(pr)
        # ps.sort_stats("time")
        # ps.print_stats(10)

    def rename_info_file(self, new_name):
        """Renames the measurement data file.
        """
        try:
            self._get_info_file().unlink()
        except OSError:
            pass
        self.name = new_name
        self._info_to_file()

    def rename_files_in_directory(self, directory: Path):
        if not directory.exists():
            return
        for file in os.listdir(directory):
            if file.endswith(".cut"):
                old_path = Path(directory, file)
                # Get everything except old measurement name from cut file
                new_name = self.name + "." + file.split('.', 1)[1]
                gf.rename_file(old_path, new_name)

    def set_axes(self, axes, progress=None):
        """Set axes information to selector within measurement.
        
        Sets axes information to selector to add selection points. Since 
        previously when creating measurement old selection could not be checked.
        Now is time to check for it, while data is still "loading".
        
        Args:
            axes: Matplotlib FigureCanvas's subplot
            progress: ProgressReporter object
        """
        self.selector.axes = axes
        # We've set axes information, check for old selection.
        self.__check_for_old_selection(progress)

    def __check_for_old_selection(self, progress=None):
        """Use old selection file_path if exists.

        Args:
            progress: ProgressReporter object
        """
        try:
            selection_file = Path(self.directory, self.directory_data,
                                  "{0}.selections".format(self.name))
            with open(selection_file):
                self.load_selection(selection_file, progress)
        except OSError:
            # TODO: Is it necessary to inform user with this?
            # FIXME crashes here when:
            #       1. user deletes all measurements from a sample
            #       2. user imports new .evnt file
            #       3. user tries to open the imported data
            log_msg = "There was no old selection file to add to this " \
                      f"request."
            logging.getLogger(self.name).info(log_msg)

    def add_point(self, point, canvas):
        """Add point into selection or create new selection if first or all
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
        """Purges (removes) all open selections and allows new selection to be
        made.
        """
        self.selector.purge()

    def remove_all(self):
        """Remove all selections in selector.
        """
        self.selector.remove_all()

    def draw_selection(self):
        """Draw all selections in measurement.
        """
        self.selector.draw()

    def end_open_selection(self, canvas):
        """End last open selection.
        
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
        """Select a selection based on point.
        
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
        """Get count of selections.
        
        Return:
            Returns the count of selections in selector object.
        """
        return self.selector.count()

    def reset_select(self):
        """Reset selection to None.
        
        Resets current selection to None and resets colors of all selections
        to their default values. 
        """
        self.selector.reset_select()

    def remove_selected(self):
        """Remove selection
        
        Removes currently selected selection.
        """
        self.selector.remove_selected()

    def save_cuts(self, progress=None):
        """Save cut files
        
        Saves data points within selections into cut files.
        """
        if self.selector.is_empty():
            self.__remove_old_cut_files()
            # Remove .selections file
            selection_file = Path(self.directory_data,
                                  f"{self.name}.selections")
            try:
                os.remove(selection_file)
            except OSError:
                pass
            return 0

        self.__make_directories(self.directory_cuts)

        starttime = time.time()

        self.__remove_old_cut_files()

        # Initializes the list size to match the number of selections.
        points_in_selection = [[] for _ in range(self.selector.count())]

        # Go through all points in measurement data
        data_count = len(self.data)
        for n in range(data_count):  # while n < data_count: 
            if n % 5000 == 0:
                # Do not always update UI to make it faster.
                if progress is not None:
                    progress.report(n / data_count * 80)
            point = self.data[n]
            # Check if point is within selectors' limits for faster processing.
            if not self.selector.axes_limits.is_inside(point):
                continue

            for i, selection in enumerate(self.selector.selections):
                if selection.point_inside(point):
                    points_in_selection[i].append(point)

        # Save all found data points into appropriate element cut files
        # Firstly clear old cut files so those won't be accidentally
        # left there.
        if progress is not None:
            progress.report(80)

        content_length = len(points_in_selection)
        for i, points in enumerate(points_in_selection):
            if points:  # If not empty selection -> save
                selection = self.selector.get_at(i)
                cut_file = CutFile(Path(self.directory, self.directory_cuts))
                cut_file.set_info(selection, points)
                cut_file.save()
            if progress is not None:
                progress.report(80 + (i / content_length) * 0.2)

        if progress is not None:
            progress.report(100)

        log_msg = f"Saving finished in {time.time() - starttime} seconds."
        logging.getLogger(self.name).info(log_msg)

    def __remove_old_cut_files(self):
        """Remove old cut files.
        """
        gf.remove_matching_files(self.directory_cuts, exts={".cut"})
        directory_changes = self.get_changes_dir()
        gf.remove_matching_files(directory_changes, exts={".cut"})

    def get_cut_files(self):
        """Get cut files from a measurement.
        
        Return:
            Returns a list of cut files in measurement.
        """
        cuts = [f for f in os.listdir(Path(self.directory, self.directory_cuts))
                if os.path.isfile(Path(self.directory, self.directory_cuts, f))]
        elemloss = [f for f in os.listdir(self.get_changes_dir())
                    if os.path.isfile(Path(self.get_changes_dir(), f))]
        return cuts, elemloss

    def load_selection(self, filename, progress=None):
        """Load selections from a file_path.
        
        Removes all current selections and loads selections from given filename.
        
        Args:
            filename: String representing (full) directory to selection
            file_path.
            progress: ProgressReporter object
        """
        self.selector.load(filename, progress=progress)

    def _get_used_settings(self):
        if self.use_default_profile_settings:
            detector = self.request.default_detector
            run = self.request.default_run
            target = self.request.default_target
            mesu = self.request.default_measurement
        else:
            detector = self.detector
            run = self.run
            target = self.target
            mesu = self
        return detector, run, target, mesu

    def generate_tof_in(self, no_foil: bool = False, directory: Path = None) \
            -> Path:
        """Generate tof.in file for external programs.

        Generates tof.in file for measurement to be used in external programs
        (tof_list, erd_depth). By default,q the file is written to measurement
        folder.

        Args:
            no_foil: overrides the thickness of foil by setting it to 0
            directory: directory in which the tof.in is saved

        Return:
            path to generated tof.in file
        """
        # TODO refactor this into smaller functions
        if directory is None:
            tof_in_file = self._get_tof_in_dir() / "tof.in"
        else:
            tof_in_file = directory / "tof.in"

        tof_in_file.parent.mkdir(exist_ok=True)

        # Get settings
        # TODO self.detector and other stuff should never be None. Instead,
        #   we should check whether measurement settings are being used and
        #   then select the correct detector
        detector, run, target, measurement = self._get_used_settings()
        global_settings = self.request.global_settings

        reference_density = measurement.reference_density
        number_of_depth_steps = measurement.number_of_depth_steps
        depth_step_for_stopping = measurement.depth_step_for_stopping
        depth_step_for_output = measurement.depth_step_for_output
        depth_for_concentration_from = measurement.depth_for_concentration_from
        depth_for_concentration_to = measurement.depth_for_concentration_to

        # Measurement settings
        str_beam = f"Beam: {run.beam.ion}\n"
        str_energy = f"Energy: {run.beam.energy}\n"
        str_detector = f"Detector angle: {detector.detector_theta}\n"
        str_target = f"Target angle: {target.target_theta}\n"

        time_of_flight_length = 0
        i = len(detector.tof_foils) - 1
        while i - 1 >= 0:
            time_of_flight_length = detector.foils[
                                        detector.tof_foils[i]].distance - \
                                    detector.foils[
                                        detector.tof_foils[i - 1]].distance
            i = i - 1

        time_of_flight_length = time_of_flight_length / 1000
        str_toflen = f"Toflen: {time_of_flight_length}\n"

        # Timing foil can only be carbon and have one layer!!!
        if no_foil:
            # no_foil parameter is used when energy spectra is generated from
            # .tof_list files in simulation mode. Foil thickness is set to 0
            # to make MCERD energy spectra and experimental energy spectra
            # comparable
            carbon_foil_thickness = 0
        else:
            carbon_foil_thickness_in_nm = 0
            layer = detector.foils[detector.tof_foils[0]].layers[0]
            carbon_foil_thickness_in_nm += layer.thickness  # first layer only
            density_in_g_per_cm3 = layer.density
            # density in ug_per_cm2
            carbon_foil_thickness = carbon_foil_thickness_in_nm * \
                density_in_g_per_cm3 * 6.0221409e+23 * \
                1.660548782e-27 * 100

        str_carbon = f"Carbon foil thickness: {carbon_foil_thickness}\n"
        str_density = f"Target density: {reference_density}\n"

        # Depth Profile settings
        str_depthnumber = f"Number of depth steps: {number_of_depth_steps}\n"
        str_depthstop = f"Depth step for stopping: {depth_step_for_stopping}\n"
        str_depthout = f"Depth step for output: {depth_step_for_output}\n"
        str_depthscale = f"Depths for concentration scaling: " \
                         f"{depth_for_concentration_from} " \
                         f"{depth_for_concentration_to}\n"

        # Cross section
        flag_cross = int(global_settings.get_cross_sections())
        str_cross = f"Cross section: {flag_cross}\n"
        # Cross Sections: 1=Rutherford, 2=L'Ecuyer, 3=Andersen

        str_num_iterations = f"Number of iterations: " \
                             f"{global_settings.get_num_iterations()}\n"

        # Efficiency file handling
        detector.copy_efficiency_files()

        str_eff_dir = "Efficiency directory: {0}".format(
            detector.get_used_efficiencies_dir())

        # Combine strings
        measurement = str_beam + str_energy + str_detector + str_target + \
            str_toflen + str_carbon + str_density
        calibration = f"TOF calibration: {detector.tof_slope} " \
                      f"{detector.tof_offset}\n"
        anglecalib = f"Angle calibration: {detector.angle_slope} " \
                     f"{detector.angle_offset}\n"
        depthprofile = str_depthnumber + str_depthstop + str_depthout + \
            str_depthscale

        tof_in = measurement + calibration + anglecalib + depthprofile + \
            str_cross + str_num_iterations + str_eff_dir

        # Get md5 of file and new settings
        md5 = hashlib.md5()
        md5.update(tof_in.encode('utf8'))
        digest = md5.digest()
        digest_file = None
        try:
            with tof_in_file.open("r") as f:
                digest_file = gf.md5_for_file(f)
        except OSError:
            pass

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
            except Exception as e:
                if not isinstance(e, FileNotFoundError):
                    error_msg = f"Error when generating tof.in: {e}"
                    logging.getLogger(self.name).error(error_msg)
            # Write new settings to the file.
            with tof_in_file.open("w") as fp:
                fp.write(tof_in)
            str_logmsg = "Generated tof.in with params> {0}". \
                format(tof_in.replace("\n", "; "))
            logging.getLogger(self.name).info(str_logmsg)

        return tof_in_file

    @staticmethod
    def _get_attrs() -> set:
        """Returns a set of attribute names. These Measument attribute values
        can be set by calling set_settings.
        """
        return {
            "profile_name", "profile_description",
            "profile_modification_time", "reference_density",
            "number_of_depth_steps", "depth_step_for_stopping",
            "depth_step_for_output", "depth_for_concentration_from",
            "depth_for_concentration_to", "channel_width", "number_of_splits",
            "normalization"
        }

    def get_settings(self) -> dict:
        """Returns the values of this Measurement's settings
        """
        return {
            attr: getattr(self, attr) for attr in self._get_attrs()
        }

    def set_settings(self, **kwargs):
        """Sets the values of this Measurement's settings.
        """
        attrs = self._get_attrs()
        for key, value in kwargs.items():
            if key in attrs:
                setattr(self, key, value)
