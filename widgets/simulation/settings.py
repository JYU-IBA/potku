# coding=utf-8
"""
Created on 15.3.2018
Updated on 30.4.2018
"""
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä " \
             "\n Sinikka Siironen"

import os
from PyQt5 import uic, QtWidgets


class SimulationSettingsWidget(QtWidgets.QWidget):
    """Class for creating a simulation settings tab.
    """
    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi(os.path.join("ui_files",
                                          "ui_request_simulation_settings.ui"),
                             self)
