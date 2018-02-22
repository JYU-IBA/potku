# coding=utf-8
'''
Created on 15.3.2013
Updated on 23.5.2013

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
'''
__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen \n Samuli Rahkonen \n Miika Raunio"
__versio__ = "1.0"

import os
# import re
import shutil
import sys
import logging
import time
from PyQt4 import QtGui, QtCore

from Modules.CutFile import CutFile
from Modules.Selection import Selector
from Modules.Settings import Settings


class Measurements:
    '''Measurements class handles multiple measurements.
    '''
    def __init__(self, project):
        '''Inits measurements class.
        
        Args:
            project: Project class object.
        '''
        self.project = project
        self.measurements = {}  # Dictionary<Measurement>
        self.measuring_unit_settings = None
        self.default_settings = None
    
    
    def is_empty(self):
        '''Check if there are any measurements.
        
        Return:
            Returns True if there are no measurements currently in the 
            measurements object.
        '''
        return len(self.measurements) == 0
    
    
    def get_key_value(self, key):
        if not key in self.measurements:
            return None
        return self.measurements[key]
    
    
    def add_measurement_file(self, measurement_file, tab_id):
        '''Add a new file to measurements.
        
        Args:
            measurement_filepath: String representing file containing measurement 
                                  data.
            tab_id: Integer representing identifier for measurement's tab.
        
        Return:
            Returns new measurement or None if it wasn't added
        '''
        measurement = None
        measurement_filename = os.path.split(measurement_file)[1]
        measurement_name = os.path.splitext(measurement_filename)
        new_file = os.path.join(self.project.directory, measurement_filename)
        # print("-------------------------------------------------")
        # print(measurement_file)
        # print(os.path.split(measurement_file))
        # print(self.project.directory)
        # print(new_file)
        # print()
        file_directory, file_name = os.path.split(measurement_file)
        try:
            if file_directory != self.project.directory and file_directory:
                dirtyinteger = 2  # Begin from 2, since 0 and 1 would be confusing.
                while os.path.exists(new_file):
                    file_name = "{0}_{1}{2}".format(measurement_name[0],
                                                    dirtyinteger,
                                                    measurement_name[1])
                    new_file = os.path.join(self.project.directory, file_name)
                    dirtyinteger += 1
                shutil.copyfile(measurement_file, new_file)
                file_directory, file_name = os.path.split(new_file)
                
                log = "Added new measurement {0} to the project.".format(file_name)
                logging.getLogger('project').info(log)
            keys = self.measurements.keys()
            for key in keys:
                if self.measurements[key].measurement_file == file_name:
                    return measurement  # measurement = None
            measurement = Measurement(new_file, self.project, tab_id)
            measurement.load_data()
            self.measurements[tab_id] = measurement
        except:
            log = "Something went wrong while adding a new measurement."
            logging.getLogger("project").critical(log)
            print(sys.exc_info())  # TODO: Remove this.
        return measurement
        
        
    def remove_by_tab_id(self, tab_id):
        '''Removes measurement from measurements by tab id
        
        Args:
            tab_id: Integer representing tab identifier.
        '''
        def remove_key(d, key):
            r = dict(d)
            del r[key]
            return r
        self.measurements = remove_key(self.measurements, tab_id)
                



