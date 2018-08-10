# coding=utf-8
"""
Created on 10.8.2018

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2018 Heta Rekilä

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


class PercentageWidget(QtWidgets.QWidget):
    """
    Class for a widget that calculates the percentages for given recoils and
    intervals.
    """

    def __init__(self, recoil_elements, same_interval):
        """
        Initialize the widget.

        Args:
            recoil_elements: List of recoil elements.
            same_interval: Interval that used for all the recoils.
        """
        super().__init__()
        self.recoil_elements = recoil_elements
        self.common_interval = same_interval
        self.ui = uic.loadUi(os.path.join("ui_files",
                                          "ui_percentage_widget.ui"), self)

        self.setWindowTitle("Percentages")

