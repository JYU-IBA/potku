# coding=utf-8
'''
Created on 11.4.2013
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

import configparser
from datetime import datetime
import logging
from os import listdir
from os import makedirs
from os.path import exists
from os.path import isfile
from os.path import join
from os.path import split
from os.path import splitext

from Modules.Measurement import Measurements
from Modules.Settings import Settings

class Project:
    '''Project class to handle all measurements.
    '''
    def __init__(self, directory, masses, statusbar, global_settings):
        '''Inits Project class. 
        
        Args:
            directory: String representing project directory
            masses: Reference to Masses (class) object.
            statusbar: QtGui.QMainWindow's QStatusBar
            global_settings: Reference to GlobalSettings object (of the program)
        '''
        # TODO: Get rid of statusbar.
        self.directory = directory
        unused_directory, self.project_name = split(self.directory)
        self.settings = Settings(self.directory)
        self.global_settings = global_settings
        self.masses = masses
        self.statusbar = statusbar
        self.measurements = Measurements(self)
        
        # Check folder exists and make project file there.
        if not exists(directory):
            makedirs(directory)
            
        self.__set_project_logger()
        
        # Project file containing necessary information of the project.
        # If it exists, we assume old project is loaded.
        self.__project_information = configparser.ConfigParser()
        self.project_file = join(directory, "{0}.proj".format(self.project_name))
        if not exists(self.project_file):
            self.__project_information.add_section("meta")
            self.__project_information.add_section("open_measurements")
            self.__project_information["meta"]["project_name"] = self.project_name
            self.__project_information["meta"]["created"] = str(datetime.now())
            self.save()
        else:
            self.load()
    
    
    def get_measurements_files(self):
        '''Get measurements files inside project folder.
        '''
        # TODO: Possible for different formats (such as binary data .lst)
        return [f for f in listdir(self.directory) 
                if isfile(join(self.directory, f)) and splitext(f)[1] == ".asc"]
     
    
    def load(self):
        '''Load project
        '''
        # TODO: Add loading project with generated measurement graphs.
        self.__project_information.read(self.project_file)
    
    
    def save(self):
        '''Save project
        '''
        # TODO: Saving properly.
        with open(self.project_file, 'wt+') as configfile:
            self.__project_information.write(configfile)
       
    
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



