# coding=utf-8
"""
Created on 15.3.2018
Updated on 13.6.2018

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

from modules.general_functions import set_input_field_red
from modules.general_functions import check_text
from modules.general_functions import validate_text_input


class SimulationSettingsWidget(QtWidgets.QWidget):
    """Class for creating a simulation settings tab.
    """
    def __init__(self):
        """
        Initializes the widget.
        """
        super().__init__()
        self.ui = uic.loadUi(os.path.join("ui_files",
                                          "ui_request_simulation_settings.ui"),
                             self)

        set_input_field_red(self.ui.nameLineEdit)
        self.fields_are_valid = False
        self.ui.nameLineEdit.textChanged.connect(lambda: self.__check_text(
            self.ui.nameLineEdit, self))

        self.ui.nameLineEdit.textEdited.connect(lambda: self.__validate())

    @staticmethod
    def __check_text(input_field, settings):
        """Checks if there is text in given input field.

        Args:
            input_field: Input field the contents of which are checked.
            settings: Settings widget.
        """
        settings.fields_are_valid = check_text(input_field)

    def __validate(self):
        """
        Validate the mcsimu settings file name.
        """
        text = self.ui.nameLineEdit.text()
        regex = "^[A-Za-z0-9-ÖöÄäÅå]*"
        valid_text = validate_text_input(text, regex)

        self.ui.nameLineEdit.setText(valid_text)
