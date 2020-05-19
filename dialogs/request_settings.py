# coding=utf-8
"""
Created on 19.3.2013
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

Dialog for the request settings
"""
__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen " \
             "\n Samuli Rahkonen \n Miika Raunio \n Severi Jääskeläinen \n " \
             "Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen \n " \
             "Juhani Sundell"
__version__ = "2.0"

import os

import dialogs.dialog_functions as df

from modules.request import Request

from pathlib import Path

from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5 import uic
from PyQt5.QtWidgets import QDesktopWidget
from PyQt5.QtWidgets import QApplication

from widgets.detector_settings import DetectorSettingsWidget
from widgets.measurement.settings import MeasurementSettingsWidget
from widgets.profile_settings import ProfileSettingsWidget
from widgets.simulation.settings import SimulationSettingsWidget


class RequestSettingsDialog(QtWidgets.QDialog):
    """
    A Dialog for modifying request settings.
    """

    settings_updated = QtCore.pyqtSignal()

    def __init__(self, main_window, request: Request, icon_manager):
        """Constructor for the program

        Args:
            main_window: Potku window.
            request: Request class object.
            icon_manager: IconManager object.
        """
        super().__init__()
        uic.loadUi(Path("ui_files", "ui_settings.ui"), self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        screen_geometry = \
            QDesktopWidget.availableGeometry(QApplication.desktop())
        self.resize(self.geometry().width() * 1.2,
                    screen_geometry.size().height() * 0.8)

        self.main_window = main_window
        self.request = request
        self.icon_manager = icon_manager

        # Connect buttons.
        self.OKButton.clicked.connect(self.update_and_close_settings)
        self.applyButton.clicked.connect(self.__update_settings)
        self.cancelButton.clicked.connect(self.close)

        # Add measurement settings view to the settings view
        self.measurement_settings_widget = MeasurementSettingsWidget(
            self.request.default_measurement)
        self.tabs.addTab(self.measurement_settings_widget, "Measurement")

        # Connect the enabling of the OKButton to a signal that indicates
        # whether beam selection is ok
        self.measurement_settings_widget.beam_selection_ok.connect(
            self.OKButton.setEnabled)

        # Add detector settings view to the settings view
        self.detector_settings_widget = DetectorSettingsWidget(
            self.request.default_detector, self.request, self.icon_manager,
            run=self.measurement_settings_widget.tmp_run)

        self.tabs.addTab(self.detector_settings_widget, "Detector")

        # Add simulation settings view to the settings view
        self.simulation_settings_widget = SimulationSettingsWidget(
            self.request.default_element_simulation)
        self.tabs.addTab(self.simulation_settings_widget, "Simulation")

        self.simulation_settings_widget.setEnabled(True)

        # Add profile settings view to the settings view
        self.profile_settings_widget = ProfileSettingsWidget(
            self.request.default_measurement)
        self.tabs.addTab(self.profile_settings_widget, "Profile")

        self.tabs.currentChanged.connect(self.__check_for_red)

        self.original_simulation_type = \
            self.request.default_element_simulation.simulation_type

    def closeEvent(self, event):
        try:
            self.settings_updated.disconnect()
        except AttributeError:
            pass
        super().closeEvent(event)

    def __check_for_red(self):
        """
        Check whether there are any invalid field in the tabs.
        """
        df.check_for_red(self)
        # Save run and beam parameters to tmp_run
        self.measurement_settings_widget.save_to_tmp_run()

    def update_and_close_settings(self):
        """Updates measuring settings values with the dialog's values and
        saves them to default settings file.
        """
        can_close = self.__update_settings()
        if can_close:
            self.settings_updated.emit()
            self.close()

    def values_changed(self):
        """
        Check if measurement, detector or simulation settings have
        changed in regards to running simulations again.

        Return:
            True or False.
        """
        if self.measurement_settings_widget.are_values_changed():
            return True
        if self.detector_settings_widget.values_changed():
            return True
        if self.simulation_settings_widget.are_values_changed():
            return True
        return False

    def __update_settings(self):
        """Reads values from Request Settings dialog and updates them in
        default objects.
        """
        if self.measurement_settings_widget.isotopeComboBox.currentIndex()\
                == -1:
            QtWidgets.QMessageBox.critical(
                self, "Warning",
                "No isotope selected.\n\n"
                "Please select an isotope for the beam element.",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return False

        # Check the target and detector angles
        if not self.measurement_settings_widget.check_angles():
            return False

        if not self.tabs.currentWidget().fields_are_valid:
            QtWidgets.QMessageBox.critical(
                self, "Warning",
                "Some of the setting values have not been set.\n"
                "Please input values in fields indicated in red.",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return False

        if self.values_changed():
            if not self.simulation_settings_widget.are_values_changed():
                filter_func = lambda e: e.simulation.use_request_settings
            else:
                filter_func = lambda e: e.use_default_settings
            if not df.delete_element_simulations(self, self.request,
                                                 msg="request settings",
                                                 filter_func=filter_func):
                return False

        try:
            self.measurement_settings_widget.update_settings()
            self.profile_settings_widget.update_settings()

            default_measurement_settings_file = Path(
                self.request.default_measurement.directory,
                "Default.measurement")
            self.request.default_measurement.measurement_to_file(
                default_measurement_settings_file)
            self.request.default_measurement.profile_to_file(Path(
                self.request.default_measurement.directory,
                "Default.profile"))
            self.request.default_measurement.run.to_file(
                default_measurement_settings_file)
            self.request.default_target.to_file(
                None, default_measurement_settings_file)

            # Detector settings
            self.detector_settings_widget.update_settings()

            # Simulation settings
            self.simulation_settings_widget.update_settings()

            self.request.default_detector.to_file(
                Path(self.request.default_detector_folder, "Default.detector"),
                default_measurement_settings_file)

            self.request.default_simulation.to_file(
                Path(self.request.default_folder, "Default.simulation"))
            self.request.default_element_simulation.to_file(
                Path(self.request.default_folder, "Default.mcsimu"))

            # Update all element simulations that use request settings to
            #  have the correct simulation type
            current_sim_type = self.request.default_element_simulation.\
                simulation_type
            if self.original_simulation_type != current_sim_type:
                if current_sim_type == "ERD":
                    rec_type = "rec"
                    rec_suffix_to_delete = ".sct"
                else:
                    rec_type = "sct"
                    rec_suffix_to_delete = ".rec"

                for sample in self.request.samples.samples:
                    for simulation in sample.simulations.simulations.values():
                        for elem_sim in simulation.element_simulations:
                            if elem_sim.use_default_settings:
                                # TODO change to sim.use_req_settings?
                                elem_sim.simulation_type = current_sim_type
                                for recoil in elem_sim.recoil_elements:
                                    try:
                                        recoil.type = rec_type
                                        path_to_rec = Path(
                                            elem_sim.directory,
                                            recoil.prefix + "-" +
                                            recoil.name +
                                            rec_suffix_to_delete)
                                        os.remove(path_to_rec)
                                    except OSError:
                                        pass
                                    recoil.to_file(elem_sim.directory)
                                fp = Path(elem_sim.directory,
                                          elem_sim.name_prefix +
                                          "-" + elem_sim.name +
                                          ".mcsimu")
                                elem_sim.to_file(fp)

            return True
        except TypeError:
            # TODO: Make a better warning text.
            QtWidgets.QMessageBox.question(
                self, "Warning",
                "Some of the setting values have not been set.\n"
                "Please input setting values to save them.",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)

    def find_related_tab(self, tab_id):
        """
        Find tab based on its id.

        Args:
             tab_id: Tab id. Doesn't correspond to places in tab.
        """
        for i in range(self.tabs.count()):
            tab_widget = self.main_window.tabs.widget(i)
            if tab_widget == self.main_window.tab_widgets[tab_id]:
                return tab_widget
        return None
