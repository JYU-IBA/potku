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

import platform

import widgets.input_validation as iv
import widgets.gui_utils as gutils

from dialogs.new_sample import NewSampleDialog

from PyQt5 import QtWidgets
from PyQt5 import uic

from modules.sample import Sample


class SimulationNewDialog(QtWidgets.QDialog):
    """Dialog creating a new simulation.
    """
    def __init__(self, samples):
        """Inits a new simulation dialog.

        Args:
            samples: Samples of request.
        """
        super().__init__()
        uic.loadUi(gutils.get_ui_dir() / "ui_new_simulation.ui", self)

        # Add existing samples to view.
        self.samples = samples
        for sample in samples:
            self.samplesComboBox.addItem(sample.long_name())

        if not samples:
            iv.set_input_field_red(self.samplesComboBox)

        self.addSampleButton.clicked.connect(self.__add_sample)
        self.pushCreate.clicked.connect(self.__create_simulation)
        self.pushCancel.clicked.connect(self.close)
        self.name = None
        self.sample = None

        iv.set_input_field_red(self.simulationNameLineEdit)
        self.simulationNameLineEdit.textChanged.connect(
            lambda: iv.check_text(self.simulationNameLineEdit))
        self.simulationNameLineEdit.textEdited.connect(
            lambda: iv.sanitize_file_name(self.simulationNameLineEdit))

        if platform.system() == "Darwin":
            self.samplesComboBox.setMinimumWidth(157)

        self.exec_()

    def __add_sample(self):
        """Open a dialog for adding a new sample.
        """
        dialog = NewSampleDialog(self.samples)
        if dialog.name:
            self.samplesComboBox.addItem(dialog.name)
            self.samplesComboBox.setCurrentIndex(
                self.samplesComboBox.findText(dialog.name))
            iv.set_input_field_white(self.samplesComboBox)

    def __create_simulation(self):
        """Check given values and store them in dialog object.
        """
        sample_str = self.samplesComboBox.currentText()
        name = self.simulationNameLineEdit.text()
        if not name:
            self.simulationNameLineEdit.setFocus()
            return
        if not sample_str:
            self.addSampleButton.setFocus()
            return

        sample = self.__find_existing_sample(sample_str)

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
                    return
        self.name = name
        self.sample_str = sample_str
        self.close()

    def __find_existing_sample(self, sample_str: str):
        """
        Find existing sample that matches the sample name in dialog.

        Return:
            Sample object or None.
        """
        for sample in self.samples:
            if sample_str == sample.long_name():
                return sample
        return None
