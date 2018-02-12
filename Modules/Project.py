# coding=utf-8
'''
Created on 11.4.2013
Updated on 26.8.2013

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

import configparser, logging
from datetime import datetime
from os import listdir, makedirs, stat
from os.path import exists, isfile, join, split, splitext

from Modules.Measurement import Measurements
from Modules.Settings import Settings

class Project:
    '''Project class to handle all measurements.
    '''
    def __init__(self, directory, name, masses, statusbar, global_settings,
                 measurement_tabs):
        '''Inits Project class. 
        
        Args:
            directory: A String representing project directory.
            masses: A Masses class object.
            statusbar: A QtGui.QMainWindow's QStatusBar.
            global_settings: A GlobalSettings class object (of the program).
            measurement_tabs: A dictionary of MeasurementTabWidgets of the 
                              measurements in the project.
        '''
        # TODO: Get rid of statusbar.
        self.directory = directory
        self.project_name = name
        unused_directory, tmp_dirname = split(self.directory)
        self.settings = Settings(self.directory)
        self.global_settings = global_settings
        self.masses = masses
        self.statusbar = statusbar
        self.measurements = Measurements(self)
        self.__measurement_tabs = measurement_tabs
        self.__master_measurement = None
        self.__non_slaves = []  # List of measurements that aren't slaves. Easier
        
        # Check folder exists and make project file there.
        if not exists(directory):
            makedirs(directory)
            
        self.__set_project_logger()
        
        # Project file containing necessary information of the project.
        # If it exists, we assume old project is loaded.
        self.__project_information = configparser.ConfigParser()
        self.project_file = join(directory, "{0}.proj".format(tmp_dirname))
        
        # Defaults
        self.__project_information.add_section("meta")
        self.__project_information.add_section("open_measurements")
        self.__project_information["meta"]["project_name"] = self.project_name
        self.__project_information["meta"]["created"] = str(datetime.now())
        self.__project_information["meta"]["master"] = ""
        self.__project_information["meta"]["nonslave"] = ""
        if not exists(self.project_file):
            self.save()
        else:
            self.load()
    
    
    def exclude_slave(self, measurement):
        """Exclude measurement from slave category under master.
        
        Args:
            measurement: A measurement class object.
        """
        name = measurement.measurement_name
        # Check if measurement is already excluded.
        if name in self.__non_slaves:
            return
        self.__non_slaves.append(name)
        self.__project_information["meta"]["nonslave"] = "|".join(self.__non_slaves)
        self.save()
        
        
    def include_slave(self, measurement):
        """Include measurement to slave category under master.
        
        Args:
            measurement: A measurement class object.
        """
        name = measurement.measurement_name
        # Check if measurement is in the list.
        if not name in self.__non_slaves:
            return
        self.__non_slaves.remove(name)
        self.__project_information["meta"]["nonslave"] = "|".join(self.__non_slaves)
        self.save()
        
        
    def get_name(self):
        '''Get the project's name.
        
        Return:
            Returns the project's name.
        '''
        return self.__project_information["meta"]["project_name"]
    
    
    def get_master(self):
        """Get master measurement of the project.
        """
        return self.__master_measurement
        
        
    def get_measurements_files(self):
        '''Get measurements files inside project folder.
        '''
        # TODO: Possible for different formats (such as binary data .lst)
        return [f for f in listdir(self.directory) 
                if isfile(join(self.directory, f)) and 
                splitext(f)[1] == ".asc" and 
                stat(join(self.directory, f)).st_size]  # Do not load empty files.
     
    
    def get_measurement_tabs(self, exclude_id= -1):
        """Get measurement tabs of a project.
        """
        list_m = []
        keys = list(filter((exclude_id).__ne__, self.__measurement_tabs.keys()))
        for key in keys:
            list_m.append(self.__measurement_tabs[key])
        return list_m
        
        
    def get_nonslaves(self):
        """Get measurement names that will be excluded from slave category.
        """
        return self.__non_slaves
    
    
    def has_master(self):
        """Does project have master measurement? Check from config file as
        it is not loaded yet.
        
        This is used when loading project. As project has no measurement in it
        when inited so check is made in potku.py after loading all measurements
        via this method. The corresponding master title in treewidget is then set.
        """
        return self.__project_information["meta"]["master"]
    
    
    def load(self):
        '''Load project
        '''
        self.__project_information.read(self.project_file)
        self.__non_slaves = self.__project_information["meta"]["nonslave"].split('|')
    
    
    def save(self):
        '''Save project
        '''
        # TODO: Saving properly.
        with open(self.project_file, 'wt+') as configfile:
            self.__project_information.write(configfile)
    
    
    def save_cuts(self, measurement):
        """Save cuts for all measurements except for master.
        
        Args:
            measurement: A measurement class object that issued save cuts.
        """
        name = measurement.measurement_name
        if name == self.has_master():
            nonslaves = self.get_nonslaves()
            tabs = self.get_measurement_tabs(measurement.tab_id)
            for tab in tabs:
                tab_name = tab.measurement.measurement_name
                if tab.data_loaded and not tab_name in nonslaves and \
                   tab_name != name:
                    # No need to save same measurement twice.
                    tab.measurement.save_cuts()
            
    
    def save_selection(self, measurement):
        """Save selection for all measurements except for master.
        
        Args:
            measurement: A measurement class object that issued save cuts.
        """
        directory = measurement.directory
        name = measurement.measurement_name
        selection_file = "{0}.sel".format(join(directory, name))
        if name == self.has_master():
            nonslaves = self.get_nonslaves()
            tabs = self.get_measurement_tabs(measurement.tab_id)
            for tab in tabs:
                tab_name = tab.measurement.measurement_name
                if tab.data_loaded and not tab_name in nonslaves and \
                   tab_name != name:
                    tab.measurement.selector.load(selection_file)
                    tab.histogram.matplotlib.on_draw()
        
        
    def set_master(self, measurement=None):
        """Set master measurement for the project.
        
        Args:
            measurement: A measurement class object.
        """
        self.__master_measurement = measurement
        if not measurement:
            self.__project_information["meta"]["master"] = ""
        else:
            name = measurement.measurement_name
            self.__project_information["meta"]["master"] = name
        self.save()
        
        
    def __set_project_logger(self):
        '''Sets the logger which is used to log everything that doesn't happen in 
        measurements.
        '''
        logger = logging.getLogger("project")
        logger.setLevel(logging.DEBUG)
        
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s",
                                      datefmt="%Y-%m-%d %H:%M:%S")    
        projectlog = logging.FileHandler(join(self.directory, "project.log"))
        projectlog.setLevel(logging.INFO)   
        projectlog.setFormatter(formatter)
        
        logger.addHandler(projectlog)



