# coding=utf-8
"""
Created on 15.5.2019
Updated on 27.5.2019

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2019 Heta Rekilä

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

__author__ = "Heta Rekilä"
__version__ = "2.0"

import os
import threading
import time
import json

import dialogs.dialog_functions as df

from pathlib import Path

from modules.energy_spectrum import EnergySpectrum
from modules.nsgaii import Nsgaii

from PyQt5 import uic
from PyQt5.QtCore import QLocale
from PyQt5 import QtWidgets

from widgets.simulation.optimization_parameters import \
    OptimizationFluenceParameterWidget
from widgets.simulation.optimization_parameters import \
    OptimizationRecoilParameterWidget


class OptimizationDialog(QtWidgets.QDialog):
    def __init__(self, simulation, parent):
        super().__init__()

        self.simulation = simulation
        self.tab = parent
        self.ui = uic.loadUi(
            os.path.join("ui_files", "ui_optimization_params.ui"), self)

        self.fluence_parameters = {}
        self.recoil_parameters = {}
        self.parameters_from_file()

        self.parameters_widget = OptimizationRecoilParameterWidget(
            **self.recoil_parameters)

        locale = QLocale.c()
        self.ui.histogramTicksDoubleSpinBox.setLocale(locale)

        self.element_simulation = None
        self.selected_cut_file = None
        self.ui.pushButton_OK.setEnabled(False)

        self.ui.pushButton_Cancel.clicked.connect(self.close)
        self.ui.pushButton_OK.clicked.connect(self.start_optimization)

        self.radios = QtWidgets.QButtonGroup(self)
        self.radios.buttonToggled[QtWidgets.QAbstractButton, bool].connect(
            self.choose_optimization_mode)
        self.current_mode = "recoil"
        self.ui.parametersLayout.addWidget(self.parameters_widget)

        self.radios.addButton(self.ui.fluenceRadioButton)
        self.radios.addButton(self.ui.recoilRadioButton)

        self.result_files = []
        for file in os.listdir(self.tab.obj.directory):
            if file.endswith(".mcsimu"):
                name = file.split(".")[0]
                item = QtWidgets.QTreeWidgetItem()
                item.setText(0, name)
                self.ui.simulationTreeWidget.addTopLevelItem(item)
        self.ui.simulationTreeWidget.itemSelectionChanged.connect(
            lambda: self.change_selected_element_simulation(
                 self.ui.simulationTreeWidget.currentItem()))

        # Add calculated tof_list files to tof_list_tree_widget by
        # measurement under the same sample.

        for sample in self.tab.obj.request.samples.samples:
            for measurement in sample.measurements.measurements.values():
                if self.simulation.sample is measurement.sample:

                    all_cuts = []

                    tree_item = QtWidgets.QTreeWidgetItem()
                    tree_item.setText(0, measurement.name)
                    tree_item.obj = measurement
                    tree_item.obj = measurement
                    self.ui.measurementTreeWidget.addTopLevelItem(tree_item)

                    # TODO make each of these into their own functions under
                    #      modules package
                    for file in os.listdir(
                            measurement.directory_cuts):
                        if file.endswith(".cut"):
                            file_name_without_suffix = \
                                file.rsplit('.', 1)[0]
                            all_cuts.append(file_name_without_suffix)

                    for file_2 in os.listdir(
                            os.path.join(
                                measurement.directory_composition_changes,
                                "Changes")):
                        if file_2.endswith(".cut"):
                            file_name_without_suffix = \
                                file_2.rsplit('.', 1)[0]
                            all_cuts.append(file_name_without_suffix)

                    all_cuts.sort()

                    for cut in all_cuts:
                        item = QtWidgets.QTreeWidgetItem()
                        item.setText(0, cut)
                        tree_item.addChild(item)
                        tree_item.setExpanded(True)
        self.ui.measurementTreeWidget.itemSelectionChanged.connect(
            lambda: self.change_selected_cut_file(
                self.ui.measurementTreeWidget.currentItem()))

        self.result_widget = None
        self.measured_element = ""
        self.optimization_thread = None
        self.check_results_thread = None

        self.exec_()

    def closeEvent(self, evnt):
        """Save current parameters to file so they can be reopened.
        """
        self.parameters_to_file()
        evnt.accept()

    def get_file_name(self):
        """Returns a file path that is used to save the optimization
        parameters.
        """
        return Path(self.simulation.directory, ".optimization_parameters")

    def parameters_to_file(self):
        """Writes current parameters to file.
        """
        # FIXME max_time parameter does not get properly saved
        # Update the set of parameters that are currently in use
        if self.current_mode == "recoil":
            self.recoil_parameters = self.parameters_widget.get_properties()
        else:
            self.fluence_parameters = self.parameters_widget.get_properties()

        params = {
            "rec": self.recoil_parameters,
            "flu": self.fluence_parameters
        }
        with open(self.get_file_name(), "w") as file:
            json.dump(params, file, indent=4)

    def parameters_from_file(self):
        """Loads previous parameters from file.
        """
        try:
            with open(self.get_file_name()) as file:
                params = json.load(file)
        except FileNotFoundError:
            return
        try:
            self.recoil_parameters = params["rec"]
        except KeyError:
            pass
        try:
            self.fluence_parameters = params["flu"]
        except KeyError:
            pass

    def change_selected_cut_file(self, item):
        """
        Update the selected cut file.

        Args:
            item: Selected TreeWidgetItem.
        """
        # Make sure that a cut file has been selected
        if "." in item.text(0):
            self.selected_cut_file = item.text(0)
            if self.element_simulation:
                self.ui.pushButton_OK.setEnabled(True)
        else:
            self.selected_cut_file = None
            self.ui.pushButton_OK.setEnabled(False)

    def change_selected_element_simulation(self, item):
        """
        Update the selected element simulation.

        Args:
            item: Selected TreeWidgetItem.
        """
        item_text = item.text(0)
        for element_simulation in self.simulation.element_simulations:
            if element_simulation.name_prefix + "-" + element_simulation.name\
                    == item_text:
                self.element_simulation = element_simulation
                if self.selected_cut_file:
                    self.ui.pushButton_OK.setEnabled(True)
                break

    def check_progress_and_results(self):
        """
        Check whether result widget needs updating.

        Args:
            measured_element: Which element (cut file) was used in optimization.
        """
        while not self.element_simulation.optimization_stopped:
            calc_sols = self.element_simulation.calculated_solutions
            self.result_widget.update_progress(calc_sols)
            if self.element_simulation.optimization_done:
                self.element_simulation.optimization_running = False
                self.result_widget.show_results(calc_sols)

                if self.element_simulation.optimized_fluence is None:
                    # Save optimized recoils
                    for recoil in self.element_simulation.optimization_recoils:
                        recoil.to_file(self.element_simulation.directory)
                    save_file_name = self.element_simulation.name_prefix + \
                                     "-opt.measured"
                    with open(os.path.join(self.element_simulation.directory,
                                           save_file_name), "w") as f:
                        f.write(self.measured_element)
                elif self.element_simulation.optimized_fluence != 0:
                    # save found fluence value
                    file_name = self.element_simulation.name_prefix + \
                                "-optfl.result"
                    with open(os.path.join(self.element_simulation.directory,
                                           file_name), "w") as f:
                        f.write(str(self.element_simulation.optimized_fluence))
                self.result_widget = None
                break
            time.sleep(5)  # Sleep for 5 seconds to save processing power

    def choose_optimization_mode(self, button, checked):
        """
        Choose whether to optimize recoils or fluence. Show correct ui.
        """
        if checked:
            if button.text() == "Recoil":
                self.fluence_parameters = \
                    self.parameters_widget.get_properties()
                self.current_mode = "recoil"
                # Clear fluence stuff
                self.ui.parametersLayout.removeWidget(self.parameters_widget)
                # Add recoil stuff
                self.parameters_widget.deleteLater()
                self.parameters_widget = OptimizationRecoilParameterWidget(
                    **self.recoil_parameters)
                self.ui.parametersLayout.addWidget(self.parameters_widget)
            else:
                self.recoil_parameters = \
                    self.parameters_widget.get_properties()
                self.current_mode = "fluence"
                # Clear recoil stuff
                self.ui.parametersLayout.removeWidget(self.parameters_widget)
                self.parameters_widget.deleteLater()
                # Add fluence stuff
                self.parameters_widget = OptimizationFluenceParameterWidget(
                    **self.fluence_parameters)
                self.ui.parametersLayout.addWidget(self.parameters_widget)

    def start_optimization(self):
        """
        Find necessary cut file and make energy spectrum with it, and start
        optimization with given parameters.
        """
        # Delete previous results widget if it exists
        if self.tab.optimization_result_widget:
            self.tab.del_widget(
                self.tab.optimization_result_widget)
            self.tab.optimization_result_widget = None
            self.element_simulation.optimized_fluence = None
            self.element_simulation.calculated_solutions = 0
            self.element_simulation.optimization_done = False
            self.element_simulation.optimization_stopped = False
            self.element_simulation.optimization_running = False
            # Delete previous energy spectra if there are any
            if self.element_simulation.optimization_recoils:
                # Delete energy spectra that use optimized recoils
                df.delete_optim_espe(self, self.element_simulation)
            self.element_simulation.optimization_recoils = []
        self.close()
        root_for_cut_files = self.ui.measurementTreeWidget.invisibleRootItem()

        cut_file = None
        item_text = None
        used_measurement = None
        cut_file_found = False
        i = 0
        while not cut_file_found:
            measurement_item = root_for_cut_files.child(i)
            mes_child_count = measurement_item.childCount()
            for j in range(mes_child_count):
                item = measurement_item.child(j)
                if item.text(0) == self.selected_cut_file:
                    item_text = item.text(0)
                    used_measurement = item.parent().obj
                    # Calculate energy spectra for cut
                    if len(item.text(0).split('.')) < 5:
                        # Normal cut
                        cut_file = os.path.join(used_measurement.directory_cuts,
                                                item.text(0)) + ".cut"
                    else:
                        cut_file = os.path.join(
                            used_measurement.directory_composition_changes,
                            "Changes", item.text(0)) + ".cut"
                    cut_file_found = True
                    break
            i += 1

        ch = self.ui.histogramTicksDoubleSpinBox.value()
        # Hist all selected cut files
        # TODO this could also be done in the Nsga2 __init__
        es = EnergySpectrum(used_measurement, [cut_file],
                            ch,
                            progress=None,
                            no_foil=True)
        es.calculate_spectrum(no_foil=True)
        # Add result files
        hist_file = Path(used_measurement.directory_energy_spectra,
                         f"{item_text}.no_foil.hist")

        nsgaii = Nsgaii(element_simulation=self.element_simulation,
                        hist_file=hist_file,
                        ch=ch,
                        **self.parameters_widget.get_properties())

        # Result checking thread
        self.check_results_thread = threading.Thread(
            target=self.check_progress_and_results)

        # Optimization running thread
        # TODO multiprocessing could also be an option instead of a thread.
        self.optimization_thread = threading.Thread(
            target=nsgaii.start_optimization)

        # Create necessary results widget
        mode_recoil = self.current_mode == "recoil"
        self.measured_element = item_text

        self.result_widget = self.tab.add_optimization_results_widget(
            self.element_simulation, item_text, mode_recoil)
        self.element_simulation.optimization_widget = self.result_widget

        self.check_results_thread.daemon = True
        self.check_results_thread.start()

        self.optimization_thread.daemon = True
        self.optimization_thread.start()

        # TODO this should be set by the element_simulation itself
        self.element_simulation.optimization_running = True
