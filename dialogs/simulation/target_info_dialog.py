# coding=utf-8
"""
Created on 16.7.2018

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

import time

import widgets.input_validation as iv
import widgets.gui_utils as gutils

from PyQt5 import uic
from PyQt5 import QtWidgets


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

        self.fields_are_valid = False
        iv.set_input_field_red(self.nameLineEdit)
        self.nameLineEdit.textChanged.connect(
            lambda: iv.check_text(self.nameLineEdit, qwidget=self))
        self.nameLineEdit.textEdited.connect(
            lambda: iv.sanitize_file_name(self.nameLineEdit))

        self.name = ""
        self.nameLineEdit.setText(target.name)
        self.descriptionLineEdit.setPlainText(target.description)
        self.description = ""
        self.isOk = False

        self.dateLabel.setText(time.strftime("%c %z %Z", time.localtime(
            target.modification_time)))

        self.__close = True

        self.exec_()

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
            self.isOk = True
            self.__close = True
        if self.__close:
            self.close()
