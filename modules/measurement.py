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

__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen " \
             "\n Samuli Rahkonen \n Miika Raunio \n Severi Jääskeläinen \n " \
             "Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen \n " \
             "Juhani Sundell \n Tuomas Pitkänen"
__version__ = "2.0"

import hashlib
import json
import logging
import os
import shutil
import time
import itertools

from pathlib import Path
from collections import namedtuple
from typing import Optional
from typing import List
from typing import Tuple

from . import general_functions as gf
from . import file_paths as fpaths
from .cut_file import CutFile
from .detector import Detector
from .profile import Profile
from .run import Run
from .target import Target
from .ui_log_handlers import MeasurementLogger
from .base import Serializable


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

    def add_measurement_file(self, sample: "Sample", file_path: Path, tab_id,
                             name, import_evnt_or_binary, selector_cls=None):
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
            mesu_file = measurement_directory / f"{name}.info"
            measurement = Measurement(
                self.request, mesu_file, tab_id, name, sample=sample)

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
                target = Target.from_file(tgt_file, self.request)
            else:
                target = None

            if det_file is not None:
                detector = Detector.from_file(
                    det_file, self.request, save_on_creation=False)
                detector.update_directories(det_file.parent)
            else:
                detector = None

            if mesu_file is not None:
                run = Run.from_file(mesu_file)
            else:
                run = None

            if profile_file is not None:
                profile = Profile.from_file(profile_file)
            else:
                profile = None

            # Create Measurement from file
            if file_path.exists() and file_path.suffix == ".info":
                measurement = Measurement.from_file(
                    file_path, mesu_file, self.request, sample=sample,
                    target=target, detector=detector, run=run, profile=profile)

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
                            measurement_directory, measurement.get_data_dir()) \
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


