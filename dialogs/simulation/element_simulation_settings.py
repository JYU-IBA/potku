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

        self.ui.okPushButton.clicked.connect(self.accept_settings)
        self.ui.cancelPushButton.clicked.connect(self.close)

        self.element_simulation = element_simulation
        self.temp_settings = {}
        self.isOk = False
        self.use_default = True

        self.ui.useRequestSettingsValuesCheckBox.stateChanged.connect(
            self.toggle_settings)
        self.import_default_settings()

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

    def import_default_settings(self):
        default_element_simu = self.element_simulation.request\
            .default_element_simulation

        self.ui.typeOfSimulationComboBox.setCurrentIndex(
            self.ui.typeOfSimulationComboBox.findText(
                default_element_simu.simulation_type))
        self.ui.modeComboBox.setCurrentIndex(
            self.ui.modeComboBox.findText(
                default_element_simu.simulation_mode))
        self.ui.numberOfIonsSpinBox.setValue(
            default_element_simu.number_of_ions)
        self.ui.numberOfPreIonsSpinBox.setValue(
            default_element_simu.number_of_preions)
        self.ui.seedSpinBox.setValue(
            default_element_simu.seed_number)
        self.ui.numberOfRecoilsSpinBox.setValue(
            default_element_simu.number_of_recoils)
        self.ui.numberOfScalingIonsSpinBox.setValue(
            default_element_simu.number_of_scaling_ions)
        self.ui.minimumScatterAngleDoubleSpinBox.setValue(
            default_element_simu.minimum_scattering_angle)
        self.ui.minimumMainScatterAngleDoubleSpinBox.setValue(
            default_element_simu.minimum_main_scattering_angle)
        self.ui.minimumEnergyDoubleSpinBox.setValue(
            default_element_simu.minimum_energy)

    def toggle_settings(self):
        """If request settings checkbox is checked, disables settings in dialog.
        Otherwise enables settings.
        """
        if self.ui.useRequestSettingsValuesCheckBox.isChecked():
            self.ui.generalParametersGroupBox.setEnabled(False)
            self.ui.physicalParametersGroupBox.setEnabled(False)
            self.import_default_settings()
            self.use_default = True
        else:
            self.ui.generalParametersGroupBox.setEnabled(True)
            self.ui.physicalParametersGroupBox.setEnabled(True)
            self.import_specific_settings()
            self.use_default = False

    def accept_settings(self):
        """Function for accepting the current settings and closing the dialog
        window.
        """
        self.temp_settings["name"] = \
            self.ui.nameLineEdit.text()
        self.temp_settings["description"] = \
            self.ui.descriptionPlainTextEdit\
            .toPlainText()
        self.temp_settings["mode"] = \
            self.ui.modeComboBox.currentText()
        self.temp_settings["simulation_type"] = \
            self.ui.typeOfSimulationComboBox.currentText()
        self.temp_settings["no_of_ions"] = \
            self.ui.numberOfIonsSpinBox.value()
        self.temp_settings["no_of_preions"] = \
            self.ui.numberOfPreIonsSpinBox\
            .value()
        self.temp_settings["seed"] = \
            self.ui.seedSpinBox.value()
        self.temp_settings["no_of_recoils"] = \
            self.ui.numberOfRecoilsSpinBox.value()
        self.temp_settings["no_of_scaling"] = \
            self.ui.numberOfScalingIonsSpinBox.value()
        self.temp_settings["scatter"] = \
            self.ui.minimumScatterAngleDoubleSpinBox.value()
        self.temp_settings["main_scatter"] = \
            self.ui.minimumMainScatterAngleDoubleSpinBox.value()
        self.temp_settings["energy"] = \
            self.ui.minimumEnergyDoubleSpinBox.value()

        self.isOk = True
        self.close()
