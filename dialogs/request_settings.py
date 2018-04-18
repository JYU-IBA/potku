# coding=utf-8
"""
Created on 19.3.2013
Updated on 17.4.2018

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

from modules.detector import DetectorType
from modules.element import Element
from modules.measurement import MeasurementProfile
from modules.simulation import SimulationMode, SimulationType
from widgets.depth_profile_settings import DepthProfileSettingsWidget
from widgets.measurement.settings import MeasurementSettingsWidget

__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen \n Samuli Rahkonen \n Miika Raunio \n" \
             "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"
__version__ = "2.0"

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
from widgets.foil import FoilWidget
from widgets.distance import DistanceWidget
from dialogs.simulation.foil import FoilDialog
from modules.foil import CircularFoil


class RequestSettingsDialog(QtWidgets.QDialog):
    
    def __init__(self, masses, request, icon_manager):
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
        self.icon_manager = icon_manager

        # Creates object that loads and holds all the measuring data
        self.measuring_unit_settings = self.settings.measuring_unit_settings
        self.calibration_settings = self.settings.calibration_settings
        self.depth_profile_settings = self.settings.depth_profile_settings

        # self.masses.load_isotopes(self.measuring_unit_settings.element.name,
        #                          self.ui.isotopeComboBox,
        #                          str(self.measuring_unit_settings.element.isotope))

        # Connect buttons.
        self.ui.OKButton.clicked.connect(self.update_and_close_settings)
        self.ui.applyButton.clicked.connect(self.update_settings)
        self.ui.cancelButton.clicked.connect(self.close)
        double_validator = InputValidator()
        positive_double_validator = InputValidator(bottom=0)
        
        # Add measurement settings view to the settings view
        self.measurement_settings_widget = MeasurementSettingsWidget()
        self.ui.tabs.addTab(self.measurement_settings_widget, "Measurement")

        if self.measuring_unit_settings.element.name:
            self.masses.load_isotopes(self.measuring_unit_settings.element.name,
                                      self.measurement_settings_widget.ui.isotopeComboBox,
                                      str(self.measuring_unit_settings.element.isotope))
        else:
            self.measurement_settings_widget.ui.beamIonButton.setText("Select")
            self.measurement_settings_widget.ui.isotopeComboBox.setEnabled(False)

        self.measurement_settings_widget.ui.loadButton.clicked\
            .connect(lambda: self.__load_file("MEASURING_UNIT_SETTINGS"))
        self.measurement_settings_widget.ui.saveButton.clicked\
            .connect(lambda: self.__save_file("MEASUREMENT_SETTINGS"))
        self.measurement_settings_widget.ui.beamIonButton.clicked.connect(
            lambda: self.__change_element(self.measurement_settings_widget.ui.beamIonButton,
                                          self.measurement_settings_widget.ui.isotopeComboBox))
        self.measurement_settings_widget.ui.TOFLengthLineEdit.setValidator(positive_double_validator)
        self.measurement_settings_widget.ui.carbonFoilThicknessLineEdit.setValidator(positive_double_validator)
        self.measurement_settings_widget.ui.targetDensityLineEdit.setValidator(positive_double_validator)

        self.measurement_settings_widget.ui.energyLineEdit.setValidator(positive_double_validator)
        double_angle_validator = InputValidator(0, 90, 10)
        self.measurement_settings_widget.ui.detectorThetaLineEdit.setValidator(double_angle_validator)
        self.measurement_settings_widget.ui.targetThetaLineEdit.setValidator(double_angle_validator)

        self.measurement_settings_widget.ui.picture.setScaledContents(True)
        pixmap = QtGui.QPixmap(os.path.join("images", "hardwaresetup.png"))
        self.measurement_settings_widget.ui.picture.setPixmap(pixmap)

#        self.measuring_unit_settings.show(self.measurement_settings_widget)
        self.show_settings()

        # Add detector settings view to the settings view
        self.detector_settings_widget = DetectorSettingsWidget()
        self.ui.tabs.addTab(self.detector_settings_widget, "Detector")

        # Temporary foils list which holds all the information given in the foil dialog
        # If user presses ok or apply, these vlues will be svaed into request's default detector
        self.tmp_foil_info = []

        # List of foils that are timing foils
        self.tof_foils = []

        # Add foil widgets and foil objects
        self.detector_structure_widgets = []
        self.foils_layout = self._add_default_foils()
        self.detector_settings_widget.ui.detectorScrollAreaContents.layout().addLayout(self.foils_layout)

        self.detector_settings_widget.ui.newFoilButton.clicked.connect(lambda: self._add_new_foil())

        self.calibration_settings.show(self.detector_settings_widget)

        self.detector_settings_widget.ui.saveButton.clicked \
            .connect(lambda: self.__save_file("DETECTOR_SETTINGS"))
        self.detector_settings_widget.ui.loadCalibrationParametersButton.clicked.connect(
            lambda: self.__load_file("CALIBRATION_SETTINGS"))
        self.detector_settings_widget.ui.saveCalibrationParametersButton.clicked.connect(
            lambda: self.__save_file("CALIBRATION_SETTINGS"))
        self.detector_settings_widget.ui.executeCalibrationButton.clicked.connect(
            self.__open_calibration_dialog)
        self.detector_settings_widget.ui.executeCalibrationButton.setEnabled(
            not self.request.samples.measurements.is_empty())
        self.detector_settings_widget.ui.slopeLineEdit.setValidator(double_validator)
        self.detector_settings_widget.ui.offsetLineEdit.setValidator(double_validator)

        # Add simulation settings view to the settings view
        self.simulation_settings_widget = SimulationSettingsWidget()
        self.ui.tabs.addTab(self.simulation_settings_widget, "Simulation")

        self.simulation_settings_widget.ui.typeOfSimulationComboBox.addItem("ERD")
        self.simulation_settings_widget.ui.typeOfSimulationComboBox.addItem("RBS")
        self.simulation_settings_widget.ui.saveButton.clicked \
            .connect(lambda: self.__save_file("SIMULATION_SETTINGS"))

        # Add depth profile settings view to the settings view
        self.depth_profile_settings_widget = DepthProfileSettingsWidget()
        self.ui.tabs.addTab(self.depth_profile_settings_widget, "Depth Profile")
        self.depth_profile_settings.show(self.depth_profile_settings_widget)

        self.depth_profile_settings_widget.ui.loadButton.clicked.connect(
            lambda: self.__load_file("DEPTH_PROFILE_SETTINGS"))
        self.depth_profile_settings_widget.ui.saveButton.clicked.connect(
            lambda: self.__save_file("DEPTH_PROFILE_SETTINGS"))

        self.depth_profile_settings_widget.ui.depthStepForStoppingLineEdit.setValidator(double_validator)
        self.depth_profile_settings_widget.ui.depthStepForOutputLineEdit.setValidator(double_validator)

        self.depth_profile_settings_widget.ui.depthsForConcentrationScalingLineEdit_1.setValidator(double_validator)
        self.depth_profile_settings_widget.ui.depthsForConcentrationScalingLineEdit_2.setValidator(double_validator)

        self.exec_()

    def _add_new_foil(self):
        distance_widget = DistanceWidget()
        self.detector_structure_widgets.append(distance_widget)
        foil_widget = FoilWidget()
        foil_widget.ui.foilButton.clicked.connect(lambda: self._open_composition_dialog())
        foil_widget.ui.timingFoilCheckBox.stateChanged.connect(lambda: self._check_and_add())
        self.detector_structure_widgets.append(foil_widget)
        self.foils_layout.addWidget(distance_widget)
        self.foils_layout.addWidget(foil_widget)

    def _add_default_foils(self):
        layout = QtWidgets.QHBoxLayout()

        target = QtWidgets.QLabel("Target")
        layout.addWidget(target)

        i = 0
        while i in range(6):
            foil_widget = FoilWidget()
            new_foil = CircularFoil("Foil")
            self.tmp_foil_info.append(new_foil)
            foil_widget.ui.foilButton.clicked.connect(lambda: self._open_composition_dialog())
            distance_widget = DistanceWidget()
            self.detector_structure_widgets.append(distance_widget)
            self.detector_structure_widgets.append(foil_widget)
            layout.addWidget(self.detector_structure_widgets[i])
            layout.addWidget(self.detector_structure_widgets[i + 1])
            i = i + 2
        return layout

    def _check_and_add(self):
        check_box = self.sender()
        i = 1
        while i in range(len(self.detector_structure_widgets)):
            if self.detector_structure_widgets[i].ui.timingFoilCheckBox is self.sender():
                if check_box.isChecked():
                    self.tof_foils.append(self.detector_structure_widgets[i])
                else:
                    self.tof_foils.remove(self.detector_structure_widgets[i])

    def _open_composition_dialog(self):
        foil_name = self.sender().text()
        foil_object_index = -1
        for i in range(len(self.tmp_foil_info)):
            if foil_name == self.tmp_foil_info[i].name:
                foil_object_index = i
                break
        FoilDialog(self.tmp_foil_info, foil_object_index, self.icon_manager)
        self.sender().setText(self.tmp_foil_info[foil_object_index].name)

    def __open_calibration_dialog(self):
        measurements = [self.request.measurements.get_key_value(key)
                        for key in self.request.samples.measurements.measurements.keys()]
        CalibrationDialog(measurements, self.settings, self.masses, self)

    def show_settings(self):
        if self.request.default_measurement.ion:
            self.measurement_settings_widget.ui.beamIonButton.setText(self.request.default_measurement.ion.name)
            # TODO Check that the isotope is also set.
            self.measurement_settings_widget.ui.isotopeComboBox.setEnabled(True)
        else:
            self.measurement_settings_widget.ui.beamIonButton.setText("Select")
            self.measurement_settings_widget.ui.isotopeComboBox.setEnabled(False)

        self.measurement_settings_widget.nameLineEdit.setText(self.request.default_measurement.measurement_name)
        self.measurement_settings_widget.descriptionLineEdit.setPlainText(self.request.default_measurement.description)
        self.measurement_settings_widget.energyLineEdit.setText(str(self.request.default_measurement.energy))
        self.measurement_settings_widget.chargeLineEdit.setText(str(self.request.default_measurement.charge))
        self.measurement_settings_widget.spotSizeXLineEdit.setText(str(self.request.default_measurement.spot_size[0]))
        self.measurement_settings_widget.spotSizeYLineEdit.setText(str(self.request.default_measurement.spot_size[1]))
        self.measurement_settings_widget.divergenceLineEdit.setText(str(self.request.default_measurement.divergence))
        self.measurement_settings_widget.profileComboBox.setCurrentIndex(self.request.default_measurement.profile.value)
        self.measurement_settings_widget.energyDistLineEdit.setText(str(self.request.default_measurement.energy_dist))
        self.measurement_settings_widget.fluenceLineEdit.setText(str(self.request.default_measurement.fluence))
        self.measurement_settings_widget.currentLineEdit.setText(str(self.request.default_measurement.current))
        self.measurement_settings_widget.timeLineEdit.setText(str(self.request.default_measurement.beam_time))
        self.measurement_settings_widget.detectorThetaLineEdit.setText(str(self.request.default_measurement.detector_theta))
        self.measurement_settings_widget.detectorFiiLineEdit.setText(str(self.request.default_measurement.detector_fii))
        self.measurement_settings_widget.targetThetaLineEdit.setText(str(self.request.default_measurement.target_theta))
        self.measurement_settings_widget.targetFiiLineEdit.setText(str(self.request.default_measurement.target_fii))

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
            settings.show(self.detector_settings_widget)
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
        elif settings_type == "DETECTOR_SETTINGS":
            pass
        elif settings_type == "MEASUREMENT_SETTINGS":
            pass
        elif settings_type == "SIMULATION_SETTINGS":
            pass
        else:
            return

        filename = save_file_dialog(self, self.request.directory,
                                    "Open measuring unit settings file",
                                    "Settings file (*.ini)")

        self.update_settings()
        if filename:
            if settings_type == "CALIBRATION_SETTINGS":
                settings.set_settings(self.detector_settings_widget)
                settings.save_settings(filename)
            elif settings_type == "MEASUREMENT_SETTINGS":
                self.request.default_measurement.save_settings(filename)
            elif settings_type == "SIMULATION_SETTINGS":
                self.request.default_simulation.save_settings(filename)
            elif settings_type == "DETECTOR_SETTINGS":
                self.request.detector.save_settings(filename)
            else:
                settings.set_settings(self.measurement_settings_widget)
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
        """Reads values from Request Settings dialog and updates them in default objects.
        """
        # TODO: Proper checking for all setting values
        try:
            # Measurement settings
            isotope_index = self.measurement_settings_widget.isotopeComboBox.currentIndex()
            if isotope_index != -1:
                isotope_data = self.measurement_settings_widget.isotopeComboBox.itemData(isotope_index)
                self.request.default_measurement.ion = Element(self.measurement_settings_widget.beamIonButton.text(), isotope_data[0])
                self.request.default_measurement.measurement_name = self.measurement_settings_widget.nameLineEdit.text()
                self.request.default_measurement.description = self.measurement_settings_widget.descriptionLineEdit.toPlainText()
                self.request.default_measurement.energy = self.measurement_settings_widget.energyLineEdit.text()
                self.request.default_measurement.charge = self.measurement_settings_widget.chargeLineEdit.text()
                self.request.default_measurement.spot_size = [self.measurement_settings_widget.spotSizeXLineEdit.text(),
                                                              self.measurement_settings_widget.spotSizeYLineEdit.text()]
                self.request.default_measurement.divergence = self.measurement_settings_widget.divergenceLineEdit.text()
                self.request.default_measurement.profile = MeasurementProfile(self.measurement_settings_widget.profileComboBox.currentIndex())
                self.request.default_measurement.energy_dist = self.measurement_settings_widget.energyDistLineEdit.text()
                self.request.default_measurement.fluence = self.measurement_settings_widget.fluenceLineEdit.text()
                self.request.default_measurement.current = self.measurement_settings_widget.currentLineEdit.text()
                self.request.default_measurement.beam_time = self.measurement_settings_widget.timeLineEdit.text()
                self.request.default_measurement.detector_theta = self.measurement_settings_widget.detectorThetaLineEdit.text()
                self.request.default_measurement.detector_fii = self.measurement_settings_widget.detectorFiiLineEdit.text()
                self.request.default_measurement.target_theta = self.measurement_settings_widget.targetThetaLineEdit.text()
                self.request.default_measurement.target_fii = self.measurement_settings_widget.targetFiiLineEdit.text()

                self.request.default_measurement.save_settings(self.request.default_folder + os.sep + "Default")

            # Detector settings
            self.request.detector.name = self.detector_settings_widget.nameLineEdit.text()
            self.request.detector.description = self.detector_settings_widget.descriptionLineEdit.toPlainText()
            self.request.detector.detector_type = DetectorType(self.detector_settings_widget.typeComboBox.currentIndex())
            self.calibration_settings.set_settings(self.detector_settings_widget)
            self.request.detector.calibration = self.calibration_settings
            # Detector foils
            for i in range(len(self.detector_structure_widgets)):
                widget = self.detector_structure_widgets[i]
                if type(widget) is DistanceWidget:
                    distance = widget.ui.distanceEdit.text()
                    # TODO: Add the distance as the attribute of the Foil corresponding to the Foilwidget in position i+1

            self.request.detector.save_settings(self.request.default_folder + os.sep + "Default")

            # Simulation settings
            self.request.default_simulation.name = self.simulation_settings_widget.nameLineEdit.text()
            self.request.default_simulation.description = self.simulation_settings_widget.descriptionLineEdit.toPlainText()
            self.request.default_simulation.mode = SimulationMode(self.simulation_settings_widget.modeComboBox
                                                                  .currentIndex())
            self.request.default_simulation.simulation_type = SimulationType(self.simulation_settings_widget
                                                                             .typeOfSimulationComboBox.currentIndex())
            self.request.default_simulation.scatter = self.simulation_settings_widget.scatterLineEdit.text()
            self.request.default_simulation.main_scatter = self.simulation_settings_widget.mainScatterLineEdit.text()
            self.request.default_simulation.energy = self.simulation_settings_widget.energyLineEdit.text()
            self.request.default_simulation.no_of_ions = self.simulation_settings_widget.noOfIonsLineEdit.text()
            self.request.default_simulation.no_of_preions = self.simulation_settings_widget.noOfPreionsLineEdit.text()
            self.request.default_simulation.seed = self.simulation_settings_widget.seedLineEdit.text()
            self.request.default_simulation.no_of_recoils = self.simulation_settings_widget.noOfRecoilsLineEdit.text()
            self.request.default_simulation.no_of_scaling = self.simulation_settings_widget.noOfScalingLineEdit.text()

            self.request.default_simulation.save_settings(self.request.default_folder + os.sep + "Default")

            #Depth profile settings
            self.depth_profile_settings.set_settings(self.depth_profile_settings_widget)

            # TODO Values should be checked.
            # if not self.settings.has_been_set():
            #     raise TypeError
            
            self.measuring_unit_settings.save_settings()
            self.calibration_settings.save_settings()
            self.depth_profile_settings.save_settings()
        except TypeError:
            QtWidgets.QMessageBox.question(self, "Warning", "Some of the setting values have not been set.\n" +
                                           "Please input setting values to save them.", QtWidgets.QMessageBox.Ok,
                                           QtWidgets.QMessageBox.Ok)
            raise TypeError
    
    def __change_element(self, button, combo_box):
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
        self.masses.load_isotopes(dialog.element, combo_box,
                                  self.measuring_unit_settings.element.isotope)
        
    def __enabled_element_information(self):
        self.measurement_settings_widget.ui.isotopeComboBox.setEnabled(True)
        self.measurement_settings_widget.ui.isotopeLabel.setEnabled(True)
        self.ui.OKButton.setEnabled(True)
