# coding=utf-8
"""
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
"""
__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen \n Samuli Rahkonen \n Miika Raunio"
__versio__ = "1.0"

import configparser, logging
from datetime import datetime
from os import path, listdir, makedirs, stat

from modules.measurement import Measurements
from modules.simulation import Simulations, Simulation
from modules.settings import Settings
from modules.detector import Detector

class Request:
    """Request class to handle all measurements.
    """
    def __init__(self, directory, name, masses, statusbar, global_settings,
                 tabs):
        """Inits Request class. 
        
        Args:
            directory: A String representing request directory.
            masses: A Masses class object.
            statusbar: A QtGui.QMainWindow's QStatusBar.
            global_settings: A GlobalSettings class object (of the program).
            tabs: A dictionary of MeasurementTabWidgets and SimulationTabWidgets
            of the request.
        """
        # TODO: Get rid of statusbar.
        self.directory = directory
        self.request_name = name
        unused_directory, tmp_dirname = path.split(self.directory)
        self.settings = Settings(self.directory)
        self.global_settings = global_settings
        self.masses = masses
        self.statusbar = statusbar
        self.measurements = Measurements(self)
        self.simulations = Simulations(self)
        self.detector = Detector(self)
        self.default_simulation = Simulation(self)
        self.__tabs = tabs
        self.__master_measurement = None
        self.__non_slaves = []  # List of measurements that aren't slaves. Easier
        
        # Check folder exists and make request file there.
        if not path.exists(directory):
            makedirs(directory)
            
        self.__set_request_logger()
        
        # Request file containing necessary information of the request.
        # If it exists, we assume old request is loaded.
        self.__request_information = configparser.ConfigParser()
        self.request_file = path.join(directory, "{0}.proj".format(tmp_dirname))
        
        # Defaults
        self.__request_information.add_section("meta")
        self.__request_information.add_section("open_measurements")
        self.__request_information["meta"]["request_name"] = self.request_name
        self.__request_information["meta"]["created"] = str(datetime.now())
        self.__request_information["meta"]["master"] = ""
        self.__request_information["meta"]["nonslave"] = ""
        if not path.exists(self.request_file):
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
        self.__request_information["meta"]["nonslave"] = "|".path.join(self.__non_slaves)
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
        self.__request_information["meta"]["nonslave"] = "|".path.join(self.__non_slaves)
        self.save()
        
        
    def get_name(self):
        """Get the request's name.
        
        Return:
            Returns the request's name.
        """
        return self.__request_information["meta"]["request_name"]
    
    
    def get_master(self):
        """Get master measurement of the request.
        """
        return self.__master_measurement
        
        
    def get_measurements_files(self):
        """Get measurements files inside request folder.
        """
        # TODO: Possible for different formats (such as binary data .lst)
        return [f for f in listdir(self.directory) 
                if path.isfile(path.join(self.directory, f)) and
                path.splitext(f)[1] == ".asc" and
                stat(path.join(self.directory, f)).st_size]  # Do not load empty files.

    def get_simulation_files(self):
        """Get simulation files inside request folder.
        """
        # TODO: Possible for different formats (such as binary data .lst)
        return [f for f in listdir(self.directory) 
                if path.isfile(path.join(self.directory, f)) and
                path.splitext(f)[1] == ".sim" and
                stat(path.join(self.directory, f)).st_size]  # Do not load empty files.
     
    
    def get_measurement_tabs(self, exclude_id= -1):
        """Get measurement tabs of a request.
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
        """Does request have master measurement? Check from config file as
        it is not loaded yet.
        
        This is used when loading request. As request has no measurement in it
        when inited so check is made in potku.py after loading all measurements
        via this method. The corresponding master title in treewidget is then set.
        """
        return self.__request_information["meta"]["master"]
    
    
    def load(self):
        """Load request
        """
        self.__request_information.read(self.request_file)
        self.__non_slaves = self.__request_information["meta"]["nonslave"].split("|")
    
    
    def save(self):
        """Save request
        """
        # TODO: Saving properly.
        with open(self.request_file, "wt+") as configfile:
            self.__request_information.write(configfile)
    
    
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
        selection_file = "{0}.sel".format(path.join(directory, name))
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
        """Set master measurement for the request.
        
        Args:
            measurement: A measurement class object.
        """
        self.__master_measurement = measurement
        if not measurement:
            self.__request_information["meta"]["master"] = ""
        else:
            name = measurement.measurement_name
            self.__request_information["meta"]["master"] = name
        self.save()
        
        
    def __set_request_logger(self):
        """Sets the logger which is used to log everything that doesn't happen in 
        measurements.
        """
        logger = logging.getLogger("request")
        logger.setLevel(logging.DEBUG)
        
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s",
                                      datefmt="%Y-%m-%d %H:%M:%S")    
        requestlog = logging.FileHandler(path.join(self.directory, "request.log"))
        requestlog.setLevel(logging.INFO)   
        requestlog.setFormatter(formatter)
        
        logger.addHandler(requestlog)



