# coding=utf-8
"""
Created on 3.5.2018

#TODO Licence and copyright

"""
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n " \
             "Sinikka Siironen"
__version__ = "2.0"

import os
from PyQt5 import uic, QtCore, QtWidgets

class RecoilInfoDialog(QtWidgets.QDialog):
    """Dialog for editing the name, description and reference density
    of a recoil element.
    """

    def __init__(self, recoil_element):
        """Inits a recoil info dialog.
        """
        super().__init__()
        self.__ui = uic.loadUi(os.path.join("ui_files", "ui_recoil_info_dialog.ui"),
                               self)

        self.__ui.okPushButton.clicked.connect(self.__accept_settings)
        self.__ui.cancelPushButton.clicked.connect(self.close)

        self.name = ""
        self.__ui.nameLineEdit.setText(recoil_element.name)
        self.__ui.descriptionLineEdit.setPlainText(
            recoil_element.description)
        self.__ui.referenceDensityDoubleSpinBox.setValue(
            recoil_element.reference_density)
        self.description = ""
        self.isOk = False

        self.exec_()

    def __accept_settings(self):
        """Function for accepting the current settings and closing the dialog
        window.
        """
        self.name = self.__ui.nameLineEdit.text()
        self.description = self.__ui.descriptionLineEdit.toPlainText()
        self.reference_density = self.__ui.referenceDensityDoubleSpinBox\
            .value()
        self.isOk = True
        self.close()
