# coding=utf-8
"""
Created on 4.5.2018
"""
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä " \
             "\n Sinikka Siironen"

import os
from PyQt5 import uic, QtWidgets


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
        self.import_specific_settings()

        self.exec_()

    def set_spinbox_maximums(self):
        # These are the max values that the spinboxes allow. They should be big
        # enough.
        intmax = 2147483647
        floatmax = 1000000000000000013287555072.00
        self.ui.numberOfIonsSpinBox.setMaximum(intmax)
        self.ui.numberOfPreIonsSpinBox.setMaximum(intmax)
        self.ui.seedSpinBox.setMaximum(intmax)
        self.ui.numberOfRecoilsSpinBox.setMaximum(intmax)
        self.ui.numberOfScalingIonsSpinBox.setMaximum(intmax)
        self.ui.minimumScatterAngleDoubleSpinBox.setMaximum(floatmax)
        self.ui.minimumMainScatterAngleDoubleSpinBox.setMaximum(floatmax)
        self.ui.minimumEnergyDoubleSpinBox.setMaximum(floatmax)

    def import_specific_settings(self):
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
