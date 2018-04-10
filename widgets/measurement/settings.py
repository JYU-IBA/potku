# coding=utf-8
"""
Created on 10.4.2018
"""
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"

from os import path
from PyQt5 import uic, QtWidgets


class MeasurementSettingsWidget(QtWidgets.QWidget):
    """Class for creating a request wide measurement settings tab.
    """
    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi(path.join("ui_files",
                                  "ui_request_measurement_settings.ui"), self)
