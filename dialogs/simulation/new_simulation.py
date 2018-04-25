# coding=utf-8
"""
Created on 26.2.2018
Updated on 6.4.2018

#TODO Description of Potku and copyright
#TODO Licence

"""
from dialogs.new_sample import NewSampleDialog

__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"
__version__ = "2.0"


import logging
import os
from PyQt5 import uic, QtWidgets


class SimulationNewDialog(QtWidgets.QDialog):
    """Dialog creating a new simulation.
    """
    def __init__(self, samples):
        """Inits a new simulation dialog.

        Args:
            samples: Samples of request.
        """
        super().__init__()
        # self.parent = parent
        
        self.ui = uic.loadUi(os.path.join("ui_files", "ui_new_simulation.ui"), self)

        self.samples = samples
        for sample in samples:
            self.ui.samplesComboBox.addItem("Sample " + "%02d" % sample.serial_number + " " + sample.name)

        self.ui.addSampleButton.clicked.connect(self.__add_sample)
        self.ui.pushCreate.clicked.connect(self.__create_simulation)
        self.ui.pushCancel.clicked.connect(self.close)
        self.name = None
        self.sample = None

        self.exec_()

    def __add_sample(self):
        dialog = NewSampleDialog(self.samples)
        if dialog.name:
            self.ui.samplesComboBox.addItem(dialog.name)
            self.ui.samplesComboBox.setCurrentIndex(self.ui.samplesComboBox.findText(dialog.name))

    def __create_simulation(self):
        self.name = self.ui.simulationNameLineEdit.text().replace(" ", "_")
        self.sample = self.ui.samplesComboBox.currentText()
        if not self.name:
            print("Simulation name required!")
            return
        self.close()
