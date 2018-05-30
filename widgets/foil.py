# coding=utf-8
"""
Created on 18.4.2018
Updated on 30.5.2018

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

import os
from PyQt5 import uic
from PyQt5 import QtWidgets


class FoilWidget(QtWidgets.QWidget):
    """Class for creating a foil widget for detector settings.
    """
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.ui = uic.loadUi(os.path.join("ui_files", "ui_foil_widget.ui"),
                             self)
        self.ui.deleteButton.clicked.connect(lambda: self._delete_foil())
        self.ui.distanceDoubleSpinBox.valueChanged.connect(
            lambda: self.__calculate_distance())

    def _delete_foil(self):
        confirm_box = QtWidgets.QMessageBox()
        confirm_box.setIcon(QtWidgets.QMessageBox.Warning)
        yes_button = confirm_box.addButton(QtWidgets.QMessageBox.Yes)
        confirm_box.addButton(QtWidgets.QMessageBox.Cancel)
        confirm_box.setText("Are you sure you want to delete the foil?")
        confirm_box.setWindowTitle("Confirm")

        confirm_box.exec()

        if confirm_box.clickedButton() == yes_button:
            self.parent.delete_foil(self)
            self.parent.calculate_distance()

    def __calculate_distance(self):
        self.parent.calculate_distance()
