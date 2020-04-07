# coding=utf-8
"""
Created on 11.4.2013
Updated on 28.8.2018

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
import platform

import widgets.input_validation as iv

from PyQt5 import uic
from PyQt5 import QtWidgets


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

        iv.set_input_field_red(self.requestNameLineEdit)
        self.requestNameLineEdit.textChanged.connect(
            lambda: iv.check_text(self.requestNameLineEdit))
        self.requestNameLineEdit.textEdited.connect(
            lambda: iv.sanitize_file_name(self.requestNameLineEdit))

        self.requestDirectoryLineEdit.textChanged.connect(
            lambda: iv.check_text(self.requestDirectoryLineEdit))

        self.__close = True

        if platform.system() == "Darwin":
            self.ui.requestNameLineEdit.setMinimumWidth(310)
            self.ui.requestDirectoryLineEdit.setMinimumWidth(234)

        self.exec_()

    def __browser_folder(self):
        """Open file browser and show the selected file in view.
        """
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self, self.ui.browseFolderButton.text())
        if folder:
            self.folder = folder
            self.ui.requestDirectoryLineEdit.setText(folder)

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
