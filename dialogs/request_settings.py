# coding=utf-8
"""
Created on 19.3.2013
Updated on 6.5.2018

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
import datetime

__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen " \
             "\n Samuli Rahkonen \n Miika Raunio \n Severi Jääskeläinen \n " \
             "Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"
__version__ = "2.0"

import os
from PyQt5 import QtCore, QtGui, uic, QtWidgets
from PyQt5.QtWidgets import QDesktopWidget, QApplication

import modules.masses as masses
from dialogs.element_selection import ElementSelectionDialog
from dialogs.measurement.calibration import CalibrationDialog
from dialogs.simulation.foil import FoilDialog
from modules.calibration_parameters import CalibrationParameters
from modules.depth_profile_settings import DepthProfileSettings
from modules.element import Element
from modules.foil import CircularFoil
from modules.general_functions import open_file_dialog
from modules.general_functions import save_file_dialog
from modules.input_validator import InputValidator
from modules.measuring_settings import MeasuringSettings
from widgets.depth_profile_settings import DepthProfileSettingsWidget
from widgets.detector_settings import DetectorSettingsWidget
from widgets.foil import FoilWidget
from widgets.measurement.settings import MeasurementSettingsWidget
from widgets.simulation.settings import SimulationSettingsWidget


class RequestSettingsDialog(QtWidgets.QDialog):

    def __init__(self, request, icon_manager):
        """Constructor for the program

        Args:
            request: Request class object.
        """
        super().__init__()
        self.ui = uic.loadUi(os.path.join("ui_files", "ui_settings.ui"), self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        screen_geometry = QDesktopWidget \
            .availableGeometry(QApplication.desktop())
        self.resize(self.geometry().width(),
                    screen_geometry.size().height() * 0.8)

        self.request = request
        self.settings = request.settings
        self.icon_manager = icon_manager

        # Creates object that loads and holds all the measuring data
        self.measuring_unit_settings = self.settings.measuring_unit_settings
        self.calibration_settings = self.settings.calibration_settings
        self.depth_profile_settings = self.settings.depth_profile_settings

        # Connect buttons.
        self.ui.OKButton.clicked.connect(self.update_and_close_settings)
        self.ui.applyButton.clicked.connect(self.update_settings)
        self.ui.cancelButton.clicked.connect(self.close)
        double_validator = InputValidator()
        positive_double_validator = InputValidator(bottom=0)

        # Add measurement settings view to the settings view
        self.measurement_settings_widget = MeasurementSettingsWidget()
        self.ui.tabs.addTab(self.measurement_settings_widget, "Measurement")

        if self.measuring_unit_settings.element:
            masses.load_isotopes(self.measuring_unit_settings.element.symbol,
                                 self.measurement_settings_widget.ui
                                 .isotopeComboBox,
                                 str(self.measuring_unit_settings.element
                                     .isotope))
        else:
            self.measurement_settings_widget.ui.beamIonButton.setText("Select")
            self.measurement_settings_widget.ui.isotopeComboBox.setEnabled(
                False)

        self.measurement_settings_widget.ui.loadButton.clicked \
            .connect(lambda: self.__load_file("MEASURING_UNIT_SETTINGS"))
        self.measurement_settings_widget.ui.saveButton.clicked \
            .connect(lambda: self.__save_file("MEASUREMENT_SETTINGS"))
        self.measurement_settings_widget.ui.beamIonButton.clicked.connect(
            lambda: self.__change_element(
                self.measurement_settings_widget.ui.beamIonButton,
                self.measurement_settings_widget.ui.isotopeComboBox))

        # self.measurement_settings_widget.ui.energyLineEdit.setValidator(
        #     positive_double_validator)
        double_angle_validator = InputValidator(0, 90, 10)
        # self.measurement_settings_widget.ui.detectorThetaLineEdit.setValidator(
        #     double_angle_validator)
        # self.measurement_settings_widget.ui.targetThetaLineEdit.setValidator(
        #     double_angle_validator)

        self.measurement_settings_widget.ui.picture.setScaledContents(True)
        pixmap = QtGui.QPixmap(os.path.join("images", "hardwaresetup.png"))
        self.measurement_settings_widget.ui.picture.setPixmap(pixmap)

        # Add detector settings view to the settings view
        self.detector_settings_widget = DetectorSettingsWidget()
        self.ui.tabs.addTab(self.detector_settings_widget, "Detector")

        self.detector_settings_widget.ui.saveButton.clicked \
            .connect(lambda: self.__save_file("DETECTOR_SETTINGS"))

        # Temporary foils list which holds all the information given in the
        # foil dialog
        # If user presses ok or apply, these values will be saved into
        # request's default detector
        self.tmp_foil_info = []

        # List of foil indexes that are timing foils
        self.tof_foils = []

        # Add foil widgets and foil objects
        self.detector_structure_widgets = []
        self.foils_layout = self._add_default_foils()
        self.detector_settings_widget.ui.detectorScrollAreaContents.layout() \
            .addLayout(self.foils_layout)
        self.detector_settings_widget.ui.newFoilButton.clicked.connect(
            lambda: self._add_new_foil(self.foils_layout))

        # Efficiency files
        self.detector_settings_widget.ui.efficiencyListWidget.addItems(
            self.request.default_detector.get_efficiency_files())
        self.detector_settings_widget.ui.addEfficiencyButton.clicked.connect(
            lambda: self.__add_efficiency())
        self.detector_settings_widget.ui.removeEfficiencyButton.clicked.connect(
            lambda: self.__remove_efficiency())

        # Calibration settings
        self.detector_settings_widget.ui.loadCalibrationParametersButton. \
            clicked.connect(lambda: self.__load_file("CALIBRATION_SETTINGS"))
        self.detector_settings_widget.ui.saveCalibrationParametersButton. \
            clicked.connect(lambda: self.__save_file("CALIBRATION_SETTINGS"))
        self.detector_settings_widget.ui.executeCalibrationButton.clicked. \
            connect(self.__open_calibration_dialog)
        self.detector_settings_widget.ui.executeCalibrationButton.setEnabled(
            not self.request.samples.measurements.is_empty())
        self.detector_settings_widget.ui.slopeLineEdit.setValidator(
            double_validator)
        self.detector_settings_widget.ui.offsetLineEdit.setValidator(
            double_validator)
        self.calibration_settings.show(self.detector_settings_widget)

        # This makes a new detector object so all the changes to
        # self.request.default_detector don't transfer to any simulations etc
        #  which should use default detector values!!!
        # TODO: read dafault detector from file somewhere else!
        self.request.default_detector = self.request.default_detector.from_file(
            os.path.join(self.request.directory,
                         self.request.default_detector_folder,
                         "Default.detector"))

        # Add simulation settings view to the settings view
        self.simulation_settings_widget = SimulationSettingsWidget()
        self.ui.tabs.addTab(self.simulation_settings_widget, "Simulation")

        self.simulation_settings_widget.ui.generalParametersGroupBox\
            .setEnabled(True)
        self.simulation_settings_widget.ui.physicalParametersGroupBox\
            .setEnabled(True)
        self.simulation_settings_widget.ui.typeOfSimulationComboBox.addItem(
            "ERD")
        self.simulation_settings_widget.ui.typeOfSimulationComboBox.addItem(
            "RBS")
        self.simulation_settings_widget.ui.saveButton.clicked \
            .connect(lambda: self.__save_file("SIMULATION_SETTINGS"))

        self.request.default_simulation = \
            self.request.default_simulation.from_file(self.request,
                os.path.join(self.request.default_folder, "Default.simulation"))
        self.request.default_element_simulation = self.request \
            .default_element_simulation.from_file(self.request,
                                                  os.path.join(
                                                      self.request.default_folder,
                                                      "Default.mcsimu"),
                                                  os.path.join(
                                                      self.request.default_folder,
                                                      "Default.rec"),
                                                  os.path.join(
                                                      self.request.default_folder,
                                                      "Default.profile"))
        self.request.default_simulation.element_simulations.append(
            self.request.default_element_simulation)

        # Add depth profile settings view to the settings view
        self.depth_profile_settings_widget = DepthProfileSettingsWidget()
        self.ui.tabs.addTab(self.depth_profile_settings_widget, "Profile")

        self.depth_profile_settings.show(self.depth_profile_settings_widget)

        self.depth_profile_settings_widget.ui.loadButton.clicked.connect(
            lambda: self.__load_file("DEPTH_PROFILE_SETTINGS"))
        self.depth_profile_settings_widget.ui.saveButton.clicked.connect(
            lambda: self.__save_file("DEPTH_PROFILE_SETTINGS"))

        # self.depth_profile_settings_widget.ui.depthStepForStoppingLineEdit. \
        #     setValidator(double_validator)
        # self.depth_profile_settings_widget.ui.depthStepForOutputLineEdit. \
        #     setValidator(double_validator)
        #
        # self.depth_profile_settings_widget.ui. \
        #     depthsForConcentrationScalingLineEdit_1.setValidator(
        #     double_validator)
        # self.depth_profile_settings_widget.ui. \
        #     depthsForConcentrationScalingLineEdit_2.setValidator(
        #     double_validator)

        self.show_settings()

        self.exec_()

    def _add_new_foil(self, layout):
        foil_widget = FoilWidget(self)
        new_foil = CircularFoil()
        self.tmp_foil_info.append(new_foil)
        foil_widget.ui.foilButton.setText(new_foil.name)
        foil_widget.ui.distanceEdit.setText(str(new_foil.distance))
        foil_widget.ui.foilButton.clicked.connect(
            lambda: self._open_composition_dialog())
        foil_widget.ui.timingFoilCheckBox.stateChanged.connect(
            lambda: self._check_and_add())
        self.detector_structure_widgets.append(foil_widget)
        layout.addWidget(foil_widget)

        if len(self.tof_foils) >= 2:
            foil_widget.ui.timingFoilCheckBox.setEnabled(False)
        return foil_widget

    def _add_default_foils(self):
        layout = QtWidgets.QHBoxLayout()
        target = QtWidgets.QLabel("Target")
        layout.addWidget(target)
        for i in range(4):
            foil_widget = self._add_new_foil(layout)
            for index in self.request.default_detector.tof_foils:
                if index == i:
                    foil_widget.ui.timingFoilCheckBox.setChecked(True)
        return layout

    def _check_and_add(self):
        check_box = self.sender()
        for i in range(len(self.detector_structure_widgets)):
            if self.detector_structure_widgets[i]. \
                    ui.timingFoilCheckBox is self.sender():
                if check_box.isChecked():
                    if self.tof_foils:
                        if self.tof_foils[0] > i:
                            self.tof_foils.insert(0, i)
                        else:
                            self.tof_foils.append(i)
                        if len(self.tof_foils) >= 2:
                            self._disable_checkboxes()
                    else:
                        self.tof_foils.append(i)
                else:
                    self.tof_foils.remove(i)
                    if 0 < len(self.tof_foils) < 2:
                        self._enable_checkboxes()
                break

    def _disable_checkboxes(self):
        for i in range(len(self.detector_structure_widgets)):
            if i not in self.tof_foils:
                widget = self.detector_structure_widgets[i]
                widget.ui.timingFoilCheckBox.setEnabled(False)

    def _enable_checkboxes(self):
        for i in range(len(self.detector_structure_widgets)):
            widget = self.detector_structure_widgets[i]
            widget.ui.timingFoilCheckBox.setEnabled(True)

    def _open_composition_dialog(self):
        foil_name = self.sender().text()
        foil_object_index = -1
        for i in range(len(self.tmp_foil_info)):
            if foil_name == self.tmp_foil_info[i].name:
                foil_object_index = i
                break
        FoilDialog(self.tmp_foil_info, foil_object_index, self.icon_manager)
        self.sender().setText(self.tmp_foil_info[foil_object_index].name)

    def __add_efficiency(self):
        """Adds efficiency file in detector's efficiency directory and
        updates settings view.
        """
        new_efficiency_file = open_file_dialog(self,
                                               self.request.default_folder,
                                               "Select efficiency file",
                                               "Efficiency File (*.eff)")
        if not new_efficiency_file:
            return
        self.request.default_detector.add_efficiency_file(new_efficiency_file)
        self.detector_settings_widget.ui.efficiencyListWidget.clear()
        self.detector_settings_widget.ui.efficiencyListWidget.addItems(
            self.request.default_detector.get_efficiency_files())

    def __remove_efficiency(self):
        """Removes efficiency file from detector's efficiency directory and
        updates settings view.
        """
        selected_efficiency_file = self.detector_settings_widget.ui. \
            efficiencyListWidget.currentItem().text()
        self.request.default_detector.remove_efficiency_file(
            selected_efficiency_file)
        self.detector_settings_widget.ui.efficiencyListWidget.clear()
        self.detector_settings_widget.ui.efficiencyListWidget.addItems(
            self.request.default_detector.get_efficiency_files())

    def __open_calibration_dialog(self):
        measurements = [self.request.measurements.get_key_value(key)
                        for key in
                        self.request.samples.measurements.measurements.keys()]
        CalibrationDialog(measurements, self.settings, self)

    def show_settings(self):
        # Measurement settings
        if self.request.default_measurement.run.beam.ion:
            self.measurement_settings_widget.ui.beamIonButton.setText(
                self.request.default_measurement.run.beam.ion.symbol)
            # TODO Check that the isotope is also set.
            self.measurement_settings_widget.ui.isotopeComboBox.setEnabled(True)
        else:
            self.measurement_settings_widget.ui.beamIonButton.setText("Select")
            self.measurement_settings_widget.ui.isotopeComboBox.setEnabled(
                False)

        self.measurement_settings_widget.nameLineEdit.setText(
            self.request.default_measurement.name)
        self.measurement_settings_widget.descriptionPlainTextEdit.setPlainText(
            self.request.default_measurement.description)
        self.measurement_settings_widget.energyDoubleSpinBox.setValue(
            self.request.default_measurement.run.beam.energy)
        self.measurement_settings_widget.energyDistDoubleSpinBox.setValue(
            self.request.default_measurement.run.beam.energy_distribution)
        self.measurement_settings_widget.beamChargeSpinBox.setValue(
            self.request.default_measurement.run.beam.charge)
        self.measurement_settings_widget.spotSizeXdoubleSpinBox.setValue(
            self.request.default_measurement.run.beam.spot_size[0])
        self.measurement_settings_widget.spotSizeXdoubleSpinBox.setValue(
            self.request.default_measurement.run.beam.spot_size[1])
        self.measurement_settings_widget.divergenceDoubleSpinBox.setValue(
            self.request.default_measurement.run.beam.divergence)
        self.measurement_settings_widget.profileComboBox.setCurrentIndex(
            self.measurement_settings_widget.profileComboBox.findText(
                self.request.default_measurement.run.beam.profile))
        self.measurement_settings_widget.fluenceDoubleSpinBox.setValue(
            self.request.default_measurement.run.fluence)
        self.measurement_settings_widget.currentDoubleSpinBox.setValue(
            self.request.default_measurement.run.current)
        self.measurement_settings_widget.timeDoubleSpinBox.setValue(
            self.request.default_measurement.run.time)
        self.measurement_settings_widget.detectorThetaDoubleSpinBox.setValue(
            self.request.default_detector.detector_theta)
        # TODO: Fix the angle links to correct values
        self.measurement_settings_widget.detectorFiiDoubleSpinBox.setValue(
            self.request.default_detector.detector_theta + 180)
        self.measurement_settings_widget.targetThetaDoubleSpinBox.setValue(
            self.request.default_target.target_theta)
        self.measurement_settings_widget.targetFiiDoubleSpinBox.setValue(
            self.request.default_target.target_theta + 180)

        self.link_angle_values(self.measurement_settings_widget.detectorThetaDoubleSpinBox,
                               self.measurement_settings_widget.detectorFiiDoubleSpinBox)
        self.link_angle_values(self.measurement_settings_widget.targetThetaDoubleSpinBox,
                               self.measurement_settings_widget.targetFiiDoubleSpinBox)


        # Detector settings
        self.detector_settings_widget.nameLineEdit.setText(
            self.request.default_detector.name)
        self.detector_settings_widget.dateLabel.setText(str(
            datetime.datetime.fromtimestamp(
                self.request.default_detector.modification_time)))
        self.detector_settings_widget.descriptionLineEdit.setPlainText(
            self.request.default_detector.description)
        self.detector_settings_widget.typeComboBox.setCurrentIndex(
            self.detector_settings_widget.typeComboBox.findText(
                self.request.default_detector.type))
        self.detector_settings_widget.slopeLineEdit.setText(
            str(self.calibration_settings.slope))
        self.detector_settings_widget.offsetLineEdit.setText(
            str(self.calibration_settings.offset))
        self.detector_settings_widget.angleSlopeLineEdit.setText(
            str(self.calibration_settings.angleslope))
        self.detector_settings_widget.angleOffsetLineEdit.setText(
            str(self.calibration_settings.angleoffset))

        # Detector foils
        self.calculate_distance()
        self.tmp_foil_info = self.request.default_detector.foils

        # Tof foils
        self.tof_foils = self.request.default_detector.tof_foils

        # Simulation settings
        self.simulation_settings_widget.nameLineEdit.setText(
            self.request.default_simulation.name)
        self.simulation_settings_widget.dateLabel.setText(str(
            datetime.datetime.fromtimestamp(
                self.request.default_simulation.modification_time)))
        self.simulation_settings_widget.descriptionPlainTextEdit.setPlainText(
            self.request.default_simulation.description)
        self.simulation_settings_widget.modeComboBox.setCurrentIndex(
            self.simulation_settings_widget.modeComboBox.findText(
                self.request.default_simulation.element_simulations[
                    0].simulation_mode))
        self.simulation_settings_widget.typeOfSimulationComboBox \
            .setCurrentIndex(self.simulation_settings_widget
            .typeOfSimulationComboBox.findText(self.request
            .default_simulation.element_simulations[0].simulation_type))
        self.simulation_settings_widget.minimumScatterAngleDoubleSpinBox\
            .setValue(self.request.default_simulation.element_simulations[
                0].minimum_scattering_angle)
        self.simulation_settings_widget.minimumMainScatterAngleDoubleSpinBox\
            .setValue(self.request.default_simulation.element_simulations[
                0].minimum_main_scattering_angle)
        self.simulation_settings_widget.minimumEnergyDoubleSpinBox.setValue(
            self.request.default_simulation.element_simulations[
                0].minimum_energy)
        self.simulation_settings_widget.numberOfIonsSpinBox.setValue(
            self.request.default_simulation.element_simulations[
                0].number_of_ions)
        self.simulation_settings_widget.numberOfPreIonsSpinBox.setValue(
            self.request.default_simulation.element_simulations[
                0].number_of_preions)
        self.simulation_settings_widget.seedSpinBox.setValue(
            self.request.default_simulation.element_simulations[0].seed_number)
        self.simulation_settings_widget.numberOfRecoilsSpinBox.setValue(
            self.request.default_simulation.element_simulations[
                0].number_of_recoils)
        self.simulation_settings_widget.numberOfScalingIonsSpinBox.setValue(
            self.request.default_simulation.element_simulations[
                0].number_of_scaling_ions)

    def link_angle_values(self, theta, fii):
        """A function to link angle spinbox values to each other.
        """
        # TODO: Fix the angle links to correct values
        theta.valueChanged.connect(
            lambda: fii.setValue(
                theta.value() + 180
            ))
        fii.valueChanged.connect(
            lambda: theta.setValue(
                fii.value() - 180
            ))

    def __load_file(self, settings_type):
        """Opens file dialog and loads and shows selected ini file's values.

        Args:
            settings_type: (string) selects which settings file type will be
                           loaded.
                           Can be "MEASURING_UNIT_SETTINGS",
                           "DEPTH_PROFILE_SETTINGS" or "CALIBRATION_SETTINGS"
        """
        filename = open_file_dialog(self, self.request.directory,
                                    "Open settings file",
                                    "Settings file (*.ini)")

        if settings_type == "MEASURING_UNIT_SETTINGS":
            settings = MeasuringSettings()
            settings.load_settings(filename)
            masses.load_isotopes(settings.element.symbol,
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
                self.request.default_detector.save_settings(filename)
            else:
                settings.set_settings(self.measurement_settings_widget)
                settings.save_settings(filename)

    def calculate_distance(self):
        distance = 0
        for i in range(len(self.detector_structure_widgets)):
            widget = self.detector_structure_widgets[i]
            distance = distance + float(widget.ui.distanceEdit.text())
            self.tmp_foil_info[i].distance = distance

    def delete_foil(self, foil_widget):
        index_of_item_to_be_deleted = self.detector_structure_widgets.index(
            foil_widget)
        del (self.detector_structure_widgets[index_of_item_to_be_deleted])
        foil_to_be_deleted = self.tmp_foil_info[index_of_item_to_be_deleted]
        # tof_foils = []
        # for i in self.tof_foils:
        #     tof_foils.append(self.tmp_foil_info[i])
        if index_of_item_to_be_deleted in self.tof_foils:
            self.tof_foils.remove(index_of_item_to_be_deleted)
            if 0 < len(self.tof_foils) < 2:
                self._enable_checkboxes()
        self.tmp_foil_info.remove(foil_to_be_deleted)
        for i in range(len(self.tof_foils)):
            if self.tof_foils[i] > index_of_item_to_be_deleted:
                self.tof_foils[i] = self.tof_foils[i] - 1

        self.foils_layout.removeWidget(foil_widget)
        foil_widget.deleteLater()

    def update_and_close_settings(self):
        """Updates measuring settings values with the dialog's values and
        saves them to default settings file.
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
        """Reads values from Request Settings dialog and updates them in
        default objects.
        """
        # TODO: Proper checking for all setting values
        try:
            # Measurement settings
            isotope_index = self.measurement_settings_widget.isotopeComboBox. \
                currentIndex()
            if isotope_index != -1:
                isotope_data = self.measurement_settings_widget. \
                    isotopeComboBox.itemData(isotope_index)
                self.request.default_measurement.ion = Element(
                    self.measurement_settings_widget.beamIonButton.text(),
                    isotope_data[0])
                self.request.default_measurement.measurement_name = \
                    self.measurement_settings_widget.nameLineEdit.text()
                self.request.default_measurement.description = \
                    self.measurement_settings_widget.descriptionPlainTextEdit. \
                        toPlainText()
                self.request.default_measurement.energy = \
                    self.measurement_settings_widget.energyDoubleSpinBox.value()
                self.request.default_measurement.energy_dist = \
                    self.measurement_settings_widget\
                        .energyDistDoubleSpinBox.value()
                self.request.default_measurement.charge = \
                    self.measurement_settings_widget.beamChargeSpinBox.value()
                self.request.default_measurement.spot_size = [
                    self.measurement_settings_widget
                        .spotSizeXdoubleSpinBox.value(),
                    self.measurement_settings_widget
                        .spotSizeYdoubleSpinBox.value()]
                self.request.default_measurement.divergence = \
                    self.measurement_settings_widget\
                        .divergenceDoubleSpinBox.value()
                self.request.default_measurement.profile = \
                    self.measurement_settings_widget\
                        .profileComboBox.currentText()
                self.request.default_measurement.fluence = \
                    self.measurement_settings_widget\
                        .fluenceDoubleSpinBox.value()
                self.request.default_measurement.current = \
                    self.measurement_settings_widget\
                        .currentDoubleSpinBox.value()
                self.request.default_measurement.beam_time = \
                    self.measurement_settings_widget.timeDoubleSpinBox.value()
                self.request.default_measurement.detector_theta = \
                    self.measurement_settings_widget\
                        .detectorThetaDoubleSpinBox.value()
                self.request.default_measurement.target_theta = \
                    self.measurement_settings_widget\
                        .targetThetaDoubleSpinBox.value()

                self.request.default_measurement.save_settings(
                    self.request.default_folder + os.sep +
                    "Default")
                # TODO Implement to_file for Measurement
            #                self.request.default_measurement.to_file(
            #                    self.request.default_folder + os.sep +
            #                    "Default.measurement")

            # Detector settings
            self.request.default_detector.name = \
                self.detector_settings_widget.nameLineEdit.text()
            self.request.default_detector.description = \
                self.detector_settings_widget.descriptionLineEdit.toPlainText()
            self.request.default_detector.type = \
                self.detector_settings_widget.typeComboBox.currentText()
            self.calibration_settings.set_settings(
                self.detector_settings_widget)
            self.request.default_detector.calibration = \
                self.calibration_settings
            # Detector foils
            self.calculate_distance()
            self.request.default_detector.foils = self.tmp_foil_info
            # Tof foils
            self.request.default_detector.tof_foils = self.tof_foils

            self.request.default_detector.to_file(os.path.join(
                self.request.default_detector_folder, "Default.detector"))

            # Simulation settings
            self.request.default_simulation.name = \
                self.simulation_settings_widget.nameLineEdit.text()
            self.request.default_simulation.description = \
                self.simulation_settings_widget.descriptionPlainTextEdit. \
                    toPlainText()
            self.request.default_simulation.element_simulations[
                0].simulation_type = self.simulation_settings_widget \
                .typeOfSimulationComboBox.currentText()
            self.request.default_simulation.element_simulations[
                0].simulation_mode = self.simulation_settings_widget \
                .modeComboBox.currentText()
            self.request.default_simulation.element_simulations[
                0].number_of_ions = self.simulation_settings_widget \
                .numberOfIonsSpinBox.value()
            self.request.default_simulation.element_simulations[
                0].number_of_preions = self.simulation_settings_widget \
                .numberOfPreIonsSpinBox.value()
            self.request.default_simulation.element_simulations[0].seed_number \
                = self.simulation_settings_widget.seedSpinBox.value()
            self.request.default_simulation.element_simulations[
                0].number_of_recoils = self.simulation_settings_widget \
                .numberOfRecoilsSpinBox.value()
            self.request.default_simulation.element_simulations[
                0].number_of_scaling_ions = self.simulation_settings_widget \
                .numberOfScalingIonsSpinBox.value()
            self.request.default_simulation.element_simulations[
                0].minimum_scattering_angle = self.simulation_settings_widget\
                .minimumScatterAngleDoubleSpinBox.value()
            self.request.default_simulation.element_simulations[
                0].minimum_main_scattering_angle = self\
                .simulation_settings_widget\
                .minimumMainScatterAngleDoubleSpinBox.value()
            self.request.default_simulation.element_simulations[
                0].minimum_energy = self.simulation_settings_widget \
                .minimumEnergyDoubleSpinBox.value()

            self.request.default_simulation.to_file(os.path.join(
                self.request.default_folder, "Default.simulation"))

            # Depth profile settings
            self.depth_profile_settings.set_settings(
                self.depth_profile_settings_widget)

            # TODO Values should be checked.
            # if not self.settings.has_been_set():
            #     raise TypeError

            self.measuring_unit_settings.save_settings()
            self.calibration_settings.save_settings()
            self.depth_profile_settings.save_settings()
        except TypeError:
            QtWidgets.QMessageBox.question(self, "Warning",
                                           "Some of the setting values have "
                                           "not been set.\n" +
                                           "Please input setting values to "
                                           "save them.",
                                           QtWidgets.QMessageBox.Ok,
                                           QtWidgets.QMessageBox.Ok)
            raise TypeError

    def __change_element(self, button, combo_box):
        """Opens element selection dialog and loads selected element's isotopes
        to a combobox.

        Args:
            button: button whose text is changed accordingly to the made
            selection.
        """
        dialog = ElementSelectionDialog()
        if dialog.element:
            button.setText(dialog.element)
            # Enabled settings once element is selected
            self.__enabled_element_information()
            masses.load_isotopes(dialog.element, combo_box,
                                 self.measuring_unit_settings.element.isotope)

    def __enabled_element_information(self):
        self.measurement_settings_widget.ui.isotopeComboBox.setEnabled(True)
        self.measurement_settings_widget.ui.isotopeLabel.setEnabled(True)
        self.ui.OKButton.setEnabled(True)
