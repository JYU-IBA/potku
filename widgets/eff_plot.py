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

import os
import shutil

import dialogs.dialog_functions as df
import widgets.gui_utils as gutils
import dialogs.file_dialogs as fdialogs
import widgets.binding as bnd

from pathlib import Path

from widgets.base_tab import BaseTab

from PyQt5 import uic
from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5.QtCore import QLocale

from widgets.matplotlib.eff_plot import \
    MatplotlibEfficiencyWidget

class EfficiencyWidget(QtWidgets.QWidget):
    """Energy spectrum widget which is added to measurement tab.
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
        #self.icon_manager = parent.icon_manager
        self.efficiency_files = efficiency_files
        print("2")
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

        
        #self.raise_()
        self.show()
        self.activateWindow()
        #self.raise_()
        #self.setFocus(True)

        self.matplotlib = MatplotlibEfficiencyWidget(self, self.efficiency_files)

    def delete(self):
        """Delete variables and do clean up.
        """
        if self.matplotlib is not None:
            self.matplotlib.delete()
        self.matplotlib = None
        self.close()
