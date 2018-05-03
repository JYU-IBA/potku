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

    def __init__(self):
        """Inits a recoil info dialog.
        """
        super().__init__()
        self.__ui = uic.loadUi(os.path.join("ui_files", "ui_recoil_info_dialog.ui"),
                               self)

        self.__ui.okPushButton.clicked.connect(self.__accept_settings)
        self.__ui.cancelPushButton.clicked.connect(self.close)
        self.exec_()


    def __accept_settings(self):
        """Function for accepting the current settings and closing the dialog
        window.
        """
        name = self.__ui.nameLineEdit.text()
        description = self.__ui.descriptionLineEdit.text()
        reference_density = self.__ui.referenceDensityDoubleSpinBox.getValue()
        self.close()
