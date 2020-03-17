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

import widgets.input_validation as iv
import widgets.gui_utils as gutils

from modules.element_simulation import ElementSimulation

from PyQt5 import QtWidgets
from PyQt5 import uic
from PyQt5.QtCore import QLocale
from PyQt5.QtCore import Qt

_TYPE_CONVERSION = {
    # 'RBS' and 'ERD' are the values stored internally in ElementSimulation,
    # while 'SCT' and 'REC' are shown in the dialog.
    "RBS": "SCT",
    "ERD": "REC",
    "SCT": "RBS",
    "REC": "ERD"
}


def _simulation_mode_from_combobox(combobox):
    return combobox.currentText().lower()


def _simulation_type_to_combobox(combobox, value):
    converted_type = _TYPE_CONVERSION[value]
    combobox.setCurrentIndex(combobox.findText(converted_type,
                                               Qt.MatchFixedString))


def _simulation_type_from_combobox(combobox):
    value = combobox.currentText()
    return _TYPE_CONVERSION[value]


class SimulationSettingsWidget(QtWidgets.QWidget,
                               gutils.BindingPropertyWidget,
                               metaclass=gutils.QtABCMeta):
    """Class for creating a simulation settings tab.
    """
    name = gutils.bind("nameLineEdit")
    description = gutils.bind("descriptionPlainTextEdit")
    simulation_type = gutils.bind("typeOfSimulationComboBox",
                                  fget=_simulation_type_from_combobox,
                                  fset=_simulation_type_to_combobox)
    simulation_mode = gutils.bind("modeComboBox",
                                  fget=_simulation_mode_from_combobox)
    number_of_ions = gutils.bind("numberOfIonsSpinBox")
    number_of_ions_in_presimu = gutils.bind("numberOfPreIonsSpinBox")
    number_of_scaling_ions = gutils.bind("numberOfScalingIonsSpinBox")
    number_of_recoils = gutils.bind("numberOfRecoilsSpinBox")
    minimum_scattering_angle = gutils.bind("minimumScatterAngleDoubleSpinBox")
    minimum_main_scattering_angle = gutils.bind(
        "minimumMainScatterAngleDoubleSpinBox")
    minimum_energy_of_ions = gutils.bind("minimumEnergyDoubleSpinBox")
    seed = gutils.bind("seedSpinBox")
    date = gutils.bind(
        "dateLabel",
        fset=lambda qobj, t: qobj.setText(time.strftime("%c %z %Z",
                                                        time.localtime(t))))

    def __init__(self, element_simulation: ElementSimulation):
        """
        Initializes the widget.

        Args:
            element_simulation: Element simulation object.
        """
        super().__init__()
        uic.loadUi(os.path.join("ui_files",
                                "ui_request_simulation_settings.ui"),
                   self)
        # By default, disable the widget, so caller has to enable it. Without
        # this, name and description fields would always be enabled when the
        # widget loads.
        self.setEnabled(False)
        self.element_simulation = element_simulation

        iv.set_input_field_red(self.nameLineEdit)
        self.fields_are_valid = False
        self.nameLineEdit.textChanged.connect(lambda: self.__check_text(
            self.nameLineEdit, self))

        self.nameLineEdit.textEdited.connect(lambda: self.__validate())

        locale = QLocale.c()
        self.minimumScatterAngleDoubleSpinBox.setLocale(locale)
        self.minimumMainScatterAngleDoubleSpinBox.setLocale(locale)
        self.minimumEnergyDoubleSpinBox.setLocale(locale)

        self.set_properties(
            name=self.element_simulation.name,
            description=self.element_simulation.description,
            date=self.element_simulation.modification_time,
            **self.element_simulation.get_simulation_settings())

    def show_settings(self):
        """
        Show simualtion settings.
        """
        self.nameLineEdit.setText(self.element_simulation.name)
        self.dateLabel.setText(time.strftime("%c %z %Z", time.localtime(
            self.element_simulation.modification_time)))
        self.descriptionPlainTextEdit.setPlainText(
            self.element_simulation.description)
        self.modeComboBox.setCurrentIndex(self.modeComboBox.findText(
            self.element_simulation.simulation_mode, Qt.MatchFixedString))
        if self.element_simulation.simulation_type == "ERD":
            self.typeOfSimulationComboBox.setCurrentIndex(
                self.typeOfSimulationComboBox.findText(
                    "REC", Qt.MatchFixedString))
        else:
            self.typeOfSimulationComboBox.setCurrentIndex(
                self.typeOfSimulationComboBox.findText("SCT",
                                                         Qt.MatchFixedString))
        self.minimumScatterAngleDoubleSpinBox.setValue(
            self.element_simulation.minimum_scattering_angle)
        self.minimumMainScatterAngleDoubleSpinBox.setValue(
            self.element_simulation.minimum_main_scattering_angle)
        self.minimumEnergyDoubleSpinBox.setValue(
            self.element_simulation.minimum_energy)
        self.numberOfIonsSpinBox.setValue(
            self.element_simulation.number_of_ions)
        self.numberOfPreIonsSpinBox.setValue(
            self.element_simulation.number_of_preions)
        self.seedSpinBox.setValue(self.element_simulation.seed_number)
        self.numberOfRecoilsSpinBox.setValue(
            self.element_simulation.number_of_recoils)
        self.numberOfScalingIonsSpinBox.setValue(
            self.element_simulation.number_of_scaling_ions)

    def setEnabled(self, b):
        """Either enables or disables widgets input fields.
        """
        super().setEnabled(b)
        try:
            # setEnabled is called when ui file is being loaded and these
            # attributes do not yet exist, so we have to catch the exception.
            self.formLayout.setEnabled(b)
            self.generalParametersGroupBox.setEnabled(b)
            self.physicalParametersGroupBox.setEnabled(b)
        except AttributeError:
            pass

    @staticmethod
    def __check_text(input_field, settings):
        """Checks if there is text in given input field.

        Args:
            input_field: Input field the contents of which are checked.
            settings: Settings widget.
        """
        settings.fields_are_valid = iv.check_text(input_field)

    def __validate(self):
        """
        Validate the mcsimu settings file name.
        """
        text = self.nameLineEdit.text()
        regex = "^[A-Za-z0-9-ÖöÄäÅå]*"
        valid_text = iv.validate_text_input(text, regex)

        self.nameLineEdit.setText(valid_text)

    def update_settings(self):
        """
        Update simulation settings.
        """
        self.element_simulation.name = self.nameLineEdit.text()
        self.element_simulation.description = \
            self.descriptionPlainTextEdit.toPlainText()
        if self.typeOfSimulationComboBox.currentText() == "REC":
            if self.element_simulation.simulation_type != "ERD":
                self.element_simulation.simulation_type = "ERD"
                for recoil in self.element_simulation.recoil_elements:
                    recoil.type = "rec"
                    try:
                        path_to_rec = os.path.join(
                            self.element_simulation.directory,
                            recoil.get_full_name() + ".sct")
                        os.remove(path_to_rec)
                    except OSError:
                        pass
                    recoil.to_file(self.element_simulation.directory)
        else:
            if self.element_simulation.simulation_type != "RBS":
                self.element_simulation.simulation_type = "RBS"
                for recoil in self.element_simulation.recoil_elements:
                    recoil.type = "sct"
                    try:
                        path_to_rec = os.path.join(
                            self.element_simulation.directory,
                            recoil.get_full_name() + ".rec")
                        os.remove(path_to_rec)
                    except OSError:
                        pass
                    recoil.to_file(self.element_simulation.directory)

        self.element_simulation.simulation_mode = \
            self.modeComboBox.currentText().lower()
        self.element_simulation.number_of_ions = \
            self.numberOfIonsSpinBox.value()
        self.element_simulation.number_of_preions = \
            self.numberOfPreIonsSpinBox.value()
        self.element_simulation.seed_number = \
            self.seedSpinBox.value()
        self.element_simulation.number_of_recoils = \
            self.numberOfRecoilsSpinBox.value()
        self.element_simulation.number_of_scaling_ions = \
            self.numberOfScalingIonsSpinBox. \
            value()
        self.element_simulation.minimum_scattering_angle = \
            self.minimumScatterAngleDoubleSpinBox.value()
        self.element_simulation.minimum_main_scattering_angle = \
            self.minimumMainScatterAngleDoubleSpinBox.value()
        self.element_simulation.minimum_energy = \
            self.minimumEnergyDoubleSpinBox.value()

    def values_changed(self):
        """
        Check if simulation settings have been changed. Seed number change is
        not registered as value change.

        Return:
            True or False.
        """
        if self.element_simulation.name != self.nameLineEdit.text():
            return True
        if self.element_simulation.description != \
                self.descriptionPlainTextEdit.toPlainText():
            return True
        if self.typeOfSimulationComboBox.currentText() == "REC":
            if self.element_simulation.simulation_type != "ERD":
                return True
        else:
            if self.element_simulation.simulation_type != "RBS":
                return True
        if self.element_simulation.simulation_mode != \
                self.modeComboBox.currentText().lower():
            return True
        if self.element_simulation.number_of_ions != \
                self.numberOfIonsSpinBox.value():
            return True
        if self.element_simulation.number_of_preions != \
                self.numberOfPreIonsSpinBox.value():
            return True
        if self.element_simulation.number_of_recoils != \
                self.numberOfRecoilsSpinBox.value():
            return True
        if self.element_simulation.number_of_scaling_ions != \
                self.numberOfScalingIonsSpinBox.value():
            return True
        if self.element_simulation.minimum_scattering_angle != \
            self.minimumScatterAngleDoubleSpinBox.value():
            return True
        if self.element_simulation.minimum_main_scattering_angle != \
            self.minimumMainScatterAngleDoubleSpinBox.value():
            return True
        if self.element_simulation.minimum_energy != \
                self.minimumEnergyDoubleSpinBox.value():
            return True
        return False
