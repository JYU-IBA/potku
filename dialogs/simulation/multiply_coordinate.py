# coding=utf-8
"""
Created on 27.8.2018

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
from PyQt5.QtCore import QLocale


class MultiplyCoordinateDialog(QtWidgets.QDialog):
    """
    A dialog that is used to multiply point coordinates.
    """
    def __init__(self, clipboard_ratio):
        """
        Initializes the dialog.

        Args:
            clipboard_ratio: Text that is in clipboard.
        """
        super().__init__()

        self.ui = uic.loadUi(os.path.join("ui_files",
                                          "ui_multiply_coordinate_dialog.ui"),
                             self)
        self.ratio_str = clipboard_ratio
        self.used_multiplier = None

        locale = QLocale.c()
        self.ui.multiplierSpinBox.setLocale(locale)

        try:
            float(self.ratio_str)

            self.ui.ratioLabel.setText(self.ratio_str)
        except ValueError:
            self.ui.ratioLabel.setText("None")
            self.ui.ratioLabel.setEnabled(False)
            self.ui.clipboardButton.setChecked(False)
            self.ui.clipboardButton.setEnabled(False)

            self.ui.customButton.setChecked(True)
            self.ui.multiplierSpinBox.setEnabled(True)

        self.ui.clipboardButton.clicked.connect(self.switch_to_clipboard_value)
        self.ui.customButton.clicked.connect(self.switch_to_custom_value)
        self.ui.okButton.clicked.connect(self.accept_params)
        self.ui.cancelButton.clicked.connect(self.close)
        self.exec_()

    def accept_params(self):
        """
        Accept params for multiplying.
        """
        if self.ui.customButton.isChecked():
            self.used_multiplier = round(self.ui.multiplierSpinBox.value(), 3)
        else:
            self.used_multiplier = float(self.ui.ratioLabel.text())
        self.close()

    def switch_to_clipboard_value(self):
        """
        Show clipboard value as selected.
        """
        self.ui.clipboardButton.setChecked(True)
        self.ui.customButton.setChecked(False)
        self.ui.multiplierSpinBox.setEnabled(False)
        self.ui.ratioLabel.setEnabled(True)

    def switch_to_custom_value(self):
        """
        Show custom value as selected.
        """
        self.ui.customButton.setChecked(True)
        self.ui.multiplierSpinBox.setEnabled(True)
        self.ui.clipboardButton.setChecked(False)
        self.ui.ratioLabel.setEnabled(False)
