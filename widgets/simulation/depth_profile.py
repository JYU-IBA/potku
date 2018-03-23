# coding=utf-8
"""
Created on 1.3.2018
Updated on 8.3.2018
"""
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"

from os.path import join
from PyQt5 import QtCore, uic, QtWidgets

from widgets.matplotlib.simulation.depth_profile import MatplotlibSimulationDepthProfileWidget
from dialogs.simulation.element_selection import SimulationElementSelectionDialog


class SimulationDepthProfileWidget(QtWidgets.QWidget):
    '''HistogramWidget used to draw ToF-E Histograms.
    '''

    def __init__(self, simulation, masses, icon_manager):
        '''Inits TofeHistogramWidget widget.

        Args:
            project: ??
            masses: A masses class object.
            icon_manager: An iconmanager class object.
        '''
        super().__init__()
        self.simulation = simulation
        self.ui = uic.loadUi(join("ui_files", "ui_simulation_depth_profile_widget_new.ui"), self)

        self.matplotlib = MatplotlibSimulationDepthProfileWidget(self, simulation, masses, icon_manager)

        self.ui.setWindowTitle("Simulation depth profile")

