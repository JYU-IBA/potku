# coding=utf-8
"""
Created on 18.4.2018
Updated on 25.6.2018

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2018 Severi Jääskeläinen, Samuel Kaiponen, Heta Rekilä and
Sinikka Siironen

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
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä " \
             "\n Sinikka Siironen"
__version__ = "2.0"

import widgets.binding as bnd
import widgets.gui_utils as gutils

from PyQt5 import uic
from PyQt5 import QtWidgets
from PyQt5.QtCore import QLocale
from PyQt5.QtCore import pyqtSignal


class FoilWidget(QtWidgets.QWidget):
    """Class for creating a foil widget for detector settings.
    """
    foil_deletion = pyqtSignal(QtWidgets.QWidget)

    # Distance in nanometers from previous foil or Target if this is the first
    # foil
    distance_from_previous = bnd.bind("distanceDoubleSpinBox")
    # Distance from Target in nanometers
    cumulative_distance = bnd.bind("distanceLabel")

    name = bnd.bind("foilButton")

    def __init__(self, foil):
        """
        Initializes the foil widget.

        Args:
            foil: foil object
        """
        super().__init__()
        uic.loadUi(gutils.get_ui_dir() / "ui_foil_widget.ui", self)

        locale = QLocale.c()
        self.distanceDoubleSpinBox.setLocale(locale)
        self.deleteButton.clicked.connect(self._delete_foil)

        self.name = foil.name
        self.distance_from_previous = 0
        self.cumulative_distance = foil.distance

    def _delete_foil(self):
        """
        Delete a foil.
        """
        confirm_box = QtWidgets.QMessageBox()
        confirm_box.setIcon(QtWidgets.QMessageBox.Warning)
        yes_button = confirm_box.addButton(QtWidgets.QMessageBox.Yes)
        confirm_box.addButton(QtWidgets.QMessageBox.Cancel)
        confirm_box.setText("Are you sure you want to delete the foil?")
        confirm_box.setWindowTitle("Confirm")

        confirm_box.exec()

        if confirm_box.clickedButton() == yes_button:
            self.foil_deletion.emit(self)
