# coding=utf-8
"""
Created on 26.2.2018
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

__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n " \
             "Sinikka Siironen"
__version__ = "2.0"

import os
import platform

import widgets.input_validation as iv

from dialogs.new_sample import NewSampleDialog

from PyQt5 import QtWidgets
from PyQt5 import uic


class SimulationNewDialog(QtWidgets.QDialog):
    """Dialog creating a new simulation.
    """
    def __init__(self, samples):
        """Inits a new simulation dialog.

        Args:
            samples: Samples of request.
        """
        super().__init__()
        self.ui = uic.loadUi(os.path.join("ui_files", "ui_new_simulation.ui"),
                             self)

        # Add existing samples to view.
        self.samples = samples
        for sample in samples:
            self.ui.samplesComboBox.addItem("Sample "
                                            + "%02d" % sample.serial_number
                                            + " " + sample.name)

        if not samples:
            iv.set_input_field_red(self.ui.samplesComboBox)

        self.ui.addSampleButton.clicked.connect(self.__add_sample)
        self.ui.pushCreate.clicked.connect(self.__create_simulation)
        self.ui.pushCancel.clicked.connect(self.close)
        self.name = None
        self.sample = None
        self.__close = True

        iv.set_input_field_red(self.simulationNameLineEdit)
        self.simulationNameLineEdit.textChanged.connect(
            lambda: self.__check_text(self.simulationNameLineEdit))
        self.simulationNameLineEdit.textEdited.connect(
            lambda: iv.sanitize_file_name(self.simulationNameLineEdit))

        if platform.system() == "Darwin":
            self.ui.samplesComboBox.setMinimumWidth(157)

        self.exec_()

    def __add_sample(self):
        """Open a dialog for adding a new sample.
        """
        dialog = NewSampleDialog(self.samples)
        if dialog.name:
            self.ui.samplesComboBox.addItem(dialog.name)
            self.ui.samplesComboBox.setCurrentIndex(self.ui.samplesComboBox
                                                    .findText(dialog.name))
            iv.set_input_field_white(self.ui.samplesComboBox)

    def __create_simulation(self):
        """Check given values and store them in dialog object.
        """
        self.name = self.ui.simulationNameLineEdit.text().replace(" ", "_")
        self.sample = self.ui.samplesComboBox.currentText()
        if not self.name:
            self.ui.simulationNameLineEdit.setFocus()
            return
        if not self.sample:
            self.ui.addSampleButton.setFocus()
            return

        sample = self.__find_existing_sample()

        if sample:
            # Check if measurement on the same name already exists.
            for key in sample.simulations.simulations.keys():
                if sample.simulations.simulations[key].name == self.name:
                    QtWidgets.QMessageBox.critical(self, "Already exists",
                                                   "There already is a "
                                                   "simulation with this name!"
                                                   "\n\n Choose another "
                                                   "name.",
                                                   QtWidgets.QMessageBox.Ok,
                                                   QtWidgets.QMessageBox.Ok)
                    self.__close = False
                    break
                else:
                    self.__close = True
        else:
            self.close()
        if self.__close:
            self.close()

    @staticmethod
    def __check_text(input_field):
        """Checks if there is text in given input field.

        Args:
            input_field: Input field the contents of which are checked.
        """
        iv.check_text(input_field)

    def __find_existing_sample(self):
        """
        Find existing sample that matches the sample name in dialog.

        Return:
            Sample object or None.
        """
        for sample in self.samples:
            if "Sample " + "%02d" % sample.serial_number + " " + sample.name \
                    == self.sample:
                return sample
        return None
