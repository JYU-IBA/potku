# coding=utf-8
"""
Created on 4.4.2018
Updated on 20.8.2018

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
import time

from modules.general_functions import check_text
from modules.general_functions import delete_simulation_results
from modules.general_functions import set_input_field_red
from modules.general_functions import validate_text_input

from PyQt5 import uic
from PyQt5 import QtWidgets
from PyQt5.QtCore import QLocale
from PyQt5.QtCore import Qt


class ElementSimulationSettingsDialog(QtWidgets.QDialog):
    """Class for creating an element simulation settings tab.
    """
    def __init__(self, element_simulation, tab):
        """
        Initializes the dialog.

        Args:
            element_simulation: An ElementSimulation object.
            tab: A SimulationTabWidget.
        """
        super().__init__()
        self.ui = uic.loadUi(os.path.join("ui_files",
                                          "ui_element_simulation_settings.ui"),
                             self)

        self.ui.okPushButton.clicked.connect(self.update_settings_and_close)
        self.ui.applyPushButton.clicked.connect(self.update_settings)
        self.ui.cancelPushButton.clicked.connect(self.close)

        self.element_simulation = element_simulation
        self.tab = tab

        self.use_default_settings = element_simulation.use_default_settings

        self.ui.useRequestSettingsValuesCheckBox.stateChanged.connect(
            self.toggle_settings)

        self.set_spinbox_maximums()

        set_input_field_red(self.ui.nameLineEdit)
        self.fields_are_valid = False
        self.ui.nameLineEdit.textChanged.connect(lambda: self.__check_text(
            self.ui.nameLineEdit, self))
        self.original_use_default_settings = \
            self.ui.useRequestSettingsValuesCheckBox.isChecked()
        self.original_simulation_type = self.element_simulation.simulation_type

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
            self.original_use_default_settings = False
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
        else:
            self.ui.settingsGroupBox.setEnabled(True)

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
        if self.ui.useRequestSettingsValuesCheckBox.isChecked():
            self.use_default_settings = True
            self.element_simulation.use_default_settings = True
        else:
            self.use_default_settings = False
            self.element_simulation.use_default_settings = False

        if not self.fields_are_valid and not self.use_default_settings:
            QtWidgets.QMessageBox.critical(self, "Warning",
                                           "Some of the setting values have"
                                           " not been set.\n" +
                                           "Please input values in fields "
                                           "indicated in red.",
                                           QtWidgets.QMessageBox.Ok,
                                           QtWidgets.QMessageBox.Ok)
            self.__close = False
            return

        # If default settings have been used before opening the dialog
        if self.original_use_default_settings and self.use_default_settings:
            self.__close = True
            return

        only_seed_changed = False
        # If element simulation settings are used and they have not been changed
        if not self.use_default_settings and not self.values_changed():
            if self.ui.seedSpinBox.value() != \
                    self.element_simulation.seed_number:
                only_seed_changed = True
            else:
                self.__close = True
                return

        simulation_run = self.element_simulation.simulations_done
        simulation_running = self.simulation_running()

        if self.original_use_default_settings:
            settings = "request"
        else:
            settings = "element simulation"

        if simulation_run and not only_seed_changed:
            reply = QtWidgets.QMessageBox.question(
                self, "Simulated simulation",
                "This is a simulation that uses " + settings +
                " settings, and has been simulated.\nIf you save changes,"
                " the result files of the simulated simulation are "
                "deleted.\n\nDo you want to save changes anyway?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No |
                QtWidgets.QMessageBox.Cancel, QtWidgets.QMessageBox.Cancel)
            if reply == QtWidgets.QMessageBox.No or reply == \
                    QtWidgets.QMessageBox.Cancel:
                self.__close = False
                return
            else:
                for recoil in self.element_simulation.recoil_elements:
                    # Delete files
                    delete_simulation_results(self.element_simulation, recoil)

                    # Delete energy spectra that use recoil
                    for energy_spectra in self.tab.energy_spectrum_widgets:
                        for element_path in energy_spectra.\
                          energy_spectrum_data.keys():
                            elem = recoil.prefix + "-" + recoil.name
                            if elem in element_path:
                                index = element_path.find(elem)
                                if element_path[index - 1] == os.path.sep and \
                                   element_path[index + len(elem)] == '.':
                                    self.tab.del_widget(energy_spectra)
                                    self.tab.energy_spectrum_widgets.remove(
                                        energy_spectra)
                                    save_file_path = os.path.join(
                                        self.tab.simulation.directory,
                                        energy_spectra.save_file)
                                    if os.path.exists(save_file_path):
                                        os.remove(save_file_path)
                                    break
                # Reset controls
                if self.element_simulation.controls:
                    self.element_simulation.controls.reset_controls()
                # Change full edit unlocked
                self.element_simulation.recoil_elements[0].widgets[0].\
                    parent.edit_lock_push_button.setText(
                    "Full edit unlocked")
                self.element_simulation.simulations_done = False

        elif simulation_running and not only_seed_changed:
            reply = QtWidgets.QMessageBox.question(
                self, "Simulation running",
                "This simulation is running and uses " + settings +
                " settings.\nIf you save changes, the running "
                "simulation will be stopped, and its result files "
                "deleted.\n\nDo you want to save changes anyway?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No |
                QtWidgets.QMessageBox.Cancel, QtWidgets.QMessageBox.Cancel)
            if reply == QtWidgets.QMessageBox.No or reply == \
                    QtWidgets.QMessageBox.Cancel:
                self.__close = False
                return
            else:
                # Stop simulation
                self.element_simulation.stop()
                self.element_simulation.controls.state_label.setText("Stopped")
                self.element_simulation.controls.run_button.setEnabled(True)
                self.element_simulation.controls.stop_button.setEnabled(False)
                # Delete files
                for recoil in self.element_simulation.recoil_elements:
                    # Delete files
                    delete_simulation_results(self.element_simulation, recoil)

                    # Delete energy spectra that use recoil
                    for energy_spectra in self.tab.energy_spectrum_widgets:
                        for element_path in energy_spectra. \
                                energy_spectrum_data.keys():
                            elem = recoil.prefix + "-" + recoil.name
                            if elem in element_path:
                                index = element_path.find(elem)
                                if element_path[index - 1] == os.path.sep and \
                                        element_path[index + len(elem)] == '.':
                                    self.tab.del_widget(energy_spectra)
                                    self.tab.energy_spectrum_widgets.remove(
                                        energy_spectra)
                                    save_file_path = os.path.join(
                                        self.tab.simulation.directory,
                                        energy_spectra.save_file)
                                    if os.path.exists(save_file_path):
                                        os.remove(save_file_path)
                                    break

                # Reset controls
                if self.element_simulation.controls:
                    self.element_simulation.controls.reset_controls()
                # Change full edit unlocked
                self.element_simulation.recoil_elements[0].widgets[0].\
                    parent.edit_lock_push_button.setText(
                    "Full edit unlocked")
                self.element_simulation.simulations_done = False

        if only_seed_changed:
            # If there are running simulation that use the same seed as the
            # new one, stop them
            seed = self.ui.seedSpinBox.value()
            running_simulation = self.running_simulation_by_seed(seed)
            if running_simulation:
                reply = QtWidgets.QMessageBox.question(
                    self, "Running simulations",
                    "There is a simulation process that has the same seed "
                    "number as the new one.\nIf you save changes, this "
                    "simulation process will be stopped (but its results will "
                    "not be deleted).\n\nDo you want save changes anyway?",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No |
                    QtWidgets.QMessageBox.Cancel,
                    QtWidgets.QMessageBox.Cancel)
                if reply == QtWidgets.QMessageBox.No or reply == \
                        QtWidgets.QMessageBox.Cancel:
                    self.__close = False
                    return
                else:
                    # Stop the running simulation's mcerd process
                    # that corresponds to seed
                    running_simulation.mcerd_objects[seed].stop_process()
                    del (running_simulation.mcerd_objects[seed])

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
                             self.element_simulation.request.
                             default_element_simulation.name + ".mcsimu"))

        # Update recoil type
        if self.original_simulation_type != \
                self.element_simulation.simulation_type:
            for recoil in self.element_simulation.recoil_elements:
                if self.element_simulation.simulation_type == "ERD":
                    recoil.type = "rec"
                    try:
                        path_to_rec = os.path.join(
                            self.element_simulation.directory,
                            recoil.prefix + "-" + recoil.name + ".sct")
                        os.remove(path_to_rec)
                    except OSError:
                        pass

                else:
                    recoil.type = "sct"
                    try:
                        path_to_sct = os.path.join(
                            self.element_simulation.directory,
                            recoil.prefix + "-" + recoil.name + ".rec")
                        os.remove(path_to_sct)
                    except OSError:
                        pass
                self.element_simulation.recoil_to_file(
                    self.element_simulation.directory, recoil)

        self.__close = True

    def values_changed(self):
        """
        Check if simulation settings have been changed. Seed number change is
        not registered as value change.

        Return:
            True or False.
        """
        if self.element_simulation.name != self.ui.nameLineEdit.text():
            return True
        if self.element_simulation.description != \
           self.ui.descriptionPlainTextEdit.toPlainText():
            return True
        if self.element_simulation.simulation_mode != \
           self.ui.modeComboBox.currentText():
            return True
        if self.ui.typeOfSimulationComboBox.currentText() == "REC":
            if self.element_simulation.simulation_type != "ERD":
                return True
        else:
            if self.element_simulation.simulation_type != "RBS":
                return True
        if self.element_simulation.number_of_ions != \
           self.ui.numberOfIonsSpinBox.value():
            return True
        if self.element_simulation.number_of_preions != \
           self.ui.numberOfPreIonsSpinBox.value():
            return True
        if self.element_simulation.number_of_recoils != \
           self.ui.numberOfRecoilsSpinBox.value():
            return True
        if self.element_simulation.number_of_scaling_ions != \
           self.ui.numberOfScalingIonsSpinBox.value():
            return True
        if self.element_simulation.minimum_scattering_angle != \
           self.ui.minimumScatterAngleDoubleSpinBox.value():
            return True
        if self.element_simulation.minimum_main_scattering_angle != \
           self.ui.minimumMainScatterAngleDoubleSpinBox.value():
            return True
        if self.element_simulation.minimum_energy != \
           self.ui.minimumEnergyDoubleSpinBox.value():
            return True
        return False

    def simulation_running(self):
        """
        Check if element simulation is running.

        Return:
            True or False.
        """
        if self.element_simulation in \
                self.element_simulation.simulation.request.running_simulations:
            return True
        elif self.element_simulation in \
                self.element_simulation.simulation.running_simulations:
            return True
        return False

    def running_simulation_by_seed(self, seed):
        """
        Check if element simulation has man mcerd process with the given seed.

        Args:
            seed: Seed number.

        Return:
            Current element simulation.
        """
        if seed in self.element_simulation.mcerd_objects.keys():
            return self.element_simulation
        return None