class Measurement:
    '''Measurement class to handle one measurement data.
    '''
    def __init__(self, measurement_file, project, tab_id):
        '''Inits measurement.
        
        Args:
            measurement_file: String representing path to measurement file.
            project: Project class object.
            tab_id: Integer representing tab identifier for measurement.
        '''
        measurement_folder, measurement_name = os.path.split(measurement_file)
        self.measurement_file = measurement_name;  # With extension
        self.measurement_name = os.path.splitext(measurement_name)[0]         
        
        self.directory = os.path.join(measurement_folder, self.measurement_name)
        self.directory_cuts = os.path.join(self.directory, "cuts")
        self.directory_elemloss = os.path.join(self.directory_cuts, "elemloss")
        
        self.project = project  # To which project be belong to
        self.data = ([], [])
        self.tab_id = tab_id

        self.__make_directories(self.directory)
        self.__make_directories(self.directory_cuts)
        self.__make_directories(self.directory_elemloss)
                
        self.set_loggers()
        
        # The settings that come from the project
        self.__project_settings = self.project.settings  
        # The settings that are individually set for this measurement
        self.measurement_settings = Settings(self.directory,
                                             self.__project_settings)  
        
        # Main window's statusbar TODO: Remove GUI stuff.
        self.statusbar = self.project.statusbar
        
        element_colors = self.project.global_settings.get_element_colors()
        self.selector = Selector(self.directory, self.measurement_name,
                                 self.project.masses, element_colors,
                                 settings=self.measurement_settings)
        
        # Which color scheme is selected by default
        self.color_scheme = "Default color"  
        
    
    def __make_directories(self, directory):
        if not os.path.exists(directory):
            os.makedirs(directory)
            log = "Created a directory {0}.".format(directory)
            logging.getLogger("project").info(log) 
    
    
    def load_data(self):
        '''Loads measurement data from filepath
        '''
        # import cProfile, pstats
        # pr = cProfile.Profile()
        # pr.enable()
        try:
            extension = os.path.splitext(self.measurement_file)[1]
            if extension == ".asc":
                with open("{0}{1}".format(self.directory, extension)) as fp:
                    for line in fp:
                        # TODO: Figure good way to split into columns. REGEX too slow.
                        # See test below
                        # split = re.split("\s+", line.strip()) #TEST #1
                        split = line.strip().split(" ")  # TEST #2
                        split_len = len(split)
                        if split_len == 1:  # Different separator
                            split = line.strip().split("    ")
                            split_len = len(split)
                        if split_len == 2:  # Two columns
                            self.data[0].append(int(split[0]))
                            self.data[1].append(int(split[1]))
        except IOError as e:
            error_log = "Error while loading the {0} {1}. {2}".format(
                        "measurement date for the measurement",
                        self.measurement_name,
                        "The error was:")
            error_log_2 = "I/O error ({0}): {1}".format(e.errno, e.strerror)
            logging.getLogger('project').error(error_log)
            logging.getLogger('project').error(error_log_2)
        except Exception as e:
            error_log = "Unexpected error: [{0}] {1}".format(e.errno, e.strerror)
            logging.getLogger('project').error(error_log)
        # pr.disable()
        # ps = pstats.Stats(pr)
        # ps.sort_stats("time")
        # ps.print_stats(10)


    def set_loggers(self):
        '''Sets the loggers for this specified measurement. 
        
        The logs will be displayed in the measurements folder.
        After this, the measurement logger can be called from anywhere of the 
        program, using logging.getLogger([measurement_name]).
        '''
        
        # Initializes the logger for this measurement.
        logger = logging.getLogger(self.measurement_name)
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
        
        # Set the formatter which will be used to log messages. Here you can edit
        # the format so it will be deprived to all log messages.
        defaultformat = logging.Formatter(
                                      '%(asctime)s - %(levelname)s - %(message)s',
                                      datefmt='%Y-%m-%d %H:%M:%S')
        
        projectlog = logging.FileHandler(os.path.join(self.project.directory,
                                                      'project.log'))
        projectlogformat = logging.Formatter(
             '%(asctime)s - %(levelname)s - [Measurement : %(name)s] - %(message)s',
             datefmt='%Y-%m-%d %H:%M:%S')
        
        # Set the formatters to the logs.
        projectlog.setFormatter(projectlogformat)
        self.defaultlog.setFormatter(defaultformat)
        self.errorlog.setFormatter(defaultformat)
        
        # Add handlers to this measurement's logger.        
        logger.addHandler(self.defaultlog)
        logger.addHandler(self.errorlog)
        logger.addHandler(projectlog)
        
        
    def remove_and_close_log(self, log_filehandler):
        """Closes the log file and removes it from the logger.
        
        Args:
            log_filehandler: Log's filehandler.
        """
        logging.getLogger(self.measurement_name).removeHandler(log_filehandler)
        log_filehandler.flush()
        log_filehandler.close()
        
        
    def set_axes(self, axes):
        '''Set axes information to selector within measurement.
        
        Sets axes information to selector to add selection points. Since 
        previously when creating measurement old selection could not be checked. 
        Now is time to check for it, while data is still "loading".
        
        Args:
            axes: Matplotlib FigureCanvas's subplot
        '''
        self.selector.axes = axes
        # We've set axes information, check for old selection.
        self.__check_for_old_selection()  
        
    
    def __check_for_old_selection(self):
        '''Use old selection file_path if exists.
        '''
        try:
            selection_file = os.path.join(self.directory,
                                          "{0}.sel".format(self.measurement_name))
            with open(selection_file): 
                self.load_selection(selection_file)
        except:
            # TODO: Is it necessary to inform user with this?
            log_msg = "There was no old selection file to add to this project."
            logging.getLogger(self.measurement_name).info(log_msg)
    
    
    def add_point(self, point, canvas):
        '''Add point into selection or create new selection if first or all closed.
        
        Args:
            point: Point (x, y) to be added to selection.
            canvas: matplotlib's FigureCanvas where selections are drawn.
            
        Return:
            1: When point closes open selection and allows new selection to 
                be made.
            0: When point was added to open selection.
            -1: When new selection is not allowed and there are no selections.
        '''
        flag = self.selector.add_point(point, canvas)
        if flag >= 0:
            self.selector.update_axes_limits()
        return flag
    
    
    def undo_point(self):
        '''Undo last point in open selection.
             
        Undo last point in open (last) selection. If there are no selections, 
        do nothing.
        '''
        return self.selector.undo_point()
    
    
    def purge_selection(self):
        '''Purges (removes) all open selections and allows new selection to be made.
        '''
        self.selector.purge()
    
    
    def remove_all(self):
        '''Remove all selections in selector.
        '''
        self.selector.remove_all()
    
    
    def draw_selection(self):
        '''Draw all selections in measurement.
        '''
        self.selector.draw()
        
    
    def end_open_selection(self, canvas):
        '''End last open selection.
        
        Ends last open selection. If selection is open, it will show dialog to 
        select element information and draws into canvas before opening the dialog.
        
        Args:
            canvas: Matplotlib's FigureCanvas

        Return:
            1: If selection closed
            0: Otherwise
        '''
        return self.selector.end_open_selection(canvas)
    
    
    def selection_select(self, cursorpoint, highlight=True):
        '''Select a selection based on point.
        
        Args:
            point: Point (x, y) which is clicked on the graph to select selection.
            highlight: Boolean to determine whether to highlight just this 
                       selection.
            
        Return:
            1: If point is within selection.
            0: If point is not within selection.
        '''
        return self.selector.select(cursorpoint, highlight)
    
    
    def selection_count(self):
        '''Get count of selections.
        
        Return:
            Returns the count of selections in selector object.
        '''
        return self.selector.count()
    
    
    def reset_select(self):
        '''Reset selection to None.
        
        Resets current selection to None and resets colors of all selections
        to their default values. 
        '''
        self.selector.reset_select()
    
    
    def remove_selected(self):
        '''Remove selection
        
        Removes currently selected selection.
        '''
        self.selector.remove_selected()
    
    # TODO: UI stuff here. Something should be in the widgets...?
    def save_cuts(self):
        '''Save cut files
        
        Saves data points within selections into cut files.
        '''
        if self.selector.is_empty():
            return 0
        if not os.path.exists(self.directory_cuts):
            os.makedirs(self.directory_cuts)

        progress_bar = QtGui.QProgressBar()
        self.statusbar.addWidget(progress_bar, 1)
        progress_bar.show()

        starttime = time.time()
        
        self.__remove_old_cut_files()
        
        # Initializes the list size to match the number of selections.
        points_in_selection = [[] for unused_i in range(self.selector.count())]

        # Go through all points in measurement data
        data_count = len(self.data[0])
        for n in range(data_count):  # while n < data_count: 
            progress_bar.setValue((n / data_count) * 90)
            
            point = [self.data[0][n], self.data[1][n], n]
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
                cut_file = CutFile(self.directory)
                cut_file.set_info(selection, points)
                cut_file.save()
            progress_bar.setValue(90 + (dirtyinteger / content_lenght) * 10) 
            dirtyinteger += 1 
            
        self.statusbar.removeWidget(progress_bar)
        progress_bar.hide()
        
        log_msg = "Saving finished in {0} seconds.".format(time.time() - starttime)
        logging.getLogger(self.measurement_name).info(log_msg)

        
    def __remove_old_cut_files(self):
        self.__unlink_files(self.directory_cuts)
        if not os.path.exists(self.directory_elemloss):
            os.makedirs(self.directory_elemloss)
        self.__unlink_files(self.directory_elemloss)

        
    def __unlink_files(self, directory):
        for the_file in os.listdir(directory):
            file_path = os.path.join(directory, the_file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception:
                log_msg = "Failed to remove the old cut files."
                logging.getLogger(self.measurement_name).error(log_msg)
    
    
    def get_cut_files(self):
        '''Get cut files from a measurement.
        
        Return:
            Returns a list of cut files in measurement.
        '''
        cuts = [f for f in os.listdir(self.directory_cuts) 
                if os.path.isfile(os.path.join(self.directory_cuts, f))]
        elemloss = [f for f in os.listdir(self.directory_elemloss) 
                    if os.path.isfile(os.path.join(self.directory_elemloss, f))]
        return cuts, elemloss
    
    
    def fill_cuts_treewidget(self, treewidget, use_elemloss=False):
        '''Fill QTreeWidget with cut files.
        
        Args:
            treewidget: QtGui.QTreeWidget, where cut files are added to.
            elemloss: Boolean representing whether to add elemental losses or not.
        '''
        treewidget.clear()
        cuts, cuts_elemloss = self.get_cut_files()
        for cut in cuts:
            item = QtGui.QTreeWidgetItem([cut]) 
            item.directory = self.directory_cuts
            item.file_name = cut
            item.setCheckState(0, QtCore.Qt.Checked)
            treewidget.addTopLevelItem(item)
        if use_elemloss:
            elem_root = QtGui.QTreeWidgetItem(["Elemental Losses"])
            for elemloss in cuts_elemloss:
                item = QtGui.QTreeWidgetItem([elemloss])
                item.setCheckState(0, QtCore.Qt.Unchecked)
                item.directory = self.directory_elemloss
                item.file_name = elemloss
                elem_root.addChild(item)
            treewidget.addTopLevelItem(elem_root)
    
    
    def load_selection(self, filename):
        '''Load selections from a file_path.
        
        Removes all current selections and loads selections from given filename.
        
        Args:
            filename: String representing (full) directory to selection file_path.
        '''
        self.selector.load(filename)


    def generate_tof_in(self):
        '''Generate tof.in file for external programs.
        
        Generates tof.in file for measurement to be used in external programs 
        (tof_list, erd_depth).
        '''
        tof_in_directory = os.path.join(os.path.realpath(os.path.curdir),
                                        "external",
                                        "Potku-bin")
        tof_in_file = os.path.join(tof_in_directory, "tof.in")
        
        if os.path.exists(tof_in_file):
            try:
                new_file = "{0}_{1}.bak".format(tof_in_file,
                                                time.strftime("%Y-%m-%d_%H.%M.%S"))
                shutil.copyfile(tof_in_file, new_file)
                back_up_msg = "Backed up old tof.in file to {0}".format(
                                                        os.path.realpath(new_file))
                logging.getLogger(self.measurement_name).info(back_up_msg)
            except:
                error_msg = "Unexpected error: {0}".format(sys.exc_info()[0])
                logging.getLogger(self.measurement_name).error(error_msg)
                
        use_settings = self.measurement_settings.get_measurement_settings()
        with open(tof_in_file, "wt+") as fp:
            measurement = "Beam: {0}\n".format(
                     use_settings.measuring_unit_settings.element) \
                + "Energy: {0}\n".format(
                     use_settings.measuring_unit_settings.energy) \
                + "Detector angle: {0}\n".format(
                     use_settings.measuring_unit_settings.detector_angle) \
                + "Target angle: {0}\n".format(
                     use_settings.measuring_unit_settings.target_angle) \
                + "Toflen: {0}\n".format(
                     use_settings.measuring_unit_settings.time_of_flight_lenght) \
                + "Carbon foil thickness: {0}\n".format(
                     use_settings.measuring_unit_settings.carbon_foil_thickness) \
                + "Target density: {0}\n".format(
                     use_settings.measuring_unit_settings.target_density)
            fp.write(measurement)
            
            # ToF Calibration
            fp.write("TOF calibration: {0} {1}\n".format(
                                        use_settings.calibration_settings.slope,
                                        use_settings.calibration_settings.offset))
            
            # Depth settings
            depth = "Depth step for stopping: {0}\n".format(
                    use_settings.depth_profile_settings.depth_step_for_stopping) \
                + "Depth step for output: {0}\n".format(
                    use_settings.depth_profile_settings.depth_step_for_output) \
                + "Depths for concentration scaling: {0} {1}\n".format(
                use_settings.depth_profile_settings.depths_for_concentration_from,
                use_settings.depth_profile_settings.depths_for_concentration_to)
            fp.write(depth)            

