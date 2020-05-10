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
from typing import Optional

from modules.element_simulation import ElementSimulation
from modules.nsgaii import OptimizationType
from modules.concurrency import CancellationToken

from widgets.gui_utils import GUIObserver

from PyQt5 import QtWidgets
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal

from widgets.matplotlib.simulation.recoil_atom_optimization import \
    RecoilAtomOptimizationWidget
from widgets.matplotlib.simulation.recoil_atom_optimization import \
    RecoilAtomParetoFront


class OptimizedRecoilsWidget(QtWidgets.QWidget, GUIObserver):
    """
    Class to show the results of optimization. Also shows the progress.
    """
    results_accepted = pyqtSignal(ElementSimulation)

    def __init__(self, element_simulation: ElementSimulation, measured_element,
                 target,
                 cancellation_token: Optional[CancellationToken] = None):
        """
        Initialize the widget.
        """
        # TODO make a common base class for result widgets
        # TODO change the push button to radio group
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
        self.pareto_front = RecoilAtomParetoFront(self)

        self.recoil_atoms.results_accepted.connect(self.results_accepted.emit)
        self.pushButton.clicked.connect(self.switch_widget)

    def switch_widget(self):
        self.stackedWidget: QtWidgets.QStackedWidget
        if self.stackedWidget.currentIndex() == 1:
            self.pushButton.setText("Show Pareto front")
            self.stackedWidget.setCurrentIndex(0)
        else:
            self.pushButton.setText("Show distribution")
            self.stackedWidget.setCurrentIndex(1)

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
        # TODO stop optimization
        self.element_simulation.delete_optimization_results(
            optim_mode=OptimizationType.RECOIL)
        try:
            self.results_accepted.disconnect()
        except (TypeError, AttributeError):
            pass
        super().closeEvent(evnt)

    def update_progress(self, evaluations, state):
        """
        Show calculated solutions in the widget.
        """
        text = f"{evaluations} evaluations left. {state}."
        self.progressLabel.setText(text)

    def show_results(self, evaluations):
        """
        Show optimized recoils and finished amount of evaluations.
        """
        self.progressLabel.setText(f"{evaluations} evaluations done. Finished.")
        self.recoil_atoms.show_recoils()

    def on_next_handler(self, msg):
        if "evaluations_left" in msg:
            self.update_progress(msg["evaluations_left"], msg["state"])
        if "pareto_front" in msg:
            self.pareto_front.update_pareto_front(msg["pareto_front"])

    def on_error_handler(self, err):
        try:
            err_msg = err["error"]
        except TypeError:
            # rx error
            err_msg = err

        text = f"Error encountered: {err_msg} Optimization stopped."
        self.progressLabel.setText(text)

    def on_completed_handler(self, msg=None):
        if msg is not None:
            self.show_results(msg["evaluations_done"])
