# coding=utf-8
'''
Created on 8.4.2013
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

Holds, loads and saves calibration parameters.
'''
__author__ = "Jarkko Aalto \n Timo Konu \n Samuli K�rkk�inen \n Samuli Rahkonen \n Miika Raunio"
__versio__ = "1.0"

import configparser
import os

class CalibrationParameters:
    """MeasuringSettings holds the all project specific measurement unit parameters.
    """
    def __init__(self, settings_filepath=None):
        """Inits MeasuringSettings.
        
        Args:
            settings_filepath: filepath for the settings file to be loaded
        """
        self.calibration_settings_filename = "calibration_settings.ini"
        self.config = configparser.ConfigParser()
        
        # This is used to determine if opened measurement 
        # uses its own settings ('MEASUREMENT') or project's 
        # settings ('PROJECT') 
        self.use_settings = ""      
        self.slope = 0
        self.offset = 0
        self.angleslope = 0
        self.angleoffset = 0

        self.__set_config_parameters()
        if settings_filepath == None:
            return
        
        self.filepath = os.path.join(settings_filepath,
                                     self.calibration_settings_filename) 
        if not os.path.exists(self.filepath):
            with open(self.filepath, 'wt+') as configfile:
                self.config.write(configfile)
        self.load_settings(self.filepath)
    
    
    def show(self, dialog):
        """Shows the measuring parameters in the given measuring settings dialog.
        
        Args:
            dialog: QDialog whose fields are updated with the Calibration 
                    parameters.
        """
        dialog.slopeLineEdit.setText(str(self.slope))
        dialog.offsetLineEdit.setText(str(self.offset))
        dialog.angleSlopeLineEdit.setText(str(self.angleslope))
        dialog.angleOffsetLineEdit.setText(str(self.angleoffset))
 
        
    def set_settings(self, dialog, used_settings=None):
        """Takes inputted parameters from the given dialog and sets them to the 
        corresponding object's parameters
        
        Args:
            dialog: QDialog from which the parameters are taken.
        """
        if used_settings == None:
            self.use_settings = ""
        else:
            self.use_settings = used_settings
        
        self.slope = float(dialog.slopeLineEdit.text())
        self.offset = float(dialog.offsetLineEdit.text())
        self.angleslope = float(dialog.angleSlopeLineEdit.text())
        self.angleoffset = float(dialog.angleOffsetLineEdit.text())
        
    def load_settings(self, filepath):
        """Loads settings' parameters from the given filepath.
        
        Args:
            filepath: Filepath to the settings file.
        """
        self.config.read(filepath)
        try:
            self.use_settings = self.config['default']['use_settings']
            
            self.slope = float(self.config['parameters']['slope'])
            self.offset = float(self.config['parameters']['offset'])
            self.angleslope = float(self.config['parameters']['angleslope'])
            self.angleoffset = float(self.config['parameters']['angleoffset'])

        except:  # If there is a problem, use default values
            return
        
        
    def __set_config_parameters(self):
        self.config.add_section('default')
        self.config.set('default', 'use_settings', str(self.use_settings))
        self.config.add_section('parameters')
        self.config.set('parameters', 'slope', str(self.slope))
        self.config.set('parameters', 'offset', str(self.offset))
        self.config.set('parameters', 'angleslope', str(self.angleslope))
        self.config.set('parameters', 'angleoffset', str(self.angleoffset))

        
    def save_settings(self, filepath=None):
        """Saves settings' parameters to the given filepath.
        
        Args:
            filepath: Filepath to the settings file.
        """
        self.config['default']['use_settings'] = self.use_settings
        self.config['parameters']['slope'] = str(self.slope)
        self.config['parameters']['offset'] = str(self.offset)
        self.config['parameters']['angleslope'] = str(self.angleslope)
        self.config['parameters']['angleoffset'] = str(self.angleoffset)


        if not filepath:
            filepath = self.filepath

        # filepathin korjaus
        if filepath[0] == '':
            return

        with open(filepath, 'wt+') as configfile:  # save
            self.config.write(configfile)
                
