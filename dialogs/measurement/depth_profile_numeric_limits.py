# coding=utf-8
"""
Created on 17.3.2021
Updated on 28.3.2021

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2013-2018 Jarkko Aalto, Severi Jääskeläinen, Samuel Kaiponen,
Timo Konu, Samuli Kärkkäinen, Samuli Rahkonen, Miika Raunio, Heta Rekilä and
Sinikka Siironen, 2020 Juhani Sundell, Tuomas Pitkänen, 2021 Aleksi Kauppi

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
__author__ = "Aleksi Kauppi \n"
__version__ = "2.0"

import widgets.gui_utils as gutils

from PyQt5 import QtCore
from PyQt5 import uic
from PyQt5 import QtWidgets


class NumericLimitsDialog(QtWidgets.QDialog):
    """Numeric limits dialog for the depth profile graph.
    """

    def __init__(self, lim_a, lim_b, lim_min=-200, lim_max=2000):
        """Inits Depth profile numeric limits dialog.
        
        Args:
            lim_a, lim_b: limits to be shown in spinboxes
        """
        super().__init__()
        uic.loadUi(gutils.get_ui_dir() / "ui_depth_profile_limits.ui", self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # Connect and show
        self.OKButton.clicked.connect(self.accept_limits)
        self.cancelButton.clicked.connect(self.close)
        self.spinbox_limit_min.setRange(lim_min, lim_max)
        self.spinbox_limit_min.setSingleStep(1.0)
        self.spinbox_limit_min.setValue(lim_a)
        self.spinbox_limit_max.setRange(lim_min, lim_max)
        self.spinbox_limit_max.setSingleStep(1.0)
        self.spinbox_limit_max.setValue(lim_b)
        self.limit_min = lim_a
        self.limit_max = lim_b
        
        
    def accept_limits(self):
        """Accept limits.
        """
        self.limit_min = self.spinbox_limit_min.value()
        self.limit_max = self.spinbox_limit_max.value() 
        self.accept()
