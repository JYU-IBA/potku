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
             "Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"
__version__ = "2.0"

import copy
import os

import dialogs.dialog_functions as df

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

    def __init__(self, main_window, request, icon_manager):
        """Constructor for the program

        Args:
            main_window: Potku window.
            request: Request class object.
            icon_manager: IconManager object.
        """
        super().__init__()
        self.ui = uic.loadUi(os.path.join("ui_files", "ui_settings.ui"), self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        screen_geometry = QDesktopWidget \
            .availableGeometry(QApplication.desktop())
        self.resize(self.geometry().width() * 1.2,
                    screen_geometry.size().height() * 0.8)

        self.main_window = main_window
        self.request = request
        self.icon_manager = icon_manager

        # Connect buttons.
        self.ui.OKButton.clicked.connect(self.update_and_close_settings)
        self.ui.applyButton.clicked.connect(self.update_settings)
        self.ui.cancelButton.clicked.connect(self.close)

        # Add measurement settings view to the settings view
        self.measurement_settings_widget = MeasurementSettingsWidget(
            self.request.default_measurement)
        self.ui.tabs.addTab(self.measurement_settings_widget, "Measurement")

        self.measurement_settings_widget.beam_selection_ok.connect(
            lambda b: self.ui.OKButton.setEnabled(b)
        )

        # Add detector settings view to the settings view
        self.detector_settings_widget = DetectorSettingsWidget(
            self.request.default_detector, self.request, self.icon_manager,
            run=self.measurement_settings_widget.tmp_run)

        self.ui.tabs.addTab(self.detector_settings_widget, "Detector")

        # Add simulation settings view to the settings view
        self.simulation_settings_widget = SimulationSettingsWidget(
            self.request.default_element_simulation)
        self.ui.tabs.addTab(self.simulation_settings_widget, "Simulation")

        self.simulation_settings_widget.setEnabled(True)

        # Add profile settings view to the settings view
        self.profile_settings_widget = ProfileSettingsWidget(
            self.request.default_measurement)
        self.ui.tabs.addTab(self.profile_settings_widget, "Profile")
        self.__close = True

        self.ui.tabs.currentChanged.connect(lambda: self.__check_for_red())

        self.original_simulation_type = \
            self.request.default_element_simulation.simulation_type

        self.exec_()

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
        try:
            self.__update_settings()
            if self.__close:
                self.close()
        except TypeError:
            # Message has already been shown in update_settings()
            pass

    def update_settings(self):
        """Update values from dialog to every setting object.
        """
        try:
            self.__update_settings()
        except TypeError:
            # Message is already displayed within private method.
            pass

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
            QtWidgets.QMessageBox.critical(self, "Warning",
                                           "No isotope selected.\n\nPlease "
                                           "select an isotope for the beam "
                                           "element.",
                                           QtWidgets.QMessageBox.Ok,
                                           QtWidgets.QMessageBox.Ok)
            self.__close = False
            return
        only_seed_changed = False
        only_unnotified_changed = False  # If only values that can be changed
        # without running simulations again are changed
        # Check that values have been changed
        if not self.values_changed():
            # Check if only those values have been changed that don't require
            #  rerunning simulations
            if self.measurement_settings_widget.other_values_changed():
                only_unnotified_changed = True
            if self.simulation_settings_widget.seedSpinBox.value() != \
                    self.request.default_element_simulation.seed_number:
                only_seed_changed = True
            if self.detector_settings_widget.other_values_changed():
                only_unnotified_changed = True
            # Profile settings
            if self.profile_settings_widget.values_changed():
                only_unnotified_changed = True

            if not only_unnotified_changed and not only_seed_changed:
                self.__close = True
                return

        # Check the target and detector angles
        ok_pressed = self.measurement_settings_widget.check_angles()
        if ok_pressed:
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

            # Lists of old and current simulations and optimizations
            simulations_run = self.check_if_simulations_run()
            simulations_running = self.request.simulations_running()
            optimization_running = self.request.optimization_running()
            optimization_run = self.check_if_optimization_run()

            if simulations_run and simulations_running and \
                    not only_seed_changed and not only_unnotified_changed:
                reply = QtWidgets.QMessageBox.question(
                    self, "Simulated and running simulations",
                    "There are simulations that use request settings, "
                    "and either have been simulated or are currently running."
                    "\nIf you save changes, the running simulations "
                    "will be stopped, and the result files of the simulated "
                    "and stopped simulations are deleted. This also "
                    "affects possible optimization.\n\nDo you want to "
                    "save changes anyway?",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No |
                    QtWidgets.QMessageBox.Cancel, QtWidgets.QMessageBox.Cancel)
                if reply == QtWidgets.QMessageBox.No or reply == \
                        QtWidgets.QMessageBox.Cancel:
                    self.__close = False
                    return
                else:
                    # Stop simulations
                    df.req_settings_stop(self)
                    df.req_settings_optim_update(self, optimization_running)

                    df.reg_settings_del_sims(self, simulations_run)

                    df.req_settings_optim_update(self, optimization_run)

            elif simulations_running and not only_seed_changed and \
                    not only_unnotified_changed:
                reply = QtWidgets.QMessageBox.question(
                    self, "Simulations running",
                    "There are simulations running that use request "
                    "settings.\nIf you save changes, the running "
                    "simulations will be stopped, and their result files "
                    "deleted. This also affects possible running "
                    "optimization.\n\nDo you want to save changes anyway?",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No |
                    QtWidgets.QMessageBox.Cancel, QtWidgets.QMessageBox.Cancel)
                if reply == QtWidgets.QMessageBox.No or reply == \
                        QtWidgets.QMessageBox.Cancel:
                    self.__close = False
                    return
                else:
                    # Stop simulations
                    df.req_settings_stop(self)

            elif simulations_run and not only_seed_changed and \
                    not only_unnotified_changed:
                reply = QtWidgets.QMessageBox.question(
                    self, "Simulated simulations",
                    "There are simulations that use request settings, "
                    "and have been simulated.\nIf you save changes,"
                    " the result files of the simulated simulations are "
                    "deleted. This also affects possible "
                    "optimization.\n\nDo you want to save changes anyway?",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No |
                    QtWidgets.QMessageBox.Cancel, QtWidgets.QMessageBox.Cancel)
                if reply == QtWidgets.QMessageBox.No or reply == \
                        QtWidgets.QMessageBox.Cancel:
                    self.__close = False
                    return
                else:
                    df.reg_settings_del_sims(self, simulations_run)

                    tmp_sims = copy.copy(optimization_running)
                    df.req_settings_optim_update(self, tmp_sims)

                    for elem_sim in optimization_run:
                        df.tab_del(self, elem_sim)

            elif optimization_running and not only_unnotified_changed:
                reply = QtWidgets.QMessageBox.question(
                    self, "Optimization running",
                    "There are optimizations running that use request "
                    "settings.\nIf you save changes, the running "
                    "optimizations will be stopped, and their result files "
                    "deleted.\n\nDo you want to save changes anyway?",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No |
                    QtWidgets.QMessageBox.Cancel, QtWidgets.QMessageBox.Cancel)
                if reply == QtWidgets.QMessageBox.No or reply == \
                        QtWidgets.QMessageBox.Cancel:
                    self.__close = False
                    return
                else:
                    tmp_sims = copy.copy(optimization_running)
                    df.req_settings_optim_update(self, tmp_sims)

            elif optimization_run and not only_unnotified_changed:
                reply = QtWidgets.QMessageBox.question(
                    self, "Optimized results",
                    "There are optimizations done that use request "
                    "settings.\nIf you save changes, their result files will be"
                    " deleted.\n\nDo you want to save changes anyway?",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No |
                    QtWidgets.QMessageBox.Cancel, QtWidgets.QMessageBox.Cancel)
                if reply == QtWidgets.QMessageBox.No or reply == \
                        QtWidgets.QMessageBox.Cancel:
                    self.__close = False
                    return
                else:
                    tmp_sims = copy.copy(optimization_run)
                    df.req_settings_optim_update(self, tmp_sims)

            if only_seed_changed:
                # If there are running simulation that use the same seed as the
                # new one, stop them
                seed = self.simulation_settings_widget.seedSpinBox.value()
                running_simulations = self.request.running_simulations_by_seed(
                    seed)
                if running_simulations:
                    reply = QtWidgets.QMessageBox.question(
                        self, "Running simulations",
                        "There are simulatio processes that have the same seed "
                        "number as the new one.\nIf you save changes, these "
                        "simulation processes will be stopped (but their "
                        "results will not be deleted).\n\nDo you want save "
                        "changes anyway?",
                        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No |
                        QtWidgets.QMessageBox.Cancel,
                        QtWidgets.QMessageBox.Cancel)
                    if reply == QtWidgets.QMessageBox.No or reply == \
                            QtWidgets.QMessageBox.Cancel:
                        self.__close = False
                        return
                    else:
                        # Stop the running simulations' mcerd process
                        # that corresponds to seed
                        for run_sim in running_simulations:
                            run_sim.mcerd_objects[seed].stop_process()
                            del (run_sim.mcerd_objects[seed])

            try:
                self.measurement_settings_widget.update_settings()
                self.profile_settings_widget.update_settings()

                default_measurement_settings_file = os.path.join(
                    self.request.default_measurement.directory,
                    "Default.measurement")
                self.request.default_measurement.profile_to_file(os.path.join(
                    self.request.default_measurement.directory,
                    "Default.profile"))
                self.request.default_measurement.run.to_file(
                    default_measurement_settings_file)
                self.request.default_target.to_file(
                    None, default_measurement_settings_file)

                # Detector settings
                self.detector_settings_widget.update_settings()

                df.update_efficiency_files(self.request.default_detector)

                # Simulation settings
                self.simulation_settings_widget.update_settings()

                self.request.default_detector.to_file(os.path.join(
                    self.request.default_detector_folder, "Default.detector"),
                    default_measurement_settings_file)

                self.request.default_simulation.to_file(os.path.join(
                    self.request.default_folder, "Default.simulation"))
                self.request.default_element_simulation.to_file(
                    os.path.join(self.request.default_folder, "Default.mcsimu"))

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
                        for simulation in sample.simulations.simulations.\
                                values():
                            for elem_sim in simulation.element_simulations:
                                if elem_sim.use_default_settings:
                                    elem_sim.simulation_type = current_sim_type
                                    for recoil in elem_sim.recoil_elements:
                                        try:
                                            recoil.type = rec_type
                                            path_to_rec = os.path.join(
                                                elem_sim.directory,
                                                recoil.prefix + "-" +
                                                recoil.name +
                                                rec_suffix_to_delete)
                                            os.remove(path_to_rec)
                                        except OSError:
                                            pass
                                        recoil.to_file(elem_sim.directory)
                                    fp = os.path.join(elem_sim.directory,
                                                      elem_sim.name_prefix +
                                                      "-" + elem_sim.name +
                                                      ".mcsimu")
                                    elem_sim.to_file(fp)

                self.__close = True
            except TypeError:
                # TODO: Make a better warning text.
                QtWidgets.QMessageBox.question(self, "Warning",
                                               "Some of the setting values have"
                                               " not been set.\n" +
                                               "Please input setting values to "
                                               "save them.",
                                               QtWidgets.QMessageBox.Ok,
                                               QtWidgets.QMessageBox.Ok)
                raise TypeError

        else:
            self.__close = False

    def find_related_tab(self, tab_id):
        """
        Find tab based on its id.

        Args:
             tab_id: Tab id. Doesn't correspond to places in tab.
        """
        for i in range(self.ui.tabs.count()):
            tab_widget = self.main_window.ui.tabs.widget(i)
            if tab_widget == self.main_window.tab_widgets[tab_id]:
                return tab_widget
        return None

    def check_if_optimization_run(self):
        """
        Check whether optimization has been done.

        Return:
             List of optimized element simulations.
        """
        optimized = []
        for sample in self.request.samples.samples:
            for simulation in sample.simulations.simulations.values():
                for elem_sim in simulation.element_simulations:
                    if elem_sim.optimization_widget and not \
                            elem_sim.optimization_running:
                        optimized.append(elem_sim)
        return optimized

    def check_if_simulations_run(self):
        """
        Check if the re are any element simulations that have been simulated.

        Return:
             List of run element simulations.
        """
        simulations_run = []
        for sample in self.request.samples.samples:
            for simulation in sample.simulations.simulations.values():
                for elem_sim in simulation.element_simulations:
                    if elem_sim.simulations_done and \
                       elem_sim.use_default_settings:
                        simulations_run.append(elem_sim)
        return simulations_run
