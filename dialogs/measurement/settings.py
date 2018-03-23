# coding=utf-8
"""
Created on 17.4.2013
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

import os
from PyQt5 import QtCore, QtGui, uic, QtWidgets

from modules.calibration_parameters import CalibrationParameters
from modules.general_functions import open_file_dialog, save_file_dialog
from modules.measuring_settings import MeasuringSettings
from modules.input_validator import InputValidator
from dialogs.measurement.element_selection import ElementSelectionDialog
from dialogs.measurement.calibration import CalibrationDialog

class MeasurementUnitSettings(QtWidgets.QDialog):
    def __init__(self, measurement_settings, masses):
        """Constructor for the program
        
        Args:
            measurement_settings: Settings class object
            masses: Reference to Masses class object.
        """
        super().__init__()
        self.ui = uic.loadUi(os.path.join("ui_files",
                              "ui_measurement_measuring_unit_settings.ui"), self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.masses = masses
        
        self.__measurement_settings = measurement_settings
        
        proj_settings = measurement_settings.project_settings
        self.project_settings = proj_settings.measuring_unit_settings
        
        self.default_folder = os.path.curdir  # TODO: DO NOT USE CURRENT DIRECTORY!
        
        # Get the settings from the measurement
        self.settings = measurement_settings.measuring_unit_settings
        # Choose which settings' parameters are shown. The project settings' or the 
        # measurement settings' parameters 
        if self.settings.use_settings == "PROJECT" or self.settings.use_settings == "":
            self.ui.useProjectSettingsValuesCheckBox.setChecked(True)
            self.project_settings.show(self)  # Show the project's settings
            self.masses.load_isotopes(self.project_settings.element.name,
                                      self.ui.isotopeComboBox,
                                      str(self.project_settings.element.isotope))
        elif self.settings.use_settings == "MEASUREMENT":
            self.ui.useProjectSettingsValuesCheckBox.setChecked(False)
            self.settings.show(self)  # Show the measurement's settings
            self.masses.load_isotopes(self.settings.element.name,
                                      self.ui.isotopeComboBox,
                                      str(self.settings.element.isotope))
        
        if self.ui.isotopeComboBox.currentText() != "":
            self.ui.isotopeComboBox.setEnabled(True)
        
        # Adds settings descriptive picture for the parameters 
        self.ui.picture.setScaledContents(True)
        
        pixmap = QtGui.QPixmap(os.path.join("images", "hardwaresetup.png"))
        self.ui.picture.setPixmap(pixmap)

        self.loadButton.clicked.connect(self.__load_file)
        self.saveButton.clicked.connect(self.__save_file)
        self.ui.OKButton.clicked.connect(self.update_and_close_settings)
        self.ui.cancelButton.clicked.connect(self.close)
        self.ui.elementButton.clicked.connect(
                          lambda: self.__change_element(self.ui.elementButton))
        self.ui.useProjectSettingsValuesCheckBox.clicked.connect(
                                                         self.__change_settings)
        
        positive_double_validator = InputValidator(bottom=0)
        self.ui.energyLineEdit.setValidator(positive_double_validator)
        
        double_angle_validator = InputValidator(0, 90, 10)
        self.ui.detectorAngleLineEdit.setValidator(double_angle_validator)
        self.ui.targetAngleLineEdit.setValidator(double_angle_validator)
        
        self.ui.TOFLengthLineEdit.setValidator(positive_double_validator)
        self.ui.carbonFoilThicknessLineEdit.setValidator(positive_double_validator)
        self.ui.targetDensityLineEdit.setValidator(positive_double_validator)
        
        
        
        self.exec_()
    
    
    def __change_settings(self):
        """Shows project settings' parameters in dialog if checkbox is checked.
        """
        if self.ui.useProjectSettingsValuesCheckBox.isChecked():
            self.project_settings.show(self)

        
    def __load_file(self):
        """Opens file dialog and loads and shows selected ini file's values.
        """
        filename = open_file_dialog(self, self.default_folder,
                                    "Load measuring unit settings file",
                                    "Settings file (*.ini)")
        if filename:  # TODO: toistuvaa koodia
            settings = MeasuringSettings()
            settings.load_settings(filename)
            self.masses.load_isotopes(settings.element.name,
                                      self.isotopeComboBox,
                                      str(settings.element.isotope))
            settings.show(self)
        
        
    def __save_file(self):
        """Opens file dialog and sets and saves the settings to a ini file.
        """
        filename = save_file_dialog(self, self.default_folder,
                                    "Save measuring unit settings file",
                                    "Settings file (*.ini)")
        if filename:
            settings = MeasuringSettings()
            settings.set_settings(self)
            settings.save_settings(filename)
        
        
    def update_and_close_settings(self):
        """Updates measuring settings values with the dialog's values and saves them to default ini file.
        """
        try:
            if self.ui.useProjectSettingsValuesCheckBox.isChecked():
                use_settings = "PROJECT"
            else:
                use_settings = "MEASUREMENT"
            
            self.settings.set_settings(self, use_settings)
            
            if not self.__measurement_settings.has_been_set() and \
            use_settings == "MEASUREMENT":
                raise TypeError
            
            self.settings.save_settings()
            self.close()
        except TypeError:
            QtWidgets.QMessageBox.question(self,
                "Warning",
                "Some of the setting values have not been set.\n" + \
                "Please input setting values to save them.",
                QtWidgets.QMessageBox.Ok)
            
            
    def __change_element(self, button):
        """Opens element selection dialog and loads selected element's isotopes to a combobox.
        
        Args:
            button: button whose text is changed accordingly to the made selection.
        """
        dialog = ElementSelectionDialog()
        if dialog.element != None:
            button.setText(dialog.element)
            self.__enabled_element_information()  # Enabled settings once element is selected
        self.masses.load_isotopes(dialog.element, self.isotopeComboBox, str(self.settings.element.isotope))

        
    def __enabled_element_information(self):
        self.ui.isotopeComboBox.setEnabled(True)
        self.ui.isotopeLabel.setEnabled(True)
        self.ui.OKButton.setEnabled(True)




class CalibrationSettings(QtWidgets.QDialog):
    def __init__(self, measurement):
        """Constructor for the program
        
        Args:
            measurement: Measurement class object.
        """
        super().__init__()
        self.default_folder = os.path.curdir
        self.measurement = measurement
        self.masses = self.measurement.project.masses
        
        self.ui = uic.loadUi(os.path.join("ui_files",
                              "ui_measurement_calibration_parameters.ui"), self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        
        self.__measurement_settings = self.measurement.measurement_settings
        self.project_settings = self.__measurement_settings.project_settings.\
            calibration_settings
        
        # Get the settings from the measurement
        self.settings = self.measurement.measurement_settings.calibration_settings
        
        # Choose which settings' parameters are shown. The project settings' or the 
        # measurement settings' parameters 
        use_settings = self.settings.use_settings
        if use_settings == "PROJECT" or use_settings == "":
            self.ui.useProjectSettingsValuesCheckBox.setChecked(True)
            self.project_settings.show(self)  # Show the project's settings
        elif use_settings == "MEASUREMENT":
            self.ui.useProjectSettingsValuesCheckBox.setChecked(False)
            self.settings.show(self)  # Show the measurement's settings
        

        self.loadCalibrationParametersButton.clicked.connect(self.__load_file)
        self.saveCalibrationParametersButton.clicked.connect(self.__save_file)
        self.ui.OKButton.clicked.connect(self.update_and_close_settings)
        self.ui.cancelButton.clicked.connect(self.close)
        self.ui.useProjectSettingsValuesCheckBox.clicked.connect(
                                                         self.__change_settings)
        self.ui.executeCalibrationButton.clicked.connect(self.__open_calibration)
        
        double_validator = InputValidator()
        self.ui.slopeLineEdit.setValidator(double_validator)
        self.ui.offsetLineEdit.setValidator(double_validator)
        
        self.exec_()
    
    
    def __open_calibration(self):
        measurements = [self.measurement]
        settings = self.measurement.measurement_settings
        # Ask from the measurement all the correct settings to be used for the calibration
        CalibrationDialog(measurements, settings.get_measurement_settings(),
                          self.masses, self) 
        
    
    
    def __change_settings(self):
        """Shows project settings' parameters in dialog if checkbox is checked.
        """
        if self.ui.useProjectSettingsValuesCheckBox.isChecked():
            self.project_settings.show(self)
        
        
    def __load_file(self):
        """Opens file dialog and loads and shows selected ini file's values.
        """
        filename = open_file_dialog(self, self.default_folder,
                                    "Load calibration settings file",
                                    "Settings file (*.ini)")
        if filename:
            settings = CalibrationParameters()
            settings.load_settings(filename)
            settings.show(self)
        
        
    def __save_file(self):
        """Opens file dialog and sets and saves the settings to a ini file.
        """
        filename = save_file_dialog(self, self.default_folder,
                                    "Save calibration settings file",
                                    "Settings file (*.ini)")
        if filename:
            settings = CalibrationParameters()
            settings.set_settings(self)
            settings.save_settings(filename)
        
        
    def update_and_close_settings(self):
        """Updates measuring settings values with the dialog's values and saves
        them to default ini file.
        """
        try:
            if self.ui.useProjectSettingsValuesCheckBox.isChecked():
                use_settings = "PROJECT"
            else:
                use_settings = "MEASUREMENT"
            
            self.settings.set_settings(self, use_settings)
            
            if not self.__measurement_settings.has_been_set() and \
            use_settings == "MEASUREMENT":
                raise TypeError
            
            self.settings.save_settings()
            self.close()
        except TypeError:
            QtWidgets.QMessageBox.question(self,
                "Warning",
                "Some of the setting values have not been set.\n" + \
                "Please input setting values to save them.",
                QtWidgets.QMessageBox.Ok)



class DepthProfileSettings(QtWidgets.QDialog):
    def __init__(self, measurement_settings):
        """Constructor for the program
        
        Args:
            measurement_settings:    
        """
        super().__init__()
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)


        self.default_folder = os.path.curdir
        self.ui = uic.loadUi("ui_files/ui_measurement_depth_profile_settings.ui", self)
        
        self.__measurement_settings = measurement_settings
        self.project_settings = measurement_settings.project_settings.\
            depth_profile_settings
        
        # Get the settings from the measurement
        self.settings = measurement_settings.depth_profile_settings
        
        # Choose which settings' parameters are shown. The project settings' or the 
        # measurement settings' parameters 
        if self.settings.use_settings == "PROJECT" or self.settings.use_settings == "":
            self.ui.useProjectSettingsValuesCheckBox.setChecked(True)
            self.project_settings.show(self)  # Show the project's settings
        elif self.settings.use_settings == "MEASUREMENT":
            self.ui.useProjectSettingsValuesCheckBox.setChecked(False)
            self.settings.show(self)  # Show the measurement's settings
        

        self.ui.loadDepthProfileSettingsButton.clicked.connect(self.__load_file)
        self.ui.saveDepthProfileSettingsButton.clicked.connect(self.__save_file)
        self.ui.OKButton.clicked.connect(self.update_and_close_settings)
        self.ui.cancelButton.clicked.connect(self.close)
        self.ui.useProjectSettingsValuesCheckBox.clicked.connect(self.__change_settings)
        
        double_validator = InputValidator()
        
        self.ui.depthStepForStoppingLineEdit.setValidator(double_validator)
        self.ui.depthStepForOutputLineEdit.setValidator(double_validator)
        
        self.ui.depthsForConcentrationScalingLineEdit_1.setValidator(double_validator)
        self.ui.depthsForConcentrationScalingLineEdit_2.setValidator(double_validator)
        
        self.exec_()
    
    
    def __change_settings(self):
        """Shows project settings' parameters in dialog if checkbox is checked.
        """
        if self.ui.useProjectSettingsValuesCheckBox.isChecked():
            self.project_settings.show(self)
        
        
    def __load_file(self):
        """Opens file dialog and loads and shows selected ini file's values.
        """
        filename = open_file_dialog(self, self.default_folder,
                                    "Load calibration settings file",
                                    "Settings file (*.ini)")
        if filename:
            settings = DepthProfileSettings()
            settings.load_settings(filename)
            settings.show(self)
        
        
    def __save_file(self):
        """Opens file dialog and sets and saves the settings to a ini file.
        """
        filename = save_file_dialog(self, self.default_folder,
                                    "Save calibration settings file",
                                    "Settings file (*.ini)")
        if filename:
            settings = DepthProfileSettings()
            settings.set_settings(self)
            settings.save_settings(filename)
        
        
    def update_and_close_settings(self):
        """Updates measuring settings values with the dialog's values and saves them to default ini file.
        """
        try:
            if self.ui.useProjectSettingsValuesCheckBox.isChecked():
                use_settings = "PROJECT"
            else:
                use_settings = "MEASUREMENT"
            
            self.settings.set_settings(self, use_settings)
            
            if not self.__measurement_settings.has_been_set() and \
            use_settings == "MEASUREMENT":
                raise TypeError
                
            self.settings.save_settings()
            self.close()
        except TypeError:
            QtWidgets.QMessageBox.question(self,
                "Warning",
                "Some of the setting values have not been set.\n" + \
                "Please input setting values to save them.",
                QtWidgets.QMessageBox.Ok)



