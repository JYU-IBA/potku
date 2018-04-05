# coding=utf-8
"""
Created on 19.3.2013
Updated on 4.4.2018

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

Dialog for the request settings
"""
__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen \n Samuli Rahkonen \n Miika Raunio"
__versio__ = "1.0"

import os
from PyQt5 import QtCore, QtGui, uic, QtWidgets

from dialogs.measurement.calibration import CalibrationDialog
from dialogs.element_selection import ElementSelectionDialog
from modules.calibration_parameters import CalibrationParameters
from modules.depth_profile_settings import DepthProfileSettings
from modules.general_functions import open_file_dialog
from modules.general_functions import save_file_dialog
from modules.input_validator import InputValidator
from modules.measuring_settings import MeasuringSettings
from widgets.simulation.settings import SimulationSettingsWidget
from widgets.detector_settings import DetectorSettingsWidget


class RequestSettingsDialog(QtWidgets.QDialog):
    
    def __init__(self, masses, request):
        """Constructor for the program
        
        Args:
            masses: Reference to Masses class object.
            request: Request class object.
        """
        super().__init__()
        self.ui = uic.loadUi(os.path.join("ui_files", "ui_measuring_settings.ui"), self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.masses = masses
        
        self.request = request
        self.settings = request.settings
        
        # Creates object that loads and holds all the measuring data
        self.measuring_unit_settings = self.settings.measuring_unit_settings
        self.calibration_settings = self.settings.calibration_settings
        self.depth_profile_settings = self.settings.depth_profile_settings

        if self.measuring_unit_settings.element.name:
            self.masses.load_isotopes(self.measuring_unit_settings.element.name,
                                      self.ui.isotopeComboBox,
                                      str(self.measuring_unit_settings.element.isotope))
        else:
            self.ui.beamIonButton.setText("Select")
            self.ui.isotopeComboBox.setEnabled(False)

        # self.masses.load_isotopes(self.measuring_unit_settings.element.name,
        #                          self.ui.isotopeComboBox,
        #                          str(self.measuring_unit_settings.element.isotope))
        
        # Tells the object to show its data in the given measuring unit widget
        self.measuring_unit_settings.show(self)
        self.depth_profile_settings.show(self)
        
        # Adds settings descriptive picture for the parameters 
        self.ui.picture.setScaledContents(True)
        
        pixmap = QtGui.QPixmap(os.path.join("images", "hardwaresetup.png"))
        self.ui.picture.setPixmap(pixmap)

        # Connect buttons.
        self.ui.loadButton.clicked.connect(
                               lambda: self.__load_file("MEASURING_UNIT_SETTINGS"))
        self.ui.saveButton.clicked.connect(
                               lambda: self.__save_file("MEASURING_UNIT_SETTINGS"))
        self.ui.loadDepthProfileSettingsButton.clicked.connect(
                               lambda: self.__load_file("DEPTH_PROFILE_SETTINGS"))
        self.ui.saveDepthProfileSettingsButton.clicked.connect(
                               lambda: self.__save_file("DEPTH_PROFILE_SETTINGS"))

        self.ui.OKButton.clicked.connect(self.update_and_close_settings)
        self.ui.applyButton.clicked.connect(self.update_settings)
        self.ui.cancelButton.clicked.connect(self.close)
        self.ui.beamIonButton.clicked.connect(
                           lambda: self.__change_element(self.ui.beamIonButton, self.ui.isotopeComboBox))
        double_validator = InputValidator()
        positive_double_validator = InputValidator(bottom=0)
        
        # Add validator that prevents user from inputting invalid values
        self.ui.energyLineEdit.setValidator(positive_double_validator)
        
        double_angle_validator = InputValidator(0, 90, 10)
        self.ui.detectorAngleLineEdit.setValidator(double_angle_validator)
        self.ui.targetAngleLineEdit.setValidator(double_angle_validator)
        
        self.ui.TOFLengthLineEdit.setValidator(positive_double_validator)
        self.ui.carbonFoilThicknessLineEdit.setValidator(positive_double_validator)
        self.ui.targetDensityLineEdit.setValidator(positive_double_validator)
        
        self.ui.depthStepForStoppingLineEdit.setValidator(double_validator)
        self.ui.depthStepForOutputLineEdit.setValidator(double_validator)
        
        self.ui.depthsForConcentrationScalingLineEdit_1.setValidator(
                                                                 double_validator)
        self.ui.depthsForConcentrationScalingLineEdit_2.setValidator(
                                                                 double_validator)

        # Add detector settings view to the settings view
        self.detector_settings = DetectorSettingsWidget()
        self.ui.tabs.addTab(self.detector_settings, "Detector Settings")

        self.calibration_settings.show(self.detector_settings)

        self.detector_settings.ui.loadCalibrationParametersButton.clicked.connect(
            lambda: self.__load_file("CALIBRATION_SETTINGS"))
        self.detector_settings.ui.saveCalibrationParametersButton.clicked.connect(
            lambda: self.__save_file("CALIBRATION_SETTINGS"))
        self.detector_settings.ui.executeCalibrationButton.clicked.connect(
            self.__open_calibration_dialog)
        self.detector_settings.ui.executeCalibrationButton.setEnabled(
            not self.request.measurements.is_empty())
        self.detector_settings.ui.slopeLineEdit.setValidator(double_validator)
        self.detector_settings.ui.offsetLineEdit.setValidator(double_validator)

        # Add simulation settings view to the settings view
        self.simulation_settings = SimulationSettingsWidget()
        self.ui.tabs.addTab(self.simulation_settings, "Simulation Settings")

        self.ui.beamIonButton.clicked.connect(
            lambda: self.__change_element(self.simulation_settings.ui.beamIonButton,
                                          self.simulation_settings.ui.isotopeComboBox))
        self.simulation_settings.ui.typeOfSimulationComboBox.addItem("ERD")
        self.simulation_settings.ui.typeOfSimulationComboBox.addItem("RBS")

        self.exec_()

    def __open_calibration_dialog(self):
        measurements = [self.request.measurements.get_key_value(key)
                        for key in self.request.measurements.measurements.keys()]
        CalibrationDialog(measurements, self.settings, self.masses, self)

    def __load_file(self, settings_type):
        """Opens file dialog and loads and shows selected ini file's values.
        
        Args:
            settings_type: (string) selects which settings file type will be loaded. 
                           Can be "MEASURING_UNIT_SETTINGS", 
                           "DEPTH_PROFILE_SETTINGS" or "CALIBRATION_SETTINGS"
        """
        filename = open_file_dialog(self, self.request.directory,
                                    "Open settings file", "Settings file (*.ini)")

        if settings_type == "MEASURING_UNIT_SETTINGS":
            settings = MeasuringSettings()
            settings.load_settings(filename)
            self.masses.load_isotopes(settings.element.name,
                                      self.isotopeComboBox,
                                      str(settings.element.isotope))
            settings.show(self)
        elif settings_type == "DEPTH_PROFILE_SETTINGS":
            settings = DepthProfileSettings()
            settings.show(self)
        elif settings_type == "CALIBRATION_SETTINGS":
            settings = CalibrationParameters()
            settings.show(self.detector_settings)
        else:
            return


    def __save_file(self, settings_type):
        """Opens file dialog and sets and saves the settings to a ini file.
        """

        if settings_type == "MEASURING_UNIT_SETTINGS":
            settings = MeasuringSettings()
        elif settings_type == "DEPTH_PROFILE_SETTINGS":
            settings = DepthProfileSettings()
        elif settings_type == "CALIBRATION_SETTINGS":
            settings = CalibrationParameters()
        else:
            return

        filename = save_file_dialog(self, self.request.directory,
                                    "Open measuring unit settings file",
                                    "Settings file (*.ini)")

        if filename:
            if settings_type == "CALIBRATION_SETTINGS":
                settings.set_settings(self.detector_settings)
                settings.save_settings(filename)
            else:
                settings.set_settings(self)
                settings.save_settings(filename)


    def update_and_close_settings(self):
        """Updates measuring settings values with the dialog's values and saves them
        to default ini file.
        """
        try:
            self.__update_settings()
            self.close()
        except TypeError:
            # Message has already been shown in update_settings()
            pass
            
    def update_settings(self):
        """Update values from dialog to every setting object.
        """
        try:
            self.__update_settings()
        except TypeError:
            # Message is already displayed within private method.
            pass
    
    def __update_settings(self):
        """Update values from dialog to every setting object.
        """
        # TODO: Proper checking for all setting values
        # This try-catch works for Beam Element that has not been set yet.
        try:
            self.measuring_unit_settings.set_settings(self)
            self.calibration_settings.set_settings(self)
            self.depth_profile_settings.set_settings(self)
            
            if not self.settings.has_been_set():
                raise TypeError
            
            self.measuring_unit_settings.save_settings()
            self.calibration_settings.save_settings()
            self.depth_profile_settings.save_settings()
        except TypeError:
            QtWidgets.QMessageBox.question(self, "Warning", "Some of the setting values have not been set.\n" +
                                           "Please input setting values to save them.", QtWidgets.QMessageBox.Ok,
                                           QtWidgets.QMessageBox.Ok)
            raise TypeError
    
    def __change_element(self, button, comboBox):
        """Opens element selection dialog and loads selected element's isotopes 
        to a combobox.
        
        Args:
            button: button whose text is changed accordingly to the made selection.
        """
        dialog = ElementSelectionDialog()
        if dialog.element:
            button.setText(dialog.element)
            # Enabled settings once element is selected
            self.__enabled_element_information()  
        self.masses.load_isotopes(dialog.element, comboBox,
                                  self.measuring_unit_settings.element.isotope)
        
    def __enabled_element_information(self):
        self.ui.isotopeComboBox.setEnabled(True)
        self.ui.isotopeLabel.setEnabled(True)
        self.ui.OKButton.setEnabled(True)

