# coding=utf-8
"""
Created on 26.2.2018
Updated on 6.4.2018

#TODO Description of Potku and copyright
#TODO Licence

"""
from dialogs.new_sample import NewSampleDialog
from modules.general_functions import open_file_dialog, check_text, \
    set_input_field_red, set_input_field_white

__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"
__version__ = "2.0"

import os
from PyQt5 import uic, QtWidgets


class LoadMeasurementDialog(QtWidgets.QDialog):
    """Dialog for loading a measurement.
    """
    def __init__(self, samples, directory):
        """Inits a load measurement dialog.

        Args:
            samples: Samples of request.
            directory: Directory where to open the file browser.
        """
        super().__init__()

        self.ui = uic.loadUi(os.path.join(
            "ui_files", "ui_new_measurement.ui"), self)

        self.ui.browseButton.clicked.connect(self.__browse_files)
        self.ui.addSampleButton.clicked.connect(self.__add_sample)
        self.ui.loadButton.clicked.connect(self.__load_measurement)
        self.ui.cancelButton.clicked.connect(self.close)
        self.name = ""
        self.sample = None
        self.directory = directory
        self.filename = ""

        for sample in samples:
            self.ui.samplesComboBox.addItem(
                "Sample " + "%02d" % sample.serial_number + " " + sample.name)

        if not samples:
            set_input_field_red(self.ui.samplesComboBox)

        set_input_field_red(self.ui.nameLineEdit)
        self.ui.nameLineEdit.textChanged.connect(lambda: self.__check_text(
            self.ui.nameLineEdit))

        set_input_field_red(self.ui.pathLineEdit)
        self.ui.pathLineEdit.textChanged.connect(lambda: self.__check_text(
            self.ui.pathLineEdit))

        self.exec_()

    def __add_sample(self):
        dialog = NewSampleDialog()
        if dialog.name:
            self.ui.samplesComboBox.addItem(dialog.name)
            self.ui.samplesComboBox.setCurrentIndex(
                self.ui.samplesComboBox.findText(dialog.name))
            set_input_field_white(self.ui.samplesComboBox)

    def __load_measurement(self):
        self.path = self.ui.pathLineEdit.text()
        self.name = self.ui.nameLineEdit.text().replace(" ", "_")
        self.sample = self.ui.samplesComboBox.currentText()
        if not self.path:
            self.ui.browseButton.setFocus()
            return
        if not self.name:
            self.ui.nameLineEdit.setFocus()
            return
        if not self.sample:
            self.ui.addSampleButton.setFocus()
            return
        self.close()

    def __browse_files(self):
        self.filename = open_file_dialog(self, self.directory,
                                         "Select a measurement to load",
                                         "Raw Measurement (*.asc)")
        self.ui.pathLineEdit.setText(self.filename)

    @staticmethod
    def __check_text(input_field):
        check_text(input_field)
