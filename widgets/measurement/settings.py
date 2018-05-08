# coding=utf-8
"""
Created on 10.4.2018
"""
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"

import os
from PyQt5 import uic, QtWidgets
from modules.element import Element


class MeasurementSettingsWidget(QtWidgets.QWidget):
    """Class for creating a request wide measurement settings tab.
    """
    def __init__(self, obj):
        super().__init__()
        self.ui = uic.loadUi(os.path.join("ui_files",
                                  "ui_request_measurement_settings.ui"), self)
        self.obj = obj

        self.show_settings()
        
    def show_settings(self):
        if self.obj.run.beam.ion:
            self.beamIonButton.setText(
                self.obj.run.beam.ion.symbol)
            # TODO Check that the isotope is also set.
            self.isotopeComboBox.setEnabled(True)
        else:
            self.beamIonButton.setText("Select")
            self.isotopeComboBox.setEnabled(
                False)

        link_angle_values(self.detectorThetaDoubleSpinBox,
                               self.detectorFiiDoubleSpinBox)
        link_angle_values(self.targetThetaDoubleSpinBox,
                               self.targetFiiDoubleSpinBox)

        self.nameLineEdit.setText(
            self.obj.measurement_setting_file_name)
        self.descriptionPlainTextEdit.setPlainText(
            self.obj.measurement_setting_file_description)
        self.energyDoubleSpinBox.setValue(
            self.obj.run.beam.energy)
        self.energyDistDoubleSpinBox.setValue(
            self.obj.run.beam.energy_distribution)
        self.beamChargeSpinBox.setValue(
            self.obj.run.beam.charge)
        self.spotSizeXdoubleSpinBox.setValue(
            self.obj.run.beam.spot_size[0])
        self.spotSizeXdoubleSpinBox.setValue(
            self.obj.run.beam.spot_size[1])
        self.divergenceDoubleSpinBox.setValue(
            self.obj.run.beam.divergence)
        self.profileComboBox.setCurrentIndex(
            self.profileComboBox.findText(
                self.obj.run.beam.profile))
        self.fluenceDoubleSpinBox.setValue(
            self.obj.run.fluence)
        self.currentDoubleSpinBox.setValue(
            self.obj.run.current)
        self.timeDoubleSpinBox.setValue(
            self.obj.run.time)
        self.detectorThetaDoubleSpinBox.setValue(
            self.obj.detector.detector_theta)
        # TODO: Fix the angle links to correct values
        self.detectorFiiDoubleSpinBox.setValue(
            self.obj.detector.detector_theta + 180)
        self.targetThetaDoubleSpinBox.setValue(
            self.obj.target.target_theta)
        self.targetFiiDoubleSpinBox.setValue(
            self.obj.target.target_theta + 180)

    def update_settings(self):
        # Measurement settings
        isotope_index = self.isotopeComboBox. \
            currentIndex()
        if isotope_index != -1:
            isotope_data = self.isotopeComboBox.itemData(isotope_index)
            self.obj.ion = Element(self.beamIonButton.text(),
                isotope_data[0])
            self.obj.measurement_setting_file_name = self.nameLineEdit.text()
            self.obj.measurement_setting_file_description = self\
                .descriptionPlainTextEdit.toPlainText()
            self.obj.run.beam.energy = self.energyDoubleSpinBox.value()
            self.obj.run.beam.energy_dist = self.energyDistDoubleSpinBox.value()
            self.obj.run.beam.charge = self.beamChargeSpinBox.value()
            self.obj.run.beam.spot_size = [
                self.spotSizeXdoubleSpinBox.value(),
                self.spotSizeYdoubleSpinBox.value()]
            self.obj.run.beam.divergence = self.divergenceDoubleSpinBox.value()
            self.obj.run.beam.profile = self.profileComboBox.currentText()
            self.obj.run.fluence = self.fluenceDoubleSpinBox.value()
            self.obj.run.current = self.currentDoubleSpinBox.value()
            self.obj.run.beam_time = self.timeDoubleSpinBox.value()
            self.obj.detector.detector_theta = self\
                .detectorThetaDoubleSpinBox.value()
            self.obj.target.target_theta = self\
                .targetThetaDoubleSpinBox.value()

            self.obj.to_file(os.path.join(
                self.obj.directory, self.obj.measurement_setting_file_name +
                ".measurement"),
                os.path.join(
                    self.obj.directory, self.obj.profile_name + ".profile"))


def link_angle_values(theta, fii):
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
