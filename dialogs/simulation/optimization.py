# coding=utf-8
"""
Created on 15.5.2019
Updated on 27.5.2019

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2019 Heta Rekilä, 2020 Juhani Sundell

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

__author__ = "Heta Rekilä \n Juhani Sundell"
__version__ = "2.0"

import threading
from pathlib import Path
from typing import Any
from typing import Dict

from PyQt5 import QtWidgets
from PyQt5 import uic
from PyQt5.QtCore import QLocale

import dialogs.dialog_functions as df
import widgets.binding as bnd
import widgets.gui_utils as gutils
from modules.concurrency import CancellationToken
from modules.element_simulation import ElementSimulation
from modules.enums import OptimizationType, OptimizationMethod
from modules.linear_optimization import LinearOptimization
from modules.nsgaii import Nsgaii
from modules.simulation import Simulation
from widgets.binding import PropertySavingWidget
from widgets.gui_utils import QtABCMeta
from widgets.simulation.optimization_parameters import \
    OptimizationFluenceParameterWidget
from widgets.simulation.optimization_parameters import \
    OptimizationRecoilParameterWidget
from widgets.simulation.optimization_linear_parameters import \
    LinearOptimizationRecoilParameterWidget
from widgets.simulation.optimization_linear_parameters import \
    LinearOptimizationFluenceParameterWidget


class OptimizationDialog(QtWidgets.QDialog, PropertySavingWidget,
                         metaclass=QtABCMeta):
    """User may either optimize fluence or recoil atom distribution.
    Optimization is done by comparing simulated spectrum to measured spectrum.
    """
    ch: float = bnd.bind("histogramTicksDoubleSpinBox")
    use_efficiency: bool = bnd.bind("eff_file_check_box")
    verbose: bool = bnd.bind("optimization_verbose_box")
    selected_cut_file: Path = bnd.bind(
        "measurementTreeWidget", fget=bnd.get_selected_tree_item,
        fset=bnd.set_selected_tree_item)
    selected_element_simulation: ElementSimulation = bnd.bind(
        "simulationTreeWidget", fget=bnd.get_selected_tree_item,
        fset=bnd.set_selected_tree_item)
    auto_adjust_x: bool = bnd.bind("auto_adjust_x_box")

    @property
    def fluence_parameters(self) -> Dict[str, Any]:
        return self.nsgaii_fluence_widget.get_properties()

    @fluence_parameters.setter
    def fluence_parameters(self, value: Dict[str, Any]) -> None:
        self.nsgaii_fluence_widget.set_properties(**value)

    @property
    def recoil_parameters(self) -> Dict[str, Any]:
        return self.nsgaii_recoil_widget.get_properties()

    @recoil_parameters.setter
    def recoil_parameters(self, value: Dict[str, Any]) -> None:
        self.nsgaii_recoil_widget.set_properties(**value)

    @property
    def linear_fluence_parameters(self) -> Dict[str, Any]:
        try:
            return self.linear_fluence_widget.get_properties()
        except AttributeError:
            pass  # Backwards compatibility

    @linear_fluence_parameters.setter
    def linear_fluence_parameters(self, value: Dict[str, Any]) -> None:
        self.linear_fluence_widget.set_properties(**value)

    @property
    def linear_recoil_parameters(self) -> Dict[str, Any]:
        try:
            return self.linear_recoil_widget.get_properties()
        except AttributeError:
            pass  # Backwards compatibility

    @linear_recoil_parameters.setter
    def linear_recoil_parameters(self, value: Dict[str, Any]) -> None:
        self.linear_recoil_widget.set_properties(**value)

    # TODO: Remember method & mode too

    def __init__(self, simulation: Simulation, parent):
        """Initializes an OptimizationDialog that displays various optimization
        parameters.

        Args:
            simulation: a Simulation object
            parent: a SimulationTabWidget
        """
        super().__init__()
        self.simulation = simulation
        self.tab = parent
        self.current_method = OptimizationMethod.NSGAII
        self.current_mode = OptimizationType.RECOIL

        uic.loadUi(gutils.get_ui_dir() / "ui_optimization_params.ui", self)

        self.nsgaii_recoil_widget = OptimizationRecoilParameterWidget()
        self.nsgaii_fluence_widget = OptimizationFluenceParameterWidget()

        # TODO check where nsgaii_*_widgets are used and do the same for these
        self.linear_recoil_widget = LinearOptimizationRecoilParameterWidget()
        self.linear_fluence_widget = LinearOptimizationFluenceParameterWidget()

        self.load_properties_from_file()

        locale = QLocale.c()
        self.histogramTicksDoubleSpinBox.setLocale(locale)

        self.pushButton_OK.setEnabled(False)

        self.pushButton_Cancel.clicked.connect(self.close)
        self.pushButton_OK.clicked.connect(self.start_optimization)

        self.method_radios = QtWidgets.QButtonGroup(self)
        self.method_radios.buttonToggled[QtWidgets.QAbstractButton, bool].connect(
            self.choose_optimization_method)

        self.method_radios.addButton(self.nsgaiiRadioButton)
        self.method_radios.addButton(self.linearRadioButton)
        self.linearRadioButton.setChecked(True)

        self.mode_radios = QtWidgets.QButtonGroup(self)
        self.mode_radios.buttonToggled[QtWidgets.QAbstractButton, bool].connect(
            self.choose_optimization_mode)
        self.parametersLayout.addWidget(self.nsgaii_recoil_widget)
        self.parametersLayout.addWidget(self.nsgaii_fluence_widget)
        self.nsgaii_recoil_widget.hide()
        self.nsgaii_fluence_widget.hide()

        # TODO: Why does selecting linear_recoil_widget by default cause a
        #   brief flash when opening the optimization dialog?
        self.parametersLayout.addWidget(self.linear_recoil_widget)
        self.parametersLayout.addWidget(self.linear_fluence_widget)
        self.linear_fluence_widget.hide()

        self.mode_radios.addButton(self.fluenceRadioButton)
        self.mode_radios.addButton(self.recoilRadioButton)
        self._enable_linear_fluence()

        gutils.fill_tree(
            self.simulationTreeWidget.invisibleRootItem(),
            simulation.element_simulations,
            text_func=lambda elem_sim: elem_sim.get_full_name())

        self.simulationTreeWidget.itemSelectionChanged.connect(
            self._enable_ok_button)
        self.simulationTreeWidget.itemSelectionChanged.connect(
            self._adjust_x)
        self.auto_adjust_x_box.clicked.connect(self._adjust_x)

        self._fill_measurement_widget()

        self.measurementTreeWidget.itemSelectionChanged.connect(
            self._enable_ok_button)
        self.verbose = False
        self.eff_file_check_box.clicked.connect(self._enable_efficiency_label)
        self._update_efficiency_label()

        self.exec_()

    def closeEvent(self, event):
        """Overrides the QDialogs closeEvent. Saves current parameters to
        file so they shown next time the dialog is opened.
        """
        params = self.get_properties()
        # Remove non-serializable values
        params.pop("selected_element_simulation")
        params.pop("selected_cut_file")
        self.save_properties_to_file(values=params)
        QtWidgets.QDialog.closeEvent(self, event)

    def _update_efficiency_label(self):
        """Updates the text of efficiency label.
        """
        self.efficiency_label.setText(
            df.get_multi_efficiency_text(
                self.measurementTreeWidget,
                self.simulation.sample.get_measurements(),
                data_func=lambda tpl: tpl[0]))

    def _enable_efficiency_label(self):
        """Enables or disables efficiency label.
        """
        self.efficiency_label.setEnabled(self.use_efficiency)

    def _fill_measurement_widget(self):
        """Add calculated tofe_list files to tofe_list_tree_widget by
        measurement under the same sample.
        """
        for sample in self.simulation.request.samples.samples:
            for measurement in sample.measurements.measurements.values():
                if self.simulation.sample is measurement.sample:
                    root = QtWidgets.QTreeWidgetItem()
                    root.setText(0, measurement.name)
                    self.measurementTreeWidget.addTopLevelItem(root)
                    cuts, elem_losses = measurement.get_cut_files()
                    gutils.fill_tree(
                        root, cuts, data_func=lambda c: (c, measurement),
                        text_func=lambda c: c.name
                    )
                    loss_node = QtWidgets.QTreeWidgetItem(["Element losses"])
                    gutils.fill_tree(
                        loss_node, elem_losses,
                        data_func=lambda c: (c, measurement),
                        text_func=lambda c: c.name
                    )
                    root.addChild(loss_node)
                    root.setExpanded(True)

    def get_property_file_path(self) -> Path:
        """Returns absolute path to the file that is used for saving and
        loading parameters.
        """
        return Path(
            self.simulation.directory, ".parameters",
            ".optimization_parameters")

    def _enable_ok_button(self, *_):
        """Enables OK button if both ElementSimulation and cut file have been
        selected.
        """
        self.pushButton_OK.setEnabled(
            self.selected_cut_file is not None and
            self.selected_element_simulation is not None)

    def _adjust_x(self):
        """Adjusts the upper limit value on x axis based on the distribution
        length of the main recoil of currently selected ElementSimulation.
        """
        if not self.auto_adjust_x:
            return
        elem_sim = self.selected_element_simulation
        if elem_sim is None:
            return

        _, max_x = elem_sim.get_main_recoil().get_range()
        if self.current_method == OptimizationMethod.NSGAII:
            _, prev_y = self.nsgaii_recoil_widget.upper_limits
        else:
            _, prev_y = self.linear_recoil_widget.upper_limits

        self.nsgaii_recoil_widget.upper_limits = max_x, prev_y
        self.linear_recoil_widget.upper_limits = max_x, prev_y

    # TODO: Remove once linear fluence optimization is done
    def _enable_linear_fluence(self) -> None:
        """Disable fluence button if linear is selected or
        linear button if fluence is selected. Otherwise enable both.
        """
        disabled_text = "Fluence optimization using linear optimization is not implemented yet"

        if self.current_method == OptimizationMethod.LINEAR:
            self.fluenceRadioButton.setEnabled(False)
            self.fluenceRadioButton.setToolTip(disabled_text)
        else:
            self.fluenceRadioButton.setEnabled(True)
            self.fluenceRadioButton.setToolTip("")

        if self.current_mode == OptimizationType.FLUENCE:
            self.linearRadioButton.setEnabled(False)
            self.linearRadioButton.setToolTip(disabled_text)
        else:
            self.linearRadioButton.setEnabled(True)
            self.linearRadioButton.setToolTip("")

    def choose_optimization_method(self, button, checked):
        """Choose whether to use NSGA-II or linear optimization method."""
        if checked:
            # TODO: Recognize the button without relying on constant text
            if button.text() == "NSGA-II (slow)":
                self.current_method = OptimizationMethod.NSGAII

                if self.current_mode == OptimizationType.RECOIL:
                    self.linear_recoil_widget.hide()
                    self.nsgaii_recoil_widget.show()
                else:
                    self.linear_fluence_widget.hide()
                    self.nsgaii_fluence_widget.show()
            else:
                self.current_method = OptimizationMethod.LINEAR

                if self.current_mode == OptimizationType.RECOIL:
                    self.nsgaii_recoil_widget.hide()
                    self.linear_recoil_widget.show()
                else:
                    self.nsgaii_fluence_widget.hide()
                    self.linear_fluence_widget.show()

            self._enable_linear_fluence()

    def choose_optimization_mode(self, button, checked):
        """Choose whether to optimize recoils or fluence. Show correct widget.
        """
        if checked:
            # TODO: Recognize the button without relying on constant text
            if button.text() == "Recoil":
                self.current_mode = OptimizationType.RECOIL

                if self.current_method == OptimizationMethod.NSGAII:
                    self.nsgaii_fluence_widget.hide()
                    self.nsgaii_recoil_widget.show()
                else:
                    self.linear_fluence_widget.hide()
                    self.linear_recoil_widget.show()
            else:
                self.current_mode = OptimizationType.FLUENCE

                if self.current_method == OptimizationMethod.NSGAII:
                    self.nsgaii_recoil_widget.hide()
                    self.nsgaii_fluence_widget.show()
                else:
                    self.linear_recoil_widget.hide()
                    self.linear_fluence_widget.show()

            self._enable_linear_fluence()

    def start_optimization(self):
        """Find necessary cut file and make energy spectrum with it, and start
        optimization with given parameters.
        """
        elem_sim = self.selected_element_simulation
        cut, measurement = self.selected_cut_file
        # Delete previous results widget if it exists
        if self.tab.optimization_result_widget:
            self.tab.del_widget(
                self.tab.optimization_result_widget)
            self.tab.optimization_result_widget = None

            # Delete previous energy spectra if there are any
            df.delete_optim_espe(self, elem_sim)

        self.close()

        # TODO move following code to the result widget
        if self.current_method == OptimizationMethod.NSGAII:
            if self.current_mode == OptimizationType.RECOIL:
                params = self.nsgaii_recoil_widget.get_properties()
                optimize_by_area = self.nsgaii_recoil_widget.optimize_by_area
            else:
                params = self.nsgaii_fluence_widget.get_properties()
                optimize_by_area = self.nsgaii_fluence_widget.optimize_by_area

            optimizer = Nsgaii(
                element_simulation=elem_sim, measurement=measurement,
                cut_file=cut, ch=self.ch, **params,
                use_efficiency=self.use_efficiency,
                optimize_by_area=optimize_by_area, verbose=self.verbose)
        else:
            if self.current_mode == OptimizationType.RECOIL:
                params = self.linear_recoil_widget.get_properties()
            else:
                params = self.linear_fluence_widget.get_properties()

            optimizer = LinearOptimization(
                element_simulation=elem_sim, measurement=measurement,
                cut_file=cut, ch=self.ch, **params,
                use_efficiency=self.use_efficiency, verbose=self.verbose)

        # Optimization running thread
        ct = CancellationToken()
        optimization_thread = threading.Thread(
            target=optimizer.start_optimization,
            kwargs={"cancellation_token": ct})

        # Create necessary results widget
        result_widget = self.tab.add_optimization_results_widget(
            elem_sim, cut.name, self.current_mode, ct=ct)

        elem_sim.optimization_widget = result_widget
        optimizer.subscribe(result_widget)

        optimization_thread.daemon = True
        optimization_thread.start()
