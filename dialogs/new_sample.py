# coding=utf-8
"""
Created on 26.2.2018
Updated on 12.6.2018

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2013-2018 Jarkko Aalto, Severi Jääskeläinen, Samuel Kaiponen,
Timo Konu, Samuli Kärkkäinen, Samuli Rahkonen, Miika Raunio, Heta Rekilä and
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
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n " \
             "Sinikka Siironen"
__version__ = "2.0"

import widgets.input_validation as iv
import widgets.gui_utils as gutils

from PyQt5 import uic
from PyQt5 import QtWidgets


class NewSampleDialog(QtWidgets.QDialog):
    """Dialog for creating a new sample.
    """
    def __init__(self, samples):
        """Inits a new sample dialog.

        Args:
            samples: List of samples.
        """
        super().__init__()
        uic.loadUi(gutils.get_ui_dir() / "ui_new_sample.ui", self)

        self.createButton.clicked.connect(self.__create_sample)
        self.cancelButton.clicked.connect(self.close)
        self.name = ""
        self.description = ""
        self.samples = samples
        self.__close = True

        iv.set_input_field_red(self.nameLineEdit)
        self.nameLineEdit.textChanged.connect(
            lambda: iv.check_text(self.nameLineEdit))
        self.nameLineEdit.textEdited.connect(
            lambda: iv.sanitize_file_name(self.nameLineEdit))

        self.exec_()

    def __create_sample(self):
        """Read sample name from view and if it is accepted, close dialog.
        """
        self.name = self.nameLineEdit.text()
        if not self.name:
            self.nameLineEdit.setFocus()
            return
        for sample in self.samples:
            if sample.name == self.name:
                QtWidgets.QMessageBox.critical(self, "Already exists",
                                               "There already is a "
                                               "sample with this name!"
                                               "\n\n Choose another "
                                               "name.",
                                               QtWidgets.QMessageBox.Ok,
                                               QtWidgets.QMessageBox.Ok)
                self.__close = False
                break
            else:
                self.__close = True
        if self.__close:
            self.close()
