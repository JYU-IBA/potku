# coding=utf-8
"""
Created on 14.5.2019
Updated on 23.5.2019

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

from pathlib import Path

from modules.element_simulation import ElementSimulation

from widgets.gui_utils import GUIObserver

from PyQt5 import QtWidgets
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal

from widgets.matplotlib.simulation.recoil_atom_optimization import \
    RecoilAtomOptimizationWidget


class OptimizedRecoilsWidget(QtWidgets.QWidget, GUIObserver):
    """
    Class to show the results of optimization. Also shows the progress.
    """
    results_accepted = pyqtSignal(ElementSimulation)

    def __init__(self, element_simulation: ElementSimulation, measured_element,
                 target, cancellation_token=None):
        """
        Initialize the widget.
        """
        super().__init__()
        GUIObserver.__init__(self)
        uic.loadUi(Path("ui_files", "ui_optimization_results_widget.ui"), self)

        self.element_simulation = element_simulation

        if self.element_simulation.run is None:
            run = self.element_simulation.request.default_run
        else:
            run = self.element_simulation.run

        self.setWindowTitle(f"Optimization Results: "
                            f"{element_simulation.recoil_elements[0].element}"
                            f" - {measured_element} - fluence: {run.fluence}")

        self.recoil_atoms = RecoilAtomOptimizationWidget(
            self, element_simulation, target,
            cancellation_token=cancellation_token)
        self.recoil_atoms.results_accepted.connect(self.results_accepted.emit)

    def delete(self):
        """Delete variables and do clean up.
        """
        self.recoil_atoms.delete()
        self.recoil_atoms = None
        self.close()

    def closeEvent(self, evnt):
        """Reimplemented method when closing widget. Remove existing
        optimization files. Stop optimization if necessary. Disconnect
        results_accepted signal.
        """
        self.element_simulation.delete_optimization_results(optim_mode="recoil")
        try:
            self.results_accepted.disconnect()
        except (TypeError, AttributeError):
            pass
        super().closeEvent(evnt)

    def update_progress(self, evaluations):
        """
        Show calculated solutions in the widget.
        """
        text = f"{evaluations} evaluations left. Running."
        if self.element_simulation.optimization_mcerd_running:
            text += " Simulating."
        self.progressLabel.setText(text)

    def show_results(self, evaluations):
        """
        Shjow optimized recoils and finished amount of evaluations.
        """
        self.progressLabel.setText(f"{evaluations} evaluations done. Finished.")
        self.recoil_atoms.show_recoils()

    def on_next_handler(self, msg):
        self.update_progress(msg["evaluations_left"])

    def on_error_handler(self, err):
        pass

    def on_complete_handler(self, msg):
        self.show_results(msg["evaluations_done"])
