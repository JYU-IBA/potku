# coding=utf-8
"""
Created on 26.2.2018
Updated on 6.4.2018

#TODO Description of Potku and copyright
#TODO Licence

"""
from modules.general_functions import open_file_dialog

__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"
__version__ = "2.0"


import logging
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

        self.ui = uic.loadUi(os.path.join("ui_files", "ui_new_measurement.ui"), self)

        self.ui.browseButton.clicked.connect(self.__browse_files)
        self.ui.loadButton.clicked.connect(self.__load_measurement)
        self.ui.cancelButton.clicked.connect(self.close)
        self.name = None
        self.directory = directory

        for sample in samples:
            self.ui.samplesComboBox.addItem("Sample " + "%02d" % sample.serial_number + " " + sample.name)
        
        self.exec_()

    def __load_measurement(self):
        self.path = self.ui.pathLineEdit.text
        self.name = self.ui.nameLineEdit.text().replace(" ", "_")
        self.sample = self.ui.samplesComboBox.currentText()
        if not self.path:
            return
        self.close()

    def __browse_files(self):
        self.filename = open_file_dialog(self, self.directory, "Select a measurement to load", "Raw Measurement (*.asc)")
        self.ui.pathLineEdit.setText(self.filename)
