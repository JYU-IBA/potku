# coding=utf-8
"""
Created on 4.4.2018
Updated on 30.5.2018

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2013-2018 Jarkko Aalto, Severi Jääskeläinen, Samuel Kaiponen,
Timo Konu, Samuli Kärkkäinen, Samuli Rahkonen, Miika Raunio, Heta Rekilä and
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

import os
from PyQt5 import uic
from PyQt5 import QtWidgets


class ElementSimulationSettingsDialog(QtWidgets.QDialog):
    """Class for creating an element simulation settings tab.
    """
    def __init__(self, element_simulation):
        super().__init__()
        self.ui = uic.loadUi(os.path.join("ui_files",
                                          "ui_element_simulation_settings.ui"),
                             self)

        self.ui.okPushButton.clicked.connect(self.update_settings_and_close)
        self.ui.applyPushButton.clicked.connect(self.update_settings)
        self.ui.cancelPushButton.clicked.connect(self.close)

        self.element_simulation = element_simulation
        self.temp_settings = {}

        self.use_default_settings = True

        self.ui.useRequestSettingsValuesCheckBox.stateChanged.connect(
            self.toggle_settings)

        self.set_spinbox_maximums()
        self.show_settings()

        self.exec_()

    def set_spinbox_maximums(self):
        """Set maximum values to spinbox components."""
        int_max = 2147483647
        float_max = 1000000000000000013287555072.00
        self.ui.numberOfIonsSpinBox.setMaximum(int_max)
        self.ui.numberOfPreIonsSpinBox.setMaximum(int_max)
        self.ui.seedSpinBox.setMaximum(int_max)
        self.ui.numberOfRecoilsSpinBox.setMaximum(int_max)
        self.ui.numberOfScalingIonsSpinBox.setMaximum(int_max)
        self.ui.minimumScatterAngleDoubleSpinBox.setMaximum(float_max)
        self.ui.minimumMainScatterAngleDoubleSpinBox.setMaximum(float_max)
        self.ui.minimumEnergyDoubleSpinBox.setMaximum(float_max)

    def show_settings(self):
        """Show settings of ElementSimulation object in view."""
        self.ui.nameLineEdit.setText(
            self.element_simulation.name)
        self.ui.descriptionPlainTextEdit.setPlainText(
            self.element_simulation.description)
        self.ui.typeOfSimulationComboBox.setCurrentIndex(
            self.ui.typeOfSimulationComboBox.findText(
                self.element_simulation.simulation_type))
        self.ui.modeComboBox.setCurrentIndex(
            self.ui.modeComboBox.findText(
                self.element_simulation.simulation_mode))
        self.ui.numberOfIonsSpinBox.setValue(
            self.element_simulation.number_of_ions)
        self.ui.numberOfPreIonsSpinBox.setValue(
            self.element_simulation.number_of_preions)
        self.ui.seedSpinBox.setValue(
            self.element_simulation.seed_number)
        self.ui.numberOfRecoilsSpinBox.setValue(
            self.element_simulation.number_of_recoils)
        self.ui.numberOfScalingIonsSpinBox.setValue(
            self.element_simulation.number_of_scaling_ions)
        self.ui.minimumScatterAngleDoubleSpinBox.setValue(
            self.element_simulation.minimum_scattering_angle)
        self.ui.minimumMainScatterAngleDoubleSpinBox.setValue(
            self.element_simulation.minimum_main_scattering_angle)
        self.ui.minimumEnergyDoubleSpinBox.setValue(
            self.element_simulation.minimum_energy)

    def toggle_settings(self):
        """If request settings checkbox is checked, disables settings in dialog.
        Otherwise enables settings.
        """
        if self.ui.useRequestSettingsValuesCheckBox.isChecked():
            self.ui.settingsGroupBox.setEnabled(False)
            self.use_default_settings = True
        else:
            self.ui.settingsGroupBox.setEnabled(True)
            self.use_default_settings = False

    def update_settings_and_close(self):
        """Updates settings and closes the dialog."""
        self.update_settings()
        self.close()

    def update_settings(self):
        """If default settings are used, put them to element simulation and
        delete the specific setting file, if it exists. If default settings are
        not used, read settings from dialog, put them to element simulation and
        save them to file.
        """

        if self.use_default_settings:
            # Use request settings
            default_element_simu = self.element_simulation.request \
                .default_element_simulation

            try:
                os.remove(
                    os.path.join(self.element_simulation.directory,
                                 self.element_simulation.name + ".mcsimu"))
            except OSError:
                pass  # The file doesn't exist

            self.element_simulation.name = \
                default_element_simu.name
            self.element_simulation.description = \
                default_element_simu.description
            self.element_simulation.simulation_type = \
                default_element_simu.simulation_type
            self.element_simulation.simulation_mode = \
                default_element_simu.simulation_mode
            self.element_simulation.number_of_ions = \
                default_element_simu.number_of_ions
            self.element_simulation.number_of_preions = \
                default_element_simu.number_of_preions
            self.element_simulation.seed_number = \
                default_element_simu.seed_number
            self.element_simulation.number_of_recoils = \
                default_element_simu.number_of_recoils
            self.element_simulation.number_of_scaling_ions = \
                default_element_simu.number_of_scaling_ions
            self.element_simulation.minimum_scattering_angle = \
                default_element_simu.minimum_scattering_angle
            self.element_simulation.minimum_main_scattering_angle = \
                default_element_simu.minimum_main_scattering_angle
            self.element_simulation.minimum_energy = \
                default_element_simu.minimum_energy
        else:
            # Use element specific settings
            self.element_simulation.name = \
                self.ui.nameLineEdit.text()
            self.element_simulation.description = \
                self.ui.descriptionPlainTextEdit.toPlainText()
            self.element_simulation.simulation_type = \
                self.ui.typeOfSimulationComboBox.currentText()
            self.element_simulation.simulation_mode = \
                self.ui.modeComboBox.currentText()
            self.element_simulation.number_of_ions = \
                self.ui.numberOfIonsSpinBox.value()
            self.element_simulation.number_of_preions = \
                self.ui.numberOfPreIonsSpinBox\
                .value()
            self.element_simulation.seed_number = \
                self.ui.seedSpinBox.value()
            self.element_simulation.number_of_recoils = \
                self.ui.numberOfRecoilsSpinBox.value()
            self.element_simulation.number_of_scaling_ions = \
                self.ui.numberOfScalingIonsSpinBox.value()
            self.element_simulation.minimum_scattering_angle = \
                self.ui.minimumScatterAngleDoubleSpinBox.value()
            self.element_simulation.minimum_main_scattering_angle = \
                self.ui.minimumMainScatterAngleDoubleSpinBox.value()
            self.element_simulation.minimum_energy = \
                self.ui.minimumEnergyDoubleSpinBox.value()

            self.element_simulation.mcsimu_to_file(
                    os.path.join(self.element_simulation.directory,
                                 self.element_simulation.name + ".mcsimu"))
