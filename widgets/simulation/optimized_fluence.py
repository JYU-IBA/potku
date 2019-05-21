# coding=utf-8
"""
Created on 21.5.2019

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

from modules.general_functions import round_value_by_four_biggest

from PyQt5 import QtWidgets
from PyQt5 import uic


class OptimizedFluenceWidget(QtWidgets.QWidget):
    """
    Class that handles showing optimized fluence in a widget.
    """
    def __init__(self, element_simulation):
        super().__init__()
        self.ui = uic.loadUi(os.path.join("ui_files",
                                          "ui_optimized_fluence_widget.ui"),
                             self)
        self.element_simulation = element_simulation

    def delete(self):
        """Delete variables and do clean up.
        """
        self.ui.close()
        self.ui = None
        self.close()

    def closeEvent(self, evnt):
        """Reimplemented method when closing widget. Remove existing
        optimization files. Stop optimization if necessary.
        """
        if self.element_simulation.mcerd_objects and \
                self.element_simulation.optimization_running:
            self.element_simulation.stop(optimize=True)
            self.element_simulation.optimization_running = False
        self.element_simulation.optimization_stopped = True
        self.element_simulation.optimization_widget = None

        # Delete existing files from previous optimization
        removed_files = []
        for file in os.listdir(self.element_simulation.directory):
            if "optfl" in file:
                removed_files.append(file)
        for rf in removed_files:
            path = os.path.join(self.element_simulation.directory, rf)
            os.remove(path)

        super().closeEvent(evnt)

    def update_progress(self, evaluations):
        """
        Show calculated solutions in the widget.
        """
        self.ui.progressLabel.setText(
            str(evaluations) + " evaluations done. Running.")

    def show_fluence(self):
        """
        Show optimized fluence in widget.
        """
        rounded_fluence = round_value_by_four_biggest(
            self.element_simulation.optimized_fluence)
        self.ui.fluenceLineEdit.setText(str(int(
            self.element_simulation.optimized_fluence)))
        self.ui.roundedFluenceLineEdit.setText(str(rounded_fluence))


    def show_results(self, evaluations):
        """
        Shjow optimized fluence and finished amount of evaluations.
        """
        self.ui.progressLabel.setText(str(evaluations) +
                                      " evaluations done. Finished.")
        self.show_fluence()
