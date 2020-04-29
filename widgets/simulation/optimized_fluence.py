# coding=utf-8
"""
Created on 21.5.2019
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

import modules.general_functions as gf

from pathlib import Path

from modules.element_simulation import ElementSimulation

from widgets.gui_utils import GUIObserver

from PyQt5 import QtWidgets
from PyQt5 import uic


class OptimizedFluenceWidget(QtWidgets.QWidget, GUIObserver):
    """
    Class that handles showing optimized fluence in a widget.
    """
    def __init__(self, element_simulation: ElementSimulation,
                 cancellation_token=None):
        # TODO common base class for optim result widgets
        super().__init__()
        uic.loadUi(Path("ui_files", "ui_optimized_fluence_widget.ui"), self)

        self.element_simulation = element_simulation
        if self.element_simulation.optimized_fluence:
            self.show_fluence()

        # TODO implement cancellation_token

    def delete(self):
        """Delete variables and do clean up.
        """
        self.close()

    def closeEvent(self, evnt):
        """Reimplemented method when closing widget. Remove existing
        optimization files. Stop optimization if necessary.
        """
        self.element_simulation.delete_optimization_results(
            optim_mode="fluence")

        super().closeEvent(evnt)

    def update_progress(self, evaluations):
        """
        Show calculated solutions in the widget.
        """
        text = f"{evaluations} evaluations left. Running."
        if self.element_simulation.optimization_mcerd_running:
            text += " Simulating."
        self.progressLabel.setText(text)

    def show_fluence(self):
        """
        Show optimized fluence in widget.
        """
        rounded_fluence = gf.round_value_by_four_biggest(
            self.element_simulation.optimized_fluence)
        self.fluenceLineEdit.setText(str(int(
            self.element_simulation.optimized_fluence)))
        self.roundedFluenceLineEdit.setText(str(rounded_fluence))

    def show_results(self, evaluations):
        """
        Shjow optimized fluence and finished amount of evaluations.
        """
        self.progressLabel.setText(f"{evaluations} evaluations left. Finished.")
        self.show_fluence()

    def on_next_handler(self, msg):
        self.update_progress(msg["evaluations_left"])

    def on_error_handler(self, err):
        pass

    def on_completed_handler(self, msg):
        self.show_results(msg["evaluations_done"])
