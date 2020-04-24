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

import dialogs.dialog_functions as df
import widgets.binding as bnd

from pathlib import Path

from modules.energy_spectrum import EnergySpectrum
from modules.nsgaii import Nsgaii

from widgets.binding import PropertySavingWidget
from widgets.gui_utils import QtABCMeta

from PyQt5 import uic
from PyQt5.QtCore import QLocale
from PyQt5 import QtWidgets

from widgets.simulation.optimization_parameters import \
    OptimizationFluenceParameterWidget
from widgets.simulation.optimization_parameters import \
    OptimizationRecoilParameterWidget


class OptimizationDialog(QtWidgets.QDialog, PropertySavingWidget,
                         metaclass=QtABCMeta):
    """
    TODO
    """
    ch = bnd.bind("histogramTicksDoubleSpinBox")

    @property
    def fluence_parameters(self):
        if self.current_mode != "recoil":
            self._fluence_parameters = self.parameters_widget.get_properties()
        return self._fluence_parameters

    @fluence_parameters.setter
    def fluence_parameters(self, value):
        self._fluence_parameters = value

    @property
    def recoil_parameters(self):
        if self.current_mode == "recoil":
            self._recoil_parameters = self.parameters_widget.get_properties()
        return self._recoil_parameters

    @recoil_parameters.setter
    def recoil_parameters(self, value):
        self._recoil_parameters = value

    def __init__(self, simulation, parent):
        """
        TODO

        Args:
            simulation: TODO
            parent: TODO
        """
        super().__init__()

        self.simulation = simulation
        self.tab = parent

        self._fluence_parameters = {}
        self._recoil_parameters = {}
        self.current_mode = "recoil"

        uic.loadUi(Path("ui_files", "ui_optimization_params.ui"), self)

        self.load_properties_from_file()

        self.parameters_widget = OptimizationRecoilParameterWidget(
            **self._recoil_parameters)

        locale = QLocale.c()
        self.histogramTicksDoubleSpinBox.setLocale(locale)

        self.element_simulation = None
        self.selected_cut_file = None
        self.pushButton_OK.setEnabled(False)

        self.pushButton_Cancel.clicked.connect(self.close)
        self.pushButton_OK.clicked.connect(self.start_optimization)

        self.radios = QtWidgets.QButtonGroup(self)
        self.radios.buttonToggled[QtWidgets.QAbstractButton, bool].connect(
            self.choose_optimization_mode)
        self.parametersLayout.addWidget(self.parameters_widget)

        self.radios.addButton(self.fluenceRadioButton)
        self.radios.addButton(self.recoilRadioButton)

        self.result_files = []
        for file in os.listdir(self.tab.obj.directory):
            if file.endswith(".mcsimu"):
                name = file.split(".")[0]
                item = QtWidgets.QTreeWidgetItem()
                item.setText(0, name)
                self.simulationTreeWidget.addTopLevelItem(item)
        self.simulationTreeWidget.itemSelectionChanged.connect(
            lambda: self.change_selected_element_simulation(
                 self.simulationTreeWidget.currentItem()))

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
                    self.measurementTreeWidget.addTopLevelItem(tree_item)

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
        self.measurementTreeWidget.itemSelectionChanged.connect(
            lambda: self.change_selected_cut_file(
                self.measurementTreeWidget.currentItem()))

        self.exec_()

    def get_property_file_path(self):
        """Returns absolute path to the file that is used for saving and
        loading parameters.
        """
        return Path(self.simulation.directory,
                    ".parameters",
                    ".optimization_parameters")

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
                self.pushButton_OK.setEnabled(True)
        else:
            self.selected_cut_file = None
            self.pushButton_OK.setEnabled(False)

    def change_selected_element_simulation(self, item):
        """
        Update the selected element simulation.

        Args:
            item: Selected TreeWidgetItem.
        """
        item_text = item.text(0)
        for element_simulation in self.simulation.element_simulations:
            if element_simulation.get_full_name() == item_text:
                self.element_simulation = element_simulation
                if self.selected_cut_file:
                    self.pushButton_OK.setEnabled(True)
                break

    def choose_optimization_mode(self, button, checked):
        """
        Choose whether to optimize recoils or fluence. Show correct ui.
        """
        if checked:
            if button.text() == "Recoil":
                self._fluence_parameters = \
                    self.parameters_widget.get_properties()
                self.current_mode = "recoil"
                # Clear fluence stuff
                self.parametersLayout.removeWidget(self.parameters_widget)
                # Add recoil stuff
                self.parameters_widget.deleteLater()
                self.parameters_widget = OptimizationRecoilParameterWidget(
                    **self._recoil_parameters)
                self.parametersLayout.addWidget(self.parameters_widget)
            else:
                self._recoil_parameters = \
                    self.parameters_widget.get_properties()
                self.current_mode = "fluence"
                # Clear recoil stuff
                self.parametersLayout.removeWidget(self.parameters_widget)
                self.parameters_widget.deleteLater()
                # Add fluence stuff
                self.parameters_widget = OptimizationFluenceParameterWidget(
                    **self._fluence_parameters)
                self.parametersLayout.addWidget(self.parameters_widget)

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

            # Delete previous energy spectra if there are any
            # TODO remove if check
            if self.element_simulation.optimization_recoils:
                # Delete energy spectra that use optimized recoils
                df.delete_optim_espe(self, self.element_simulation)
            self.element_simulation.optimization_recoils = []
        self.close()
        root_for_cut_files = self.measurementTreeWidget.invisibleRootItem()

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
                        cut_file = Path(used_measurement.directory_cuts,
                                        item.text(0) + ".cut")
                    else:
                        cut_file = Path(
                            used_measurement.directory_composition_changes,
                            "Changes", item.text(0) + ".cut")
                    cut_file_found = True
                    break
            i += 1

        nsgaii = Nsgaii(element_simulation=self.element_simulation,
                        measurement=used_measurement, cut_file=cut_file,
                        ch=self.ch,
                        **self.parameters_widget.get_properties())

        # Optimization running thread
        optimization_thread = threading.Thread(
            target=nsgaii.start_optimization)

        # Create necessary results widget
        mode_recoil = self.current_mode == "recoil"

        result_widget = self.tab.add_optimization_results_widget(
            self.element_simulation, item_text, mode_recoil)

        self.element_simulation.optimization_widget = result_widget
        nsgaii.subscribe(result_widget)

        optimization_thread.daemon = True
        optimization_thread.start()
