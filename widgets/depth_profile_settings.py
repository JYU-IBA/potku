# coding=utf-8
"""
Created on 10.4.2018
"""
import time

from PyQt5.QtCore import Qt

__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"

from os import path
from PyQt5 import uic, QtWidgets


class DepthProfileSettingsWidget(QtWidgets.QWidget):
    """Class for creating a request wide depth profile settings tab.
    """
    def __init__(self, obj):
        super().__init__()
        self.ui = uic.loadUi(path.join("ui_files", "ui_request_depth_profile_settings.ui"), self)

        self.obj = obj

        self.show_settings()

    def show_settings(self):
        """Show settings in dialog.
        """
        self.nameLineEdit.setText(self.obj.profile_name)
        self.descriptionPlainTextEdit.setPlainText(self.obj.profile_description)
        self.dateLabel.setText(time.strftime("%c %z %Z", time.localtime(
            self.obj.profile_modification_time)))

        self.referenceDensityDoubleSpinBox.setValue(self.obj.reference_density)
        self.numberOfDepthStepsSpinBox.setValue(self.obj.number_of_depth_steps)
        self.depthStepForStoppingSpinBox.setValue(
            self.obj.depth_step_for_stopping)
        self.depthStepForOutputSpinBox.setValue(self.obj.depth_step_for_output)
        self.depthForConcentrationFromDoubleSpinBox.setValue(
            self.obj.depth_for_concentration_from)
        self.depthForConcentrationToDoubleSpinBox.setValue(
            self.obj.depth_for_concentration_to)

        self.channelWidthDoubleSpinBox.setValue(self.obj.channel_width)

        self.referenceCutLineEdit.setText(self.obj.reference_cut)
        self.numberOfSplitsSpinBox.setValue(self.obj.number_of_splits)
        self.normalizationComboBox.setCurrentIndex(
            self.normalizationComboBox.findText(self.obj.normalization,
                                                Qt.MatchFixedString))

    def update_settings(self):
        """Updates settings to Measurement object.
        """
        self.obj.profile_name = self.nameLineEdit.text()
        self.obj.profile_description = self \
            .descriptionPlainTextEdit.toPlainText()

        self.obj.reference_density = self.referenceDensityDoubleSpinBox.value()
        self.obj.number_of_depth_steps = self.numberOfDepthStepsSpinBox.value()
        self.obj.depth_step_for_stopping = \
            self.depthStepForStoppingSpinBox.value()
        self.obj.depth_step_for_output = self.depthStepForOutputSpinBox.value()
        self.obj.depths_for_concentration_from = \
            self.depthForConcentrationFromDoubleSpinBox.value()
        self.obj.depths_for_concentration_to = \
            self.depthForConcentrationToDoubleSpinBox.value()

        self.obj.channel_width = self.channelWidthDoubleSpinBox.value()

        self.obj.reference_cut = self.referenceCutLineEdit.text()
        self.obj.number_of_splits = self.numberOfSplitsSpinBox.value()
        self.obj.normalization = self.normalizationComboBox.currentText().lower()
