# coding=utf-8
"""
Created on 15.3.2013
Updated on 4.5.2018

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) Jarkko Aalto, Timo Konu, Samuli Kärkkäinen, Samuli Rahkonen and
Miika Raunio

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
import datetime

from modules.element import Element

__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen " \
             "\n Samuli Rahkonen \n Miika Raunio \n Severi Jääskeläinen \n " \
             "Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"
__version__ = "2.0"

import json
import logging

import hashlib
import os
import shutil
import sys
import time
from PyQt5 import QtCore, QtWidgets

from modules.beam import Beam
from modules.cut_file import CutFile
from modules.detector import Detector
from modules.general_functions import md5_for_file, save_settings, rename_file
from modules.run import Run
from modules.selection import Selector
from modules.settings import Settings
from modules.target import Target


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
        if key not in self.measurements:
            return None
        return self.measurements[key]

    def add_measurement_file(self, sample, measurement_file, tab_id):
        """Add a new file to measurements.

        Args:
            sample: The sample under which the measurement is put.
            measurement_file: String representing file containing measurement
                                  data.
            tab_id: Integer representing identifier for measurement's tab.

        Return:
            Returns new measurement or None if it wasn't added
        """
        try:
            measurement_filename = os.path.split(measurement_file)[1]
            measurement_name = os.path.splitext(measurement_filename)
            file_directory, file_name = os.path.split(measurement_file)

            # Check if measurement on the same name already exists.
            for key in sample.measurements.measurements.keys():
                if sample.measurements.measurements[key].measurement_file \
                        == file_name:
                    return None

            # Create new Measurement object.
            measurement = Measurement(self.request, tab_id=tab_id,
                                      name=measurement_name[0])
            measurement.serial_number = sample.get_running_int_measurement()
            # TODO Can increasing the int be handled by sample?
            sample.increase_running_int_measurement_by_1()

            # Create path for measurement directory.
            measurement_directory = os.path.join(self.request.directory,
                                                 sample.directory,
                                                 measurement.name_prefix
                                                 + "%02d" %
                                                 measurement.serial_number +
                                                 "-" + measurement.name)

            # Create path for measurement file used by the program and create
            # folder structure.
            new_measurement_file = os.path.join(measurement_directory,
                                                "Data", measurement_filename)
            measurement.create_folder_structure(measurement_directory,
                                                new_measurement_file)
            if file_directory != os.path.join(measurement.directory,
                                              measurement.directory_data) and \
                    file_directory:
                measurement.copy_file_into_measurement(measurement_file)

            # Add Measurement to  Measurements.
            sample.measurements.measurements[tab_id] = measurement
            self.request.samples.measurements.measurements[tab_id] = measurement
        except:
            log = "Something went wrong while adding a new measurement."
            logging.getLogger("request").critical(log)
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


class Measurement:
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

    def __init__(self, request, tab_id=-1, name="Default",
                 description="This a default measurement.",
                 modification_time=time.time(), run=None, detector=None,
                 target=Target(), profile_name="Default",
                 profile_description="This is a default profile setting file.",
                 profile_modification_time=time.time(),
                 reference_density=3.5, number_of_depth_steps=40,
                 depth_step_for_stopping=50, depth_step_for_output=50,
                 depth_for_concentration_from=800,
                 depth_for_concentration_to=1500, channel_width=0.1,
                 reference_cut="", number_of_splits=10, normalization="first",
                 measurement_setting_file_name="Default",
                 measurement_setting_file_description=
                 "This a default measurement setting file."
                 ):
        """Initializes a measurement.

        Args:
            request: Request class object.
        """
        # TODO: Add missing attributes listed in class definition.
        self.tab_id = tab_id

        self.request = request  # To which request be belong to
        self.name = name
        self.description = description
        self.modification_time = modification_time

        self.run = run
        self.detector = detector
        self.target = target

        self.measurement_setting_file_name = measurement_setting_file_name
        self.measurement_setting_file_description = \
            measurement_setting_file_description

        self.profile_name = profile_name
        self.profile_description = profile_description
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

        self.measurement_file = None
        self.name_prefix = "Measurement_"
        self.serial_number = 0
        self.directory = request.default_folder
        self.directory_cuts = None
        self.directory_composition_changes = None
        self.directory_depth_profiles = None
        self.directory_energy_spectra = None
        self.directory_data = None

        self.__request_settings = None
        self.measurement_settings = None
        self.selector = None

        self.errorlog = None
        self.defaultlog = None

    @classmethod
    def from_file(cls, measurement_file_path, profile_file_path, request):

        obj_measurement = json.load(open(measurement_file_path))
        obj_profile = json.load(open(profile_file_path))

        name = obj_measurement["general"]["name"]
        description = obj_measurement["general"]["description"]
        modification_time = obj_measurement["general"]["modification_time_unix"]

        ion = Element.from_string(obj_measurement["beam"]["ion"])
        energy = obj_measurement["beam"]["energy"]
        energy_distribution = obj_measurement["beam"]["energy_distribution"]
        beam_charge = obj_measurement["beam"]["charge"]

        spot_size = tuple(obj_measurement["run"]["spot_size"])
        divergence = obj_measurement["run"]["divergence"]
        profile = obj_measurement["run"]["profile"]
        fluence = obj_measurement["run"]["fluence"]
        current = obj_measurement["run"]["current"]
        run_charge = obj_measurement["run"]["charge"]
        run_time = obj_measurement["run"]["time"]

        detector_theta = obj_measurement["geometry"]["detector_theta"]
        target_theta = obj_measurement["geometry"]["target_theta"]

        profile_name = obj_profile["general"]["name"]
        profile_description = obj_profile["general"]["description"]
        profile_modification_time = obj_profile["general"][
            "modification_time_unix"]

        reference_density = obj_profile["depth_profiles"]["reference_density"]
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

        beam = Beam(ion, energy, beam_charge, energy_distribution, spot_size,
                    divergence, profile)
        run = Run(beam, fluence, current, run_charge, run_time)

        detector = request.default_detector
        detector.detector_theta = detector_theta

        target = request.default_target
        target.target_theta = target_theta

        return cls(request=request, name=name, description=description,
            modification_time=modification_time,
            run=run, detector=detector,
            target=target, profile_name=profile_name,
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
            reference_density=reference_density)

    def to_file(self, measurement_file_path, profile_file_path):

        obj_measurement = {}
        obj_profile = {}

        obj_measurement["general"] = {}
        obj_measurement["beam"] = {}
        obj_measurement["run"] = {}
        obj_measurement["geometry"] = {}
        obj_profile["general"] = {}
        obj_profile["depth_profiles"] = {}
        obj_profile["energy_spectra"] = {}
        obj_profile["composition_changes"] = {}

        obj_measurement["general"]["name"] = self.measurement_setting_file_name
        obj_measurement["general"]["description"] = \
            self.measurement_setting_file_description
        obj_measurement["general"]["modification_time"] = str(datetime.datetime.fromtimestamp(
            time.time()))
        obj_measurement["general"]["modification_time_unix"] = time.time()

        obj_measurement["beam"]["ion"] = str(self.run.beam.ion)
        obj_measurement["beam"]["energy"] = self.run.beam.energy
        obj_measurement["beam"]["energy_distribution"] = \
            self.run.beam.energy_distribution
        obj_measurement["beam"]["charge"] = self.run.beam.charge
        obj_measurement["run"]["spot_size"] = self.run.beam.spot_size
        obj_measurement["run"]["divergence"] = self.run.beam.divergence
        obj_measurement["run"]["profile"] = self.run.beam.profile
        obj_measurement["run"]["fluence"] = self.run.fluence
        obj_measurement["run"]["current"] = self.run.current
        obj_measurement["run"]["charge"] = self.run.charge
        obj_measurement["run"]["time"] = self.run.time

        obj_measurement["geometry"]["detector_theta"] = \
            self.request.default_detector.detector_theta
        obj_measurement["geometry"]["target_theta"] = \
            self.request.default_target.target_theta

        obj_profile["general"]["name"] = self.profile_name
        obj_profile["general"]["description"] = \
            self.profile_description
        obj_profile["general"]["modification_time"] = str(
            datetime.datetime.fromtimestamp(time.time()))
        obj_profile["general"]["modification_time_unix"] = \
            self.profile_modification_time

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

        with open(measurement_file_path, "w") as file:
            json.dump(obj_measurement, file, indent=4)

        with open(profile_file_path, "w") as file:
            json.dump(obj_profile, file, indent=4)

    def create_folder_structure(self, measurement_folder, measurement_file):
        """ Creates folder structure for the measurement.

        Args:
            measurement_folder: Path of the measurement folder.
            measurement_file: Path of the measurement file. (under Data)
        """
        measurement_data_folder, measurement_name = \
            os.path.split(measurement_file)
        self.measurement_file = measurement_name  # With extension

        self.directory = measurement_folder
        self.directory_data = "Data"
        self.directory_cuts = os.path.join(self.directory_data, "Cuts")
        self.directory_composition_changes = os.path.join("Composition_changes")
        self.directory_depth_profiles = os.path.join("Depth_profiles")
        self.directory_energy_spectra = os.path.join("Energy spectra")

        self.__make_directories(self.directory)
        self.__make_directories(self.directory_data)
        self.__make_directories(self.directory_cuts)
        self.__make_directories(self.directory_composition_changes)
        self.__make_directories(self.directory_depth_profiles)
        self.__make_directories(self.directory_energy_spectra)

        self.set_loggers()

        # The settings that come from the request
        self.__request_settings = self.request.settings
        # The settings that are individually set for this measurement
        self.measurement_settings = Settings(self.directory,
                                             self.__request_settings)

        element_colors = self.request.global_settings.get_element_colors()
        self.selector = Selector(self, element_colors)

        # Which color scheme is selected by default
        self.color_scheme = "Default color"

    def __make_directories(self, directory):
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
            extension = os.path.splitext(self.measurement_file)[1]
            extension = extension.lower()
            if extension == ".asc":
                file_to_open = os.path.join(self.directory,
                                            self.directory_data,
                                            self.name + extension)
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

    def rename_data_file(self, new_name=None):
        """Renames the measurement data file.
        """
        if new_name is None:
            return
        rename_file(os.path.join(self.directory, self.directory_data,
                                 self.measurement_file), new_name + ".asc")
        self.measurement_file = new_name + ".asc"

    def set_loggers(self):
        """Sets the loggers for this specified measurement.

        The logs will be displayed in the measurements folder.
        After this, the measurement logger can be called from anywhere of the
        program, using logging.getLogger([measurement_name]).
        """

        # Initializes the logger for this measurement.
        logger = logging.getLogger(self.name)
        logger.setLevel(logging.DEBUG)

        # Adds two loghandlers. The other one will be used to log info (and up)
        # messages to a default.log file. The other one will log errors and
        # criticals to the errors.log file.
        self.defaultlog = logging.FileHandler(os.path.join(self.directory,
                                                           'default.log'))
        self.defaultlog.setLevel(logging.INFO)
        self.errorlog = logging.FileHandler(os.path.join(self.directory,
                                                         'errors.log'))
        self.errorlog.setLevel(logging.ERROR)

        # Set the formatter which will be used to log messages. Here you can
        # edit the format so it will be deprived to all log messages.
        defaultformat = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S')

        requestlog = logging.FileHandler(os.path.join(self.request.directory,
                                                      'request.log'))
        requestlogformat = logging.Formatter(
            '%(asctime)s - %(levelname)s - [Measurement : '
            '%(name)s] - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

        # Set the formatters to the logs.
        requestlog.setFormatter(requestlogformat)
        self.defaultlog.setFormatter(defaultformat)
        self.errorlog.setFormatter(defaultformat)

        # Add handlers to this measurement's logger.
        logger.addHandler(self.defaultlog)
        logger.addHandler(self.errorlog)
        logger.addHandler(requestlog)

    def remove_and_close_log(self, log_filehandler):
        """Closes the log file and removes it from the logger.
        
        Args:
            log_filehandler: Log's filehandler.
        """
        logging.getLogger(self.name).removeHandler(log_filehandler)
        log_filehandler.flush()
        log_filehandler.close()

    def set_axes(self, axes):
        """ Set axes information to selector within measurement.
        
        Sets axes information to selector to add selection points. Since 
        previously when creating measurement old selection could not be checked. 
        Now is time to check for it, while data is still "loading".
        
        Args:
            axes: Matplotlib FigureCanvas's subplot
        """
        self.selector.axes = axes
        # We've set axes information, check for old selection.
        self.__check_for_old_selection()

    def __check_for_old_selection(self):
        """ Use old selection file_path if exists.
        """
        try:
            selection_file = os.path.join(self.directory, self.directory_data,
                                          "{0}.selections".format(self.name))
            with open(selection_file):
                self.load_selection(selection_file)
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

    # TODO: UI stuff here. Something should be in the widgets...?
    def save_cuts(self):
        """ Save cut files
        
        Saves data points within selections into cut files.
        """
        if self.selector.is_empty():
            return 0
        if not os.path.exists(os.path.join(self.directory,
                                           self.directory_cuts)):
            self.__make_directories(self.directory_cuts)

        progress_bar = QtWidgets.QProgressBar()
        self.statusbar.addWidget(progress_bar, 1)
        progress_bar.show()
        QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents)
        # Mac requires event processing to show progress bar and its
        # process.

        starttime = time.time()

        self.__remove_old_cut_files()

        # Initializes the list size to match the number of selections.
        points_in_selection = [[] for unused_i in range(self.selector.count())]

        # Go through all points in measurement data
        data_count = len(self.data)
        for n in range(data_count):  # while n < data_count: 
            if n % 5000 == 0:
                # Do not always update UI to make it faster.
                progress_bar.setValue((n / data_count) * 90)
                QtCore.QCoreApplication.processEvents(
                    QtCore.QEventLoop.AllEvents)
                # Mac requires event processing to show progress bar and its
                # process.
            point = self.data[n]
            # Check if point is within selectors' limits for faster processing.
            if not self.selector.axes_limits.is_inside(point):
                continue

            dirtyinteger = 0  # Lazyway
            for selection in self.selector.selections:
                if selection.point_inside(point):
                    points_in_selection[dirtyinteger].append(point)
                dirtyinteger += 1

        # Save all found data points into appropriate element cut files
        # Firstly clear old cut files so those won't be accidentally
        # left there.

        dirtyinteger = 0  # Increases with for, for each selection
        content_lenght = len(points_in_selection)
        for points in points_in_selection:
            if points:  # If not empty selection -> save
                selection = self.selector.get_at(dirtyinteger)
                cut_file = CutFile(os.path.join(self.directory,
                                                self.directory_cuts))
                cut_file.set_info(selection, points)
                cut_file.save()
            dirtyinteger += 1
            progress_bar.setValue(90 + (dirtyinteger / content_lenght) * 10)
            QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents)
            # Mac requires event processing to show progress bar and its
            # process.

        self.statusbar.removeWidget(progress_bar)
        progress_bar.hide()

        log_msg = "Saving finished in {0} seconds.".format(time.time() -
                                                           starttime)
        logging.getLogger(self.name).info(log_msg)

    def __remove_old_cut_files(self):
        self.__unlink_files(os.path.join(self.directory, self.directory_cuts))
        if not os.path.exists(os.path.join(self.directory,
                                           self.directory_composition_changes)):
            self.__make_directories(self.directory_composition_changes)
        self.__unlink_files(os.path.join(self.directory,
                                         self.directory_composition_changes))

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
            self.directory, self.directory_composition_changes))
                    if os.path.isfile(os.path.join(
                self.directory, self.directory_composition_changes, f))]
        return cuts, elemloss

    def fill_cuts_treewidget(self, treewidget, use_elemloss=False,
                             checked_files=[]):
        """ Fill QTreeWidget with cut files.
        
        Args:
            treewidget: A QtGui.QTreeWidget, where cut files are added to.
            use_elemloss: A boolean representing whether to add elemental
                          losses.
            checked_files: A list of previously checked files.
        """
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
                    self.directory, self.directory_composition_changes)
                item.file_name = elemloss
                if item.file_name in checked_files:
                    item.setCheckState(0, QtCore.Qt.Checked)
                else:
                    item.setCheckState(0, QtCore.Qt.Unchecked)
                elem_root.addChild(item)
            treewidget.addTopLevelItem(elem_root)

    def load_selection(self, filename):
        """ Load selections from a file_path.
        
        Removes all current selections and loads selections from given filename.
        
        Args:
            filename: String representing (full) directory to selection
            file_path.
        """
        self.selector.load(filename)

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
        use_settings = self.measurement_settings.get_measurement_settings()
        global_settings = self.request.global_settings

        # Measurement settings
        str_beam = "Beam: {0}\n".format(
            use_settings.measuring_unit_settings.element)
        str_energy = "Energy: {0}\n".format(
            use_settings.measuring_unit_settings.energy)
        str_detector = "Detector angle: {0}\n".format(
            use_settings.measuring_unit_settings.detector_angle)
        str_target = "Target angle: {0}\n".format(
            use_settings.measuring_unit_settings.target_angle)
        str_toflen = "Toflen: {0}\n".format(
            use_settings.measuring_unit_settings.time_of_flight_lenght)
        str_carbon = "Carbon foil thickness: {0}\n".format(
            use_settings.measuring_unit_settings.carbon_foil_thickness)
        str_density = "Target density: {0}\n".format(
            use_settings.measuring_unit_settings.target_density)

        # Depth Profile settings
        str_depthnumber = "Number of depth steps: {0}\n".format(
            use_settings.depth_profile_settings.number_of_depth_steps)
        str_depthstop = "Depth step for stopping: {0}\n".format(
            use_settings.depth_profile_settings.depth_step_for_stopping)
        str_depthout = "Depth step for output: {0}\n".format(
            use_settings.depth_profile_settings.depth_step_for_output)
        str_depthscale = "Depths for concentration scaling: {0} {1}\n".format(
            use_settings.depth_profile_settings.depths_for_concentration_from,
            use_settings.depth_profile_settings.depths_for_concentration_to)

        # Cross section
        flag_cross = global_settings.get_cross_sections()
        str_cross = "Cross section: {0}\n".format(flag_cross)
        # Cross Sections: 1=Rutherford, 2=L'Ecuyer, 3=Andersen

        str_num_iterations = "Number of iterations: {0}\n".format(
            global_settings.get_num_iterations())

        # Efficiency directory
        # TODO Efficiency directory should be measurement's detector's
        # directory and not request's.
        eff_directory = self.request.detector.efficiency_directory
        str_eff_dir = "Efficiency directory: {0}".format(eff_directory)

        # Combine strings
        measurement = str_beam + str_energy + str_detector + str_target + \
                      str_toflen + str_carbon + str_density
        calibration = "TOF calibration: {0} {1}\n".format(
            use_settings.calibration_settings.slope,
            use_settings.calibration_settings.offset)
        anglecalib = "Angle calibration: {0} {1}\n".format(
            use_settings.calibration_settings.angleslope,
            use_settings.calibration_settings.angleoffset)
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
