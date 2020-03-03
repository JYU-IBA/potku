# coding=utf-8
"""
Created on 4.5.2018
Updated on 24.5.2019

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
__version__ = "2.0"

import json
import os
import shutil
import time
import copy

import dialogs.dialog_functions as df

from modules.general_functions import delete_simulation_results
from modules.run import Run

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5 import uic

from widgets.detector_settings import DetectorSettingsWidget
from widgets.measurement.settings import MeasurementSettingsWidget


class SimulationSettingsDialog(QtWidgets.QDialog):
    """
    Dialog class for handling the simulation parameter input.
    """

    def __init__(self, tab, simulation, icon_manager):
        """
        Initializes the dialog.

        Args:
            tab: A SimulationTabWidget.
            simulation: A Simulation object whose parameters are handled.
            icon_manager: An icon manager.
        """
        super().__init__()
        self.tab = tab
        self.simulation = simulation
        self.icon_manager = icon_manager
        self.ui = uic.loadUi(os.path.join("ui_files",
                                          "ui_specific_settings.ui"), self)
        self.ui.setWindowTitle("Simulation Settings")
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        screen_geometry = QtWidgets.QDesktopWidget.availableGeometry(
            QtWidgets.QApplication.desktop())
        self.resize(self.geometry().width() * 1.1,
                    screen_geometry.size().height() * 0.8)
        self.ui.defaultSettingsCheckBox.stateChanged.connect(
            self.__change_used_settings)
        self.ui.OKButton.clicked.connect(self.__save_settings_and_close)
        self.ui.applyButton.clicked.connect(self.__update_parameters)
        self.ui.cancelButton.clicked.connect(self.close)

        # Add measurement settings view to the settings view
        self.measurement_settings_widget = MeasurementSettingsWidget(
            self.simulation)
        self.ui.tabs.addTab(self.measurement_settings_widget, "Measurement")

        self.measurement_settings_widget.ui.picture.setScaledContents(True)
        pixmap = QtGui.QPixmap(os.path.join("images",
                                            "measurement_setup_angles.png"))
        self.measurement_settings_widget.ui.picture.setPixmap(pixmap)

        self.measurement_settings_widget.ui.beamIonButton.clicked.connect(
            lambda: df.change_element(
                self,
                self.measurement_settings_widget.ui.beamIonButton,
                self.measurement_settings_widget.ui.isotopeComboBox))

        # Add detector settings view to the settings view
        detector_object = self.simulation.detector
        if not detector_object:
            detector_object = self.simulation.request.default_detector
        self.detector_settings_widget = DetectorSettingsWidget(
            detector_object, self.simulation.request, self.icon_manager)

        # 2 is calibration tab that is not needed
        calib_tab_widget = self.detector_settings_widget.ui.tabs.widget(2)
        self.detector_settings_widget.ui.tabs.removeTab(2)
        calib_tab_widget.deleteLater()

        self.ui.tabs.addTab(self.detector_settings_widget, "Detector")

        if self.simulation.detector is not None:
            self.ui.defaultSettingsCheckBox.setCheckState(0)
            self.measurement_settings_widget.ui.nameLineEdit.setText(
                self.simulation.measurement_setting_file_name)
            self.measurement_settings_widget.ui.descriptionPlainTextEdit \
                .setPlainText(
                    self.simulation.measurement_setting_file_description)
            self.measurement_settings_widget.dateLabel.setText(time.strftime(
                "%c %z %Z", time.localtime(self.simulation.modification_time)))

        self.ui.tabs.currentChanged.connect(lambda: self.__check_for_red())
        self.__close = True

        self.use_default_settings = self.ui.defaultSettingsCheckBox.isChecked()

        self.exec()

    def __change_used_settings(self):
        """Set specific settings enabled or disabled based on the "Use
        request settings" checkbox.
        """
        check_box = self.sender()
        if check_box.isChecked():
            self.ui.tabs.setEnabled(False)
        else:
            self.ui.tabs.setEnabled(True)

    def __check_for_red(self):
        """
        Check whether there are any invalid field in the tabs.
        """
        df.check_for_red(self)

    def enabled_element_information(self):
        """
        Change the UI accordingly when an element is selected.
        """
        self.measurement_settings_widget.ui.isotopeComboBox.setEnabled(True)
        self.measurement_settings_widget.ui.isotopeLabel.setEnabled(True)
        self.ui.OKButton.setEnabled(True)

    def __update_parameters(self):
        """
         Update Simulation's Run, Detector and Target objects. If simulation
         specific parameters are in use, save them into a file.
        """
        if self.measurement_settings_widget.ui.isotopeComboBox.currentIndex()\
                == -1:
            QtWidgets.QMessageBox.critical(self, "Warning",
                                           "No isotope selected.\n\nPlease "
                                           "select an isotope for the beam "
                                           "element.",
                                           QtWidgets.QMessageBox.Ok,
                                           QtWidgets.QMessageBox.Ok)
            self.__close = False
            return

        if not self.simulation.measurement_setting_file_name:
            self.simulation.measurement_setting_file_name = \
                self.simulation.name

        if not self.ui.tabs.currentWidget().fields_are_valid:
            QtWidgets.QMessageBox.critical(self, "Warning",
                                           "Some of the setting values have"
                                           " not been set.\n" +
                                           "Please input values in fields "
                                           "indicated in red.",
                                           QtWidgets.QMessageBox.Ok,
                                           QtWidgets.QMessageBox.Ok)
            self.__close = False
            return

        check_box = self.ui.defaultSettingsCheckBox
        if check_box.isChecked() and not self.use_default_settings:
            if not df.delete_element_simulations(
                    self, self.tab, self.simulation,
                    msg_str="simulation settings"):
                return

            # Use request settings
            self.simulation.run = None
            self.simulation.detector = None
            self.simulation.measurement_setting_file_description = ""
            self.simulation.target.target_theta = \
                self.simulation.request.default_target.target_theta

            # Remove setting files and folders
            det_folder_path = os.path.join(self.simulation.directory,
                                           "Detector")
            if os.path.exists(det_folder_path):
                shutil.rmtree(det_folder_path)
            filename_to_remove = ""
            for file in os.listdir(self.simulation.directory):
                if file.endswith(".measurement"):
                    filename_to_remove = file
                    break
            if filename_to_remove:
                os.remove(os.path.join(self.simulation.directory,
                                       filename_to_remove))
            self.use_default_settings = True
        else:
            if self.use_default_settings and check_box.isChecked():
                self.__close = True
                return
            only_unnotified_changed = False
            if not self.use_default_settings and not check_box.isChecked():
                # Check that values have been changed
                if not self.values_changed():
                    # Check if only those values that don't require rerunning
                    #  the simulations have been changed
                    if self.measurement_settings_widget.other_values_changed():
                        only_unnotified_changed = True
                    if self.detector_settings_widget.other_values_changed():
                        only_unnotified_changed = True
                    if not only_unnotified_changed:
                        self.__close = True
                        return
            if self.use_default_settings:
                settings = "request settings"
            else:
                settings = "simulation settings"

            if not df.delete_element_simulations(
                    self, self.tab, self.simulation,
                    msg_str=settings):
                return

            # Use simulation specific settings
            try:
                measurement_settings_file_path = os.path.join(
                    self.simulation.directory,
                    self.simulation.measurement_setting_file_name
                    + ".measurement")
                target_file_path = os.path.join(self.simulation.directory,
                                                self.simulation.target.name
                                                + ".target")
                det_folder_path = os.path.join(self.simulation.directory,
                                               "Detector")

                if self.simulation.run is None:
                    # Create a default Run for simulation
                    self.simulation.run = Run()
                if self.simulation.detector is None:
                    df.update_detector_settings(
                        self.simulation,
                        det_folder_path,
                        measurement_settings_file_path)

                # Set Detector object to settings widget
                self.detector_settings_widget.obj = self.simulation. \
                    detector

                # Update settings
                self.measurement_settings_widget.update_settings()
                self.detector_settings_widget.update_settings()
                self.simulation.detector.path = \
                    os.path.join(det_folder_path,
                                 self.simulation.detector.name +
                                 ".detector")

                df.update_efficiency_files(self.simulation.detector)

                # Save measurement settings parameters.
                new_measurement_settings_file_path = os.path.join(
                    self.simulation.directory,
                    self.simulation.measurement_setting_file_name +
                    ".measurement")
                general_obj = {
                    "name": self.simulation.measurement_setting_file_name,
                    "description":
                        self.simulation.
                            measurement_setting_file_description,
                    "modification_time":
                        time.strftime("%c %z %Z", time.localtime(
                            time.time())),
                    "modification_time_unix": time.time()
                }

                if os.path.exists(new_measurement_settings_file_path):
                    obj = json.load(open(
                        new_measurement_settings_file_path))
                    obj["general"] = general_obj
                else:
                    obj = {
                        "general": general_obj
                    }

                # Delete possible extra .measurement files
                filename_to_remove = ""
                for file in os.listdir(self.simulation.directory):
                    if file.endswith(".measurement"):
                        filename_to_remove = file
                        break
                if filename_to_remove:
                    os.remove(os.path.join(self.simulation.directory,
                                           filename_to_remove))

                # Write measurement settings to file
                with open(new_measurement_settings_file_path, "w") as file:
                    json.dump(obj, file, indent=4)

                # Save Run object to file
                self.simulation.run.to_file(
                    new_measurement_settings_file_path)
                # Save Detector object to file
                self.simulation.detector.to_file(
                    self.simulation.detector.path,
                    new_measurement_settings_file_path)

                # Save Target object to file
                self.simulation.target.to_file(
                    target_file_path, new_measurement_settings_file_path)

            except TypeError:
                QtWidgets.QMessageBox.question(self, "Warning",
                                               "Some of the setting values "
                                               "have not been set.\n" +
                                               "Please input setting values"
                                               " to save them.",
                                               QtWidgets.QMessageBox.Ok,
                                               QtWidgets.QMessageBox.Ok)
            self.use_default_settings = False

    def __save_settings_and_close(self):
        """Save settings and close the dialog.
        """
        self.__update_parameters()
        if self.__close:
            self.close()

    def values_changed(self):
        """
        Check if measurement or detector settings have
        changed.

        Return:

            True or False.
        """
        if self.measurement_settings_widget.values_changed():
            return True
        if self.detector_settings_widget.values_changed():
            return True
        return False
