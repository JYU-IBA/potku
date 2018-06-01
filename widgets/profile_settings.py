# coding=utf-8
"""
Created on 10.4.2018
Updated on 1.6.2018

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

        self.show_settings()

    def show_settings(self):
        """
        Show profile settings.
        """
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
        self.referenceCutLineEdit.setText(
            self.measurement.reference_cut)
        self.numberOfSplitsSpinBox.setValue(
            self.measurement.number_of_splits)
        self.normalizationComboBox.setCurrentIndex(
            self.normalizationComboBox.findText(
                self.measurement.normalization))

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
        self.measurement.reference_cut = \
            self.referenceCutLineEdit.text()
        self.measurement.number_of_splits = \
            self.numberOfSplitsSpinBox.value()
        self.measurement.normalization = \
            self.normalizationComboBox.currentText()
