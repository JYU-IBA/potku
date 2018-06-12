# coding=utf-8
"""
Created on 3.5.2018
Updated on 30.5.2018

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

import os

from PyQt5 import uic
from PyQt5 import QtWidgets
import time


class RecoilInfoDialog(QtWidgets.QDialog):
    """Dialog for editing the name, description and reference density
    of a recoil element.
    """

    def __init__(self, recoil_element):
        """Inits a recoil info dialog.
        """
        super().__init__()
        self.__ui = uic.loadUi(os.path.join("ui_files",
                                            "ui_recoil_info_dialog.ui"),
                               self)

        self.__ui.okPushButton.clicked.connect(self.__accept_settings)
        self.__ui.cancelPushButton.clicked.connect(self.close)

        self.name = ""
        self.__ui.nameLineEdit.setText(recoil_element.name)
        self.__ui.descriptionLineEdit.setPlainText(
            recoil_element.description)
        self.__ui.referenceDensityDoubleSpinBox.setValue(
            recoil_element.reference_density)
        self.description = ""
        self.isOk = False

        self.__ui.dateLabel.setText(time.strftime("%c %z %Z", time.localtime(
            recoil_element.modification_time)))

        self.exec_()

    def __accept_settings(self):
        """Function for accepting the current settings and closing the dialog
        window.
        """
        self.name = self.__ui.nameLineEdit.text()
        self.description = self.__ui.descriptionLineEdit.toPlainText()
        self.reference_density = self.__ui.referenceDensityDoubleSpinBox\
            .value()
        self.isOk = True
        self.close()
