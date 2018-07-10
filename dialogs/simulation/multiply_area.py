# coding=utf-8
"""
Created on 10.7.2018

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


class MultiplyAreaDialog(QtWidgets.QDialog):
    """
    Dialog for choosing area multiplication parameters.
    """
    def __init__(self, main_recoil):
        """
        Initializes the dialog.

        Args:
            main_recoil: Main RecoilElement object.
        """
        super().__init__()
        self.ui = uic.loadUi(os.path.join("ui_files",
                                          "ui_multiply_area_dialog.ui"),
                             self)
        self.main_recoil = main_recoil

        locale = QLocale.c()
        self.ui.fractionDoubleSpinBox.setLocale(locale)
        self.ui.customAreaDoubleSpinBox.setLocale(locale)

        self.ui.cancelButton.clicked.connect(self.close)
        self.ui.fractionCheckBox.stateChanged.connect(self.change_custom)
        self.ui.mainRecoilAreaRadioButton.clicked.connect(self.change_custom)
        self.ui.customAreaRadioButton.clicked.connect(self.change_custom)
        self.ui.customAreaDoubleSpinBox.valueChanged.connect(
            self.calculate_new_area)
        self.ui.fractionDoubleSpinBox.valueChanged.connect(
            self.calculate_new_area)

        if self.main_recoil.area is None:
            text = str(None)
        else:
            text = str(round(self.main_recoil.area, 2))

        self.ui.mainAreaLabel.setText(text)
        self.ui.totalAreaLabel.setText(text)

        self.new_area = self.main_recoil.area
        self.reference_area = None
        self.fraction = None

        self.exec_()

    def calculate_new_area(self):
        """
        Calculate new area based on dialog's values.
        """
        # Find reference area value
        if self.ui.mainAreaLabel.isEnabled():
            ref_area = self.main_recoil.area
        else:
            ref_area = self.ui.customAreaDoubleSpinBox.value()

        # Find fraction
        if self.ui.fractionCheckBox.isChecked():
            fraction = self.ui.fractionDoubleSpinBox.value()
        else:
            fraction = 1.0

        area = ref_area * fraction
        self.ui.totalAreaLabel.setText(str(round(area, 2)))

        self.new_area = area
        self.reference_area = ref_area
        self.fraction = fraction

    def change_custom(self):
        """
        Enable or disable custom area or fraction usage.
        """
        if self.sender() is self.ui.fractionCheckBox:
            checked = self.ui.fractionCheckBox.isChecked()
            self.ui.fractionDoubleSpinBox.setEnabled(checked)
        elif self.sender() is self.ui.customAreaRadioButton:
            self.ui.customAreaDoubleSpinBox.setEnabled(True)
            self.ui.mainAreaLabel.setEnabled(False)
        elif self.sender() is self.ui.mainRecoilAreaRadioButton:
            self.ui.customAreaDoubleSpinBox.setEnabled(False)
            self.ui.mainAreaLabel.setEnabled(True)
        self.calculate_new_area()
