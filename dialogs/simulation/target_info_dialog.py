# coding=utf-8
"""
Created on 16.7.2018
Updated on 13.4.2023

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2018 Heta Rekilä, 2023 Sami Voutilainen

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
__author__ = "Heta Rekilä \n Sami Voutilainen"
__version__ = "2.0"

import time

import widgets.input_validation as iv
import widgets.gui_utils as gutils

from PyQt5 import uic
from PyQt5 import QtWidgets

from widgets.scientific_spinbox import ScientificSpinBox


class TargetInfoDialog(QtWidgets.QDialog):
    """
    Dialog for editing target name and description.
    """

    def __init__(self, target):
        """
        Initialize the dialog.

        Args:
            target: Target object.
        """
        super().__init__()
        uic.loadUi(gutils.get_ui_dir() / "ui_target_info.ui", self)

        self.target = target

        self.okPushButton.clicked.connect(self.__accept_settings)
        self.cancelPushButton.clicked.connect(self.close)

        self.fields_are_valid = True
        iv.set_input_field_red(self.nameLineEdit)
        self.nameLineEdit.textChanged.connect(
            lambda: iv.check_text(self.nameLineEdit, qwidget=self))
        self.nameLineEdit.textEdited.connect(
            lambda: iv.sanitize_file_name(self.nameLineEdit))
        self.nameLineEdit.setEnabled(False)

        self.name = ""
        self.nameLineEdit.setText(target.name)
        self.descriptionLineEdit.setPlainText(target.description)
        self.description = ""
        self.isOk = False

        self.dateLabel.setText(time.strftime("%c %z %Z", time.localtime(
            target.modification_time)))

        self.manual_value = self.target.reference_density.manual_density
        self.dynamic_value = self.target.reference_density.dynamic_density
        self.use_user_value = self.target.reference_density.use_user_value
        self.scientific_spinbox_manual = ScientificSpinBox(
            value=self.manual_value, minimum=0.0, maximum=9.99e26)
        if not self.use_user_value:
            self.scientific_spinbox_manual.setEnabled(False)

        self.useManualValueCheckBox.setChecked(self.use_user_value)
        self.useManualValueCheckBox.stateChanged.connect(self.toggle_settings)

        self.formLayout.insertRow(
            4,
            QtWidgets.QLabel(r"Manual [at./cm<sup>3</sup>]:"),
            self.scientific_spinbox_manual)

        self.valueLabelDynamic.setText(f"{self.dynamic_value}")

        # Hide unnecessary UI elements for now, instead of deleting.
        self.nameLineEdit.hide()
        self.descriptionLineEdit.hide()
        self.dateLabel.hide()
        self.label_31.hide()
        self.label_32.hide()
        self.label_33.hide()

        self.resize(self.minimumSizeHint())

        self.__close = True

        self.exec_()

    def toggle_settings(self):

        if self.use_user_value:
            self.scientific_spinbox_manual.setEnabled(False)
            self.use_user_value = False
        else:
            self.scientific_spinbox_manual.setEnabled(True)
            self.use_user_value = True

    def __accept_settings(self):
        """Function for accepting the current settings and closing the dialog
        window.
        """
        if not self.fields_are_valid:
            QtWidgets.QMessageBox.critical(self, "Warning",
                                           "Target must always have "
                                           "a name.\nPlease input a name for "
                                           "the target.",
                                           QtWidgets.QMessageBox.Ok,
                                           QtWidgets.QMessageBox.Ok)
            self.__close = False
        else:
            self.name = self.nameLineEdit.text()
            self.description = self.descriptionLineEdit.toPlainText()
            if self.use_user_value:
                self.manual_value = self.scientific_spinbox_manual.value()
            self.isOk = True
            self.__close = True
        if self.__close:
            self.close()
