# coding=utf-8
"""
Created on 4.4.2018
Updated on 25.6.2018

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
from PyQt5.QtCore import Qt
import time
from modules.general_functions import set_input_field_red
from modules.general_functions import check_text
from modules.general_functions import validate_text_input
from PyQt5.QtCore import QLocale


class ElementSimulationSettingsDialog(QtWidgets.QDialog):
    """Class for creating an element simulation settings tab.
    """
    def __init__(self, element_simulation):
        """
        Inintializes the dialog.

        Args:
            element_simulation: An ElementSimulation object.
        """
        super().__init__()
        self.ui = uic.loadUi(os.path.join("ui_files",
                                          "ui_element_simulation_settings.ui"),
                             self)

        self.ui.okPushButton.clicked.connect(self.update_settings_and_close)
        self.ui.applyPushButton.clicked.connect(self.update_settings)
        self.ui.cancelPushButton.clicked.connect(self.close)

        self.element_simulation = element_simulation
        self.temp_settings = {}

        self.use_default_settings = element_simulation.use_default_settings

        self.ui.useRequestSettingsValuesCheckBox.stateChanged.connect(
            self.toggle_settings)

        self.set_spinbox_maximums()

        set_input_field_red(self.ui.nameLineEdit)
        self.fields_are_valid = False
        self.ui.nameLineEdit.textChanged.connect(lambda: self.__check_text(
            self.ui.nameLineEdit, self))

        self.show_settings()

        self.ui.nameLineEdit.textEdited.connect(lambda: self.__validate())

        locale = QLocale.c()
        self.ui.minimumScatterAngleDoubleSpinBox.setLocale(locale)
        self.ui.minimumMainScatterAngleDoubleSpinBox.setLocale(locale)
        self.ui.minimumEnergyDoubleSpinBox.setLocale(locale)

        self.__close = True

        self.exec_()

    @staticmethod
    def __check_text(input_field, settings):
        """Checks if there is text in given input field.

        Args:
            input_field: Input field the contents of which are checked.
            settings: Settings dialog.
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
        if self.use_default_settings:
            elem_simu = self.element_simulation.request.\
                default_element_simulation
        else:
            elem_simu = self.element_simulation
            self.ui.useRequestSettingsValuesCheckBox.setCheckState(0)
            self.ui.settingsGroupBox.setEnabled(True)
            self.use_default_settings = False
        self.ui.nameLineEdit.setText(
            elem_simu.name)
        self.ui.descriptionPlainTextEdit.setPlainText(
            elem_simu.description)
        self.ui.dateLabel.setText(time.strftime("%c %z %Z", time.localtime(
            elem_simu.modification_time)))
        if elem_simu.simulation_type == "ERD":
            self.ui.typeOfSimulationComboBox.setCurrentIndex(
                self.ui.typeOfSimulationComboBox.findText(
                    "REC", Qt.MatchFixedString))
        else:
            self.ui.typeOfSimulationComboBox.setCurrentIndex(
                self.ui.typeOfSimulationComboBox.findText(
                    "SCT", Qt.MatchFixedString))
        self.ui.modeComboBox.setCurrentIndex(
            self.ui.modeComboBox.findText(
                elem_simu.simulation_mode, Qt.MatchFixedString))
        self.ui.numberOfIonsSpinBox.setValue(
            elem_simu.number_of_ions)
        self.ui.numberOfPreIonsSpinBox.setValue(
            elem_simu.number_of_preions)
        self.ui.seedSpinBox.setValue(
            elem_simu.seed_number)
        self.ui.numberOfRecoilsSpinBox.setValue(
            elem_simu.number_of_recoils)
        self.ui.numberOfScalingIonsSpinBox.setValue(
            elem_simu.number_of_scaling_ions)
        self.ui.minimumScatterAngleDoubleSpinBox.setValue(
            elem_simu.minimum_scattering_angle)
        self.ui.minimumMainScatterAngleDoubleSpinBox.setValue(
            elem_simu.minimum_main_scattering_angle)
        self.ui.minimumEnergyDoubleSpinBox.setValue(
            elem_simu.minimum_energy)

    def toggle_settings(self):
        """If request settings checkbox is checked, disables settings in dialog.
        Otherwise enables settings.
        """
        if self.ui.useRequestSettingsValuesCheckBox.isChecked():
            self.ui.settingsGroupBox.setEnabled(False)
            self.use_default_settings = True
            self.element_simulation.use_default_settings = True
        else:
            self.ui.settingsGroupBox.setEnabled(True)
            self.use_default_settings = False
            self.element_simulation.use_default_settings = False

    def update_settings_and_close(self):
        """Updates settings and closes the dialog."""
        self.update_settings()
        if self.__close:
            self.close()

    def update_settings(self):
        """Delete existing file.
        If default settings are used, put them to element simulation and save
        into a file.
        If default settings are not used, read settings from dialog,
        put them to element simulation and save them to file.
        """
        if not self.fields_are_valid:
            QtWidgets.QMessageBox.critical(self, "Warning",
                                           "Some of the setting values have"
                                           " not been set.\n" +
                                           "Please input values in fields "
                                           "indicated in red.",
                                           QtWidgets.QMessageBox.Ok,
                                           QtWidgets.QMessageBox.Ok)
            self.__close = False
            return

        # Delete .mcsimu file if exists
        filename_to_remove = ""
        for file in os.listdir(self.element_simulation.directory):
            if file.endswith(".mcsimu") and file.startswith(
                    self.element_simulation.name_prefix):
                filename_to_remove = file
                break
        if filename_to_remove:
            os.remove(os.path.join(self.element_simulation.directory,
                                   filename_to_remove))

        if not self.use_default_settings:
            # Use element specific settings
            self.element_simulation.name = \
                self.ui.nameLineEdit.text()
            self.element_simulation.description = \
                self.ui.descriptionPlainTextEdit.toPlainText()
            self.element_simulation.simulation_mode = \
                self.ui.modeComboBox.currentText()
            if self.ui.typeOfSimulationComboBox.currentText() == "REC":
                self.element_simulation.simulation_type = "ERD"
            else:
                self.element_simulation.simulation_type = "RBS"
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
                                 self.element_simulation.name_prefix + "-" +
                                 self.element_simulation.name + ".mcsimu"))

        # Revert ot default settings
        else:
            self.element_simulation.name = \
                self.element_simulation.request.default_element_simulation.name
            self.element_simulation.description = \
                self.element_simulation.request.default_element_simulation\
                    .description
            self.element_simulation.simulation_mode = \
                self.element_simulation.request.default_element_simulation\
                    .simulation_mode
            self.element_simulation.simulation_type = \
                self.element_simulation.request.default_element_simulation\
                    .simulation_type
            self.element_simulation.number_of_ions = \
                self.element_simulation.request.default_element_simulation\
                    .number_of_ions
            self.element_simulation.number_of_preions = \
                self.element_simulation.request.default_element_simulation\
                    .number_of_preions
            self.element_simulation.seed_number = \
                self.element_simulation.request.default_element_simulation\
                    .seed_number
            self.element_simulation.number_of_recoils = \
                self.element_simulation.request.default_element_simulation\
                    .number_of_recoils
            self.element_simulation.number_of_scaling_ions = \
                self.element_simulation.request.default_element_simulation\
                    .number_of_scaling_ions
            self.element_simulation.minimum_scattering_angle = \
                self.element_simulation.request.default_element_simulation\
                    .minimum_scattering_angle
            self.element_simulation.minimum_main_scattering_angle = \
                self.element_simulation.request.default_element_simulation\
                    .minimum_main_scattering_angle
            self.element_simulation.minimum_energy = \
                self.element_simulation.request.default_element_simulation\
                    .minimum_energy

            self.element_simulation.mcsimu_to_file(
                os.path.join(self.element_simulation.directory,
                             self.element_simulation.name_prefix + "-" +
                             self.element_simulation.name + ".mcsimu"))

        self.__close = True
