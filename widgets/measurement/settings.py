# coding=utf-8
"""
Created on 10.4.2018
Updated on 29.6.2018

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2018 Severi Jääskeläinen, Samuel Kaiponen, Heta Rekilä and
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
"""

__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä " \
             "\n Sinikka Siironen"
__version__ = "2.0"

import copy
import modules.masses as masses
import os
import time

from modules.element import Element
from modules.general_functions import set_input_field_red
from modules.general_functions import check_text
from modules.general_functions import validate_text_input

from PyQt5 import uic, QtWidgets
from PyQt5.QtCore import QLocale


class MeasurementSettingsWidget(QtWidgets.QWidget):
    """Class for creating a measurement settings tab.
    """

    def __init__(self, obj):
        """
        Initializes the widget.

        Args:
            obj: Object that uses these settings.
        """
        super().__init__()
        self.ui = uic.loadUi(os.path.join("ui_files",
                                          "ui_measurement_settings_tab.ui"),
                             self)
        self.obj = obj

        set_input_field_red(self.ui.nameLineEdit)
        self.fields_are_valid = False
        self.ui.nameLineEdit.textChanged.connect(lambda: self.__check_text(
            self.ui.nameLineEdit, self))

        locale = QLocale.c()

        self.energyDoubleSpinBox.setLocale(locale)
        self.energyDistDoubleSpinBox.setLocale(locale)
        self.spotSizeXdoubleSpinBox.setLocale(locale)
        self.spotSizeYdoubleSpinBox.setLocale(locale)
        self.divergenceDoubleSpinBox.setLocale(locale)
        # self.fluenceDoubleSpinBox.setLocale(locale)
        self.currentDoubleSpinBox.setLocale(locale)
        self.timeDoubleSpinBox.setLocale(locale)
        self.runChargeDoubleSpinBox.setLocale(locale)

        self.targetThetaDoubleSpinBox.setLocale(locale)
        self.detectorThetaDoubleSpinBox.setLocale(locale)
        self.detectorFiiDoubleSpinBox.setLocale(locale)
        self.targetFiiDoubleSpinBox.setLocale(locale)

        run_object = self.obj.run
        if not run_object:
            run_object = self.obj.request.default_run

        self.tmp_run = copy.deepcopy(run_object)  # Copy of measurement's run
        #  or default run

        self.show_settings()

        self.ui.nameLineEdit.textEdited.connect(lambda: self.__validate())

    def show_settings(self):
        """
        Show measurement settings.
        """
        if self.tmp_run.beam.ion:
            self.ui.beamIonButton.setText(
                self.tmp_run.beam.ion.symbol)
            # TODO Check that the isotope is also set.
            self.isotopeComboBox.setEnabled(True)

            masses.load_isotopes(self.tmp_run.beam.ion.symbol,
                                 self.ui.isotopeComboBox,
                                 str(self.tmp_run.beam.ion.isotope))
        else:
            self.beamIonButton.setText("Select")
            self.isotopeComboBox.setEnabled(
                False)

        self.nameLineEdit.setText(
            self.obj.measurement_setting_file_name)
        self.descriptionPlainTextEdit.setPlainText(
            self.obj.measurement_setting_file_description)
        self.dateLabel.setText(time.strftime("%c %z %Z", time.localtime(
            self.obj.modification_time)))
        self.energyDoubleSpinBox.setValue(
            self.tmp_run.beam.energy)
        self.energyDistDoubleSpinBox.setValue(
            self.tmp_run.beam.energy_distribution)
        self.beamChargeSpinBox.setValue(
            self.tmp_run.beam.charge)
        self.spotSizeXdoubleSpinBox.setValue(
            self.tmp_run.beam.spot_size[0])
        self.spotSizeYdoubleSpinBox.setValue(
            self.tmp_run.beam.spot_size[1])
        self.divergenceDoubleSpinBox.setValue(
            self.tmp_run.beam.divergence)
        self.profileComboBox.setCurrentIndex(
            self.profileComboBox.findText(
                self.tmp_run.beam.profile))
        self.fluenceDoubleSpinBox.setValue(
            self.tmp_run.fluence)
        self.currentDoubleSpinBox.setValue(
            self.tmp_run.current)
        self.timeDoubleSpinBox.setValue(
            self.tmp_run.time)
        self.runChargeDoubleSpinBox.setValue(self.tmp_run.charge)

        detector_object = self.obj.detector
        target_object = self.obj.target
        if not detector_object:  # Detector is an indicator whether default
            # settings should be used.
            detector_object = self.obj.request.default_detector
            target_object = self.obj.request.default_target
        self.targetThetaDoubleSpinBox.setValue(
                target_object.target_theta)
        self.detectorThetaDoubleSpinBox.setValue(
            detector_object.detector_theta)
        # TODO: Fix the angles!
        # self.detectorFiiDoubleSpinBox.setValue(
        #     detector_object.detector_theta + 180)

        # TODO: update angles!
        # self.targetFiiDoubleSpinBox.setValue(
        #     target_object.target_theta + 180)

    def check_angles(self):
        """
        Check that detector angle is bigger than target angle.
        This is a must for measurement. Simulation can handle target angles
        greater than the detector angle.

        Return:
            Whether it is ok to use current angle settings.
        """
        det_theta = self.detectorThetaDoubleSpinBox.value()
        target_theta = self.targetThetaDoubleSpinBox.value()

        if target_theta > det_theta:
            reply = QtWidgets.QMessageBox.question(self, "Warning",
                                                   "Measurement cannot use a "
                                                   "target angle that is "
                                                   "bigger than the detector "
                                                   "angle (for simulation "
                                                   "this is possible).\n\n Do "
                                                   "you want to use these "
                                                   "settings anyway?",
                                           QtWidgets.QMessageBox.Ok |
                                           QtWidgets.QMessageBox.Cancel,
                                           QtWidgets.QMessageBox.Cancel)
            if reply == QtWidgets.QMessageBox.Cancel:
                return False
        return True

    def update_settings(self):
        """
        Update measurement settings.
        """
        isotope_index = self.isotopeComboBox. \
            currentIndex()
        if isotope_index != -1:
            isotope_data = self.isotopeComboBox.itemData(isotope_index)
            self.obj.run.beam.ion = Element(self.beamIonButton.text(),
                                            isotope_data[0])
            self.obj.measurement_setting_file_name = self.nameLineEdit.text()
            self.obj.measurement_setting_file_description = self \
                .descriptionPlainTextEdit.toPlainText()
            self.obj.run.beam.energy = self.energyDoubleSpinBox.value()
            self.obj.run.beam.energy_distribution = \
                self.energyDistDoubleSpinBox.value()
            self.obj.run.beam.charge = self.beamChargeSpinBox.value()
            self.obj.run.beam.spot_size = (self.spotSizeXdoubleSpinBox.value(),
                                           self.spotSizeYdoubleSpinBox.value())
            self.obj.run.beam.divergence = self.divergenceDoubleSpinBox.value()
            self.obj.run.beam.profile = self.profileComboBox.currentText()
            self.obj.run.fluence = self.fluenceDoubleSpinBox.value()
            self.obj.run.current = self.currentDoubleSpinBox.value()
            self.obj.run.time = self.timeDoubleSpinBox.value()
            self.obj.detector.detector_theta = self \
                .detectorThetaDoubleSpinBox.value()
            self.obj.target.target_theta = self \
                .targetThetaDoubleSpinBox.value()
        else:
            QtWidgets.QMessageBox.critical(self, "Warning",
                                           "No isotope selected.\n\nPlease "
                                           "select an isotope for the beam "
                                           "element.",
                                           QtWidgets.QMessageBox.Ok,
                                           QtWidgets.QMessageBox.Ok)

    def values_changed(self):
        """
        Check whether measurement settings values have changed.

        Return:
             True or False.
        """
        isotope_index = self.isotopeComboBox. \
            currentIndex()
        if isotope_index != -1:
            isotope_data = self.isotopeComboBox.itemData(isotope_index)
            if self.obj.run.beam.ion != Element(self.beamIonButton.text(),
                                                isotope_data[0]):
                return True
            if self.obj.measurement_setting_file_name != \
                    self.nameLineEdit.text():
                return True
            if self.obj.measurement_setting_file_description != self \
                .descriptionPlainTextEdit.toPlainText():
                return True
            if self.obj.run.beam.energy != self.energyDoubleSpinBox.value():
                return True
            if self.obj.run.beam.energy_distribution != \
                self.energyDistDoubleSpinBox.value():
                return True
            if self.obj.run.beam.charge != self.beamChargeSpinBox.value():
                return True
            if self.obj.run.beam.spot_size != (
                self.spotSizeXdoubleSpinBox.value(),
                                           self.spotSizeYdoubleSpinBox.value()):
                return True
            if self.obj.run.beam.divergence != \
                self.divergenceDoubleSpinBox.value():
                return True
            if self.obj.run.beam.profile != self.profileComboBox.currentText():
                return True
            if self.obj.run.fluence != self.fluenceDoubleSpinBox.value():
                return True
            if self.obj.run.current != self.currentDoubleSpinBox.value():
                return True
            if self.obj.run.time != self.timeDoubleSpinBox.value():
                return True
            if self.obj.detector.detector_theta != self \
                .detectorThetaDoubleSpinBox.value():
                return True
            if self.obj.target.target_theta != self \
                .targetThetaDoubleSpinBox.value():
                return True
            return False

    def save_to_tmp_run(self):
        """
        Save run and beam parameters to tmp_run object.
        """
        isotope_index = self.isotopeComboBox. \
            currentIndex()
        # TODO: Show a message box, don't just quietly do nothing
        if isotope_index != -1:
            isotope_data = self.isotopeComboBox.itemData(isotope_index)
            self.tmp_run.beam.ion = Element(self.beamIonButton.text(),
                                            isotope_data[0])
            self.tmp_run.beam.energy = self.energyDoubleSpinBox.value()
            self.tmp_run.beam.energy_distribution = \
                self.energyDistDoubleSpinBox.value()
            self.tmp_run.beam.charge = self.beamChargeSpinBox.value()
            self.tmp_run.beam.spot_size = (self.spotSizeXdoubleSpinBox.value(),
                                           self.spotSizeYdoubleSpinBox.value())
            self.tmp_run.beam.divergence = self.divergenceDoubleSpinBox.value()
            self.tmp_run.beam.profile = self.profileComboBox.currentText()
            self.tmp_run.fluence = self.fluenceDoubleSpinBox.value()
            self.tmp_run.current = self.currentDoubleSpinBox.value()
            self.tmp_run.time = self.timeDoubleSpinBox.value()

    @staticmethod
    def __check_text(input_field, settings):
        """Checks if there is text in given input field.

        Args:
            input_field: Input field the contents of which are checked.
        """
        settings.fields_are_valid = check_text(input_field)

    def __validate(self):
        """
        Validate the measurement settings file name.
        """
        text = self.ui.nameLineEdit.text()
        regex = "^[A-Za-z0-9-ÖöÄäÅå]*"
        valid_text = validate_text_input(text, regex)

        self.ui.nameLineEdit.setText(valid_text)