class Measurement(MeasurementLogger, Serializable):
    """Measurement class to handle one measurement data.
    """

    __slots__ = "request", "tab_id", "name", "description",\
                "modification_time", "run", "detector", "target", \
                "profile", "path", "sample", "measurement_setting_file_name", \
                "measurement_setting_file_description", "serial_number", \
                "measurement_setting_modification_time", "data", \
                "measurement_file", "directory", "use_request_settings", \
                "selector"

    DIRECTORY_PREFIX = "Measurement_"

    def __init__(self, request, path, tab_id=-1, name="Default",
                 description="", modification_time=None, run=None,
                 detector=None, target=None, profile=None,
                 measurement_setting_file_name="Default",
                 measurement_setting_file_description="",
                 measurement_setting_modification_time=None,
                 use_request_settings=True, sample=None,
                 save_on_creation=True, enable_logging=True):
        """Initializes a measurement.

        Args:
            request: Request class object.
            path: Full path to measurement's .info file.
        """
        # Run the base class initializer to establish logging
        MeasurementLogger.__init__(self, enable_logging=enable_logging)
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
        self.measurement_setting_file_description = \
            measurement_setting_file_description
        if not measurement_setting_modification_time:
            measurement_setting_modification_time = time.time()
        self.measurement_setting_modification_time = \
            measurement_setting_modification_time

        self.data = []

        self.serial_number = 0
        self.directory = self.path.parent
        # TODO rename this to data_file
        self.measurement_file = None

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
            # TODO: Is target used for anything other than displaying
            #       target_theta in settings?
            self.target = self.request.copy_default_target()
        else:
            self.target = target

        if profile is None:
            self.profile = self.request.copy_default_profile()
        else:
            self.profile = profile

        # TODO: Should this be copied from default?
        self.selector = None

        self.use_request_settings = use_request_settings

        if save_on_creation:
            self.to_file()

    def get_detector_or_default(self) -> Detector:
        """Get measurement specific detector of default.

        Return:
            A Detector.
        """
        detector, *_ = self.get_used_settings()
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
        with os.scandir(self.get_data_dir()) as scdir:
            for entry in scdir:
                path = Path(entry.path)
                if path.is_file() and path.suffix == ".asc":
                    self.measurement_file = path
                    break

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

        self.detector.update_directory_references(self)

        if self.selector is not None:
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
    def from_file(
            cls,
            info_file: Path,
            measurement_file: Path,
            request: "Request",
            detector: Optional[Detector] = None,
            run: Optional[Run] = None,
            target: Optional[Target] = None,
            profile: Optional[Profile] = None,
            sample: Optional["Sample"] = None) -> "Measurement":
        """Read Measurement information from file.

        Args:
            info_file: Path to .info file.
            measurement_file: Path to .measurement file.
            request: Request that the Measurement belongs to.
            detector: Measurement's Detector object.
            run: Measurement's Run object.
            target: Measurement's Target object.
            profile: Measurement's Profile object.
            sample: Sample under which this Measurement belongs to.

        Return:
            Measurement object.
        """
        with info_file.open("r") as mesu_info:
            obj_info = json.load(mesu_info)
        obj_info["modification_time"] = obj_info.pop("modification_time_unix")

        if measurement_file is not None:
            try:
                with measurement_file.open("r") as mesu_file:
                    obj_gen = json.load(mesu_file)["general"]

                mesu_general = {
                    "measurement_setting_file_name": obj_gen["name"],
                    "measurement_setting_file_description":
                        obj_gen["description"],
                    "measurement_setting_modification_time":
                        obj_gen["modification_time_unix"]
                }
            except (OSError, KeyError, AttributeError) as e:
                logging.getLogger("request").error(
                    f"Failed to read settings from .measurement file "
                    f"{measurement_file}: {e}"
                )
                mesu_general = {}
        else:
            mesu_general = {}

        return cls(
            request=request, path=info_file, run=run,
            detector=detector, target=target, profile=profile,
            **obj_info, **mesu_general, sample=sample)

    def get_data_dir(self) -> Path:
        """Returns path to Data directory.
        """
        return self.directory / "Data"

    def get_cuts_dir(self) -> Path:
        """Returns path to Cuts directory.
        """
        return self.get_data_dir() / "Cuts"

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

    def _get_tof_in_dir(self) -> Path:
        """Returns the directory where tof.in is located.
        """
        return self.directory / "tof_in"

    def _get_info_file(self) -> Path:
        """Returns the path to this Measurment's .info file.
        """
        return self.directory / f"{self.name}.info"

    def to_file(self, measurement_file: Optional[Path] = None,
                info_file: Optional[Path] = None):
        """Writes measurement to file.

        If optional path arguments are 'None', default values will be
        used as file names. Settings will not be saved if
        self.use_request_settings is True.

        Args:
            measurement_file: path to .measurement file
            info_file: path to .info file
        """
        self._info_to_file(info_file)

        if not self.use_request_settings:
            if measurement_file is None:
                measurement_file = self._get_measurement_file()
            target_file = Path(self.directory, f"{self.target.name}.target")
            profile_file = Path(self.directory / f"{self.profile.name}.profile")

            self._measurement_to_file(measurement_file)
            self.run.to_file(measurement_file)
            self.detector.to_file(self.detector.path)
            self.target.to_file(target_file)
            self.profile.to_file(profile_file)

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
            "modification_time_unix": time_stamp,
            "use_request_settings": self.use_request_settings
        }

        with info_file.open("w") as file:
            json.dump(obj_info, file, indent=4)

    def create_folder_structure(self, measurement_folder: Path,
                                measurement_file: Path = None,
                                selector_cls=None):
        """Creates folder structure for the measurement. If selector_cls is
        given, selector will be initialized as an object of that class.

        Args:
            measurement_folder: Path of the measurement folder.
            measurement_file: Path of the measurement file. (under Data)
            selector_cls: class of the selector.
        """
        self.directory = measurement_folder
        self.measurement_file = measurement_file

        self.__make_directories(self.directory)
        self.__make_directories(self.get_data_dir())
        self.__make_directories(self.get_cuts_dir())
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

    def copy_file_into_measurement(self, file_path: Path):
        """Copies the given file into the measurement's data folder

        Args:
            file_path: The file that needs to be copied.
        """
        file_name = file_path.name
        new_path = self.get_data_dir() / file_name
        shutil.copyfile(file_path, new_path)

    def load_data(self):
        """Loads measurement data from filepath
        """
        n = 0
        try:
            filename = Path(self.measurement_file)

            measurement_name, extension = filename.stem, filename.suffix.lower()
            if extension == ".asc":
                file_to_open = self.get_data_dir() / f"{measurement_name}.asc"
                with file_to_open.open("r") as fp:
                    for line in fp:
                        n += 1  # Event number
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

    def get_available_asc_file_name(self, new_name: str) -> Path:
        """Returns an .asc file name that does not already exist.
        """
        def file_name_generator():
            yield self.get_data_dir() / f"{new_name}.asc"
            for i in itertools.count(start=2):
                yield self.get_data_dir() / f"{new_name}-{i}.asc"

        return fpaths.find_available_file_path(file_name_generator())

    def rename(self, new_name: str):
        """Renames Measurement with given name and updates folders and cut
        files.
        """
        # TODO should this also rename spectra files?
        gf.rename_entity(self, new_name)
        try:
            self.rename_info_file()
        except OSError as e:
            e.args = f"Failed to rename info file: {e}",
            raise
        try:
            self.rename_cut_files()
        except OSError as e:
            e.args = f"Failed to rename .cut files: {e}",
            raise

    def rename_info_file(self):
        """Renames the measurement data file.
        """
        # Remove existing files and create a new one
        gf.remove_matching_files(self.directory, exts={".info"})
        self._info_to_file()

    def rename_cut_files(self):
        """Renames .cut files with the new measurement name.
        """
        cuts, splits = self.get_cut_files()
        for cut in (*cuts, *splits):
            new_name = self.name + "." + cut.name.split(".", 1)[1]
            gf.rename_file(cut, new_name)

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
            selection_file = self.get_data_dir() / f"{self.name}.selections"
            with selection_file.open("r"):
                self.load_selection(selection_file, progress)
        except OSError:
            log_msg = "There was no old selection file to add to this " \
                      f"request."
            self.log(log_msg)

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
            selection_file = self.get_data_dir() / f"{self.name}.selections"
            gf.remove_files(selection_file)
            return 0

        self.__make_directories(self.get_cuts_dir())

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

        self.selector.update_selection_beams()
        self.selector.auto_save()

        # Save all found data points into appropriate element cut files
        # Firstly clear old cut files so those won't be accidentally
        # left there.
        if progress is not None:
            progress.report(80)

        content_length = len(points_in_selection)
        for i, points in enumerate(points_in_selection):
            if points:  # If not empty selection -> save
                selection = self.selector.get_at(i)
                cut_file = CutFile(self.get_cuts_dir())
                cut_file.set_info(selection, points)
                cut_file.save()
            if progress is not None:
                progress.report(80 + (i / content_length) * 0.2)

        if progress is not None:
            progress.report(100)

        log_msg = f"Saving finished in {time.time() - starttime} seconds."
        self.log(log_msg)

    def __remove_old_cut_files(self):
        """Remove old cut files.
        """
        gf.remove_matching_files(self.get_cuts_dir(), exts={".cut"})
        gf.remove_matching_files(self.get_changes_dir(), exts={".cut"})

    @staticmethod
    def _get_cut_files(directory: Path) -> List[Path]:
        try:
            return gf.find_files_by_extension(directory, ".cut")[".cut"]
        except OSError:
            return []

    def get_cut_files(self) -> Tuple[List[Path], List[Path]]:
        """Get cut files from a measurement.
        
        Return:
            Returns a list of cut files in measurement.
        """
        cuts = self._get_cut_files(self.get_cuts_dir())
        elem_losses = self._get_cut_files(self.get_changes_dir())
        return cuts, elem_losses

    def load_selection(self, filename, progress=None):
        """Load selections from a file_path.
        
        Removes all current selections and loads selections from given filename.
        
        Args:
            filename: String representing (full) directory to selection
            file_path.
            progress: ProgressReporter object
        """
        self.selector.load(filename, progress=progress)

    def get_used_settings(
            self) -> Tuple[Detector, Run, Target, Profile, "Measurement"]:
        if self.use_request_settings:
            detector = self.request.default_detector
            run = self.request.default_run
            target = self.request.default_target
            profile = self.request.default_profile
            mesu = self.request.default_measurement
        else:
            detector = self.detector
            run = self.run
            target = self.target
            profile = self.profile
            mesu = self
        return detector, run, target, profile, mesu

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
        detector, run, target, profile, measurement = self.get_used_settings()
        global_settings = self.request.global_settings

        reference_density = profile.reference_density
        number_of_depth_steps = profile.number_of_depth_steps
        depth_step_for_stopping = profile.depth_step_for_stopping
        depth_step_for_output = profile.depth_step_for_output
        depth_for_concentration_from = profile.depth_for_concentration_from
        depth_for_concentration_to = profile.depth_for_concentration_to

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
        detector.copy_efficiency_files_for_tof_list()

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
                self.log(back_up_msg)
            except Exception as e:
                if not isinstance(e, FileNotFoundError):
                    error_msg = f"Error when generating tof.in: {e}"
                    self.log_error(error_msg)
            # Write new settings to the file.
            with tof_in_file.open("w") as fp:
                fp.write(tof_in)
            str_logmsg = f"Generated tof.in with params> {0}". \
                format(tof_in.replace("\n", "; "))
            self.log(str_logmsg)

        return tof_in_file

    def clone_request_settings(self, save_on_creation=False) -> None:
        """Clone settings from request."""
        self.run = self.request.copy_default_run()
        self.detector = self.request.copy_default_detector(
            self.directory, save_on_creation=save_on_creation)
        self.target = self.request.copy_default_target()
        self.profile = self.request.copy_default_profile()
