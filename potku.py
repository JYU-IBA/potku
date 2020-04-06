# coding=utf-8
"""
Created on 21.3.2013
Updated on 24.8.2018

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

__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen \n Samuli " \
             "Rahkonen \n Miika Raunio \n Severi Jääskeläinen \n Samuel " \
             "Kaiponen \n Heta Rekilä \n Sinikka Siironen"
__version__ = "2.0"

import gc
import os
import platform
import shutil
import subprocess
import sys

import dialogs.dialog_functions as df
import widgets.input_validation as iv

from datetime import datetime
from datetime import timedelta
from pathlib import Path

from dialogs.about import AboutDialog
from dialogs.global_settings import GlobalSettingsDialog
from dialogs.measurement.import_binary import ImportDialogBinary
from dialogs.measurement.import_measurement import ImportMeasurementsDialog
from dialogs.measurement.load_measurement import LoadMeasurementDialog
from dialogs.new_request import RequestNewDialog
from dialogs.request_settings import RequestSettingsDialog
from dialogs.simulation.new_simulation import SimulationNewDialog
from dialogs.file_dialogs import open_file_dialog

from widgets.gui_utils import GUIReporter
from widgets.icon_manager import IconManager

from modules.general_functions import remove_file
from modules.general_functions import rename_file
from modules.global_settings import GlobalSettings
from modules.measurement import Measurement
from modules.request import Request
from modules.simulation import Simulation

from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAbstractItemView
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QTreeWidgetItem

from widgets.measurement.tab import MeasurementTabWidget
from widgets.simulation.tab import SimulationTabWidget


class Potku(QtWidgets.QMainWindow):
    """Potku is main window class.
    """

    def __init__(self):
        """Init main window for Potku.
        """
        super().__init__()
        # TODO remove ui reference
        self.ui = uic.loadUi(Path("ui_files", "ui_main_window.ui"), self)

        self.title = self.ui.windowTitle()
        self.ui.treeWidget.setHeaderLabel("")

        self.icon_manager = IconManager()
        self.settings = GlobalSettings()
        self.request = None
        self.potku_bin_dir = os.getcwd()

        # Holds references to all the tab widgets in "tab_measurements"
        # (even when they are removed from the QTabWidget)
        self.tab_widgets = {}
        self.tab_id = 0  # identification for each tab

        # Set up connections within UI
        self.ui.actionNew_Measurement.triggered.connect(
            self.open_new_measurement)
        self.ui.requestSettingsButton.clicked.connect(
            self.open_request_settings)
        self.ui.globalSettingsButton.clicked.connect(self.open_global_settings)
        self.ui.tabs.tabCloseRequested.connect(self.remove_tab)
        self.ui.treeWidget.itemDoubleClicked.connect(self.focus_selected_tab)

        self.ui.requestNewButton.clicked.connect(self.make_new_request)
        self.ui.requestOpenButton.clicked.connect(self.open_request)
        self.ui.actionNew_Request.triggered.connect(self.make_new_request)
        self.ui.actionOpen_Request.triggered.connect(self.open_request)
        self.ui.addNewMeasurementButton.clicked.connect(
            self.open_new_measurement)
        self.ui.actionNew_measurement_2.triggered.connect(
            self.open_new_measurement)
        self.ui.actionImport_pelletron.triggered.connect(self.import_pelletron)
        self.ui.actionBinary_data_lst.triggered.connect(self.import_binary)
        self.ui.action_manual.triggered.connect(self.__open_manual)

        self.ui.actionSave_cuts.triggered.connect(
            self.current_measurement_save_cuts)
        self.ui.actionAnalyze_elemental_losses.triggered.connect(
            self.current_measurement_analyze_elemental_losses)
        self.ui.actionCreate_energy_spectrum.triggered.connect(
            self.current_measurement_create_energy_spectrum)
        self.ui.actionCreate_depth_profile.triggered.connect(
            self.current_measurement_create_depth_profile)
        self.ui.actionGlobal_Settings.triggered.connect(
            self.open_global_settings)
        self.ui.actionRequest_Settings.triggered.connect(
            self.open_request_settings)
        self.ui.actionAbout.triggered.connect(self.open_about_dialog)

        self.ui.actionNew_Request_2.triggered.connect(self.make_new_request)
        self.ui.actionOpen_Request_2.triggered.connect(self.open_request)
        self.ui.actionExit.triggered.connect(self.closeEvent)  # Should
        # save changes

        self.ui.menuImport.setEnabled(False)

        # Show or hide left panel depending on the previous usage
        df.set_up_side_panel(self, "left_panel_shown", "left")

        # Set up simulation connections within UI
        self.ui.actionNew_Simulation.triggered.connect(
            self.create_new_simulation)
        self.ui.actionNew_Simulation_2.triggered.connect(
            self.create_new_simulation)
        self.ui.actionCreate_energy_spectrum_sim.triggered.connect(
            self.current_simulation_create_energy_spectrum)
        self.ui.addNewSimulationButton.clicked.connect(
            self.create_new_simulation)

        # Set up report tool connection in UI
        self.ui.actionCreate_report.triggered.connect(self.create_report)

        # Set up styles for main window
        # Cannot use os.path.join (PyQT+css)
        bg_blue = "images/background_blue.svg"
        bg_green = "images/background_green.svg"
        style_intro = "QWidget#introduceTab {border-image: url(" \
                      + bg_blue + ");}"
        style_mesinfo = ("QWidget#infoTab {border-image: url(" +
                         bg_green + ");}")
        self.ui.introduceTab.setStyleSheet(style_intro)
        self.ui.infoTab.setStyleSheet(style_mesinfo)
        self.__remove_info_tab()

        self.ui.setWindowIcon(self.icon_manager.get_icon("potku_icon.ico"))

        # Set main window's icons to place
        self.__set_icons()
        self.ui.showMaximized()

    def __initialize_tree_view(self):
        """Inits the tree view and creates the top level items.
        """
        self.tree_widget = self.ui.treeWidget
        self.tree_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_widget.customContextMenuRequested.connect(self.__open_menu)
        self.tree_widget.setDropIndicatorShown(True)
        self.tree_widget.setDragDropMode(QAbstractItemView.InternalMove)
        # Disable dragging since it doesn't do anything yet
        # TODO: Dragging changes the order of the items in tree and directory
        self.tree_widget.setDragEnabled(False)
        self.tree_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tree_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tree_widget.itemChanged[QTreeWidgetItem, int].connect(
            self.__rename_dir)

    def __open_menu(self, position):
        """Opens the right click menu in tree view.
        """
        indexes = self.tree_widget.selectedIndexes()
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

        if isinstance(self.tree_widget.currentItem().obj, Measurement):
            menu.addAction("Make master", self.__make_master_measurement)
            menu.addAction("Remove master", self.__remove_master_measurement)
            menu.addAction("Exclude from slaves",
                           self.__make_nonslave_measurement)
            menu.addAction("Include as slave", self.__make_slave_measurement)

        menu.exec_(self.tree_widget.viewport().mapToGlobal(position))

    def __rename_tree_item(self):
        """Renames selected tree item in tree view and in folder structure.
        """
        clicked_item = self.tree_widget.currentItem()
        self.tree_widget.editItem(clicked_item)

    def __rename_dir(self):
        """Renames object based on selected tree item. This method is called
        when tree item is changed.
        """
        clicked_item = self.tree_widget.currentItem()

        if clicked_item:
            regex = "^[A-Za-z0-9-ÖöÄäÅå]+"
            valid_text = iv.validate_text_input(clicked_item.text(0), regex)

            if valid_text != clicked_item.text(0):
                QtWidgets.QMessageBox.information(
                    self, "Notice", "You can't use special characters other "
                                    "than '-' in the name.",
                    QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
                clicked_item.setText(0, clicked_item.obj.name)
                return

            if valid_text == "":
                self.tree_widget.blockSignals(True)
                clicked_item.setText(0, clicked_item.obj.name)
                self.tree_widget.blockSignals(False)
                return

            if valid_text == clicked_item.obj.name:
                clicked_item.setText(0, clicked_item.obj.name)
                return

            new_name = valid_text
            try:
                # TODO function that returns full name of Simu/Mesu
                new_path = clicked_item.obj.name_prefix + "%02d" % \
                    clicked_item.obj.serial_number + "-" + new_name

                # Close and remove logs
                clicked_item.obj.remove_and_close_log(
                    clicked_item.obj.defaultlog)
                clicked_item.obj.remove_and_close_log(clicked_item.obj.errorlog)

                new_dir = rename_file(clicked_item.obj.directory, new_path)
            except OSError:
                QtWidgets.QMessageBox.critical(self, "Error",
                                               "A file or folder already exists"
                                               " on name " + new_name,
                                               QtWidgets.QMessageBox.Ok,
                                               QtWidgets.QMessageBox.Ok)
                # Block edit event from tree view when changing the name back
                # to original.
                self.tree_widget.blockSignals(True)
                clicked_item.setText(0, clicked_item.obj.name)
                self.tree_widget.blockSignals(False)
                return
            self.tree_widget.blockSignals(True)
            clicked_item.obj.name = new_name
            clicked_item.setText(0, clicked_item.obj.name)

            clicked_item.obj.update_directory_references(new_dir)

            if type(clicked_item.obj) is Measurement:
                try:
                    clicked_item.obj.rename_info_file(new_name)
                    clicked_item.obj.info_to_file(
                        os.path.join(new_dir, clicked_item.obj.name
                                     + ".info"))
                except OSError:
                    QtWidgets.QMessageBox.critical(self, "Error",
                                                   "Something went wrong while "
                                                   "renaming info file.",
                                                   QtWidgets.QMessageBox.Ok,
                                                   QtWidgets.QMessageBox.Ok)

                # Rename all cut files
                try:
                    clicked_item.obj.rename_files_in_directory(
                        clicked_item.obj.directory_cuts)
                except OSError:
                    QtWidgets.QMessageBox.critical(self, "Error",
                                                   "Something went wrong while "
                                                   "renaming cuts.",
                                                   QtWidgets.QMessageBox.Ok,
                                                   QtWidgets.QMessageBox.Ok)
                # Rename all split files
                try:
                    clicked_item.obj.rename_files_in_directory(os.path.join(
                        clicked_item.obj.directory_composition_changes,
                        "Changes"))
                except OSError:
                    QtWidgets.QMessageBox.critical(self, "Error",
                                                   "Something went wrong while "
                                                   "renaming splits.",
                                                   QtWidgets.QMessageBox.Ok,
                                                   QtWidgets.QMessageBox.Ok)

                # Update Energy spectrum, Composition changes and Depth profile
                # save files.
                for i in range(self.ui.tabs.count()):
                    tab_widget = self.ui.tabs.widget(i)
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
                        self.ui.tabs.insertTab(i, tab_widget,
                                               clicked_item.obj.name)
                        self.ui.tabs.setCurrentWidget(tab_widget)
                        break

            elif type(clicked_item.obj) is Simulation:
                try:
                    clicked_item.obj.rename_simulation_file()
                    clicked_item.obj.to_file(
                        os.path.join(new_dir, clicked_item.obj.name
                                     + ".simulation"))
                except OSError:
                    QtWidgets.QMessageBox.critical(self, "Error",
                                                   "Something went wrong while "
                                                   "renaming info file.",
                                                   QtWidgets.QMessageBox.Ok,
                                                   QtWidgets.QMessageBox.Ok)

                # Update Tab name
                for i in range(self.ui.tabs.count()):
                    tab_widget = self.ui.tabs.widget(i)
                    if tab_widget.obj is clicked_item.obj:
                        self.remove_tab(i)
                        self.ui.tabs.insertTab(i, tab_widget,
                                               clicked_item.obj.name)
                        self.ui.tabs.setCurrentWidget(tab_widget)
                        break

            self.tree_widget.blockSignals(False)

    def __remove_tree_item(self):
        """Removes selected tree item in tree view and in folder structure.
        """
        clicked_item = self.tree_widget.currentItem()

        if clicked_item:
            if type(clicked_item.obj) is Measurement:
                obj_type = "measurement"
            elif type(clicked_item.obj) is Simulation:
                obj_type = "simulation"
            else:
                obj_type = ""  # TODO: place for sample type checking.
            reply = QtWidgets.QMessageBox.question(self, "Confirmation",
                                                   "Deleting selected " +
                                                   obj_type + " will delete"
                                                   " all files and folders "
                                                   "under selected " +
                                                   obj_type + " directory."
                                                   "\n\nAre you sure you want "
                                                   "to delete selected "
                                                   + obj_type + "?",
                                                   QtWidgets.QMessageBox.Yes |
                                                   QtWidgets.QMessageBox.No |
                                                   QtWidgets.QMessageBox.Cancel,
                                                   QtWidgets.QMessageBox.Cancel)
            if reply == QtWidgets.QMessageBox.No or reply == \
                    QtWidgets.QMessageBox.Cancel:
                return  # If clicked Yes, then continue normally

            # Remove object from Sample
            clicked_item.parent().obj.remove_obj(clicked_item.obj)
            clicked_item.obj.defaultlog.close()
            clicked_item.obj.errorlog.close()

            # Remove object directory
            remove_file(clicked_item.obj.directory)

            # Remove object from tree
            self.tree_widget.blockSignals(True)
            clicked_item.parent().removeChild(clicked_item)
            self.tree_widget.blockSignals(False)

            # Remove object tab
            for i in range(self.ui.tabs.count()):
                if self.ui.tabs.widget(i).obj is clicked_item.obj:
                    self.ui.tabs.removeTab(i)
                    break
            self.tab_widgets.pop(clicked_item.obj.tab_id)

    def closeEvent(self, event):
        """
        Save recoil elements and simulation targets and close the program.
        """
        if self.request:
            for sample in self.request.samples.samples:
                for simulation in sample.simulations.simulations.values():
                    for elem_sim in simulation.element_simulations:
                        for recoil_element in elem_sim.recoil_elements:
                            recoil_element.to_file(elem_sim.directory)
                    simulation.target.to_file(
                        os.path.join(simulation.directory,
                                     simulation.target.name + ".target"), None)
        self.close()

    def create_report(self):
        """
        Opens a dialog for making a report.
        """
        # TODO: Replace this with the actual dialog call.
        QtWidgets.QMessageBox.critical(self, "Error",
                                       "Report tool not yet implemented!",
                                       QtWidgets.QMessageBox.Ok,
                                       QtWidgets.QMessageBox.Ok)

    def current_measurement_create_depth_profile(self):
        """Opens the depth profile analyzation tool for the current open
        measurement tab widget.
        """
        widget = self.ui.tabs.currentWidget()
        if isinstance(widget, MeasurementTabWidget):
            widget.open_depth_profile()
        else:
            QtWidgets.QMessageBox.question(self, "Notification",
                                           "An open measurement is required to "
                                           "do this action.",
                                           QtWidgets.QMessageBox.Ok,
                                           QtWidgets.QMessageBox.Ok)

    def current_measurement_analyze_elemental_losses(self):
        """Opens the element losses analyzation tool for the current open
        measurement tab widget.
        """
        widget = self.ui.tabs.currentWidget()
        if isinstance(widget, MeasurementTabWidget):
            widget.open_element_losses()
        else:
            QtWidgets.QMessageBox.question(self, "Notification",
                                           "An open measurement is required to"
                                           " do this action.",
                                           QtWidgets.QMessageBox.Ok,
                                           QtWidgets.QMessageBox.Ok)

    def current_measurement_create_energy_spectrum(self):
        """Opens the energy spectrum analyzation tool for the current open
        measurement tab widget.
        """
        widget = self.ui.tabs.currentWidget()
        if isinstance(widget, MeasurementTabWidget):
            widget.open_energy_spectrum()
        else:
            QtWidgets.QMessageBox.question(self, "Notification",
                                           "An open measurement is required to"
                                           " do this action.",
                                           QtWidgets.QMessageBox.Ok,
                                           QtWidgets.QMessageBox.Ok)

    def current_measurement_save_cuts(self):
        """Saves the current open measurement tab widget's selected cuts
        to cut files.
        """
        widget = self.ui.tabs.currentWidget()
        if isinstance(widget, MeasurementTabWidget):
            widget.measurement_save_cuts()
        else:
            QtWidgets.QMessageBox.question(self, "Notification",
                                           "An open measurement is required to"
                                           " do this action.",
                                           QtWidgets.QMessageBox.Ok,
                                           QtWidgets.QMessageBox.Ok)

    def current_simulation_create_energy_spectrum(self):
        """
        Opens the energy spectrum analyzation tool for the current open
        simulation tab widget.
        """
        widget = self.ui.tabs.currentWidget()
        if isinstance(widget, MeasurementTabWidget):
            widget.open_energy_spectrum()
        else:
            QtWidgets.QMessageBox.question(self, "Notification",
                                           "An open simulation is required to "
                                           "do this action.",
                                           QtWidgets.QMessageBox.Ok,
                                           QtWidgets.QMessageBox.Ok)

    def delete_selections(self):
        """Deletes the selected tree widget items.
        """
        # TODO: Memory isn't released correctly. Maybe because of matplotlib.
        selected_tabs = [self.tab_widgets[item.tab_id] for
                         item in self.ui.treeWidget.selectedItems()]
        if selected_tabs:  # Ask user a confirmation.
            reply = QtWidgets.QMessageBox.question(self, "Confirmation",
                                                   "Deleting selected "
                                                   "measurements will delete"
                                                   " all files and folders "
                                                   "under selected measurement "
                                                   "directories."
                                                   "\n\nAre you sure you want "
                                                   "to delete selected "
                                                   "measurements?",
                                                   QtWidgets.QMessageBox.Yes |
                                                   QtWidgets.QMessageBox.No |
                                                   QtWidgets.QMessageBox.Cancel,
                                                   QtWidgets.QMessageBox.Cancel)
            if reply == QtWidgets.QMessageBox.No or reply == \
                    QtWidgets.QMessageBox.Cancel:
                return  # If clicked Yes, then continue normally

        for tab in selected_tabs:
            measurement = self.request.samples.measurements.get_key_value(
                tab.tab_id)
            try:
                # Close and remove logs
                measurement.remove_and_close_log(measurement.defaultlog)
                measurement.remove_and_close_log(measurement.errorlog)

                # Remove measurement's directory tree
                shutil.rmtree(measurement.directory)
                os.remove(os.path.join(self.request.directory,
                                       measurement.measurement_file))
            except:
                print("Error with removing files")
                QtWidgets.QMessageBox.question(self, "Confirmation",
                                               "Problem with deleting files.",
                                               QtWidgets.QMessageBox.Ok,
                                               QtWidgets.QMessageBox.Ok)
                # TODO check that this is the intented way of setting the
                #  loggers in case something went wrong.
                measurement.set_loggers(measurement.directory,
                                        measurement.request.directory)
                return

            self.request.samples.measurements.remove_by_tab_id(tab.tab_id)
            remove_index = self.ui.tabs.indexOf(tab)
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
        root = self.ui.treeWidget.invisibleRootItem()
        for item in self.ui.treeWidget.selectedItems():
            (item.parent() or root).removeChild(item)
        gc.collect()  # Suggest garbage collector to clean.

    def focus_selected_tab(self, clicked_item):
        """Focus to selected tab (in tree widget) and if it isn't open, open it.

        Args:
            clicked_item: TreeWidgetItem with tab_id attribute (int) that
            connects the item to the corresponding MeasurementTabWidget
        """

        # Blocking signals from tree view to prevent edit event
        self.tree_widget.blockSignals(True)

        try:
            tab_id = clicked_item.tab_id
            tab = self.tab_widgets[tab_id]

            if type(tab) is MeasurementTabWidget:
                name = tab.obj.name

                # Check that the data is read.
                if not tab.data_loaded:
                    tab.data_loaded = True
                    progress_bar = QtWidgets.QProgressBar()
                    self.statusbar.addWidget(progress_bar, 1)
                    progress_bar.show()
                    progress_bar.setValue(5)
                    QtCore.QCoreApplication.processEvents(
                        QtCore.QEventLoop.AllEvents)

                    tab.obj.load_data()
                    progress_bar.setValue(35)
                    QtCore.QCoreApplication.processEvents(
                        QtCore.QEventLoop.AllEvents)

                    tab.add_histogram(GUIReporter(progress_bar))

                    progress_bar.setValue(65)
                    QtCore.QCoreApplication.processEvents(
                        QtCore.QEventLoop.AllEvents)
                    # Load previous states.
                    tab.check_previous_state_files(progress_bar)
                    progress_bar.setValue(100)
                    QtCore.QCoreApplication.processEvents(
                        QtCore.QEventLoop.AllEvents)

                    self.statusbar.removeWidget(progress_bar)
                    progress_bar.hide()

                    self.__change_tab_icon(clicked_item)
                    master_mea = tab.obj.request.get_master()
                    if master_mea and tab.obj.name == master_mea.name:
                        name = "{0} (master)".format(name)

            elif type(tab) is SimulationTabWidget:
                name = tab.obj.name

                # Check that the data is read.
                if not tab.data_loaded:
                    tab.data_loaded = True
                    progress_bar = QtWidgets.QProgressBar()
                    self.statusbar.addWidget(progress_bar, 1)
                    progress_bar.show()

                    tab.add_simulation_target_and_recoil(progress_bar)

                    tab.check_previous_state_files(progress_bar)

                    progress_bar.setValue(100)
                    QtCore.QCoreApplication.processEvents(
                        QtCore.QEventLoop.AllEvents)

                    self.statusbar.removeWidget(progress_bar)
                    progress_bar.hide()

                    self.__change_tab_icon(clicked_item)
            else:
                raise TabError("No such tab widget")

            # Check that the tab to be focused exists.
            if not self.__tab_exists(tab_id):
                self.ui.tabs.addTab(tab, name)
            self.ui.tabs.setCurrentWidget(tab)

        except AttributeError:
            pass
        self.tree_widget.blockSignals(False)

    def import_pelletron(self):
        """Import Pelletron's measurements into request.

        Import Pelletron's measurements from
        """
        if not self.request:
            return
        # For loading measurements.
        import_dialog = ImportMeasurementsDialog(self.request,
                                                 self.icon_manager,
                                                 self.statusbar,
                                                 self)
        if import_dialog.imported:
            self.__remove_info_tab()

    def import_binary(self):
        """Import binary measurements into request.

        Import binary measurements from
        """
        if not self.request:
            return
        import_dialog = ImportDialogBinary(self.request,
                                           self.icon_manager,
                                           self.statusbar,
                                           self)  # For loading measurements.
        if import_dialog.imported:
            self.__remove_info_tab()

    def load_request_measurements(self, measurements=None):
        """Load measurement files in the request.

        Args:
            measurements: A list representing loadable measurements when
            importing measurements to the request.
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
        progress_bar = QtWidgets.QProgressBar()
        self.statusbar.addWidget(progress_bar, 1)
        progress_bar.show()

        count = len(samples_with_measurements)
        dirtyinteger = 0
        for sample, measurements in samples_with_measurements.items():
            for measurement_file in measurements:
                self.add_new_tab("measurement", measurement_file, sample,
                                 progress_bar, dirtyinteger, count,
                                 load_data=load_data)
                dirtyinteger += 1

        self.statusbar.removeWidget(progress_bar)
        progress_bar.hide()

    def load_request_samples(self):
        """"Load sample files in the request.
        """
        sample_paths_in_request = self.request.get_samples_files()
        if sample_paths_in_request:
            for sample_path in sample_paths_in_request:
                sample = self.request.samples.add_sample(sample_path)
                self.add_root_item_to_tree(sample)
            self.request.increase_running_int_by_1()

    def load_request_simulations(self, simulations=None):
        """Load simulation files in the request.

        Args:
            simulations: A list representing loadable simulation when importing
                          simulation to the request.
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
        progress_bar = QtWidgets.QProgressBar()
        self.statusbar.addWidget(progress_bar, 1)
        progress_bar.show()

        count = len(samples_with_simulations)
        dirtyinteger = 0
        for sample, simulations in samples_with_simulations.items():
            for simulation_file in simulations:
                self.add_new_tab("simulation", simulation_file, sample,
                                 progress_bar, dirtyinteger, count,
                                 load_data=load_data)
                dirtyinteger += 1

        self.statusbar.removeWidget(progress_bar)
        progress_bar.hide()

    def make_new_request(self):
        """Opens a dialog for creating a new request.
        """
        # The directory for request is already created after this
        dialog = RequestNewDialog(self)

        # TODO: regex check for directory. I.E. do not allow asd/asd
        if dialog.directory:
            self.__close_request()
            title = "{0} - Request: {1}".format(self.title, dialog.name)
            self.ui.setWindowTitle(title)

            self.ui.treeWidget.setHeaderLabel(
                "Request: {0}".format(dialog.name))
            self.__initialize_tree_view()

            self.request = Request(dialog.directory, dialog.name, self.settings,
                                   self.tab_widgets)
            self.settings.set_request_directory_last_open(dialog.directory)
            # Request made, close introduction tab
            self.__remove_introduction_tab()
            self.__open_info_tab()
            self.__set_request_buttons_enabled(True)

    def open_about_dialog(self):
        """Show Potku program about dialog.
        """
        AboutDialog()

    def open_global_settings(self):
        """Opens global settings dialog.
        """
        GlobalSettingsDialog(self.settings)

    def open_new_measurement(self):
        """Opens file an open dialog and if filename is given opens new
        measurement from it.
        """
        if not self.request:
            return

        dialog = LoadMeasurementDialog(self.request.samples.samples,
                                       self.request.directory)
        sample_name = dialog.sample

        if dialog.filename:
            try:
                self.ui.tabs.removeTab(self.ui.tabs.indexOf(
                    self.measurement_info_tab))
            except:
                pass  # If there is no info tab, no need to worry about.
            progress_bar = QtWidgets.QProgressBar()
            self.statusbar.addWidget(progress_bar, 1)
            progress_bar.show()

            try:
                sample_item = (self.tree_widget.findItems(sample_name,
                                                          Qt.MatchEndsWith,
                                                          0))[0]
            except Exception as e:
                # Sample is not yet in the tree, so add it
                self.__add_sample(sample_name)

            sample_item = (self.tree_widget.findItems(sample_name,
                                                      Qt.MatchEndsWith, 0))[0]

            self.add_new_tab("measurement", dialog.filename,
                             sample_item.obj,
                             progress_bar, load_data=True,
                             object_name=dialog.name)
            self.__remove_info_tab()
            self.statusbar.removeWidget(progress_bar)
            progress_bar.hide()

    def create_new_simulation(self):
        """
        Opens a dialog for creating a new simulation.
        """
        dialog = SimulationNewDialog(self.request.samples.samples)

        simulation_name = dialog.name
        sample_name = dialog.sample
        if simulation_name and sample_name:
            progress_bar = QtWidgets.QProgressBar()
            self.statusbar.addWidget(progress_bar, 1)
            progress_bar.show()

            try:
                sample_item = (self.tree_widget.findItems(sample_name,
                                                          Qt.MatchEndsWith,
                                                          0))[0]
            except Exception as e:
                # Sample is not yet in the tree, so add it
                self.__add_sample(sample_name)

            sample_item = (self.tree_widget.findItems(sample_name,
                                                      Qt.MatchEndsWith, 0))[0]

            serial_number = sample_item.obj.get_running_int_simulation()
            sample_item.obj.increase_running_int_simulation_by_1()

            self.add_new_tab("simulation", os.path.join(
                self.request.directory, sample_item.obj.directory,
                Simulation.directory_prefix + "%02d" % serial_number + "-" +
                dialog.name,
                dialog.name + ".simulation"), sample_item.obj, progress_bar,
                               load_data=True)
            self.__remove_info_tab()
            self.statusbar.removeWidget(progress_bar)
            progress_bar.hide()

    def __add_sample(self, sample_name):
        """Creates a new Sample object and adds it to tree view.

        Args:
            sample_name: Sample name.
        """
        sample = self.request.samples.add_sample(name=sample_name)
        self.add_root_item_to_tree(sample)

    def open_request(self):
        """Shows a dialog to open a request.
        """
        file = open_file_dialog(self,
                                self.settings.get_request_directory_last_open(),
                                "Open an existing request",
                                "Request file (*.request)")
        if file:
            self.__close_request()
            folder = os.path.split(file)[0]
            folders = folder.split("/")
            fd_with_correct_sep = os.sep.join(folders)
            tmp_name = os.path.splitext(os.path.basename(file))[0]
            self.request = Request(fd_with_correct_sep, tmp_name,
                                   self.settings, self.tab_widgets)
            self.ui.setWindowTitle("{0} - Request: {1}".format(
                self.title,
                self.request.get_name()))
            self.ui.treeWidget.setHeaderLabel(
                "Request: {0}".format(self.request.get_name()))
            self.__initialize_tree_view()
            self.settings.set_request_directory_last_open(folder)

            self.load_request_samples()
            self.load_request_measurements()
            self.load_request_simulations()
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
                    sample_item = (self.tree_widget.findItems(
                        "%02d" % sample.serial_number + " " + sample.name,
                        Qt.MatchEndsWith,
                        0))[0]
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

    def open_request_settings(self):
        """Opens request settings dialog.
        """
        RequestSettingsDialog(self, self.request, self.icon_manager)

    def remove_tab(self, tab_index):
        """Remove tab.

        Args:
            tab_index: Integer representing index of the current tab
        """
        self.ui.tabs.removeTab(tab_index)

    def add_root_item_to_tree(self, obj):
        """Adds a root item to tree.

        Args:
            obj: Object related to item.
        """
        tree_item = QtWidgets.QTreeWidgetItem()
        tree_item.setText(0, "Sample " + "%02d" % obj.serial_number + " " +
                          obj.name)
        self.__change_tab_icon(tree_item, "folder_locked.svg")
        tree_item.setFlags(tree_item.flags() ^ Qt.ItemIsDragEnabled)
        tree_item.obj = obj

        self.tree_widget.addTopLevelItem(tree_item)

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
        # self.ui.treeWidget.addTopLevelItem(tree_item)
        parent_item.addChild(tree_item)
        parent_item.setExpanded(True)

    def add_new_tab(self, tab_type, filepath, sample, progress_bar=None,
                    file_current=0, file_count=1, load_data=False,
                    object_name="", import_evnt_or_binary=False):
        """Add new tab into TabWidget.

        Adds a new tab into program's tabWidget. Makes a new measurement or
        simulation for said tab.

        Args:
            tab_type: Either "measurement" or "simulation".
            filepath: A string representing measurement or simulation file
            path, or data path when creating a new measurement.
            sample: The sample under which the measurement or simulation is put.
            progress_bar: A QtWidgets.QProgressBar to be updated.
            file_current: An integer representing which number is currently
            being read. (for GUI)
            file_count: An integer representing how many files will be loaded.
            load_data: A boolean representing whether to load data or not. This
            is to save time when loading a request and we do not want to load
            every measurement.
            object_name: When creating a new Measurement, this is the name
            for it.
            import_evnt_or_binary: Whether evnt or lst data is being imported
            or not.
        """
        if progress_bar is not None:
            progress_bar.setValue((100 / file_count) * file_current)
            QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents)

        if tab_type == "measurement":
            measurement = \
                self.request.samples.measurements.add_measurement_file(
                    sample, filepath, self.tab_id, object_name,
                    import_evnt_or_binary=import_evnt_or_binary)
            if measurement == "already exists":
                return None
            if measurement:
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

                    tab.add_histogram(GUIReporter(progress_bar))    # TODO
                    self.ui.tabs.addTab(tab, measurement.name)
                    self.ui.tabs.setCurrentWidget(tab)

                    if progress_bar:
                        progress_bar.setValue(100)
                        QtCore.QCoreApplication.processEvents(
                            QtCore.QEventLoop.AllEvents)

                sample_item = (self.tree_widget.findItems(
                    "%02d" % sample.serial_number + " " + sample.name,
                    Qt.MatchEndsWith, 0))[0]
                self.__add_item_to_tree(sample_item, measurement, load_data)
                self.tab_id += 1
                return measurement

        if tab_type == "simulation":
            simulation = self.request.samples.simulations.add_simulation_file(
                sample, filepath, self.tab_id)

            if simulation:
                tab = SimulationTabWidget(self.request, self.tab_id, simulation,
                                          self.icon_manager,
                                          statusbar=self.statusbar)

                tab.setAttribute(QtCore.Qt.WA_DeleteOnClose)
                tab.add_log()
                self.tab_widgets[self.tab_id] = tab
                # tab.add_log()
                tab.data_loaded = load_data
                if load_data:
                    tab.add_simulation_target_and_recoil()

                    progress_bar.setValue(100)
                    QtCore.QCoreApplication.processEvents(
                        QtCore.QEventLoop.AllEvents)

                    self.ui.tabs.addTab(tab, simulation.name)
                    self.ui.tabs.setCurrentWidget(tab)

                sample_item = (self.tree_widget.findItems(
                    "%02d" % sample.serial_number + " " + sample.name,
                    Qt.MatchEndsWith, 0))[0]
                self.__add_item_to_tree(sample_item, simulation, load_data)
                self.tab_id += 1

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
        if self.request:
            # TODO: Doesn't release memory
            # Clear the treewidget
            self.ui.treeWidget.clear()
            self.ui.tabs.clear()
            self.request = None
            self.tab_widgets = {}
            self.tab_id = 0

    def __make_nonslave_measurement(self):
        """Exclude selected measurement from slave category.
        """
        self.tree_widget.blockSignals(True)
        items = self.ui.treeWidget.selectedItems()
        if not items:
            return
        clicked_item = self.tree_widget.currentItem()

        self.request.exclude_slave(clicked_item.obj)
        clicked_item.setText(0, clicked_item.obj.name)

        # tree_root = self.tree_widget.invisibleRootItem()
        # for i in range(tree_root.childCount()):
        #     sample_item = tree_root.child(i)
        #     for j in range(sample_item.childCount()):
        #         tree_item = sample_item.child(j)
        #         if isinstance(tree_item.obj, Measurement):
        #             tab_widget = self.tab_widgets[tree_item.tab_id]
        #             if master and tab_widget.obj.directory != master.directory:
        #                 self.request.exclude_slave(tab_widget.obj)
        #                 tree_item.setText(0, tab_widget.obj.name)
        self.tree_widget.blockSignals(False)

    def __make_slave_measurement(self):
        """Include selected measurements in slave category.
        """
        self.tree_widget.blockSignals(True)
        items = self.ui.treeWidget.selectedItems()
        if not items:
            return
        clicked_item = self.tree_widget.currentItem()
        self.request.include_slave(clicked_item.obj)
        clicked_item.setText(0, clicked_item.obj.name + " (slave)")

        # tree_root = self.tree_widget.invisibleRootItem()
        # for i in range(tree_root.childCount()):
        #     sample_item = tree_root.child(i)
        #     for j in range(sample_item.childCount()):
        #         tree_item = sample_item.child(j)
        #         if isinstance(tree_item.obj, Measurement):
        #             tab_widget = self.tab_widgets[tree_item.tab_id]
        #             if master and master.directory != tab_widget.obj.directory:
        #                 self.request.include_slave(tab_widget.obj)
        #                 tree_item.setText(0, "{0} (slave)".format(
        #                     tab_widget.obj.name))
        self.tree_widget.blockSignals(False)

    def __make_master_measurement(self):
        """Make selected or first of the selected measurements
        a master measurement.
        """
        self.tree_widget.blockSignals(True)

        items = self.ui.treeWidget.selectedItems()
        if not items:
            return
        master_tree = items[0]
        master_tab = self.tab_widgets[master_tree.tab_id]
        self.request.set_master(master_tab.obj)
        # old_master = self.request.get_master()
        nonslaves = self.request.get_nonslaves()

        tree_root = self.tree_widget.invisibleRootItem()
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

                for k in range(self.ui.tabs.count()):
                    tab = self.ui.tabs.widget(k)
                    tab_name = tab.obj.name
                    if tab.tab_id == master_tab.tab_id:
                        tab_name = "{0} (master)".format(tab_name)
                        self.ui.tabs.setTabText(tab.tab_id, tab_name)
                    else:
                        self.ui.tabs.setTabText(tab.tab_id, tab_name)

        self.tree_widget.blockSignals(False)

    def __master_issue_commands(self):
        """Issue commands from master measurement to all slave measurements in
        the request.
        """
        reply = QtWidgets.QMessageBox.question(self, "Confirmation",
                                               "You are about to issue actions "
                                               "from master measurement to all "
                                               "slave measurements in the "
                                               "request. This can take several "
                                               "minutes. Please wait until "
                                               "notification is shown.\nDo you "
                                               "wish to continue?",
                                               QtWidgets.QMessageBox.Yes |
                                               QtWidgets.QMessageBox.No,
                                               QtWidgets.QMessageBox.Yes)
        if reply == QtWidgets.QMessageBox.No:
            return

        time_start = datetime.now()
        progress_bar = QtWidgets.QProgressBar()
        self.statusbar.addWidget(progress_bar, 1)
        progress_bar.show()
        nonslaves = self.request.get_nonslaves()
        master = self.request.get_master()
        master_tab = self.tab_widgets[master.tab_id]
        master_name = master.name
        directory_d = master.directory_depth_profiles
        directory_e = master.directory_energy_spectra
        directory_c = master.directory_composition_changes
        progress_bar.setValue(1)
        QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents)
        # Load selections and save cut files
        # TODO: Make a check for these if identical already -> don't redo.
        # TODO
        self.request.save_selection(master, GUIReporter(progress_bar), 20)
        progress_bar.setValue(21)
        QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents)

        # TODO
        self.request.save_cuts(master, GUIReporter(progress_bar), 21, 11)
        progress_bar.setValue(33)
        QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents)

        tree_root = self.tree_widget.invisibleRootItem()
        tree_child_count = tree_root.childCount()
        start = 33
        sample_percentage = 67 / tree_child_count
        for i in range(tree_child_count):
            sample_item = tree_root.child(i)
            sample_child_count = sample_item.childCount()
            for j in range(sample_child_count):
                item_percentage = sample_percentage / sample_child_count
                tree_item = sample_item.child(j)
                if isinstance(tree_item.obj, Measurement):
                    tab = self.tab_widgets[tree_item.tab_id]
                    tab_obj = tab.obj
                    tab_name = tab_obj.name
                    if tab_name == master_name or tab_obj in nonslaves:
                        progress_bar.setValue(start + item_percentage)
                        QtCore.QCoreApplication.processEvents(
                            QtCore.QEventLoop.AllEvents)
                        start += item_percentage
                        continue
                    # Load measurement data if the slave is
                    if not tab.data_loaded:
                        tab.data_loaded = True

                        tab.obj.load_data()

                        after_load = start + 0.2 * item_percentage
                        progress_bar.setValue(after_load)
                        QtCore.QCoreApplication.processEvents(
                            QtCore.QEventLoop.AllEvents)

                        after_hist = start + 0.4 * item_percentage
                        add = after_hist - after_load
                        tab.add_histogram(progress_bar, after_load, add)
                        progress_bar.setValue(after_hist)
                        QtCore.QCoreApplication.processEvents(
                            QtCore.QEventLoop.AllEvents)

                        # Load selection
                        directory = master.directory_data
                        selection_file = "{0}.selections".format(
                            os.path.join(directory, master_name))
                        tab.obj.selector.load(selection_file)
                        tab.histogram.matplotlib.on_draw()

                        # Save cuts
                        tab.obj.save_cuts(GUIReporter(progress_bar),
                                          after_hist,
                                          0.1 * item_percentage)

                        # Update tree item icon to open folder
                        self.tree_widget.blockSignals(True)
                        self.__change_tab_icon(tree_item)
                        self.tree_widget.blockSignals(False)

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
                        progress_bar.setValue(start + 0.6 * item_percentage)
                        QtCore.QCoreApplication.processEvents(
                            QtCore.QEventLoop.AllEvents)

                    if master_tab.elemental_losses_widget and tab.data_loaded:
                        if tab.elemental_losses_widget:
                            tab.del_widget(tab.elemental_losses_widget)
                        tab.make_elemental_losses(directory_c, master_name,
                                                  master.serial_number,
                                                  sample_folder_name)
                        tab.elemental_losses_widget.save_to_file()
                        progress_bar.setValue(start + 0.8 * item_percentage)
                        QtCore.QCoreApplication.processEvents(
                            QtCore.QEventLoop.AllEvents)

                    if master_tab.energy_spectrum_widget and tab.data_loaded:
                        if tab.energy_spectrum_widget:
                            tab.del_widget(tab.energy_spectrum_widget)
                        tab.make_energy_spectrum(directory_e, master_name,
                                                 master.serial_number,
                                                 sample_folder_name)
                        tab.energy_spectrum_widget.save_to_file()
                        progress_bar.setValue(start + 0.95 * item_percentage)
                        QtCore.QCoreApplication.processEvents(
                            QtCore.QEventLoop.AllEvents)

                progress_bar.setValue(start + item_percentage)
                QtCore.QCoreApplication.processEvents(
                QtCore.QEventLoop.AllEvents)

                start += item_percentage

        self.statusbar.removeWidget(progress_bar)
        progress_bar.hide()
        time_end = datetime.now()
        time_duration = (time_end - time_start).seconds
        time_str = timedelta(seconds=time_duration)
        QtWidgets.QMessageBox.question(self, "Notification",
                                       "Master measurement's actions have been "
                                       "issued to slaves. \nElapsed time: {0}"
                                       .format(time_str),
                                       QtWidgets.QMessageBox.Ok,
                                       QtWidgets.QMessageBox.Ok)

    def __open_info_tab(self):
        """Opens an info tab to the QTabWidget 'tab_measurements' that guides
        the user to add a new measurement to the request.
        """
        self.ui.tabs.addTab(self.ui.infoTab, "Info")

    def __remove_introduction_tab(self):
        """Removes an info tab from the QTabWidget 'tab_measurements' that
        guides the user to create a new request.
        """
        index = self.ui.tabs.indexOf(self.ui.introduceTab)
        if index >= 0:
            self.ui.tabs.removeTab(index)

    def __remove_master_measurement(self):
        """Remove master measurement
        """
        self.tree_widget.blockSignals(True)

        old_master = self.request.get_master()
        self.request.set_master()  # No master measurement

        tree_root = self.tree_widget.invisibleRootItem()
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
            self.ui.tabs.setTabText(old_master.tab_id, measurement_name)
            old_master_tab = self.tab_widgets[old_master.tab_id]
            old_master_tab.toggle_master_button()
        self.request.set_master()  # No master measurement

        self.tree_widget.blockSignals(False)

    def __remove_info_tab(self):
        """Removes an info tab from the QTabWidget 'tab_measurements' that
        guides the user to add a new measurement to the request.
        """
        index = self.ui.tabs.indexOf(self.ui.infoTab)
        if index >= 0:
            self.ui.tabs.removeTab(index)

    def __set_icons(self):
        """Adds icons to the main window.
        """
        self.icon_manager.set_icon(self.ui.requestSettingsButton, "gear.svg")
        self.icon_manager.set_icon(self.ui.globalSettingsButton, "gear.svg")
        self.icon_manager.set_icon(self.ui.actionNew_Request, "file.svg")
        self.icon_manager.set_icon(self.ui.actionOpen_Request,
                                   "folder_open.svg")
        self.icon_manager.set_icon(self.ui.actionSave_Request,
                                   "amarok_save.svg")
        self.icon_manager.set_icon(self.ui.actionNew_Measurement, "log.svg")
        self.icon_manager.set_icon(self.ui.actionNew_Simulation,
                                   "new_simulation.png")

    def __set_request_buttons_enabled(self, state=False):
        """Enables 'request settings', 'save request' and 'new measurement'
        buttons.
           Enables simulation related buttons.
        Args:
            state: True/False enables or disables buttons
        """
        self.ui.requestSettingsButton.setEnabled(state)
        self.ui.actionSave_Request.setEnabled(state)
        self.ui.actionNew_Measurement.setEnabled(state)
        self.ui.actionNew_measurement_2.setEnabled(state)
        self.ui.menuImport.setEnabled(state)
        self.ui.actionRequest_Settings.setEnabled(state)
        # TODO: Should these only be enabled when there is measurement open?
        self.ui.actionAnalyze_elemental_losses.setEnabled(state)
        self.ui.actionCreate_energy_spectrum.setEnabled(state)
        self.ui.actionCreate_depth_profile.setEnabled(state)

        # enable simulation buttons
        self.ui.actionNew_Simulation.setEnabled(state)
        self.ui.actionNew_Simulation_2.setEnabled(state)

        # enable simulation energy spectra button
        self.ui.actionCreate_energy_spectrum_sim.setEnabled(state)

    def __tab_exists(self, tab_id):
        """Check if there is an open tab with the tab_id (identifier).

        Args:
            tab_id: Identifier (int) for the MeasurementTabWidget

        Returns:
            True if tab is found, False if not
        """
        # Try to find the clicked item from QTabWidget.
        for i in range(0, self.ui.tabs.count()):
            if self.ui.tabs.widget(i).tab_id == tab_id:
                return True
        return False

    def __open_manual(self):
        """Open user manual.
        """
        # TODO changed the file path to point to the manual, I guess this needs
        #      to be updated in the .spec file too?
        manual_filename = os.path.join("documentation", "manual",
                                       "Potku-manual.pdf")
        used_os = platform.system()
        try:
            if used_os == "Windows":
                os.startfile(manual_filename)
            elif used_os == "Linux":
                subprocess.call(("xdg-open", manual_filename))
            elif used_os == "Darwin":
                subprocess.call(("open", manual_filename))
        except FileNotFoundError:
            QtWidgets.QMessageBox.critical(self, "Not found",
                                           "There is no manual to be found!",
                                           QtWidgets.QMessageBox.Ok,
                                           QtWidgets.QMessageBox.Ok)


def main():
    """Main function
    """
    app = QtWidgets.QApplication(sys.argv)
    window = Potku()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
