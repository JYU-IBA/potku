# coding=utf-8
'''
Created on 18.3.2013
Updated on 26.6.2013

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

Holds, loads and saves measuring settings.
'''
__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen \n Samuli Rahkonen \n Miika Raunio"
__versio__ = "1.0"

import configparser, os
from Modules.Element import Element

class MeasuringSettings:
    """MeasuringSettings holds the all project specific measurement unit parameters.
    """
    def __init__(self, settings_filepath=None):
        """Inits MeasuringSettings.
        
        Args:
            settings_filepath: filepath for the settings file to be loaded.
        """
        self.measuring_unit_settings_filename = "measuring_unit_settings.ini"
        self.config = configparser.ConfigParser()
        # This is used to determine if opened measurement 
        # uses its own settings ('MEASUREMENT') or project's 
        # settings ('PROJECT') 
        self.use_settings = ""         
        
        self.element = Element()
        self.energy = 0
        self.detector_angle = 0
        self.target_angle = 0
        self.time_of_flight_lenght = 0
        self.carbon_foil_thickness = 0
        self.target_density = 0

        self.__set_config_parameters()
        if settings_filepath == None:
            return
        
        self.filepath = os.path.join(settings_filepath,
                                     self.measuring_unit_settings_filename) 
        if not os.path.exists(self.filepath):
            # print("Creating " + self.filepath)
            with open(self.filepath, 'wt+') as configfile:
                self.config.write(configfile)
        
        self.filepath = os.path.join(settings_filepath,
                                     self.measuring_unit_settings_filename) 
        if not os.path.exists(settings_filepath):
            # print("Creating " + settings_filepath)
            with open(settings_filepath, 'wt+') as configfile:
                self.config.write(configfile)

        self.load_settings(self.filepath)

        
    def show(self, dialog):
        """Shows the measuring parameters in the given measuring settings dialog.
        
        Args:
            dialog: Measuring Settings QDialog whose fields are updated with the 
            MeasuringSettings parameters.
        """
        try:
            if self.use_settings == "PROJECT":
                dialog.ui.useProjectSettingsValuesCheckBox.setChecked(True)
            elif self.use_settings == "MEASUREMENT":
                dialog.ui.useProjectSettingsValuesCheckBox.setChecked(False)
        except:
            print("Can't find the checkbox in the dialog")
        if self.element.name:
            dialog.elementButton.setText(self.element.name)
            dialog.isotopeComboBox.setEnabled(True)
        else:
            dialog.elementButton.setText("Select")
            dialog.isotopeComboBox.setEnabled(False)
        dialog.energyLineEdit.setText(str(self.energy))
        dialog.detectorAngleLineEdit.setText(str(self.detector_angle))
        dialog.targetAngleLineEdit.setText(str(self.target_angle))
        dialog.TOFLengthLineEdit.setText(str(self.time_of_flight_lenght))
        dialog.carbonFoilThicknessLineEdit.setText(str(self.carbon_foil_thickness))
        dialog.targetDensityLineEdit.setText(str(self.target_density))
        
        
    def set_settings(self, dialog, used_settings=None):
        """Takes inputted parameters from the given dialog and sets them to the 
        corresponding object's parameters
        
        Args:
            dialog: Measuring Settings QDialog from which the parameters are taken.
        """
        
        if used_settings == None:
            self.use_settings = ""
        else:
            self.use_settings = used_settings
        
        isotope_index = dialog.isotopeComboBox.currentIndex()
        isotope_data = dialog.isotopeComboBox.itemData(isotope_index)
        self.element = Element(dialog.elementButton.text(), isotope_data[0])
        self.energy = float(dialog.energyLineEdit.text())
        self.detector_angle = float(dialog.detectorAngleLineEdit.text())
        self.target_angle = float(dialog.targetAngleLineEdit.text())
        self.time_of_flight_lenght = float(dialog.TOFLengthLineEdit.text())
        self.carbon_foil_thickness = float(
                                       dialog.carbonFoilThicknessLineEdit.text())
        self.target_density = float(dialog.targetDensityLineEdit.text())
        
        
    def load_settings(self, filepath):
        """Loads settings' parameters from the given filepath.
        
        Args:
            filepath: Filepath to the settings file.
        """
        if not os.path.exists(filepath):
            print("Filepath " + filepath + " does not exist.")
            return
        self.config.read(filepath)
        try:
            # For line length.
            mu = "measuring_unit"
            tofl = "time_of_flight_lenght"
            cft = "carbon_foil_thickness"
            self.use_settings = self.config['default']['use_settings']
            self.element = Element(self.config['beam']['element'],
                                   self.config['beam']['isotope'])
            self.energy = float(self.config['beam']['energy'])
            self.detector_angle = float(self.config[mu]['detector_angle'])
            self.target_angle = float(self.config[mu]['target_angle'])
            self.time_of_flight_lenght = float(self.config[mu][tofl])
            self.carbon_foil_thickness = float(self.config[mu][cft])
            self.target_density = float(self.config[mu]['target_density'])
        except:  # If there is a problem, use default values
            print("Couldn't load measurement unit settings from file")
    
        
    def __set_config_parameters(self):
        # For line length.
        mu = "measuring_unit" 
        tofl = "time_of_flight_lenght"
        cft = "carbon_foil_thickness"
        self.config.add_section('default')
        self.config.set('default', 'use_settings', str(self.use_settings))
        self.config.add_section('beam')
        self.config.set('beam', 'element', self.element.name)
        self.config.set('beam', 'isotope', str(self.element.isotope))
        self.config.set('beam', 'energy', str(self.energy))
        self.config.add_section(mu)
        self.config.set(mu, 'detector_angle', str(self.detector_angle))
        self.config.set(mu, 'target_angle', str(self.target_angle))
        self.config.set(mu, tofl, str(self.time_of_flight_lenght)) 
        self.config.set(mu, cft, str(self.carbon_foil_thickness))
        self.config.set(mu, 'target_density', str(self.target_density))
    
    
    def save_settings(self, filepath=None):
        """Saves settings' parameters to the given filepath.
        
        Args:
            filepath: Filepath to the settings file.
        """
        # For line length.
        mu = "measuring_unit" 
        tofl = "time_of_flight_lenght"
        cft = "carbon_foil_thickness"
        self.config['default']['use_settings'] = self.use_settings
        self.config['beam']['element'] = str(self.element.name)
        self.config['beam']['isotope'] = str(self.element.isotope)
        self.config['beam']['energy'] = str(self.energy)
        self.config[mu]['detector_angle'] = str(self.detector_angle)
        self.config[mu]['target_angle'] = str(self.target_angle)
        self.config[mu][tofl] = str(self.time_of_flight_lenght)
        self.config[mu][cft] = str(self.carbon_foil_thickness)
        self.config[mu]['target_density'] = str(self.target_density)
        
        if filepath == None:
            filepath = self.filepath
        
        with open(filepath, 'wt+') as configfile:
            self.config.write(configfile)
        
