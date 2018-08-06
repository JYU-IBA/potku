# coding=utf-8
"""
Created on 15.3.2018
Updated on 25.7.2018

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
__version__ = "2.0"

import os
import time

from modules.general_functions import check_text
from modules.general_functions import set_input_field_red
from modules.general_functions import validate_text_input

from PyQt5 import QtWidgets
from PyQt5 import uic
from PyQt5.QtCore import QLocale
from PyQt5.QtCore import Qt


class SimulationSettingsWidget(QtWidgets.QWidget):
    """Class for creating a simulation settings tab.
    """
    def __init__(self, obj):
        """
        Initializes the widget.

        Args:
            obj: Element simulation object.
        """
        super().__init__()
        self.ui = uic.loadUi(os.path.join("ui_files",
                                          "ui_request_simulation_settings.ui"),
                             self)
        self.obj = obj

        set_input_field_red(self.ui.nameLineEdit)
        self.fields_are_valid = False
        self.ui.nameLineEdit.textChanged.connect(lambda: self.__check_text(
            self.ui.nameLineEdit, self))

        self.ui.nameLineEdit.textEdited.connect(lambda: self.__validate())

        locale = QLocale.c()
        self.ui.minimumScatterAngleDoubleSpinBox.setLocale(locale)
        self.ui.minimumMainScatterAngleDoubleSpinBox.setLocale(locale)
        self.ui.minimumEnergyDoubleSpinBox.setLocale(locale)

        self.show_settings()

    def show_settings(self):
        """
        Show simualtion settings.
        """
        self.ui.nameLineEdit.setText(self.obj.name)
        self.ui.dateLabel.setText(time.strftime("%c %z %Z", time.localtime(
            self.obj.modification_time)))
        self.ui.descriptionPlainTextEdit.setPlainText(self.obj.description)
        self.ui.modeComboBox.setCurrentIndex(self.ui.modeComboBox.findText(
            self.obj.simulation_mode, Qt.MatchFixedString))
        if self.obj.simulation_type == "ERD":
            self.ui.typeOfSimulationComboBox.setCurrentIndex(
                self.ui.typeOfSimulationComboBox.findText(
                    "REC", Qt.MatchFixedString))
        else:
            self.ui.typeOfSimulationComboBox.setCurrentIndex(
                self.ui.typeOfSimulationComboBox.findText("SCT",
                                                         Qt.MatchFixedString))
        self.ui.minimumScatterAngleDoubleSpinBox.setValue(
            self.obj.minimum_scattering_angle)
        self.ui.minimumMainScatterAngleDoubleSpinBox.setValue(
            self.obj.minimum_main_scattering_angle)
        self.ui.minimumEnergyDoubleSpinBox.setValue(self.obj.minimum_energy)
        self.ui.numberOfIonsSpinBox.setValue(self.obj.number_of_ions)
        self.ui.numberOfPreIonsSpinBox.setValue(self.obj.number_of_preions)
        self.ui.seedSpinBox.setValue(self.obj.seed_number)
        self.ui.numberOfRecoilsSpinBox.setValue(self.obj.number_of_recoils)
        self.ui.numberOfScalingIonsSpinBox.setValue(
            self.obj.number_of_scaling_ions)

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

    def update_settings(self):
        """
        Update simulation settings.
        """
        self.obj.name = self.ui.nameLineEdit.text()
        self.obj.description = self.ui.descriptionPlainTextEdit.toPlainText()
        if self.ui.typeOfSimulationComboBox.currentText() == "REC":
            if self.obj.simulation_type != "ERD":
                self.obj.simulation_type = "ERD"
                for recoil in self.obj.recoil_elements:
                    recoil.type = "rec"
                    try:
                        path_to_rec = os.path.join(
                            self.obj.directory,
                            recoil.prefix + "-" + recoil.name + ".sct")
                        os.remove(path_to_rec)
                    except OSError:
                        pass
                    self.obj.recoil_to_file(
                        self.obj.directory, recoil)
        else:
            if self.obj.simulation_type != "RBS":
                self.obj.simulation_type = "RBS"
                for recoil in self.obj.recoil_elements:
                    recoil.type = "sct"
                    try:
                        path_to_rec = os.path.join(
                            self.obj.directory,
                            recoil.prefix + "-" + recoil.name + ".rec")
                        os.remove(path_to_rec)
                    except OSError:
                        pass
                    self.obj.recoil_to_file(
                        self.obj.directory, recoil)

        self.obj.simulation_mode = self.ui.modeComboBox.currentText().lower()
        self.obj.number_of_ions = self.ui.numberOfIonsSpinBox.value()
        self.obj.number_of_preions = self.ui.numberOfPreIonsSpinBox.value()
        self.obj.seed_number = self.ui.seedSpinBox.value()
        self.obj.number_of_recoils = self.ui.numberOfRecoilsSpinBox.value()
        self.obj.number_of_scaling_ions = self.ui.numberOfScalingIonsSpinBox. \
            value()
        self.obj.minimum_scattering_angle = \
            self.ui.minimumScatterAngleDoubleSpinBox.value()
        self.obj.minimum_main_scattering_angle = \
            self.ui.minimumMainScatterAngleDoubleSpinBox.value()
        self.obj.minimum_energy = self.ui.minimumEnergyDoubleSpinBox.value()

    def values_changed(self):
        """
        Check if simulation settings have been changed. Seed number change is
        not registered as value change.

        Return:
            True or False.
        """
        if self.obj.name != self.ui.nameLineEdit.text():
            return True
        if self.obj.description != \
                self.ui.descriptionPlainTextEdit.toPlainText():
            return True
        if self.ui.typeOfSimulationComboBox.currentText() == "REC":
            if self.obj.simulation_type != "ERD":
                return True
        else:
            if self.obj.simulation_type != "RBS":
                return True
        if self.obj.simulation_mode != self.ui.modeComboBox.currentText().\
           lower():
            return True
        if self.obj.number_of_ions != self.ui.numberOfIonsSpinBox.value():
            return True
        if self.obj.number_of_preions != self.ui.numberOfPreIonsSpinBox.value():
            return True
        if self.obj.number_of_recoils != self.ui.numberOfRecoilsSpinBox.value():
            return True
        if self.obj.number_of_scaling_ions != \
                self.ui.numberOfScalingIonsSpinBox.value():
            return True
        if self.obj.minimum_scattering_angle != \
            self.ui.minimumScatterAngleDoubleSpinBox.value():
            return True
        if self.obj.minimum_main_scattering_angle != \
            self.ui.minimumMainScatterAngleDoubleSpinBox.value():
            return True
        if self.obj.minimum_energy != \
                self.ui.minimumEnergyDoubleSpinBox.value():
            return True
        return False
