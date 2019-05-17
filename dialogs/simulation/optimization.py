# coding=utf-8
"""
Created on 15.5.2019
Updated on 17.5.2019

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

from modules.energy_spectrum import EnergySpectrum
from modules.nsgaii import Nsgaii

from PyQt5 import uic
from PyQt5.QtCore import QLocale
from PyQt5 import QtWidgets


class OptimizationDialog(QtWidgets.QDialog):
    def __init__(self, simulation, parent):
        super().__init__()

        self.simulation = simulation
        self.parent_tab = parent
        self.ui = uic.loadUi(
            os.path.join("ui_files", "ui_optimization_params.ui"), self)

        locale = QLocale.c()
        self.ui.histogramTicksDoubleSpinBox.setLocale(locale)
        self.upperXDoubleSpinBox.setLocale(locale)
        self.lowerXDoubleSpinBox.setLocale(locale)
        self.upperYDoubleSpinBox.setLocale(locale)
        self.lowerYDoubleSpinBox.setLocale(locale)
        self.crossoverProbDoubleSpinBox.setLocale(locale)
        self.mutationProbDoubleSpinBox.setLocale(locale)
        self.percentDoubleSpinBox.setLocale(locale)

        self.element_simulation = None
        self.selected_cut_file = None
        self.ui.pushButton_OK.setEnabled(False)

        self.ui.pushButton_Cancel.clicked.connect(self.close)
        self.ui.pushButton_OK.clicked.connect(self.start_optimization)

        self.result_files = []
        for file in os.listdir(self.parent_tab.obj.directory):
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

        for sample in self.parent_tab.obj.request.samples.samples:
            for measurement in sample.measurements.measurements.values():
                if self.simulation.sample is measurement.sample:

                    all_cuts = []

                    tree_item = QtWidgets.QTreeWidgetItem()
                    tree_item.setText(0, measurement.name)
                    tree_item.obj = measurement
                    tree_item.obj = measurement
                    self.ui.measurementTreeWidget.addTopLevelItem(tree_item)

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
                # Save optimized recoils
                for recoil in self.element_simulation.optimization_recoils:
                    self.element_simulation.recoil_to_file(
                        self.element_simulation.directory, recoil)
                save_file_name = self.element_simulation.name_prefix + \
                                 "-opt.measured"
                with open(os.path.join(self.element_simulation.directory,
                                       save_file_name), "w") as f:
                    f.write(self.measured_element)
                self.result_widget = None
                break
            time.sleep(5)  # Sleep for 5 seconds to save processing power

    def start_optimization(self):
        """
        Find necessary cut file and make energy spectrum with it, and start
        optimization with given parameters.
        """
        # Delete previous results widget if it exists
        if self.parent_tab.optimization_result_widget:
            self.parent_tab.del_widget(
                self.parent_tab.optimization_result_widget)
            self.parent_tab.optimization_result_widget = None
            self.element_simulation.optimization_recoils = []
            self.element_simulation.calculated_solutions = 0
            self.element_simulation.optimization_done = False
            self.element_simulation.optimization_stopped = False
            self.element_simulation.optimization_running = False

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

        # Hist all selected cut files
        es = EnergySpectrum(used_measurement, [cut_file],
                            self.ui.histogramTicksDoubleSpinBox.value(),
                            None)
        es.calculate_spectrum()
        # Add result files
        hist_file = os.path.join(used_measurement.directory_energy_spectra,
                                 item_text + ".hist")

        channel_width = self.ui.histogramTicksDoubleSpinBox.value()
        upper_x = self.upperXDoubleSpinBox.value()
        lower_x = self.lowerXDoubleSpinBox.value()
        upper_y = self.upperYDoubleSpinBox.value()
        lower_y = self.lowerYDoubleSpinBox.value()
        crossover_prob = self.crossoverProbDoubleSpinBox.value()
        mutation_prob = self.mutationProbDoubleSpinBox.value()
        stop_percent = self.percentDoubleSpinBox.value()

        population_size = self.ui.populationSpinBox.value()
        generations = self.ui.generationSpinBox.value()
        no_of_processes = self.ui.processesSpinBox.value()
        check_time = self.ui.timeSpinBox.value()

        if self.ui.recoilTypeComboBox.currentText() == "4-point box":
            recoil_type = "box"
            solution_size = 5
        elif self.ui.recoilTypeComboBox.currentText() == "6-point box":
            recoil_type = "box"
            solution_size = 7
        elif self.ui.recoilTypeComboBox.currentText() == "8-point two-peak":
            recoil_type = "two-peak"
            solution_size = 9
        else:
            recoil_type = "two-peak"
            solution_size = 11

        self.measured_element = item_text
        # Update result widget with progress or results
        thread_results = threading.Thread(
            target=self.check_progress_and_results)
        self.check_results_thread = thread_results

        # Run optimization in a thread
        thread = threading.Thread(
            target=Nsgaii, args=(generations, self.element_simulation,
                                 population_size, solution_size,
                                 [upper_x, upper_y], [lower_x, lower_y],
                                 True, recoil_type, None, no_of_processes,
                                 crossover_prob, mutation_prob, stop_percent,
                                 check_time, channel_width, hist_file))
        self.optimization_thread = thread

        # Create necessary results widget
        self.result_widget = self.parent_tab.add_optimization_results_widget(
            self.element_simulation, item_text)
        self.element_simulation.optimization_widget = self.result_widget

        self.check_results_thread.daemon = True
        self.check_results_thread.start()

        self.optimization_thread.daemon = True
        self.optimization_thread.start()

        self.element_simulation.optimization_running = True
