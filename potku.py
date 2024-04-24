#!/usr/bin/env python
# coding=utf-8
"""
Created on 21.3.2013
Updated on 18.4.2024

Potku

Copyright (C) 2013-2018 Jarkko Aalto, Severi Jääskeläinen, Samuel Kaiponen,
Timo Konu, Samuli Kärkkäinen, Samuli Rahkonen, Miika Raunio, Heta Rekilä and
Sinikka Siironen, 2020 Juhani Sundell, 2013-2024 Jaakko Julin

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program (file named 'LICENSE').
"""

__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen \n Samuli " \
             "Rahkonen \n Miika Raunio \n Severi Jääskeläinen \n Samuel " \
             "Kaiponen \n Heta Rekilä \n Sinikka Siironen \n Juhani Sundell \
             \n Jaakko Julin"
__version__ = "2.0"

import functools
import gc
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime
from datetime import timedelta
from pathlib import Path
from typing import Union

from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAbstractItemView, QMessageBox
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QTreeWidgetItem

import modules.general_functions as gf
import dialogs.dialog_functions as df
import widgets.gui_utils as gutils
import widgets.input_validation as iv
from dialogs.about import AboutDialog
from dialogs.file_dialogs import open_file_dialog
from dialogs.global_settings import GlobalSettingsDialog
from dialogs.measurement.import_binary import ImportDialogBinary
from dialogs.measurement.import_measurement import ImportMeasurementsDialog
from dialogs.measurement.load_measurement import LoadMeasurementDialog
from dialogs.new_request import RequestNewDialog
from dialogs.request_settings import RequestSettingsDialog
from dialogs.simulation.new_simulation import SimulationNewDialog
from modules.global_settings import GlobalSettings
from modules.measurement import Measurement
from modules.request import Request
from modules.selection import Selector
from modules.simulation import Simulation
from widgets.base_tab import BaseTab
from widgets.gui_utils import StatusBarHandler
from widgets.icon_manager import IconManager
from widgets.measurement.tab import MeasurementTabWidget
from widgets.simulation.tab import SimulationTabWidget
from modules.config_manager import ConfigManager


