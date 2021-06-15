# coding=utf-8
"""
Created on 18.5.2021
Updated on 18.5.2021

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2013-2018 Jarkko Aalto, Severi Jääskeläinen, Samuel Kaiponen,
Timo Konu, Samuli Kärkkäinen, Samuli Rahkonen, Miika Raunio, Heta Rekilä and
Sinikka Siironen, 2020 Juhani Sundell, 2021 Aleksi Kauppi

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

__author__ = "Aleksi Kauppi"
__version__ = "2.0"

import widgets.gui_utils as gutils

from PyQt5 import uic
from PyQt5 import QtCore
from PyQt5 import QtWidgets

from widgets.matplotlib.eff_plot import \
    MatplotlibEfficiencyWidget

class EfficiencyWidget(QtWidgets.QWidget):
    """Efficiency widget which is opened on top of detector settings.
    """

    def __init__(self, efficiency_files, parent_widget=None):
        """Inits widget.
        
        Args:
            parent: A TabWidget.
            efficiency_files: Paths to .eff files
        """
        super().__init__()
        uic.loadUi(gutils.get_ui_dir() / "ui_eff_plot.ui", self)
        
        self.parent_widget = parent_widget
        self.efficiency_files = efficiency_files

        self.show()
        self.raise_()
        self.activateWindow()


        self.matplotlib = MatplotlibEfficiencyWidget(self, self.efficiency_files)

    def delete(self):
        """Delete variables and do clean up.
        """
        if self.matplotlib is not None:
            self.matplotlib.delete()
        self.matplotlib = None
        self.close()
