# coding=utf-8
"""
Created on 8.4.2013
Updated on 1.6.2018

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

Holds, loads and saves depth profile settings.
"""
__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen " \
             "\n Samuli Rahkonen \n Miika Raunio \n Severi Jääskeläinen \n " \
             "Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"
__version__ = "2.0"

import configparser
import os


class DepthProfileSettings:
    """DepthProfileSettings holds the all request specific measurement unit
    parameters.
    """
    def __init__(self, settings_filepath=None):
        """Inits DepthProfileSettings.
        
        Args:
            settings_filepath: filepath for the settings file to be loaded
        """
        self.depth_profile_settings_filename = "depth_profile_settings.ini"
        self.config = configparser.ConfigParser()
        
        # This is used to determine if opened measurement 
        # uses its own settings ('MEASUREMENT') or request's 
        # settings ('REQUEST')
        self.use_settings = ""   
        self.number_of_depth_steps = 0
        self.depth_step_for_stopping = 0
        self.depth_step_for_output = 0
        self.depths_for_concentration_from = 0
        self.depths_for_concentration_to = 0
        
        self.__set_config_parameters()
        if settings_filepath is None:
            return
          
        self.filepath = os.path.join(settings_filepath,
                                     self.depth_profile_settings_filename) 
        if not os.path.exists(self.filepath):
            print("Creating " + self.filepath)
            with open(self.filepath, 'w+') as configfile:  # save
                self.config.write(configfile)
        
        self.load_settings(self.filepath)

    def __set_config_parameters(self):
        """ Set configuration parameters.
        """
        self.config.add_section('default')
        self.config.set('default', 'use_settings', str(self.use_settings))
        depth_profile_settings = "depth_profile_settings"
        self.config.add_section(depth_profile_settings)
        self.config.set(depth_profile_settings,
                        'number_of_depth_steps',
                        str(self.number_of_depth_steps))
        self.config.set(depth_profile_settings,
                        'depth_step_for_stopping',
                        str(self.depth_step_for_stopping))
        self.config.set(depth_profile_settings,
                        'depth_step_for_output',
                        str(self.depth_step_for_output))
        self.config.set(depth_profile_settings,
                        'depths_for_concentration_from',
                        str(self.depths_for_concentration_from))
        self.config.set(depth_profile_settings,
                        'depths_for_concentration_to',
                        str(self.depths_for_concentration_to))

    def show(self, dialog):
        """Shows the measuring parameters in the given measuring settings dialog.
        
        Args:
            dialog: QDialog whose fields are updated with the depth profile 
                    parameters.
        """
        dialog.numberOfDepthStepsSpinBox.setValue(self.number_of_depth_steps)
        dialog.depthStepForStoppingSpinBox.setValue(
            self.depth_step_for_stopping)
        dialog.depthStepForOutputSpinBox.setValue(self.depth_step_for_output)
        dialog.depthForConcentrationFromDoubleSpinBox.setValue(
            self.depths_for_concentration_from)
        dialog.depthForConcentrationToDoubleSpinBox.setValue(
            self.depths_for_concentration_to)

    def set_settings(self, dialog, used_settings=None):
        """Takes inputted parameters from the given dialog and sets them to the 
        corresponding object's parameters
        
        Args:
            dialog: QDialog from which the parameters are taken.
            used_settings: Used settings.
        """
        if not used_settings:
            self.use_settings = ""
        else:
            self.use_settings = used_settings
        
        self.number_of_depth_steps = dialog.numberOfDepthStepsSpinBox.value()
        self.depth_step_for_stopping = \
            dialog.depthStepForStoppingSpinBox.value()
        self.depth_step_for_output = dialog.depthStepForOutputSpinBox.value()
        self.depths_for_concentration_from = \
            dialog.depthForConcentrationFromDoubleSpinBox.value()
        self.depths_for_concentration_to = \
            dialog.depthForConcentrationToDoubleSpinBox.value()

    def load_settings(self, filepath):
        """Loads settings' parameters from the given filepath.
        
        Args:
            filepath: Filepath to the settings file.
        """
        self.config.read(filepath)
        
        try:
            self.use_settings = self.config['default']['use_settings']

            depth = "depth_profile_settings"
            self.number_of_depth_steps = int(
                            self.config[depth]['number_of_depth_steps'])
            self.depth_step_for_stopping = float(
                             self.config[depth]['depth_step_for_stopping'])
            self.depth_step_for_output = float(
                             self.config[depth]['depth_step_for_output'])
            self.depths_for_concentration_from = float(
                             self.config[
                                 depth]['depths_for_concentration_from'])
            self.depths_for_concentration_to = float(
                             self.config[depth]['depths_for_concentration_to'])
            
        except:  # If there is a problem, use default values
            # print("Bad calibration parameters loaded. Using default values.")
            return

    def save_settings(self, filepath=None):
        """Saves settings' parameters to the given filepath.
        
        Args:
            filepath: Filepath to the settings file.
        """
        
        self.config['default']['use_settings'] = self.use_settings
        
        # self.config['DEFAULT']['path'] = 'value'
        depth = "depth_profile_settings"
        self.config[depth]['number_of_depth_steps'] = str(
            self.number_of_depth_steps)
        self.config[depth]['depth_step_for_stopping'] = str(
            self.depth_step_for_stopping)
        self.config[depth]['depth_step_for_output'] = str(
            self.depth_step_for_output)
        self.config[depth]['depths_for_concentration_from'] = str(
            self.depths_for_concentration_from)
        self.config[depth]['depths_for_concentration_to'] = str(
            self.depths_for_concentration_to)
        
        if not filepath:
            filepath = self.filepath

        # filepathin korjaus
        if filepath[0] == '':
            return
        
        with open(filepath, 'wt+') as configfile:  # save
            self.config.write(configfile)
