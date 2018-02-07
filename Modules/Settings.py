# coding=utf-8
'''
Created on 12.4.2013
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

from Modules.MeasuringSettings import MeasuringSettings
from Modules.CalibrationParameters import CalibrationParameters
from Modules.DepthProfileSettings import DepthProfileSettings

class Settings:
    '''Settings class to handle settings of project and measurement.
    '''
    def __init__(self, directory=None, project_settings=None):
        '''Inits Settings class.
        
        Args:
            directory: String representing directory for settings.
            project_settings: Settings class object of project.
        '''
        self.project_settings = project_settings 
        self.measuring_unit_settings = MeasuringSettings(directory)
        self.calibration_settings = CalibrationParameters(directory)
        self.depth_profile_settings = DepthProfileSettings(directory)
    
    
    def get_measurement_settings(self):
        """Get the measurement specific settings.
        
        Get currently used settings by measurement. If measurement uses project
        settings (by default), it will return project's settings instead.
        
        Returns:
            Settings object that has all the references to settings that a 
            measurement uses.
        """
        if self.measuring_unit_settings.use_settings == "MEASUREMENT":
            use_measuring = self.measuring_unit_settings
        else:  # If there is "" or "PROJECT"
            use_measuring = self.project_settings.measuring_unit_settings
            
        if self.calibration_settings.use_settings == "MEASUREMENT":
            use_calibration = self.calibration_settings
        else:
            use_calibration = self.project_settings.calibration_settings    
            
        if self.depth_profile_settings.use_settings == "MEASUREMENT":
            use_depth = self.depth_profile_settings
        else:
            use_depth = self.project_settings.depth_profile_settings
            
        settings = Settings() # TODO: Use setters instead of directly modifying.
        settings.measuring_unit_settings = use_measuring
        settings.calibration_settings = use_calibration
        settings.depth_profile_settings = use_depth
        return settings
    
