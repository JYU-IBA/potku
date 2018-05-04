# coding=utf-8
"""
Created on 4.5.2018
"""
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä " \
             "\n Sinikka Siironen"

import os
from PyQt5 import uic, QtWidgets


class ElementSimulationSettingsDialog(QtWidgets.QDialog):
    """Class for creating an element simulation settings tab.
    """
    def __init__(self, element_simulation):
        super().__init__()
        self.ui = uic.loadUi(os.path.join("ui_files",
                                          "ui_element_simulation_settings.ui"),
                             self)
        self.element_simulation = element_simulation
        self.temp_settings = {}
        self.isOk = False

        self.exec_()

    def __accept_settings(self):
        """Function for accepting the current settings and closing the dialog
        window.
        """
        self.temp_settings["name"] = self.simulation_settings_widget\
            .nameLineEdit.text()
        self.temp_settings["description"] = self.simulation_settings_widget\
            .descriptionLineEdit.toPlainText()
        self.temp_settings["mode"] = \
            self.simulation_settings_widget.modeComboBox.currentText()
        self.temp_settings["simulation_type"] = \
            self.simulation_settings_widget \
                .typeOfSimulationComboBox.currentText()
        self.temp_settings["scatter"] = self.simulation_settings_widget\
            .scatterLineEdit.text()
        self.temp_settings["main_scatter"] = self.simulation_settings_widget\
            .mainScatterLineEdit.text()
        self.temp_settings["energy"] = self.simulation_settings_widget\
            .energyLineEdit.text()
        self.temp_settings["no_of_ions"] = self.simulation_settings_widget\
            .noOfIonsLineEdit.text()
        self.temp_settings["no_of_preions"] = self.simulation_settings_widget\
            .noOfPreionsLineEdit.text()
        self.temp_settings["seed"] = self.simulation_settings_widget\
            .seedLineEdit.text()
        self.temp_settings["no_of_recoils"] = self.simulation_settings_widget\
            .noOfRecoilsLineEdit.text()
        self.temp_settings["no_of_scaling"] = self.simulation_settings_widget\
            .noOfScalingLineEdit.text()

        self.isOk = True
        self.close()
