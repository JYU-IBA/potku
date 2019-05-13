# coding=utf-8
"""
Created on 13.5.2019

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

from PyQt5 import uic
from PyQt5 import QtCore
from PyQt5.QtCore import QLocale
from PyQt5 import QtWidgets


class OptimizationDialog(QtWidgets.QDialog):
    def __init__(self, simulation):
        super().__init__()

        self.simulation = simulation
        self.ui = uic.loadUi(
            os.path.join("ui_files", "ui_optimization_params.ui"), self)

        locale = QLocale.c()
        self.ui.histogramTicksDoubleSpinBox.setLocale(locale)
        self.ui.pushButton_Cancel.clicked.connect(self.close)

        self.exec_()