class Potku(QtWidgets.QMainWindow):
    """Potku is main window class.
    """
    # Maximum number of recently opened .request files to store and show in
    # the menu.
    MAX_RECENT_FILES = 20
    RECENT_FILES_KEY = "recently_opened"

    settings_updated = QtCore.pyqtSignal([], [GlobalSettings])

    def __init__(self):
        """Init main window for Potku.
        """
        super().__init__()
        uic.loadUi(gutils.get_ui_dir() / "ui_main_window.ui", self)

        # Disable mouse wheel scrolling in all spin boxes and combo boxes as
        # requested by a user (see comments in
        # https://github.com/JYU-IBA/potku/issues/214).
        gutils.disable_scrolling_in_spin_boxes()
        gutils.disable_scrolling_in_combo_boxes()

        version_number, version_date = gf.get_version_number_and_date()
        self.setWindowTitle(f'Potku {version_number} - {version_date}')
        self.title = self.windowTitle()
        self.treeWidget.setHeaderLabel("")

        self.icon_manager = IconManager()
        self.settings = GlobalSettings()
        self.request = None
        self.potku_bin_dir = os.getcwd()

        # Holds references to all the tab widgets in "tab_measurements"
        # (even when they are removed from the QTabWidget)
        self.tab_widgets = {}
        self.tab_id = 0  # identification for each tab

        # Set up connections within UI
        self.actionNew_Measurement.triggered.connect(self.open_new_measurement)
        self.requestSettingsButton.clicked.connect(self.open_request_settings)
        self.globalSettingsButton.clicked.connect(self.open_global_settings)
        self.tabs.tabCloseRequested.connect(self.remove_tab)
        self.treeWidget.itemDoubleClicked.connect(self.focus_selected_tab)

        self.requestNewButton.clicked.connect(self.make_new_request)
        self.requestOpenButton.clicked.connect(self.open_request)
        self.actionNew_Request.triggered.connect(self.make_new_request)
        self.actionOpen_Request.triggered.connect(self.open_request)
        self.addNewMeasurementButton.clicked.connect(self.open_new_measurement)
        self.actionNew_measurement_2.triggered.connect(
            self.open_new_measurement)
        self.actionImport_pelletron.triggered.connect(self.import_pelletron)
        self.actionBinary_data_lst.triggered.connect(self.import_binary)
        self.action_manual.triggered.connect(self.__open_manual)
        self.actionDataHelp.triggered.connect(self.__open_data_help)

        self.actionSave_cuts.triggered.connect(
            self.current_measurement_save_cuts)
        self.actionAnalyze_elemental_losses.triggered.connect(
            self.current_measurement_analyze_elemental_losses)
        self.actionCreate_energy_spectrum.triggered.connect(
            self.current_measurement_create_energy_spectrum)
        self.actionCreate_depth_profile.triggered.connect(
            self.current_measurement_create_depth_profile)
        self.actionGlobal_Settings.triggered.connect(self.open_global_settings)
        self.actionRequest_Settings.triggered.connect(
            self.open_request_settings)
        self.actionAbout.triggered.connect(AboutDialog)

        self.actionNew_Request_2.triggered.connect(self.make_new_request)
        self.actionOpen_Request_2.triggered.connect(self.open_request)

        # Should save changes
        self.actionExit.triggered.connect(self.close)

        self.menuImport.setEnabled(False)

        # by default show left panel when opening application
        gutils.set_potku_setting("left_panel_shown", True)
        df.set_up_side_panel(self, "left_panel_shown", "left")

        # Set up simulation connections within UI
        self.actionNew_Simulation.triggered.connect(
            self.create_new_simulation)
        self.actionNew_Simulation_2.triggered.connect(
            self.create_new_simulation)
        self.actionCreate_energy_spectrum_sim.triggered.connect(
            self.current_simulation_create_energy_spectrum)
        self.addNewSimulationButton.clicked.connect(
            self.create_new_simulation)

        # Set up report tool connection in UI
        self.actionCreate_report.triggered.connect(self.create_report)

        # Set up styles for main window
        # Cannot use os.path.join (PyQT+css)
        print("Root directory is " + str(gf.get_root_dir()))
        print("Root directory relative to CWD is " + str(gf.get_root_dir().relative_to(os.getcwd())))
        images_dir = str(gf.get_images_dir().relative_to(os.getcwd()))
        images_dir.replace("\\", "/") #Not sure if needed, it's a hack anyway.
        print("Images directory relative to CWD is " + images_dir)
        bg_blue = images_dir + "/background_blue.svg"
        bg_green = images_dir + "/background_green.svg"
        print("Blue background should be: " + bg_blue)


        style_intro = "QWidget#introduceTab {border-image: url(" \
                      + bg_blue + ");}"
        style_mesinfo = ("QWidget#infoTab {border-image: url(" +
                         bg_green + ");}")
        self.introduceTab.setStyleSheet(style_intro)
        self.infoTab.setStyleSheet(style_mesinfo)
        self.__remove_info_tab()

        self.setWindowIcon(self.icon_manager.get_icon("potku_icon.ico"))
        self.update_recent_file_menu()

        # Set main window's icons to place
        self.__set_icons()
        self.showMaximized()

    def __initialize_tree_view(self):
        """Inits the tree view and creates the top level items.
        """
        self.treeWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.treeWidget.customContextMenuRequested.connect(self.__open_menu)
        self.treeWidget.setDropIndicatorShown(True)
        self.treeWidget.setDragDropMode(QAbstractItemView.InternalMove)
        # Disable dragging since it doesn't do anything yet
        # TODO: Dragging changes the order of the items in tree and directory
        self.treeWidget.setDragEnabled(False)
        self.treeWidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.treeWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.treeWidget.itemChanged[QTreeWidgetItem, int].connect(
            self.__rename_dir)

    def __open_menu(self, position):
        """Opens the right click menu in tree view.
        """
        indexes = self.treeWidget.selectedIndexes()
        level = 0
        if len(indexes) > 0:
            level = 0
            index = indexes[0]
            while index.parent().isValid():
                index = index.parent()
                level += 1

        menu = QMenu()
        if level == 1:
            menu.addAction("Rename", self.__rename_tree_item)
            menu.addAction("Remove", self.__remove_tree_item)

        current_item = self.treeWidget.currentItem()
        if current_item and isinstance(current_item.obj, Measurement):
            menu.addAction("Make master", self.__make_master_measurement)
            menu.addAction("Remove master", self.__remove_master_measurement)
            menu.addAction(
                "Exclude from slaves", lambda: self.__set_slave_status(False))
            menu.addAction(
                "Include as slave", lambda: self.__set_slave_status(True))

        menu.exec_(self.treeWidget.viewport().mapToGlobal(position))

    def __rename_tree_item(self):
        """Renames selected tree item in tree view and in folder structure.
        """
        clicked_item = self.treeWidget.currentItem()
        self.treeWidget.editItem(clicked_item)

    @gutils.block_treewidget_signals
    def __rename_dir(self, *_):
        """Renames object based on selected tree item. This method is called
        when tree item is changed.
        """
        clicked_item = self.treeWidget.currentItem()

        if not clicked_item:
            return
        # TODO do all name validation in the backend modules
        regex = "^[A-Za-z0-9-ÖöÄäÅå]+"
        valid_text = iv.validate_text_input(clicked_item.text(0), regex)

        if valid_text != clicked_item.text(0):
            QtWidgets.QMessageBox.information(
                self, "Notice",
                "You can't use special characters other than '-' in the name.",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            clicked_item.setText(0, clicked_item.obj.name)
            return

        if valid_text == "":
            clicked_item.setText(0, clicked_item.obj.name)
            return

        if valid_text == clicked_item.obj.name:
            clicked_item.setText(0, clicked_item.obj.name)
            return

        new_name = valid_text
        try:
            clicked_item.obj: Union[Measurement, Simulation]
            clicked_item.obj.rename(new_name)
        except OSError as e:
            QtWidgets.QMessageBox.critical(
                self, "Error", str(e),
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)

        if type(clicked_item.obj) is Measurement:
            # Update Energy spectrum, Composition changes and Depth profile
            # save files.
            for i in range(self.tabs.count()):
                tab_widget = self.tabs.widget(i)
                if tab_widget.obj is clicked_item.obj:
                    if tab_widget.energy_spectrum_widget:
                        tab_widget.energy_spectrum_widget.update_use_cuts()
                        tab_widget.energy_spectrum_widget.save_to_file()

                    if tab_widget.elemental_losses_widget:
                        tab_widget.elemental_losses_widget.update_cuts()
                        tab_widget.elemental_losses_widget.save_to_file()

                    if tab_widget.depth_profile_widget:
                        tab_widget.depth_profile_widget.update_use_cuts()
                        tab_widget.depth_profile_widget.save_to_file()

                    self.remove_tab(i)
                    self.tabs.insertTab(i, tab_widget,
                                        clicked_item.obj.name)
                    self.tabs.setCurrentWidget(tab_widget)
                    break

        elif type(clicked_item.obj) is Simulation:
            # Update Tab name
            for i in range(self.tabs.count()):
                tab_widget = self.tabs.widget(i)
                if tab_widget.obj is clicked_item.obj:
                    self.remove_tab(i)
                    self.tabs.insertTab(i, tab_widget,
                                        clicked_item.obj.name)
                    self.tabs.setCurrentWidget(tab_widget)
                    break
        clicked_item.setText(0, clicked_item.obj.name)

    @gutils.block_treewidget_signals
    def __remove_tree_item(self):
        """Removes selected tree item in tree view and in folder structure.
        """
        clicked_item = self.treeWidget.currentItem()

        if clicked_item:
            if type(clicked_item.obj) is Measurement:
                obj_type = "measurement"
            elif type(clicked_item.obj) is Simulation:
                obj_type = "simulation"
            else:
                obj_type = ""  # TODO: place for sample type checking.
            reply = QtWidgets.QMessageBox.question(
                self, "Confirmation",
                f"Deleting selected {obj_type} will delete all files and "
                f"folders under selected {obj_type} directory.\n\n"
                f"Are you sure you want to delete selected {obj_type}?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No |
                QtWidgets.QMessageBox.Cancel, QtWidgets.QMessageBox.Cancel)
            if reply == QtWidgets.QMessageBox.No or reply == \
                    QtWidgets.QMessageBox.Cancel:
                return  # If clicked Yes, then continue normally

            # Remove object from Sample
            clicked_item.parent().obj.remove_obj(clicked_item.obj)
            clicked_item.obj.close_log_files()

            # Remove object directory
            shutil.rmtree(clicked_item.obj.directory)

            # Remove object from tree
            clicked_item.parent().removeChild(clicked_item)

            # Remove object tab
            for i in range(self.tabs.count()):
                if self.tabs.widget(i).obj is clicked_item.obj:
                    self.tabs.removeTab(i)
                    break
            self.tab_widgets.pop(clicked_item.obj.tab_id)

    def closeEvent(self, event):
        """
        Save recoil elements and simulation targets and close the program.
        """
        if self.request is not None:
            for sample in self.request.samples.samples:
                for simulation in sample.simulations.simulations.values():
                    for elem_sim in simulation.element_simulations:
                        for recoil_element in elem_sim.recoil_elements:
                            recoil_element.to_file(elem_sim.directory)
                    simulation.target.to_file(
                        Path(simulation.directory, simulation.target.name +
                             ".target"))

        if not self.are_simulations_stopped():
            # TODO also needs to be done when new request is being opened
            event.ignore()
            return

        widget = self.tabs.currentWidget()
        if isinstance(widget, BaseTab):
            widget.save_geometries()

        super().closeEvent(event)

    def are_simulations_stopped(self):
        """Checks all running simulations for current request and prompts
        user to stop them. Returns True if user chooses to stop the
        simulations or there are no simulations, otherwise returns False.
        """
        if self.request is not None:
            sims = {
                *self.request.get_running_optimizations(),
                *self.request.get_running_simulations()
            }
            if sims:
                reply = QtWidgets.QMessageBox.question(
                    self, "Running simulations",
                    "There are simulations currently running. These must be "
                    "stopped before closing the program.\n"
                    "Do you want stop the simulations?",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel,
                    QtWidgets.QMessageBox.Yes
                )
                if reply == QtWidgets.QMessageBox.Cancel:
                    return False
                events = [sim.stop() for sim in sims]
                for e in events:
                    # Note: while the worst case scenario is that we'll be
                    # stuck here for len(sims) seconds, it is likely that
                    # all simulations have stopped within 0.2 seconds (the
                    # default interval for checking stopping requests). Some
                    # overhead for releasing locks and notifying listeners
                    # is also to be expected.
                    e.wait(timeout=1)
        return True

    def create_report(self):
        """
        Opens a dialog for making a report.
        """
        # TODO: Replace this with the actual dialog call.
        QtWidgets.QMessageBox.critical(
            self, "Error", "Report tool not yet implemented!",
            QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)

    def current_measurement_create_depth_profile(self):
        """Opens the depth profile analyzation tool for the current open
        measurement tab widget.
        """
        widget = self.tabs.currentWidget()
        if isinstance(widget, MeasurementTabWidget):
            widget.open_depth_profile()
        else:
            QtWidgets.QMessageBox.question(
                self, "Notification",
                "An open measurement is required to do this action.",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)

    def current_measurement_analyze_elemental_losses(self):
        """Opens the element losses analyzation tool for the current open
        measurement tab widget.
        """
        widget = self.tabs.currentWidget()
        if isinstance(widget, MeasurementTabWidget):
            widget.open_element_losses()
        else:
            QtWidgets.QMessageBox.question(
                self, "Notification",
                "An open measurement is required to do this action.",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)

    def current_measurement_create_energy_spectrum(self):
        """Opens the energy spectrum analyzation tool for the current open
        measurement tab widget.
        """
        widget = self.tabs.currentWidget()
        if isinstance(widget, MeasurementTabWidget):
            widget.open_energy_spectrum()
        else:
            QtWidgets.QMessageBox.question(
                self, "Notification",
                "An open measurement is required to do this action.",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)

    def current_measurement_save_cuts(self):
        """Saves the current open measurement tab widget's selected cuts
        to cut files.
        """
        widget = self.tabs.currentWidget()
        if isinstance(widget, MeasurementTabWidget):
            widget.measurement_save_cuts()
        else:
            QtWidgets.QMessageBox.question(
                self, "Notification",
                "An open measurement is required to do this action.",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)

    def current_simulation_create_energy_spectrum(self):
        """
        Opens the energy spectrum analyzation tool for the current open
        simulation tab widget.
        """
        widget = self.tabs.currentWidget()
        if isinstance(widget, MeasurementTabWidget):
            widget.open_energy_spectrum()
        else:
            QtWidgets.QMessageBox.question(
                self, "Notification",
                "An open simulation is required to do this action.",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)

    def delete_selections(self):
        """Deletes the selected tree widget items.
        """
        # TODO: Memory isn't released correctly. Maybe because of matplotlib.
        selected_tabs = [self.tab_widgets[item.tab_id] for
                         item in self.treeWidget.selectedItems()]
        if selected_tabs:  # Ask user a confirmation.
            reply = QtWidgets.QMessageBox.question(
                self, "Confirmation",
                "Deleting selected measurements will delete all files and "
                "folders under selected measurement directories.\n\n"
                "Are you sure you want to delete selected measurements?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No |
                QtWidgets.QMessageBox.Cancel, QtWidgets.QMessageBox.Cancel)
            if reply == QtWidgets.QMessageBox.No or reply == \
                    QtWidgets.QMessageBox.Cancel:
                return  # If clicked Yes, then continue normally

        for tab in selected_tabs:
            measurement = self.request.samples.measurements.get_key_value(
                tab.tab_id)
            try:
                # Close and remove logs
                measurement.close_log_files()

                # Remove measurement's directory tree
                shutil.rmtree(measurement.directory)
                Path(self.request.directory /
                     measurement.measurement_file).unlink()
            except:
                QtWidgets.QMessageBox.question(
                    self, "Confirmation",
                    "Problem with deleting files.",
                    QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
                # TODO check that this is the intented way of setting the
                #  loggers in case something went wrong.
                measurement.set_up_log_files(measurement.directory,
                                             measurement.request.directory)
                return

            self.request.samples.measurements.remove_by_tab_id(tab.tab_id)
            remove_index = self.tabs.indexOf(tab)
            self.remove_tab(remove_index)  # Remove measurement from open tabs

            tab.histogram.matplotlib.delete()
            tab.elemental_losses_widget.matplotlib.delete()
            tab.energy_spectrum_widget.matplotlib.delete()
            tab.depth_profile_widget.matplotlib.delete()

            tab.mdiArea.closeAllSubWindows()
            del self.tab_widgets[tab.tab_id]
            tab.close()
            tab.deleteLater()

        # Remove selected from tree widget
        root = self.treeWidget.invisibleRootItem()
        for item in self.treeWidget.selectedItems():
            (item.parent() or root).removeChild(item)
        gc.collect()  # Suggest garbage collector to clean.

    @gutils.block_treewidget_signals
    def focus_selected_tab(self, clicked_item, *_):
        """Focus to selected tab (in tree widget) and if it isn't open, open it.

        Args:
            clicked_item: TreeWidgetItem with tab_id attribute (int) that
                connects the item to the corresponding MeasurementTabWidget
            *_: unused event args.
        """
        sbh = StatusBarHandler(self.statusbar)
        try:
            tab_id = clicked_item.tab_id
            tab = self.tab_widgets[tab_id]

            if type(tab) is SimulationTabWidget:
                kwargs = {
                    "settings": self.settings,
                    "settings_updated": self.settings_updated,
                    "ion_division": self.settings.get_ion_division(),
                    "min_presim_ions": self.settings.get_min_presim_ions(),
                    "min_sim_ions": self.settings.get_min_simulation_ions()
                }
            else:
                kwargs = {}
            tab.load_data(
                progress=sbh.reporter.get_sub_reporter(lambda x: 0.9 * x),
                **kwargs)

            name = tab.obj.name
            if type(tab) is MeasurementTabWidget:
                master_mea = tab.obj.request.get_master()
                if master_mea and tab.obj.name == master_mea.name:
                    name = f"{name} (master)"

            # Check that the tab to be focused exists.
            if not self.__tab_exists(tab_id):
                self.tabs.addTab(tab, name)
            self.tabs.setCurrentWidget(tab)
            self.__change_tab_icon(clicked_item)

        except AttributeError as e:
            print(e)  # TODO remove print
        sbh.reporter.report(100)

    def import_pelletron(self):
        """Import Pelletron's measurements into request.

        Import Pelletron's measurements from
        """
        if not self.request:
            return
        # For loading measurements.
        import_dialog = ImportMeasurementsDialog(
            self.request, self.icon_manager, self.statusbar, self)
        if import_dialog.imported:
            self.__remove_info_tab()

    def import_binary(self):
        """Import binary measurements into request.

        Import binary measurements from
        """
        if not self.request:
            return
        import_dialog = ImportDialogBinary(
            self.request, self.icon_manager, self.statusbar, self)
        if import_dialog.imported:
            self.__remove_info_tab()

    def load_request_measurements(self, measurements=None, progress=None):
        """Load measurement files in the request.

        Args:
            measurements: A list representing loadable measurements when
                importing measurements to the request.
            progress: a ProgressReporter object
        """
        if measurements is None:
            measurements = []
        if measurements:
            samples_with_measurements = measurements
            load_data = True
        else:
            # a dict with the sample as a key, and measurements' info file paths
            # in the value as a list
            samples_with_measurements = \
                self.request.samples.get_samples_and_measurements()
            load_data = False

        count = len(samples_with_measurements)
        dirtyinteger = 0
        for sample, measurements in samples_with_measurements.items():
            for measurement_file in measurements:
                self.add_new_tab("measurement", measurement_file, sample,
                                 dirtyinteger, count, load_data=load_data)

                if progress is not None:
                    progress.report(dirtyinteger / count * 100)
                dirtyinteger += 1

        if progress is not None:
            progress.report(100)

    def load_request_samples(self, progress=None):
        """"Load sample files in the request.

        Args:
            progress: a ProgressReporter object
        """
        sample_paths_in_request = self.request.get_samples_files()
        if sample_paths_in_request:
            for i, sample_path in enumerate(sample_paths_in_request):
                sample = self.request.samples.add_sample(
                    sample_path=sample_path)
                self.add_root_item_to_tree(sample)

                if progress is not None:
                    progress.report(i / len(sample_paths_in_request) * 100)

            self.request.increase_running_int_by_1()

        if progress is not None:
            progress.report(100)

    def load_request_simulations(self, simulations=None, progress=None):
        """Load simulation files in the request.

        Args:
            simulations: A list representing loadable simulation when importing
                simulation to the request.
            progress: a ProgressReporter object
        """
        if simulations is None:
            simulations = []
        if simulations:
            samples_with_simulations = simulations
            load_data = True
        else:
            samples_with_simulations = \
                self.request.samples.get_samples_and_simulations()
            load_data = False

        count = len(samples_with_simulations)
        dirtyinteger = 0
        for sample, simulations in samples_with_simulations.items():
            for simulation_file in simulations:
                self.add_new_tab("simulation", simulation_file, sample,
                                 dirtyinteger, count, load_data=load_data)

                if progress is not None:
                    progress.report(dirtyinteger / count * 100)
                dirtyinteger += 1

        if progress is not None:
            progress.report(100)
    pass

    def make_new_request(self):
        """Opens a dialog for creating a new request.
        """
        if not self.are_simulations_stopped():
            return
        # The directory for request is already created after this
        dialog = RequestNewDialog(self)

        # TODO: regex check for directory. I.E. do not allow asd/asd
        if dialog.directory:
            self.__close_request()
            title = f"{self.title} - Request: {dialog.name}"
            self.setWindowTitle(title)

            self.treeWidget.setHeaderLabel(f"Request: {dialog.name}")
            self.__initialize_tree_view()

            self.request = Request(
                dialog.directory, dialog.name, self.settings, self.tab_widgets)
            self.settings.set_request_directory_last_open(dialog.directory)
            self.request.log("Request created.")
            # Request made, close introduction tab
            self.__remove_introduction_tab()
            self.__open_info_tab()
            self.__set_request_buttons_enabled(True)
            self.add_to_recent_files(Path(self.request.request_file))

    def open_global_settings(self):
        """Opens global settings dialog.
        """
        gsd = GlobalSettingsDialog(self.settings)
        gsd.settings_updated.connect(self.settings_updated[GlobalSettings].emit)
        gsd.exec_()

    def open_new_measurement(self):
        """Opens file an open dialog and if filename is given opens new
        measurement from it.
        """
        if self.request is None:
            return

        dialog = LoadMeasurementDialog(self.request.samples.samples,
                                       self.request.directory)
        sample_name = dialog.sample

        if dialog.filename:
            try:
                self.tabs.removeTab(self.tabs.indexOf(
                    self.measurement_info_tab))
            except AttributeError:
                pass  # If there is no info tab, no need to worry about.
            sbh = StatusBarHandler(self.statusbar)

            try:
                sample_item = self.treeWidget.findItems(
                    sample_name, Qt.MatchEndsWith, 0)[0]
            except IndexError:
                # Sample is not yet in the tree, so add it
                sample_item = self.__add_sample(sample_name)

            self.add_new_tab(
                "measurement", dialog.filename, sample_item.obj, load_data=True,
                object_name=dialog.name,
                progress=sbh.reporter.get_sub_reporter(lambda x: 0.9 * x))
            self.__remove_info_tab()

            sbh.reporter.report(100)

    def create_new_simulation(self):
        """
        Opens a dialog for creating a new simulation.
        """
        dialog = SimulationNewDialog(self.request.samples.samples)

        simulation_name = dialog.name
        sample_name = dialog.sample
        if simulation_name and sample_name:
            sbh = StatusBarHandler(self.statusbar)

            try:
                sample_item = self.treeWidget.findItems(sample_name,
                                                        Qt.MatchEndsWith, 0)[0]
            except IndexError:
                # Sample is not yet in the tree, so add it
                sample_item = self.__add_sample(sample_name)

            serial_number = sample_item.obj.get_running_int_simulation()
            sample_item.obj.increase_running_int_simulation_by_1()

            self.add_new_tab("simulation", Path(
                self.request.directory, sample_item.obj.directory,
                Simulation.DIRECTORY_PREFIX + "%02d" % serial_number + "-" +
                dialog.name, f"{dialog.name}.mccfg"), sample_item.obj,
                             load_data=True,
                             progress=sbh.reporter.get_sub_reporter(
                                 lambda x: 0.9 * x
                             ))
            self.__remove_info_tab()

            sbh.reporter.report(100)

    def __add_sample(self, sample_name):
        """Creates a new Sample object and adds it to tree view.

        Args:
            sample_name: Sample name.

        Return:
            TreeWidgetItem
        """
        sample = self.request.samples.add_sample(name=sample_name)
        return self.add_root_item_to_tree(sample)

    def update_recent_file_menu(self, files=None):
        """Updates the recently opened file menu. Previous actions are
        replaced by new ones based on the given list of files.

        Args:
            files: list of files to be shown in the menu
        """
        # Note: when running Potku as a Python script on Mac, the recently
        # opened files menu becomes inactive after creating a new request.
        # This is fixed when Potku is bundled intp an app.
        self.menuOpen_recent.clear()

        if files is None:
            files = Potku.get_recent_files()

        for f in files[:Potku.MAX_RECENT_FILES]:
            act = self.menuOpen_recent.addAction(str(f))
            act.triggered.connect(
                functools.partial(self.__open_request, Path(f)))

        if not files:
            act = self.menuOpen_recent.addAction("<empty>")
            act.setEnabled(False)
        else:
            self.menuOpen_recent.addSeparator()
            act = self.menuOpen_recent.addAction("Empty recently opened list")
            act.triggered.connect(self.clear_recent_files)

    def clear_recent_files(self):
        """Clears the list of recently opened files.
        """
        gutils.remove_potku_setting(key=Potku.RECENT_FILES_KEY)
        self.update_recent_file_menu(files=[])

    @staticmethod
    def get_recent_files():
        """Returns a list of recently opened .request files. Files are sorted
        so that the most recent is first.
        """
        return gutils.get_potku_setting(Potku.RECENT_FILES_KEY, [], list)

    @staticmethod
    def set_recent_files(files):
        """Stores the list of files as the most recently opened files.

        Args:
            files: list of file paths (as strings) to store
        """
        gutils.set_potku_setting(Potku.RECENT_FILES_KEY,
                                 files[:Potku.MAX_RECENT_FILES])

    def add_to_recent_files(self, file):
        """Inserts the given file as the first element in the recently
        opened file list and updates the menu.

        Args:
            file: file to be added to the list
        """
        files = Potku.get_recent_files()
        file_str = str(file)
        try:
            files.remove(file_str)
        except ValueError:
            # File was not in list, nothing to do
            pass
        files.insert(0, file_str)
        Potku.set_recent_files(files)
        self.update_recent_file_menu(files=files)

    def remove_from_recent_files(self, file):
        """Removes a file from recently added file list.

        Args:
            file: file to be removed
        """
        files = Potku.get_recent_files()
        try:
            files.remove(str(file))
            Potku.set_recent_files(files)
            self.update_recent_file_menu(files=files)
        except ValueError:
            # File was not in list, nothing to do
            pass

    def open_request(self):
        """Shows a dialog to open a request.
        """
        if not self.are_simulations_stopped():
            return
        file = open_file_dialog(
            self, self.settings.get_request_directory_last_open(),
            "Open an existing request", "Request file (*.request)")
        if file:
            self.__open_request(Path(file))

    def __open_request(self, file: Path):
        """Opens a request in the main"""
        if not self.are_simulations_stopped():
            return
        try:
            request = Request.from_file(file, self.settings, self.tab_widgets)
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Error", f"Could not open the request: {e}",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok
            )
            self.remove_from_recent_files(file)
            return

        # Checks for maximum path length. If too long some files might not be reachable
        if (gf.check_max_path_length()[0] > 240):
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setText( f"Longest path is now {gf.check_max_path_length()[0]} characters long.\n"
                            f"There might be problems if Windows maximum path length (256) is exceeded")
            msgBox.setWindowTitle("Path length warning")
            msgBox.setStandardButtons(QMessageBox.Ok)
            msgBox.exec()

        sbh = StatusBarHandler(self.statusbar)
        self.__close_request()
        self.add_to_recent_files(Path(file))
        self.request = request
        self.setWindowTitle("{0} - Request: {1}".format(
            self.title,
            self.request.get_name()))
        self.treeWidget.setHeaderLabel(
            "Request: {0}".format(self.request.get_name()))
        self.__initialize_tree_view()

        folder = file.parent
        self.settings.set_request_directory_last_open(folder)

        sbh.reporter.report(20)
        self.load_request_samples(progress=sbh.reporter.get_sub_reporter(
            lambda x: 20 + 0.2 * x
        ))
        self.load_request_measurements(progress=sbh.reporter.get_sub_reporter(
            lambda x: 40 + 0.2 * x
        ))
        self.load_request_simulations(progress=sbh.reporter.get_sub_reporter(
            lambda x: 80 + 0.2 * x
        ))

        self.__remove_introduction_tab()
        self.__set_request_buttons_enabled(True)

        master_measurement = self.request.has_master()
        nonslaves = self.request.get_nonslaves()
        if master_measurement != "":
            self.request.set_master(master_measurement)
            master_measurement_name = master_measurement.name
        else:
            master_measurement_name = None

        for sample in self.request.samples.samples:
            # Get Sample item from tree
            try:
                sample_item = self.treeWidget.findItems(
                    "%02d" % sample.serial_number + " " + sample.name,
                    Qt.MatchEndsWith,
                    0)[0]
                for i in range(sample_item.childCount()):
                    item = sample_item.child(i)
                    tab_widget = self.tab_widgets[item.tab_id]
                    tab_name = tab_widget.obj.name
                    if master_measurement_name and \
                            item.tab_id == master_measurement.tab_id:
                        item.setText(0,
                                     "{0} (master)".format(
                                         master_measurement_name))
                    elif tab_widget.obj in nonslaves or \
                            not master_measurement_name or type(
                        tab_widget.obj) == Simulation:
                        item.setText(0, tab_name)
                    else:
                        item.setText(0, "{0} (slave)".format(tab_name))

                for i in range(sample_item.childCount()):
                    item = sample_item.child(i)
                    tab_widget = self.tab_widgets[item.tab_id]
                    tab_name = tab_widget.simulation.name
                    item.setText(0, tab_name)
            except:
                # TODO Sample was not found in tree.
                pass

        sbh.reporter.report(100)

    def open_request_settings(self):
        """Opens request settings dialog.
        """
        rsd = RequestSettingsDialog(self, self.request, self.icon_manager)
        rsd.settings_updated.connect(self.settings_updated.emit)
        rsd.exec_()

    def remove_tab(self, tab_index):
        """Remove tab.

        Args:
            tab_index: Integer representing index of the current tab
        """
        self.tabs.removeTab(tab_index)

    def add_root_item_to_tree(self, obj):
        """Adds a root item to tree.

        Args:
            obj: Object related to item.

        Return:
              QTreeWidgetItem that was added
        """
        tree_item = QtWidgets.QTreeWidgetItem()
        tree_item.setText(0, "Sample " + "%02d" % obj.serial_number + " " +
                          obj.name)
        self.__change_tab_icon(tree_item, "folder_locked.svg")
        tree_item.setFlags(tree_item.flags() ^ Qt.ItemIsDragEnabled)
        tree_item.obj = obj

        self.treeWidget.addTopLevelItem(tree_item)
        return tree_item

    def __add_item_to_tree(self, parent_item, obj, load_data):
        """Add item to tree where it can be opened.

        Args:
            obj: Object related to item.
            load_data: A boolean representing if data is loaded.
        """
        tree_item = QtWidgets.QTreeWidgetItem()
        tree_item.setText(0, obj.name)
        tree_item.tab_id = self.tab_id
        tree_item.item_name = obj.name
        tree_item.obj = obj
        tree_item.setFlags(tree_item.flags() | Qt.ItemNeverHasChildren)
        tree_item.setFlags(tree_item.flags() ^ Qt.ItemIsDropEnabled)
        tree_item.setFlags(tree_item.flags() | Qt.ItemIsEditable)
        # tree_item.setIcon(0, self.icon_manager.get_icon("folder_open.svg"))
        if load_data:
            self.__change_tab_icon(tree_item, "folder_open.svg")
        else:
            self.__change_tab_icon(tree_item, "folder_locked.svg")
        # self.treeWidget.addTopLevelItem(tree_item)
        parent_item.addChild(tree_item)
        parent_item.setExpanded(True)

    def add_new_tab(self, tab_type, filepath: Path, sample, file_current=0,
                    file_count=1, load_data=False, object_name="",
                    import_evnt_or_binary=False, progress=None):
        """Add new tab into TabWidget.

        Adds a new tab into program's tabWidget. Makes a new measurement or
        simulation for said tab.

        Args:
            tab_type: Either "measurement" or "simulation".
            filepath: A Path representing measurement or simulation file
            path, or data path when creating a new measurement.
            sample: The sample under which the measurement or simulation is put.
            file_current: An integer representing which number is currently
            being read. (for GUI)
            file_count: An integer representing how many files will be loaded.
            load_data: A boolean representing whether to load data or not. This
                is to save time when loading a request and we do not want to
                load every measurement.
            object_name: When creating a new Measurement, this is the name
                for it.
            import_evnt_or_binary: Whether evnt or lst data is being imported
                or not.
            progress: a ProgressReporter object
        """
        try:
            cur_progress = (100 / file_count) * file_current
        except ZeroDivisionError:
            cur_progress = 0
        filepath = Path(filepath)
        rest = (100 - cur_progress) * 0.01

        if progress is not None:
            progress.report(cur_progress)

        if tab_type == "measurement":
            measurement = \
                self.request.samples.measurements.add_measurement_file(
                    sample, filepath, self.tab_id, object_name,
                    import_evnt_or_binary=import_evnt_or_binary,
                    selector_cls=Selector)
            if measurement is not None:
                tab = MeasurementTabWidget(self.tab_id, measurement,
                                           self.icon_manager,
                                           statusbar=self.statusbar)
                tab.issueMaster.connect(self.__master_issue_commands)

                tab.setAttribute(QtCore.Qt.WA_DeleteOnClose)
                self.tab_widgets[self.tab_id] = tab
                tab.add_log()
                tab.data_loaded = load_data
                if load_data:
                    measurement.load_data()

                    if progress is not None:
                        sub_progress = progress.get_sub_reporter(
                            lambda x: cur_progress + rest * x * 0.9
                        )
                    else:
                        sub_progress = None

                    tab.add_histogram(progress=sub_progress)
                    self.tabs.addTab(tab, measurement.name)
                    self.tabs.setCurrentWidget(tab)

                sample_item = self.treeWidget.findItems(
                    "%02d" % sample.serial_number + " " + sample.name,
                    Qt.MatchEndsWith, 0)[0]
                self.__add_item_to_tree(sample_item, measurement, load_data)
                self.tab_id += 1

            return measurement

        if tab_type == "simulation":
            filepath_json = filepath.with_suffix(".mccfg")
            config_manager = ConfigManager()
            config_manager.set_config_file(filepath_json)
            if filepath_json.is_file():
                simulation = self.request.samples.simulations.add_simulation_json(
                    sample, filepath_json, self.tab_id)
            else:
                simulation = self.request.samples.simulations.add_simulation_file(
                    sample, filepath, self.tab_id)

            if simulation is not None:
                tab = SimulationTabWidget(self.request, self.tab_id, simulation,
                                          self.icon_manager,
                                          statusbar=self.statusbar)

                tab.setAttribute(QtCore.Qt.WA_DeleteOnClose)
                tab.add_log()
                self.tab_widgets[self.tab_id] = tab
                tab.data_loaded = load_data
                if load_data:
                    tab.add_simulation_target_and_recoil(
                        settings=self.settings,
                        ion_division=self.settings.get_ion_division(),
                        min_presim_ions=self.settings.get_min_presim_ions(),
                        min_sim_ions=self.settings.get_min_simulation_ions(),
                        settings_updated=self.settings_updated
                    )

                    self.tabs.addTab(tab, simulation.name)
                    self.tabs.setCurrentWidget(tab)

                sample_item = self.treeWidget.findItems(
                    "%02d" % sample.serial_number + " " + sample.name,
                    Qt.MatchEndsWith, 0)[0]
                self.__add_item_to_tree(sample_item, simulation, load_data)
                self.tab_id += 1

    @gutils.block_treewidget_signals
    def __change_tab_icon(self, tree_item, icon="folder_open.svg"):
        """Change tab icon in QTreeWidgetItem.

        Args:
            tree_item: A QtWidgets.QTreeWidgetItem class object.
            icon: A string representing the icon name.
        """
        tree_item.setIcon(0, self.icon_manager.get_icon(icon))

    def __close_request(self):
        """Closes the request for opening a new one.
        """
        if self.request is not None:
            # TODO: Doesn't release memory
            # Clear the treewidget
            self.treeWidget.clear()
            self.tabs.clear()
            self.request.close_log_files()
            self.request = None
            self.tab_widgets = {}
            self.tab_id = 0

    @gutils.block_treewidget_signals
    def __set_slave_status(self, is_slave):
        """Sets the currently selected tree item as either a slave or non-slave

        Args:
            is_slave: whether the item will be a slave or not.
        """
        items = self.treeWidget.selectedItems()
        if not items:
            return
        clicked_item = self.treeWidget.currentItem()

        if is_slave:
            self.request.include_slave(clicked_item.obj)
            clicked_item.setText(0, clicked_item.obj.name + " (slave)")
        else:
            self.request.exclude_slave(clicked_item.obj)
            clicked_item.setText(0, clicked_item.obj.name)

    @gutils.block_treewidget_signals
    def __make_master_measurement(self):
        """Make selected or first of the selected measurements
        a master measurement.
        """
        items = self.treeWidget.selectedItems()
        if not items:
            return
        master_tree = items[0]
        master_tab = self.tab_widgets[master_tree.tab_id]
        self.request.set_master(master_tab.obj)
        # old_master = self.request.get_master()
        nonslaves = self.request.get_nonslaves()

        tree_root = self.treeWidget.invisibleRootItem()
        for i in range(tree_root.childCount()):
            sample_item = tree_root.child(i)
            for j in range(sample_item.childCount()):
                tree_item = sample_item.child(j)
                if isinstance(tree_item.obj, Measurement):
                    tab_widget = self.tab_widgets[tree_item.tab_id]
                    tab_name = tab_widget.obj.name
                    if tree_item.tab_id == master_tab.tab_id:
                        tree_item.setText(0, "{0} (master)".format(tab_name))
                    elif tab_widget.obj in nonslaves:
                        tree_item.setText(0, tab_name)
                    else:
                        tree_item.setText(0, "{0} (slave)".format(tab_name))
                    tab_widget.toggle_master_button()

                for k in range(self.tabs.count()):
                    tab = self.tabs.widget(k)
                    tab_name = tab.obj.name
                    if tab.tab_id == master_tab.tab_id:
                        tab_name = "{0} (master)".format(tab_name)
                        self.tabs.setTabText(tab.tab_id, tab_name)
                    else:
                        self.tabs.setTabText(tab.tab_id, tab_name)

    def __master_issue_commands(self):
        """Issue commands from master measurement to all slave measurements in
        the request.
        """
        reply = QtWidgets.QMessageBox.question(
            self, "Confirmation",
            "You are about to issue actions from master measurement to all "
            "slave measurements in the request. This can take several minutes. "
            "Please wait until notification is shown.\n"
            "Do you wish to continue?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.Yes)
        if reply == QtWidgets.QMessageBox.No:
            return

        time_start = datetime.now()

        sbh = StatusBarHandler(self.statusbar, autoremove=True)

        # TODO add request.get_slaves method?
        nonslaves = self.request.get_nonslaves()
        master = self.request.get_master()
        master_tab = self.tab_widgets[master.tab_id]
        master_name = master.name
        directory_d = master.get_depth_profile_dir()
        directory_e = master.get_energy_spectra_dir()
        directory_c = master.get_composition_changes_dir()

        # Load selections and save cut files
        # TODO: Make a check for these if identical already -> don't redo.
        # Saving selections takes about 20 % of the processing time
        self.request.save_selection(
            master, progress=sbh.reporter.get_sub_reporter(lambda x: 0.2 * x))

        sbh.reporter.report(21)

        self.request.save_cuts(master, progress=sbh.reporter.get_sub_reporter(
            lambda x: 21 + 0.12 * x))

        sbh.reporter.report(33)

        tree_root = self.treeWidget.invisibleRootItem()
        tree_child_count = tree_root.childCount()

        for i in range(tree_child_count):
            sample_item = tree_root.child(i)
            sample_child_count = sample_item.childCount()

            sample_reporter = sbh.reporter.get_sub_reporter(
                lambda x: 33 + 0.67 * (100 * i + x) / tree_child_count
            )
            for j in range(sample_child_count):
                tree_item = sample_item.child(j)

                item_reporter = sample_reporter.get_sub_reporter(
                    lambda x: (100 * j + x) / sample_child_count
                )

                if isinstance(tree_item.obj, Measurement):
                    tab = self.tab_widgets[tree_item.tab_id]
                    tab_obj = tab.obj
                    tab_name = tab_obj.name
                    if tab_name == master_name or tab_obj in nonslaves:
                        continue
                    # Load measurement data if the slave is
                    if not tab.data_loaded:
                        tab.data_loaded = True

                        tab.obj.load_data()
                        item_reporter.report(20)

                        tab.add_histogram(
                            progress=item_reporter.get_sub_reporter(
                                lambda x: 20 + 0.4 * x
                            ))

                        item_reporter.report(60)

                        # Load selection
                        directory = master.get_data_dir()
                        selection_file = Path(directory,
                                              f"{master_name}.selections")
                        tab.obj.selector.load(selection_file)
                        tab.histogram.matplotlib.on_draw()

                        # Save cuts
                        tab.obj.save_cuts(
                            progress=item_reporter.get_sub_reporter(
                                lambda x: 60 + 0.2 * x
                            ))

                        # Update tree item icon to open folder
                        self.__change_tab_icon(tree_item)

                    sample_folder_name = "Sample_" + "%02d" % \
                                         master.sample.serial_number + "-" \
                                         + master.sample.name
                    # Check all widgets of master and do them for slaves.
                    if master_tab.depth_profile_widget and tab.data_loaded:
                        if tab.depth_profile_widget:
                            tab.del_widget(tab.depth_profile_widget)
                        tab.make_depth_profile(directory_d, master_name,
                                               master.serial_number,
                                               sample_folder_name)
                        tab.depth_profile_widget.save_to_file()

                    item_reporter.report(80)

                    if master_tab.elemental_losses_widget and tab.data_loaded:
                        if tab.elemental_losses_widget:
                            tab.del_widget(tab.elemental_losses_widget)
                        tab.make_elemental_losses(directory_c, master_name,
                                                  master.serial_number,
                                                  sample_folder_name)
                        tab.elemental_losses_widget.save_to_file()

                    item_reporter.report(90)

                    if master_tab.energy_spectrum_widget and tab.data_loaded:
                        if tab.energy_spectrum_widget:
                            tab.del_widget(tab.energy_spectrum_widget)
                        tab.make_energy_spectrum(directory_e, master_name,
                                                 master.serial_number,
                                                 sample_folder_name)
                        tab.energy_spectrum_widget.save_to_file()

                item_reporter.report(100)

        sbh.reporter.report(100)

        time_end = datetime.now()
        time_duration = (time_end - time_start).seconds
        time_str = timedelta(seconds=time_duration)
        QtWidgets.QMessageBox.question(
            self, "Notification",
            "Master measurement's actions have been issued to slaves. \n"
            "Elapsed time: {0}".format(time_str),
            QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)

    def __open_info_tab(self):
        """Opens an info tab to the QTabWidget 'tab_measurements' that guides
        the user to add a new measurement to the request.
        """
        self.tabs.addTab(self.infoTab, "Info")

    def __remove_introduction_tab(self):
        """Removes an info tab from the QTabWidget 'tab_measurements' that
        guides the user to create a new request.
        """
        index = self.tabs.indexOf(self.introduceTab)
        if index >= 0:
            self.tabs.removeTab(index)

    @gutils.block_treewidget_signals
    def __remove_master_measurement(self):
        """Remove master measurement
        """
        old_master = self.request.get_master()
        self.request.set_master()  # No master measurement

        tree_root = self.treeWidget.invisibleRootItem()
        for i in range(tree_root.childCount()):
            sample_item = tree_root.child(i)
            for j in range(sample_item.childCount()):
                tree_item = sample_item.child(j)
                if isinstance(tree_item.obj, Measurement):
                    tab_widget = self.tab_widgets[tree_item.tab_id]
                    tab_name = tab_widget.obj.name
                    tree_item.setText(0, tab_name)
                    tab_widget.toggle_master_button()

        if old_master:
            measurement_name = old_master.name
            self.tabs.setTabText(old_master.tab_id, measurement_name)
            old_master_tab = self.tab_widgets[old_master.tab_id]
            old_master_tab.toggle_master_button()
        self.request.set_master()  # No master measurement

    def __remove_info_tab(self):
        """Removes an info tab from the QTabWidget 'tab_measurements' that
        guides the user to add a new measurement to the request.
        """
        index = self.tabs.indexOf(self.infoTab)
        if index >= 0:
            self.tabs.removeTab(index)

    def __set_icons(self):
        """Adds icons to the main window.
        """
        self.icon_manager.set_icon(self.requestSettingsButton, "gear.svg")
        self.icon_manager.set_icon(self.globalSettingsButton, "gear.svg")
        self.icon_manager.set_icon(self.actionNew_Request, "file.svg")
        self.icon_manager.set_icon(self.actionOpen_Request, "folder_open.svg")
        self.icon_manager.set_icon(self.actionSave_Request, "amarok_save.svg")
        self.icon_manager.set_icon(self.actionNew_Measurement, "log.svg")
        self.icon_manager.set_icon(self.actionNew_Simulation,
                                   "new_simulation.png")

    def __set_request_buttons_enabled(self, state=False):
        """Enables 'request settings', 'save request' and 'new measurement'
        buttons.
           Enables simulation related buttons.
        Args:
            state: True/False enables or disables buttons
        """
        self.requestSettingsButton.setEnabled(state)
        self.actionSave_Request.setEnabled(state)
        self.actionNew_Measurement.setEnabled(state)
        self.actionNew_measurement_2.setEnabled(state)
        self.menuImport.setEnabled(state)
        self.actionRequest_Settings.setEnabled(state)
        # TODO: Should these only be enabled when there is measurement open?
        self.actionAnalyze_elemental_losses.setEnabled(state)
        self.actionCreate_energy_spectrum.setEnabled(state)
        self.actionCreate_depth_profile.setEnabled(state)

        # enable simulation buttons
        self.actionNew_Simulation.setEnabled(state)
        self.actionNew_Simulation_2.setEnabled(state)

        # enable simulation energy spectra button
        self.actionCreate_energy_spectrum_sim.setEnabled(state)

    def __tab_exists(self, tab_id):
        """Check if there is an open tab with the tab_id (identifier).

        Args:
            tab_id: Identifier (int) for the MeasurementTabWidget

        Returns:
            True if tab is found, False if not
        """
        # Try to find the clicked item from QTabWidget.
        for i in range(0, self.tabs.count()):
            if self.tabs.widget(i).tab_id == tab_id:
                return True
        return False

    def __open_manual(self):
        """Open user manual.
        """
        manual_filename = gf.get_root_dir() / "documentation" / "Potku-User-Manual.pdf"
        self.__open_file(manual_filename)        

    def __open_data_help(self):
        """Open data help file.
        """        
        data_help_filename = gf.get_root_dir() / "documentation" / "Potku_data_explained.pdf"
        self.__open_file(data_help_filename)
                
    def __open_file(self, filepath):
        """Opens file from filepath. 
        
        Args: 
                filepath: Path of the file                
        """
        # TODO changed the file path to point to the manual, I guess this needs
        #      to be updated in the .spec file too?
        used_os = platform.system()
        try:
            if used_os == "Windows":
                os.startfile(filepath)
            elif used_os == "Linux":
                subprocess.call(("xdg-open", filepath))
            elif used_os == "Darwin":
                subprocess.call(("open", filepath))
        except OSError:
            QtWidgets.QMessageBox.critical(
                self, "Not found",
                "There is no file to be found!",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)                     


def main():
    """Main function
    """
    app = QtWidgets.QApplication(sys.argv)
    window = Potku()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
