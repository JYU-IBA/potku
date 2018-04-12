# coding=utf-8
"""
Created on 10.4.2018
"""
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"

from os import path
from PyQt5 import uic, QtWidgets


class DepthProfileSettingsWidget(QtWidgets.QWidget):
    """Class for creating a request wide depth profile settings tab.
    """
    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi(path.join("ui_files", "ui_request_depth_profile_settings.ui"), self)
