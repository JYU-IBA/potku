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
import widgets.binding as bnd

from modules.element_simulation import ElementSimulation

from widgets.binding import PropertyTrackingWidget
from widgets.gui_utils import QtABCMeta

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


def _simulation_mode_from_combobox(instance, combobox):
    qbox = getattr(instance, combobox)
    return qbox.currentText().lower()


def _simulation_type_to_combobox(instance, combobox, value):
    qbox = getattr(instance, combobox)
    converted_type = _TYPE_CONVERSION[value]
    qbox.setCurrentIndex(qbox.findText(converted_type, Qt.MatchFixedString))


def _simulation_type_from_combobox(instance, combobox):
    qbox = getattr(instance, combobox)
    value = qbox.currentText()
    return _TYPE_CONVERSION[value]


class SimulationSettingsWidget(QtWidgets.QWidget,
                               PropertyTrackingWidget,
                               metaclass=QtABCMeta):
    """Class for creating a simulation settings tab.
    """
    # TODO name, desc, number_of_ions and number_of_ions_in_presimu should
    #   perhaps not be tracked
    name = bnd.bind("nameLineEdit", track_change=True)
    description = bnd.bind("descriptionPlainTextEdit", track_change=True)
    simulation_type = bnd.bind("typeOfSimulationComboBox",
                               fget=_simulation_type_from_combobox,
                               fset=_simulation_type_to_combobox,
                               track_change=True)
    simulation_mode = bnd.bind("modeComboBox",
                               fget=_simulation_mode_from_combobox,
                               track_change=True)
    number_of_ions = bnd.bind("numberOfIonsSpinBox", track_change=True)
    number_of_ions_in_presimu = bnd.bind("numberOfPreIonsSpinBox",
                                         track_change=True)
    number_of_scaling_ions = bnd.bind("numberOfScalingIonsSpinBox",
                                      track_change=True)
    number_of_recoils = bnd.bind("numberOfRecoilsSpinBox",
                                 track_change=True)
    minimum_scattering_angle = bnd.bind("minimumScatterAngleDoubleSpinBox",
                                        track_change=True)
    minimum_main_scattering_angle = bnd.bind(
        "minimumMainScatterAngleDoubleSpinBox", track_change=True)
    minimum_energy_of_ions = bnd.bind("minimumEnergyDoubleSpinBox",
                                      track_change=True)

    # Seed and date are not tracked for changes
    seed_number = bnd.bind("seedSpinBox")
    date = bnd.bind(
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
        self.set_spinbox_maximums()

        iv.set_input_field_red(self.nameLineEdit)
        self.fields_are_valid = False
        self.nameLineEdit.textChanged.connect(lambda: self.__check_text(
            self.nameLineEdit, self))
        self.nameLineEdit.textEdited.connect(lambda: self.__validate())

        locale = QLocale.c()
        self.minimumScatterAngleDoubleSpinBox.setLocale(locale)
        self.minimumMainScatterAngleDoubleSpinBox.setLocale(locale)
        self.minimumEnergyDoubleSpinBox.setLocale(locale)

        self.__original_property_values = {}

        self.set_properties(
            name=self.element_simulation.name,
            description=self.element_simulation.description,
            date=self.element_simulation.modification_time,
            **self.element_simulation.get_simulation_settings())

    def get_original_property_values(self):
        """Returns a dictionary of original property values.
        """
        return self.__original_property_values

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

    def set_spinbox_maximums(self, int_max=2147483647,
                             float_max=1000000000000000013287555072.00):
        """Set maximum values to spinbox components.
        """
        self.numberOfIonsSpinBox.setMaximum(int_max)
        self.numberOfPreIonsSpinBox.setMaximum(int_max)
        self.seedSpinBox.setMaximum(int_max)
        self.numberOfRecoilsSpinBox.setMaximum(int_max)
        self.numberOfScalingIonsSpinBox.setMaximum(int_max)
        self.minimumScatterAngleDoubleSpinBox.setMaximum(float_max)
        self.minimumMainScatterAngleDoubleSpinBox.setMaximum(float_max)
        self.minimumEnergyDoubleSpinBox.setMaximum(float_max)

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
        params = self.get_properties()
        self.element_simulation.name = params.pop("name")
        self.element_simulation.description = params.pop("description")
        params.pop("date")

        if self.simulation_type != self.element_simulation.simulation_type:
            if self.simulation_type == "ERD":
                new_type = "rec"
                old_type = ".sct"
            else:
                new_type = "sct"
                old_type = ".rec"
            for recoil in self.element_simulation.recoil_elements:
                recoil.type = new_type
                try:
                    path_to_rec = os.path.join(
                        self.element_simulation.directory,
                        recoil.get_full_name() + old_type)
                    os.remove(path_to_rec)
                except OSError:
                    pass
                recoil.to_file(self.element_simulation.directory)

        self.element_simulation.set_simulation_settings(**params)
