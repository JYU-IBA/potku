# coding=utf-8
"""
Created on 21.5.2019
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

import modules.general_functions as gf
import widgets.gui_utils as gutils

from typing import Optional

from modules.element_simulation import ElementSimulation
from modules.nsgaii import OptimizationType
from modules.concurrency import CancellationToken

from widgets.gui_utils import GUIObserver

from PyQt5 import QtWidgets
from PyQt5 import uic


class OptimizedFluenceWidget(QtWidgets.QWidget, GUIObserver):
    """Class that handles showing optimized fluence in a widget.
    """
    def __init__(self, element_simulation: ElementSimulation,
                 ct: Optional[CancellationToken] = None):
        # TODO common base class for optim result widgets
        super().__init__()
        uic.loadUi(gutils.get_ui_dir() / "ui_optimized_fluence_widget.ui", self)

        self.element_simulation = element_simulation
        if self.element_simulation.optimized_fluence:
            self.show_fluence()

        self.cancellation_token = ct

    def delete(self):
        """Delete variables and do clean up.
        """
        self.close()

    def closeEvent(self, evnt):
        """Reimplemented method when closing widget. Remove existing
        optimization files. Stop optimization if necessary.
        """
        if self.cancellation_token is not None:
            self.cancellation_token.request_cancellation()
        self.element_simulation.delete_optimization_results(
            optim_mode=OptimizationType.FLUENCE)

        super().closeEvent(evnt)

    def update_progress(self, state, evaluations=None):
        """Show calculated solutions in the widget.
        """
        if evaluations is not None:
            text = f"{evaluations} evaluations left. Running."
        else:
            text = f"{state}."

        if self.element_simulation.is_optimization_running():
            text += " Simulating."
        self.progressLabel.setText(text)

    def show_fluence(self):
        """
        Show optimized fluence in widget.
        """
        rounded_fluence = gf.round_value_by_four_biggest(
            self.element_simulation.optimized_fluence)
        self.fluenceLineEdit.setText(
            f"{self.element_simulation.optimized_fluence:e}")
        self.roundedFluenceLineEdit.setText(f"{rounded_fluence:e}")

    def show_results(self, evaluations=None, errors=None):
        """Show optimized fluence. Optionally show finished amount of
        evaluations and/or errors.
        """
        if evaluations is not None:
            progress_text = f"{evaluations} evaluations done. Finished."
        else:
            progress_text = "Finished."

        if errors is not None:
            progress_text += str(errors)

        self.progressLabel.setText(progress_text)
        self.show_fluence()

    def on_next_handler(self, msg):
        if "evaluations_left" in msg:
            self.update_progress(
                msg["state"], evaluations=msg["evaluations_left"])
        else:
            self.update_progress(msg["state"])

    def on_error_handler(self, err):
        # TODO fix the layout of the dialog show that this is shown properly.
        self.progressLabel.setText(
            f"Error occurred: {err['error']}. Optimization stopped.")

    def on_completed_handler(self, msg=None):
        if msg is not None:
            evaluations_done = msg.get("evaluations_done")
            error = msg.get("error")
            self.show_results(evaluations_done, errors=error)
