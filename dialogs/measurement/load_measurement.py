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
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä " \
             "\n Sinikka Siironen"
__version__ = "2.0"

import widgets.input_validation as iv
import dialogs.file_dialogs as fdialogs
import widgets.gui_utils as gutils

from PyQt5 import uic
from PyQt5 import QtWidgets

from dialogs.new_sample import NewSampleDialog
from modules.sample import Sample


class LoadMeasurementDialog(QtWidgets.QDialog):
    """Dialog for loading a measurement.
    """
    def __init__(self, samples: list[Sample], directory):
        """Inits a load measurement dialog.

        Args:
            samples: Samples of request.
            directory: Directory where to open the file browser.
        """
        super().__init__()
        uic.loadUi(gutils.get_ui_dir() / "ui_new_measurement.ui", self)

        self.browseButton.clicked.connect(self.__browse_files)
        self.addSampleButton.clicked.connect(self.__add_sample)
        self.loadButton.clicked.connect(self.__load_measurement)
        self.cancelButton.clicked.connect(self.close)
        self.name = ""
        self.sample_str = None
        self.directory = directory
        self.filename = ""
        self.samples = samples

        self.__close = True
        for sample in samples:
            self.samplesComboBox.addItem(sample.long_name())

        if not samples:
            iv.set_input_field_red(self.samplesComboBox)

        iv.set_input_field_red(self.pathLineEdit)
        self.pathLineEdit.textChanged.connect(
            lambda: iv.check_text(self.pathLineEdit))

        iv.set_input_field_red(self.nameLineEdit)
        self.nameLineEdit.textChanged.connect(
            lambda: iv.check_text(self.nameLineEdit))
        self.nameLineEdit.textEdited.connect(
            lambda: iv.sanitize_file_name(self.nameLineEdit))

        self.exec_()

    def __add_sample(self):
        dialog = NewSampleDialog(self.samples)
        if dialog.name:
            self.samplesComboBox.addItem(dialog.name)
            self.samplesComboBox.setCurrentIndex(
                self.samplesComboBox.findText(dialog.name))
            iv.set_input_field_white(self.samplesComboBox)

    def __load_measurement(self):
        self.path = self.pathLineEdit.text()
        self.name = self.nameLineEdit.text().replace(" ", "_")
        self.sample_str = self.samplesComboBox.currentText()
        if not self.path:
            self.browseButton.setFocus()
            return
        if not self.name:
            self.nameLineEdit.setFocus()
            return
        if not self.sample_str:
            self.addSampleButton.setFocus()
            return

        sample = self.__find_existing_sample(self.sample_str)

        if sample:
            # Check if measurement on the same name already exists.
            for key in sample.measurements.measurements.keys():
                if sample.measurements.measurements[key].name == self.name:
                    QtWidgets.QMessageBox.critical(self, "Already exists",
                                                   "There already is a "
                                                   "measurement with this name!"
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

    def __browse_files(self):
        self.filename = fdialogs.open_file_dialog(
            self, self.directory, "Select a measurement to load",
            "Raw Measurement (*.asc)")
        self.pathLineEdit.setText(str(self.filename))
        self.nameLineEdit.setText(self.filename.stem)

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
