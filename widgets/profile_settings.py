# coding=utf-8
"""
Created on 10.4.2018
Updated on 25.6.2018

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

from os import path
from PyQt5 import uic
from PyQt5 import QtWidgets

from modules.general_functions import set_input_field_red
from modules.general_functions import check_text
from modules.general_functions import validate_text_input
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
        self.ui = uic.loadUi(path.join("ui_files",
                                       "ui_profile_settings_tab.ui"), self)
        self.measurement = measurement

        set_input_field_red(self.ui.nameLineEdit)
        self.fields_are_valid = False
        self.ui.nameLineEdit.textChanged.connect(lambda: self.__check_text(
            self.ui.nameLineEdit, self))

        self.ui.nameLineEdit.textEdited.connect(lambda: self.__validate())

        locale = QLocale.c()
        self.referenceDensityDoubleSpinBox.setLocale(locale)
        self.depthForConcentrationFromDoubleSpinBox.setLocale(locale)
        self.depthForConcentrationToDoubleSpinBox.setLocale(locale)
        self.channelWidthDoubleSpinBox.setLocale(locale)

        self.show_settings()

    def show_settings(self):
        """
        Show profile settings.
        """
        if not self.measurement.use_default_profile_settings:
            self.nameLineEdit.setText(
                self.measurement.profile_name)
            self.descriptionPlainTextEdit.setPlainText(
                self.measurement.profile_description)
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
        self.measurement.profile_name = \
            self.nameLineEdit.text()
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
        self.measurement.channel_width = \
            self.channelWidthDoubleSpinBox.value()
        self.measurement.number_of_splits = \
            self.numberOfSplitsSpinBox.value()
        self.measurement.normalization = \
            self.normalizationComboBox.currentText()

    @staticmethod
    def __check_text(input_field, settings):
        """Checks if there is text in given input field.

        Args:
            input_field: Input field the contents of which are checked.
            settings: Settings widget.
        """
        settings.fields_are_valid = check_text(input_field)

    def __validate(self):
        """
        Validate the mcsimu settings file name.
        """
        text = self.ui.nameLineEdit.text()
        regex = "^[A-Za-z0-9-ÖöÄäÅå]*"
        valid_text = validate_text_input(text, regex)

        self.ui.nameLineEdit.setText(valid_text)
