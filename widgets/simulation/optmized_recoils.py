# coding=utf-8
"""
Created on 15.5.2019

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

from PyQt5 import QtWidgets
from PyQt5 import uic

from widgets.matplotlib.simulation.recoil_atom_optimization import \
    RecoilAtomOptimizationWidget


class OptimizedRecoilsWidget(QtWidgets.QWidget):
    """
    Class to show the results of optimization. Also shows the progress.
    """
    def __init__(self, element_simulation, measured_element):
        """
        Initialize the widget.
        """
        super().__init__()
        # TODO: Make ui file something proper
        self.ui = uic.loadUi(os.path.join("ui_files",
                                          "ui_optimization_results_widget.ui"),
                             self)
        self.ui.setWindowTitle(
            "Optimization Results: " +
            element_simulation.recoil_elements[0].element.__str__() +
            " - " + measured_element)
        self.recoil_atoms = RecoilAtomOptimizationWidget(self,
                                                         element_simulation)

    def update_progress(self, evaluations):
        """
        Show calculated solutions in the widget.
        """
        self.ui.progressLabel.setText(
            str(evaluations) + " evaluations done. Running.")

    def show_results(self, evaluations):
        """
        Shjow optimized recoils and finished amount of evaluations.
        """
        self.ui.progressLabel.setText(str(evaluations) +
                                      " evaluations done. Finished.")
        self.recoil_atoms.show_recoils()
