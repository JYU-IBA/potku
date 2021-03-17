# coding=utf-8
"""
Created on 21.3.2013
Updated on 30.5.2018

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2013-2018 Jarkko Aalto, Severi Jääskeläinen, Samuel Kaiponen,
Timo Konu, Samuli Kärkkäinen, Samuli Rahkonen, Miika Raunio, Heta Rekilä and
Sinikka Siironen, 2020 Juhani Sundell, Tuomas Pitkänen

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
__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen" \
             " \n Samuli Rahkonen \n Miika Raunio \n Severi Jääskelänen \n " \
             "Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen" \
             "Juhani Sundell \n Tuomas Pitkänen"
__version__ = "2.0"

import widgets.binding as bnd
import widgets.gui_utils as gutils

from PyQt5 import QtCore
from PyQt5 import uic
from PyQt5 import QtWidgets


class NumericLimitsDialog(QtWidgets.QDialog):
    """Numeric limits dialog for the depth profile graph.
    """
    color_scheme = bnd.bind("colorbox")

    def __init__(self, parent):
        """Inits Depth profile numeric limits dialog.
        
        Args:
            parent: MatplotlibDepthProfileWidget which limits are being changed.
        """
        super().__init__()
        uic.loadUi(gutils.get_ui_dir() / "ui_depth_profile_limits.ui", self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.parent = parent
        self.parent.show_yourself(self)

        # Connect and show
        self.OKButton.clicked.connect(self.accept_limits)
        self.cancelButton.clicked.connect(self.close)

        self.exec_()

    def accept_limits(self):
        """Accept limits.
        """
        limit_min = self.spinbox_limit_min.value()
        limit_max = self.spinbox_limit_max.value()
        self.parent._limit_lines.update_graph(limit_min)
        self.parent._limit_lines.update_graph(limit_max)  
        self.close()
        
