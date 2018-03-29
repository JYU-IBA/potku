# coding=utf-8
'''
Created on 12.4.2013
Updated on 15.7.2013

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

from modules.measuring_settings import MeasuringSettings
from modules.calibration_parameters import CalibrationParameters
from modules.depth_profile_settings import DepthProfileSettings

class Settings:
    '''Settings class to handle settings of request and measurement.
    '''
    def __init__(self, directory=None, request_settings=None):
        '''Inits Settings class.
        
        Args:
            directory: String representing directory for settings.
            request_settings: Settings class object of request.
        '''
        self.request_settings = request_settings 
        self.measuring_unit_settings = MeasuringSettings(directory)
        self.calibration_settings = CalibrationParameters(directory)
        self.depth_profile_settings = DepthProfileSettings(directory)
    
    
    def get_measurement_settings(self):
        """Get the measurement specific settings.
        
        Get currently used settings by measurement. If measurement uses request
        settings (by default), it will return request's settings instead.
        
        Returns:
            Settings object that has all the references to settings that a 
            measurement uses.
        """
        if self.measuring_unit_settings.use_settings == "MEASUREMENT":
            use_measuring = self.measuring_unit_settings
        else:  # If there is "" or "REQUEST"
            use_measuring = self.request_settings.measuring_unit_settings
            
        if self.calibration_settings.use_settings == "MEASUREMENT":
            use_calibration = self.calibration_settings
        else:
            use_calibration = self.request_settings.calibration_settings    
            
        if self.depth_profile_settings.use_settings == "MEASUREMENT":
            use_depth = self.depth_profile_settings
        else:
            use_depth = self.request_settings.depth_profile_settings
            
        settings = Settings()  # TODO: Use setters instead of directly modifying.
        settings.measuring_unit_settings = use_measuring
        settings.calibration_settings = use_calibration
        settings.depth_profile_settings = use_depth
        return settings
    
    
    def has_been_set(self):
        '''Are settings changed or still default values.
        
        Return:
            Returns True if user has changed settings and False if settings 
            have default values.
        '''
        zero_equality_large = 0.01
        zero_equality_small = 0.000000000000001  # For calibration, e-15
        if self.request_settings:
            settings = self.get_measurement_settings()
        else:
            settings = self
        mus = settings.measuring_unit_settings
        cs = settings.calibration_settings
        dps = settings.depth_profile_settings
        
        # Check Measurement Settings
        if not mus.element:
            return False
        if abs(mus.carbon_foil_thickness) < zero_equality_large:
            return False
        if abs(mus.energy) < zero_equality_large:
            return False
        if abs(mus.detector_angle) < zero_equality_large:
            return False
        if abs(mus.target_angle) < zero_equality_large:
            return False
        if abs(mus.target_density) < zero_equality_large:
            return False
        if abs(mus.time_of_flight_lenght) < zero_equality_large:
            return False
        
        # Check Calibration Settings
        if abs(cs.slope) < zero_equality_small:
            return False
        if abs(cs.offset) < zero_equality_small:
            return False
        
        # Check Depth Profile Settings
        if dps.number_of_depth_steps == 0:
            return False
        if abs(dps.depth_step_for_stopping) < zero_equality_large:
            return False
        if abs(dps.depth_step_for_output) < zero_equality_large:
            return False
        if abs(dps.depths_for_concentration_from) < zero_equality_large:
            return False
        if abs(dps.depths_for_concentration_to) < zero_equality_large:
            return False
        return True



