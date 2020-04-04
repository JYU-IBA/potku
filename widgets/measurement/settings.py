# coding=utf-8
"""
Created on 10.4.2018
Updated on 27.11.2018

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
import time

import widgets.binding as bnd
import widgets.input_validation as iv
import modules.masses as masses

from pathlib import Path
from modules.element import Element
from widgets.gui_utils import QtABCMeta

from PyQt5 import QtWidgets
from PyQt5 import uic
from PyQt5.QtCore import QLocale
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QGuiApplication


class MeasurementSettingsWidget(QtWidgets.QWidget,
                                bnd.PropertyTrackingWidget,
                                metaclass=QtABCMeta):
    """Class for creating a measurement settings tab.
    """
    measurement_setting_file_name = bnd.bind("nameLineEdit")
    measurement_setting_file_description = bnd.bind("descriptionPlainTextEdit")

    beam_energy = bnd.bind("energyDoubleSpinBox", track_change=True)
    beam_energy_distribution = bnd.bind("energyDistDoubleSpinBox",
                                        track_change=True)
    beam_charge = bnd.bind("beamChargeSpinBox")
    beam_spot_size = bnd.multi_bind(["spotSizeXdoubleSpinBox",
                                    "spotSizeYdoubleSpinBox"],
                                    track_change=True)
    beam_divergence = bnd.bind("divergenceDoubleSpinBox", track_change=True)
    beam_profile = bnd.bind("profileComboBox", track_change=True)

    run_fluence = bnd.bind("fluenceDoubleSpinBox")
    run_current = bnd.bind("currentDoubleSpinBox")
    run_time = bnd.bind("timeDoubleSpinBox")
    run_charge = bnd.bind("runChargeDoubleSpinBox")

    target_theta = bnd.bind("targetThetaDoubleSpinBox", track_change=True)
    detector_theta = bnd.bind("detectorThetaDoubleSpinBox", track_change=True)

    def __init__(self, obj):
        """
        Initializes the widget.

        Args:
            obj: object that uses these settings, either a Measurement or a
                Simulation.
        """
        super().__init__()
        uic.loadUi(Path("ui_files", "ui_measurement_settings_tab.ui"), self)
        self.obj = obj
        self.__original_property_values = {}

        iv.set_input_field_red(self.nameLineEdit)
        self.fields_are_valid = False
        self.nameLineEdit.textChanged.connect(lambda: self.check_text(
            self.nameLineEdit, self))

        locale = QLocale.c()

        self.energyDoubleSpinBox.setLocale(locale)
        self.energyDistDoubleSpinBox.setLocale(locale)
        self.spotSizeXdoubleSpinBox.setLocale(locale)
        self.spotSizeYdoubleSpinBox.setLocale(locale)
        self.divergenceDoubleSpinBox.setLocale(locale)
        self.fluenceDoubleSpinBox.setLocale(locale)
        self.currentDoubleSpinBox.setLocale(locale)
        self.timeDoubleSpinBox.setLocale(locale)
        self.runChargeDoubleSpinBox.setLocale(locale)

        self.targetThetaDoubleSpinBox.setLocale(locale)
        self.detectorThetaDoubleSpinBox.setLocale(locale)
        self.detectorFiiDoubleSpinBox.setLocale(locale)
        self.targetFiiDoubleSpinBox.setLocale(locale)

        # Copy of measurement's/simulation's run or default run
        # TODO should default run also be copied?
        if not self.obj.run:
            self.tmp_run = self.obj.request.default_run
        else:
            self.tmp_run = copy.deepcopy(self.obj.run)

        self.isotopeInfoLabel.setVisible(False)

        self.show_settings()

        self.nameLineEdit.textEdited.connect(self.__validate)

        self.clipboard = QGuiApplication.clipboard()
        self.ratio_str = self.clipboard.text()
        self.clipboard.changed.connect(self.__update_multiply_action)

        self.fluenceDoubleSpinBox.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.actionMultiply = QtWidgets.QAction(self.fluenceDoubleSpinBox)
        self.actionMultiply.setText("Multiply with value in clipboard\n(" +
                                    self.ratio_str + ")")
        self.actionMultiply.triggered.connect(self.__multiply_fluence)
        self.fluenceDoubleSpinBox.addAction(self.actionMultiply)

        self.actionUndo = QtWidgets.QAction(self.fluenceDoubleSpinBox)
        self.actionUndo.setText("Undo multiply")
        self.actionUndo.triggered.connect(self.__undo_fluence)
        if self.tmp_run.previous_fluence:
            self.actionUndo.setEnabled(True)
        else:
            self.actionUndo.setEnabled(False)
        self.fluenceDoubleSpinBox.addAction(self.actionUndo)

        self.energyDoubleSpinBox.setToolTip("Energy set in MeV with .")

    def get_original_property_values(self):
        return self.__original_property_values

    def show_settings(self):
        """
        Show measurement settings.
        """
        if self.tmp_run.beam.ion is not None:
            self.beamIonButton.setText(
                self.tmp_run.beam.ion.symbol)
            # TODO Check that the isotope is also set.
            self.isotopeComboBox.setEnabled(True)

            masses.load_isotopes(self.tmp_run.beam.ion.symbol,
                                 self.isotopeComboBox,
                                 str(self.tmp_run.beam.ion.isotope))
        else:
            self.beamIonButton.setText("Select")
            self.isotopeComboBox.setEnabled(
                False)

        self.measurement_setting_file_name = \
            self.obj.measurement_setting_file_name
        self.measurement_setting_file_description = \
            self.obj.measurement_setting_file_description
        self.dateLabel.setText(time.strftime("%c %z %Z", time.localtime(
            self.obj.modification_time)))

        run_params = {
            f"run_{key}": value
            for key, value in self.tmp_run.get_setting_parameters().items()
        }
        bean_params = {
            f"beam_{key}": value
            for key, value in self.tmp_run.beam.get_setting_parameters().items()
        }
        self.set_properties(**run_params, **bean_params)

        if self.obj.detector is None:
            self.detector_theta = \
                self.obj.request.default_detector.detector_theta
            # TODO should there be a none check for target too?
            self.target_theta = self.obj.request.default_target.target_theta
        else:
            self.detector_theta = self.obj.detector.detector_theta
            self.target_theta = self.obj.target.target_theta

    def check_angles(self):
        """
        Check that detector angle is bigger than target angle.
        This is a must for measurement. Simulation can handle target angles
        greater than the detector angle.

        Return:
            Whether it is ok to use current angle settings.
        """
        if self.target_theta > self.detector_theta:
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
            self.obj.run.charge = self.runChargeDoubleSpinBox.value()
            self.obj.run.previous_fluence = self.tmp_run.previous_fluence
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
        Check whether measurement settings values that trigger possible
        rerunning of simulations have changed.

        Return:
             True or False.
        """
        isotope_index = self.isotopeComboBox.currentIndex()
        if isotope_index != -1:
            # TODO check when the index is -1
            isotope_data = self.isotopeComboBox.itemData(isotope_index)
            if self.obj.run.beam.ion != Element(self.beamIonButton.text(),
                                                isotope_data[0]):
                return True
            if self.obj.run.beam.energy != self.energyDoubleSpinBox.value():
                return True
            if self.obj.run.beam.energy_distribution != \
                    self.energyDistDoubleSpinBox.value():
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
            if self.obj.detector.detector_theta != \
                    self.detectorThetaDoubleSpinBox.value():
                return True
            if self.obj.target.target_theta != \
                    self.targetThetaDoubleSpinBox.value():
                return True
            return False

    def other_values_changed(self):
        """
        Check whether measurement values that don't require running a
        simulation again have been changed.

        Return:
             True or False.
        """
        if self.obj.measurement_setting_file_name != \
                self.nameLineEdit.text():
            return True
        if self.obj.measurement_setting_file_description != self \
                .descriptionPlainTextEdit.toPlainText():
            return True
        if self.obj.run.beam.charge != self.beamChargeSpinBox.value():
            return True
        if self.obj.run.current != self.currentDoubleSpinBox.value():
            return True
        if self.obj.run.time != self.timeDoubleSpinBox.value():
            return True
        if self.obj.run.charge != self.runChargeDoubleSpinBox.value():
            return True
        if self.obj.run.fluence != self.fluenceDoubleSpinBox.value():
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
        else:
            QtWidgets.QMessageBox.critical(self, "Warning",
                                           "No isotope selected.\n\nPlease "
                                           "select an isotope for the beam "
                                           "element.",
                                           QtWidgets.QMessageBox.Ok,
                                           QtWidgets.QMessageBox.Ok)

    @staticmethod
    def check_text(input_field, settings):
        """Checks if there is text in given input field.

        Args:
            input_field: Input field the contents of which are checked.
        """
        settings.fields_are_valid = iv.check_text(input_field)

    def __validate(self):
        """
        Validate the measurement settings file name.
        """
        text = self.nameLineEdit.text()
        regex = "^[A-Za-z0-9-ÖöÄäÅå]*"
        valid_text = iv.validate_text_input(text, regex)

        self.nameLineEdit.setText(valid_text)

    def __multiply_fluence(self):
        """
        Multiply fluence with clipboard's value.
        """
        try:
            ratio = float(self.ratio_str)
            old_fluence = self.fluenceDoubleSpinBox.value()
            self.tmp_run.previous_fluence.append(old_fluence)
            new_fluence = round(ratio * old_fluence, 2)
            self.fluenceDoubleSpinBox.setValue(new_fluence)
            self.actionUndo.setEnabled(True)
        except ValueError:
            QtWidgets.QMessageBox.critical(self, "Error",
                                           "Value '" + self.ratio_str +
                                           "' is not suitable for "
                                           "multiplying.\n\nPlease copy a "
                                           "suitable value to clipboard.",
                                           QtWidgets.QMessageBox.Ok,
                                           QtWidgets.QMessageBox.Ok)

    def __undo_fluence(self):
        """
        Undo latest change to fluence.
        """
        try:
            old_value = self.tmp_run.previous_fluence.pop()
        except IndexError:
            # cannot undo as the previous fluence list was empty.
            self.actionUndo.setEnabled(False)
            return

        self.fluenceDoubleSpinBox.setValue(old_value)
        self.actionUndo.setEnabled(bool(self.tmp_run.previous_fluence))

    def __update_multiply_action(self):
        """
        Update the value with which the multiplication is done.
        """
        self.ratio_str = self.clipboard.text()
        self.actionMultiply.setText("Multiply with value in clipboard\n(" +
                                    self.ratio_str + ")")

