# coding=utf-8
"""
Created on 10.4.2018
Updated on 1.8.2018

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

import time

import widgets.input_validation as iv

from pathlib import Path

from PyQt5 import QtWidgets
from PyQt5 import uic
from PyQt5.QtCore import QLocale


class ProfileSettingsWidget(QtWidgets.QWidget):
    """Class for creating a profile settings tab.
    """
    def __init__(self, measurement):
        """
        Initializes the widget.

        Args:
            measurement: Measurement object.
        """
        super().__init__()
        uic.loadUi(Path("ui_files", "ui_profile_settings_tab.ui"), self)
        self.measurement = measurement

        self.fields_are_valid = False
        iv.set_input_field_red(self.nameLineEdit)
        self.nameLineEdit.textChanged.connect(
            lambda: self.__check_text(self.nameLineEdit, self))
        self.nameLineEdit.textEdited.connect(
            lambda: iv.sanitize_file_name(self.nameLineEdit))

        locale = QLocale.c()
        self.referenceDensityDoubleSpinBox.setLocale(locale)
        self.depthForConcentrationFromDoubleSpinBox.setLocale(locale)
        self.depthForConcentrationToDoubleSpinBox.setLocale(locale)
        self.channelWidthDoubleSpinBox.setLocale(locale)

        self.show_settings()

        self.depthForConcentrationFromDoubleSpinBox.valueChanged.connect(
            lambda: self.__check_values(
                self.depthForConcentrationFromDoubleSpinBox))
        self.depthForConcentrationToDoubleSpinBox.valueChanged.connect(
            lambda: self.__check_values(
                self.depthForConcentrationToDoubleSpinBox))

    def __check_values(self, spinbox):
        """
        Check that depth for concentration from isn't bigger than depth for
        concentration to value and other way around.

        Args:
            spinbox: Spinbox whose value is changed.
        """
        from_value = self.depthForConcentrationFromDoubleSpinBox.value()
        to_value = self.depthForConcentrationToDoubleSpinBox.value()
        if spinbox is self.depthForConcentrationFromDoubleSpinBox:
            if from_value > to_value:
                self.depthForConcentrationFromDoubleSpinBox.setValue(
                    to_value - 0.01)
        else:
            if to_value < from_value:
                self.depthForConcentrationToDoubleSpinBox.setValue(
                    from_value + 0.01)

    def show_settings(self):
        """
        Show profile settings.
        """
        if not self.measurement.use_default_profile_settings:
            self.nameLineEdit.setText(
                self.measurement.profile_name)
            self.descriptionPlainTextEdit.setPlainText(
                self.measurement.profile_description)
            self.dateLabel.setText(time.strftime("%c %z %Z", time.localtime(
                self.measurement.profile_modification_time)))
            self.referenceDensityDoubleSpinBox.setValue(
                self.measurement.reference_density)
            self.numberOfDepthStepsSpinBox.setValue(
                self.measurement.number_of_depth_steps)
            self.depthStepForStoppingSpinBox.setValue(
                self.measurement.depth_step_for_stopping)
            self.depthStepForOutputSpinBox.setValue(
                self.measurement.depth_step_for_output)
            self.depthForConcentrationFromDoubleSpinBox.setValue(
                self.measurement.depth_for_concentration_from)
            self.depthForConcentrationToDoubleSpinBox.setValue(
                self.measurement.depth_for_concentration_to)
            self.channelWidthDoubleSpinBox.setValue(
                self.measurement.channel_width)
            self.numberOfSplitsSpinBox.setValue(
                self.measurement.number_of_splits)
            self.normalizationComboBox.setCurrentIndex(
                self.normalizationComboBox.findText(
                    self.measurement.normalization))
        else:
            self.nameLineEdit.setText(
                self.measurement.request.default_measurement.profile_name)
            self.dateLabel.setText(time.strftime("%c %z %Z", time.localtime(
                self.measurement.request.default_measurement
                    .profile_modification_time)))
            self.descriptionPlainTextEdit.setPlainText(
                self.measurement.request.default_measurement
                    .profile_description)
            self.referenceDensityDoubleSpinBox.setValue(
                self.measurement.request.default_measurement
                    .reference_density)
            self.numberOfDepthStepsSpinBox.setValue(
                self.measurement.request.default_measurement
                    .number_of_depth_steps)
            self.depthStepForStoppingSpinBox.setValue(
                self.measurement.request.default_measurement
                    .depth_step_for_stopping)
            self.depthStepForOutputSpinBox.setValue(
                self.measurement.request.default_measurement
                    .depth_step_for_output)
            self.depthForConcentrationFromDoubleSpinBox.setValue(
                self.measurement.request.default_measurement
                    .depth_for_concentration_from)
            self.depthForConcentrationToDoubleSpinBox.setValue(
                self.measurement.request.default_measurement
                    .depth_for_concentration_to)
            self.channelWidthDoubleSpinBox.setValue(
                self.measurement.request.default_measurement.channel_width)
            self.numberOfSplitsSpinBox.setValue(
                self.measurement.request.default_measurement.number_of_splits)
            self.normalizationComboBox.setCurrentIndex(
                self.normalizationComboBox.findText(
                    self.measurement.request.default_measurement.normalization))

    def update_settings(self):
        """
        Update profile settings.
        """
        self.measurement.profile_name = self.nameLineEdit.text()
        self.measurement.profile_description = \
            self.descriptionPlainTextEdit.toPlainText()
        self.measurement.reference_density = \
            self.referenceDensityDoubleSpinBox.value()
        self.measurement.number_of_depth_steps = \
            self.numberOfDepthStepsSpinBox.value()
        self.measurement.depth_step_for_stopping = \
            self.depthStepForStoppingSpinBox.value()
        self.measurement.depth_step_for_output = \
            self.depthStepForOutputSpinBox.value()
        self.measurement.depth_for_concentration_from = \
            self.depthForConcentrationFromDoubleSpinBox.value()
        self.measurement.depth_for_concentration_to = \
            self.depthForConcentrationToDoubleSpinBox.value()
        self.measurement.channel_width = self.channelWidthDoubleSpinBox.value()
        self.measurement.number_of_splits = self.numberOfSplitsSpinBox.value()
        self.measurement.normalization = \
            self.normalizationComboBox.currentText()

    def values_changed(self):
        """
        Check if profile settings have changed.

        Return:
            True or False.
        """
        if self.measurement.profile_name != self.nameLineEdit.text():
            return True
        if self.measurement.profile_description != \
            self.descriptionPlainTextEdit.toPlainText():
            return True
        if self.measurement.reference_density != \
            self.referenceDensityDoubleSpinBox.value():
            return True
        if self.measurement.number_of_depth_steps != \
            self.numberOfDepthStepsSpinBox.value():
            return True
        if self.measurement.depth_step_for_stopping != \
            self.depthStepForStoppingSpinBox.value():
            return True
        if self.measurement.depth_step_for_output != \
            self.depthStepForOutputSpinBox.value():
            return True
        if self.measurement.depth_for_concentration_from != \
            self.depthForConcentrationFromDoubleSpinBox.value():
            return True
        if self.measurement.depth_for_concentration_to != \
            self.depthForConcentrationToDoubleSpinBox.value():
            return True
        if self.measurement.channel_width != \
            self.channelWidthDoubleSpinBox.value():
            return True
        if self.measurement.number_of_splits != \
            self.numberOfSplitsSpinBox.value():
            return True
        if self.measurement.normalization != \
            self.normalizationComboBox.currentText():
            return True
        return False

    @staticmethod
    def __check_text(input_field, settings):
        """Checks if there is text in given input field.

        Args:
            input_field: Input field the contents of which are checked.
            settings: Settings widget.
        """
        settings.fields_are_valid = iv.check_text(input_field)
