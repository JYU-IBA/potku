# coding=utf-8
"""
Created on 26.2.2018
Updated on 6.4.2018

#TODO Description of Potku and copyright
#TODO Licence

"""
from modules.general_functions import check_text, set_input_field_red

__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"
__version__ = "2.0"


import os
from PyQt5 import uic, QtWidgets


class NewSampleDialog(QtWidgets.QDialog):
    """Dialog for creating a new sample.
    """
    def __init__(self):
        """Inits a new sample dialog.
        """
        super().__init__()

        self.ui = uic.loadUi(os.path.join("ui_files", "ui_new_sample.ui"), self)

        set_input_field_red(self.ui.nameLineEdit)
        self.ui.nameLineEdit.textChanged.connect(
            lambda: self.__check_text(self.ui.nameLineEdit))

        self.ui.createButton.clicked.connect(self.__create_sample)
        self.ui.cancelButton.clicked.connect(self.close)
        self.name = ""
        self.description = ""

        self.exec_()

    def __create_sample(self):
        self.name = self.ui.nameLineEdit.text().replace(" ", "_")
        if not self.name:
            self.ui.nameLineEdit.setFocus()
            return
        self.close()

    @staticmethod
    def __check_text(input_field):
        check_text(input_field)
