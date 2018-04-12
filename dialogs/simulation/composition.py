# coding=utf-8
"""
Created on 12.4.2018
"""
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"
__version__ = "2.0"

import os
from PyQt5 import uic
from PyQt5 import QtWidgets
from widgets.matplotlib.simulation.target_composition import TargetCompositionWidget
from widgets.simulation.target import TargetWidget


class CompositionDialog(QtWidgets.QDialog):
    """ Class for creating a foil widget for detector settings.
    """
    def __init__(self, icon_manager):
        super().__init__()
        self.ui = uic.loadUi(os.path.join("ui_files", "ui_composition_dialog.ui"), self)
        self.icon_manager = icon_manager
        TargetCompositionWidget(self, self.icon_manager)  # This widget adds itself into the matplotlib_layout

        self.exec_()
