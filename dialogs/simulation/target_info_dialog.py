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

import os
import time

import widgets.input_validation as iv

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
        self.ui = uic.loadUi(os.path.join("ui_files", "ui_target_info.ui"),
                             self)
        self.target = target

        self.ui.okPushButton.clicked.connect(self.__accept_settings)
        self.ui.cancelPushButton.clicked.connect(self.close)

        iv.set_input_field_red(self.ui.nameLineEdit)
        self.fields_are_valid = False
        self.ui.nameLineEdit.textChanged.connect(
            lambda: self.__check_text(self.ui.nameLineEdit, self))

        self.name = ""
        self.ui.nameLineEdit.setText(target.name)
        self.ui.descriptionLineEdit.setPlainText(target.description)
        self.description = ""
        self.isOk = False

        self.ui.dateLabel.setText(time.strftime("%c %z %Z", time.localtime(
            target.modification_time)))

        self.nameLineEdit.textEdited.connect(
            lambda: iv.sanitize_file_name(self.nameLineEdit))

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
            self.name = self.ui.nameLineEdit.text()
            self.description = self.ui.descriptionLineEdit.toPlainText()
            self.isOk = True
            self.__close = True
        if self.__close:
            self.close()

    @staticmethod
    def __check_text(input_field, settings):
        """Checks if there is text in given input field.

        Args:
            input_field: Input field the contents of which are checked.
            settings: Settings dialog.
        """
        settings.fields_are_valid = iv.check_text(input_field)
