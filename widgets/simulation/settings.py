# coding=utf-8
"""
Created on 15.3.2018
"""
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"

from os.path import join
from PyQt5 import uic, QtWidgets


class SimulationSettingsWidget(QtWidgets.QWidget):
    """Class for creating a project wide simulation settings tab.
    """
    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi(join("ui_files",
                                  "ui_project_simulation_settings.ui"), self)
