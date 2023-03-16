# coding=utf-8
"""
Created on 14.5.2019
Updated on 23.5.2019

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

import widgets.gui_utils as gutils

from typing import Optional

from modules.element_simulation import ElementSimulation
from modules.nsgaii import OptimizationType
from modules.concurrency import CancellationToken
from modules.target import Target

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

    def __init__(self, element_simulation: ElementSimulation,
                 cut_file_name: str, target: Target,
                 ct: Optional[CancellationToken] = None):
        """
        Initialize the widget.
        """
        # TODO make a common base class for result widgets
        # TODO change the push button to radio group
        super().__init__()
        GUIObserver.__init__(self)
        uic.loadUi(
            gutils.get_ui_dir() / "ui_optimization_results_widget.ui", self)

        self.element_simulation = element_simulation
        _, run, _ = self.element_simulation.get_mcerd_params()

        self.setWindowTitle(f"Optimization Results: "
                            f"{element_simulation.get_main_recoil().element}"
                            f" - {cut_file_name} - fluence: {run.fluence:e}")

        self.recoil_atoms = RecoilAtomOptimizationWidget(
            self, element_simulation, target, ct=ct)
        self.pareto_front = RecoilAtomParetoFront(self)

        self.recoil_atoms.results_accepted.connect(self.results_accepted.emit)
        self.rb_group_optim.buttonToggled.connect(self.switch_widget)

    def switch_widget(self, rb: QtWidgets.QRadioButton, b: bool):
        """Switches between Recoil distribution and Pareto front views.
        """
        if not b:
            return
        if rb.text().startswith("Recoil"):
            self.stackedWidget.setCurrentIndex(0)
            self.beamLabel.show()
        else:
            self.stackedWidget.setCurrentIndex(1)
            self.beamLabel.hide()

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

    def update_progress(self, state, evaluations=None):
        """
        Show calculated solutions in the widget.
        """
        if evaluations is not None:
            text = f"{evaluations} evaluations left. {state}."
        else:
            text = f"{state}."
        self.progressLabel.setText(text)

    def show_results(self, evaluations=None, errors=None):
        """
        Show optimized recoils. Optionally show finished amount of evaluations
        and/or errors.
        """
        if evaluations is not None:
            progress_text = f"{evaluations} evaluations done. Finished."
        else:
            progress_text = "Finished."

        if errors is not None:
            progress_text += str(errors)

        self.progressLabel.setText(progress_text)
        self.recoil_atoms.show_recoils()

    def on_next_handler(self, msg):
        if "evaluations_left" in msg:
            self.update_progress(
                msg["state"], evaluations=msg["evaluations_left"])
        else:
            self.update_progress(msg["state"])
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
            evaluations_done = msg.get("evaluations_done")
            error = msg.get("error")
            self.show_results(evaluations_done, errors=error)
