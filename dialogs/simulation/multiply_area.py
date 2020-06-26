# coding=utf-8
"""
Created on 10.7.2018
Updated on 14.8.2018

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

import widgets.gui_utils as gutils

from typing import Optional
from modules.recoil_element import RecoilElement

from PyQt5 import QtWidgets
from PyQt5 import uic
from PyQt5.QtCore import QLocale


class MultiplyAreaDialog(QtWidgets.QDialog):
    """Dialog for choosing area multiplication parameters.
    """
    def __init__(self, main_recoil: RecoilElement, low: Optional[float] = None,
                 high: Optional[float] = None):
        """
        Initializes the dialog.

        Args:
            main_recoil: Main RecoilElement object.
        """
        super().__init__()
        uic.loadUi(gutils.get_ui_dir() / "ui_multiply_area_dialog.ui", self)

        self.main_recoil = main_recoil

        locale = QLocale.c()
        self.fractionDoubleSpinBox.setLocale(locale)

        self.cancelButton.clicked.connect(self.close)
        self.okButton.clicked.connect(self.ok_pressed)

        self.fractionCheckBox.stateChanged.connect(self.change_custom)
        self.fractionDoubleSpinBox.valueChanged.connect(
            self.calculate_new_area)

        self.main_area = self.main_recoil.calculate_area(start=low, end=high)
        text = str(round(self.main_area, 2))

        self.mainAreaLabel.setText(text)
        self.totalAreaLabel.setText(text)

        self.new_area = self.main_area
        self.reference_area = self.main_area
        self.fraction = None

        self.is_ok = False

        self.exec_()

    def calculate_new_area(self):
        """Calculate new area based on dialog's values.
        """
        ref_area = self.main_area

        if not ref_area:
            return

        # Find fraction
        if self.fractionCheckBox.isChecked():
            fraction = self.fractionDoubleSpinBox.value()
        else:
            fraction = 1.0

        area = ref_area * fraction
        self.totalAreaLabel.setText(str(round(area, 2)))

        self.new_area = area
        self.reference_area = ref_area
        self.fraction = fraction

    def change_custom(self):
        """Enable or disable custom area or fraction usage.
        """
        if self.sender() is self.fractionCheckBox:
            checked = self.fractionCheckBox.isChecked()
            self.fractionDoubleSpinBox.setEnabled(checked)
        self.calculate_new_area()

    def ok_pressed(self):
        """Note that Ok was pressed.
        """
        self.is_ok = True
        self.close()

    def can_multiply(self) -> bool:
        """Whether multiplication can be applied or not.

        Reference are and new are must be defined.
        """
        return self.is_ok and self.reference_area and self.new_area
