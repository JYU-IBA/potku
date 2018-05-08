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
    def __init__(self, measurement, detector, target):
        super().__init__()
        self.ui = uic.loadUi(os.path.join("ui_files",
                                  "ui_request_measurement_settings.ui"), self)
        self.measurement = measurement
        self.detector = detector
        self.target = target

        self.show_settings()
        
    def show_settings(self):
        if self.measurement.run.beam.ion:
            self.beamIonButton.setText(
                self.measurement.run.beam.ion.symbol)
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
            self.measurement.name)
        self.descriptionPlainTextEdit.setPlainText(
            self.measurement.description)
        self.energyDoubleSpinBox.setValue(
            self.measurement.run.beam.energy)
        self.energyDistDoubleSpinBox.setValue(
            self.measurement.run.beam.energy_distribution)
        self.beamChargeSpinBox.setValue(
            self.measurement.run.beam.charge)
        self.spotSizeXdoubleSpinBox.setValue(
            self.measurement.run.beam.spot_size[0])
        self.spotSizeXdoubleSpinBox.setValue(
            self.measurement.run.beam.spot_size[1])
        self.divergenceDoubleSpinBox.setValue(
            self.measurement.run.beam.divergence)
        self.profileComboBox.setCurrentIndex(
            self.profileComboBox.findText(
                self.measurement.run.beam.profile))
        self.fluenceDoubleSpinBox.setValue(
            self.measurement.run.fluence)
        self.currentDoubleSpinBox.setValue(
            self.measurement.run.current)
        self.timeDoubleSpinBox.setValue(
            self.measurement.run.time)
        self.detectorThetaDoubleSpinBox.setValue(
            self.detector.detector_theta)
        # TODO: Fix the angle links to correct values
        self.detectorFiiDoubleSpinBox.setValue(
            self.detector.detector_theta + 180)
        self.targetThetaDoubleSpinBox.setValue(
            self.target.target_theta)
        self.targetFiiDoubleSpinBox.setValue(
            self.target.target_theta + 180)

    def update_settings(self):
        # Measurement settings
        isotope_index = self.isotopeComboBox. \
            currentIndex()
        if isotope_index != -1:
            isotope_data = self.isotopeComboBox.itemData(isotope_index)
            self.measurement.ion = Element(self.beamIonButton.text(),
                isotope_data[0])
            self.measurement.name = self.nameLineEdit.text()
            self.measurement.description = self.descriptionPlainTextEdit\
                .toPlainText()
            self.measurement.energy = self.energyDoubleSpinBox.value()
            self.measurement.energy_dist = self.energyDistDoubleSpinBox.value()
            self.measurement.charge = self.beamChargeSpinBox.value()
            self.measurement.spot_size = [
                self.spotSizeXdoubleSpinBox.value(),
                self.spotSizeYdoubleSpinBox.value()]
            self.measurement.divergence = self.divergenceDoubleSpinBox.value()
            self.measurement.profile = self.profileComboBox.currentText()
            self.measurement.fluence = self.fluenceDoubleSpinBox.value()
            self.measurement.current = self.currentDoubleSpinBox.value()
            self.measurement.beam_time = self.timeDoubleSpinBox.value()
            self.measurement.detector_theta = self\
                .detectorThetaDoubleSpinBox.value()
            self.measurement.target_theta = self\
                .targetThetaDoubleSpinBox.value()

            self.measurement.save_settings(
                self.folder + os.sep +
                "Default")
            # TODO Implement to_file for Measurement
        #                self.measurement.to_file(
        #                    self.folder + os.sep +
        #                    "Default.measurement")



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
