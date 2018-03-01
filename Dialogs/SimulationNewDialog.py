# coding=utf-8
"""
Created on 26.2.2018
Updated on 28.2.2018

#TODO Description of Potku and copyright
#TODO Licence

"""
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"
__versio__ = "2.0"


import logging
import os
from PyQt5 import uic, QtWidgets


class SimulationNewDialog(QtWidgets.QDialog):
    """Dialog creating a new simulation.
    """
    def __init__(self, parent):
        """Inits a new simulation dialog.
        TODO: Right now only the Cancel button works.
        Args:
            parent: Ibasoft class object.
        """
        super().__init__()
        self.parent = parent
        
        self.ui = uic.loadUi(os.path.join("ui_files", "ui_new_simulation.ui"), self)

        self.ui.CancelButton.clicked.connect(self.close)
        
        self.exec_()
