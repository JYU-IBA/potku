# coding=utf-8
"""
Created on 1.3.2018
Updated on 26.3.2018
"""
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"

from os.path import join
from PyQt5 import QtCore, uic, QtWidgets

from widgets.matplotlib.simulation.depth_profile import MatplotlibSimulationDepthProfileWidget
from widgets.matplotlib.simulation.target_composition import MatplotlibTargetCompositionWidget
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
        self.ui.addLayerButton.clicked.connect(self.add_layer)
        self.ui.removeLayerButton.clicked.connect(self.remove_layer)
        self.ui.recoilRadioButton.clicked.connect(lambda: self.ui.stackedWidget.setCurrentIndex(0))
        self.ui.targetRadioButton.clicked.connect(lambda: self.ui.stackedWidget.setCurrentIndex(1))

        self.targetWidget = MatplotlibTargetCompositionWidget(self, icon_manager)
        self.ui.stackedWidget.addWidget(MatplotlibSimulationDepthProfileWidget(self, simulation, masses, icon_manager))
        self.ui.stackedWidget.addWidget(self.targetWidget)

        self.ui.setWindowTitle("Simulation depth profile")

    def add_layer(self):
        """Adds a layer in the target composition.
        """
        self.targetWidget.add_layer()

    def remove_layer(self):
        """Removes a layer in the target composition.
        """
        QtWidgets.QMessageBox.critical(self, "Error", "Not implemented",
                                       QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
