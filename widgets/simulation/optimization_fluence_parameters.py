# coding=utf-8
"""
Created on 20.5.2019
Updated on 21.5.2019

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
from PyQt5.QtCore import QLocale


class OptimizationFluenceParameterWidget(QtWidgets.QWidget):
    """
    Class that handles the fluence optimization parameters' ui.
    """
    def __init__(self, params=None):
        """
        Initialize the widget.

        Args:
            params: Possible paramaters tos display in the widget.
        """
        super().__init__()
        self.ui = uic.loadUi(
            os.path.join("ui_files", "ui_optimization_fluence_params.ui"), self)

        locale = QLocale.c()
        self.ui.crossoverProbDoubleSpinBox.setLocale(locale)
        self.ui.mutationProbDoubleSpinBox.setLocale(locale)
        self.ui.percentDoubleSpinBox.setLocale(locale)
        self.ui.fluenceDoubleSpinBox.setLocale(locale)

        if params:
            self.ui.populationSpinBox.setValue(params[0])
            self.ui.generationSpinBox.setValue(params[1])
            self.ui.processesSpinBox.setValue(params[2])
            self.ui.percentDoubleSpinBox.setValue(params[3])
            self.ui.timeSpinBox.setValue(params[4])
            self.ui.crossoverProbDoubleSpinBox.setValue(params[5])
            self.ui.mutationProbDoubleSpinBox.setValue(params[6])
            self.ui.disCSpinBox.setValue(params[7])
            self.ui.disMSpinBox.setValue(params[8])
            self.ui.fluenceDoubleSpinBox.setValue(params[9])
