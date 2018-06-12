# coding=utf-8
"""
Created on 11.4.2013
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
__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen \n " \
             "Samuli Rahkonen \n Miika Raunio \n Severi Jääskeläinen \n "\
             "Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"
__version__ = "2.0"

import logging
import os

from PyQt5 import uic
from PyQt5 import QtWidgets
from modules.general_functions import validate_text_input
from modules.general_functions import check_text
from modules.general_functions import set_input_field_white
from modules.general_functions import set_input_field_red


class RequestNewDialog(QtWidgets.QDialog):
    """Dialog creating a new request.
    """

    def __init__(self, parent):
        """Inits energy spectrum dialog.
        
        Args:
            parent: Ibasoft class object.
        """
        super().__init__()
        self.parent = parent
        self.folder = None  # Temporary for browsing folder
        self.directory = None

        self.ui = uic.loadUi(
            os.path.join("ui_files", "ui_new_request.ui"), self)
        self.ui.requestDirectoryLineEdit.setText(
            self.parent.settings.get_request_directory())

        # Connect buttons
        self.ui.pushOk.clicked.connect(self.__create_request)
        self.ui.pushCancel.clicked.connect(self.close)
        self.ui.browseFolderButton.clicked.connect(self.__browser_folder)

        self.ui.requestNameLineEdit.textEdited.connect(lambda:
                                                         self.__validate())
        set_input_field_red(self.ui.requestNameLineEdit)
        self.ui.requestNameLineEdit.textChanged.connect(
            lambda: self.__check_text(self.ui.requestNameLineEdit))

        self.ui.requestDirectoryLineEdit.textChanged.connect(
            lambda: self.__check_text(self.ui.requestDirectoryLineEdit))

        self.__close = True

        self.exec_()

    def __browser_folder(self):
        """Open file browser and show the selected file in view.
        """
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self, self.ui.browseFolderButton.text())
        if folder:
            self.folder = folder
            self.ui.requestDirectoryLineEdit.setText(folder)

    def __validate(self):
        """
        Validate the request name.
        """
        text = self.ui.requestNameLineEdit.text()
        regex = "^[A-Za-z0-9_-]*"
        valid_text = validate_text_input(text, regex)

        self.ui.requestNameLineEdit.setText(valid_text)

    @staticmethod
    def __check_text(input_field):
        """Checks if there is text in given input field.

        Args:
            input_field: Input field the contents of which are checked.
        """
        check_text(input_field)

    def __create_request(self):
        """Create new request.
        """
        self.folder = self.ui.requestDirectoryLineEdit.text()
        self.name = self.ui.requestNameLineEdit.text()

        # TODO: Remove replace above to allow spaces in request names.
        # This does not include the actual request folder, replace below.
        # TODO: check for valid folder needed
        # TODO: Get rid of print -> message window perhaps
        if not self.folder:
            self.ui.browseFolderButton.setFocus()
            return
        if not self.name:
            self.ui.requestNameLineEdit.setFocus()
            return
        try:
            # Adding .potku gives all requests the same ending.
            directory = os.path.join(self.folder, self.name) + ".potku"
            if not os.path.exists(directory):
                os.makedirs(directory)
                self.directory = directory
                logging.getLogger("request").info("Created the request.")
                self.__close = True
            else:
                QtWidgets.QMessageBox.critical(self, "Already exists",
                                               "There already is a "
                                               "request with this name!"
                                               "\n\n Choose another "
                                               "name.",
                                               QtWidgets.QMessageBox.Ok,
                                               QtWidgets.QMessageBox.Ok)
                self.__close = False
            if self.__close:
                self.close()
        except:
            print("We've done something wrong. "
                  "Most likely invalid request name.")
