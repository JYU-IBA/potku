# coding=utf-8
"""
Created on 1.3.2018
Updated on 8.3.2018
"""
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"

from os.path import join
from PyQt5 import QtCore, uic, QtWidgets

from Widgets.MatplotlibSimulationDepthProfileWidget import MatplotlibSimulationDepthProfileWidget
from Dialogs.SimulationElementSelectionDialog import SimulationElementSelectionDialog


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

        self.ui.addElementButton.clicked.connect(self.__select_element)
        self.__set_shortcuts()
        self.ui.setWindowTitle("Simulation depth profile")


    # def __init__(self, measurement, masses, icon_manager):
    #     '''Inits TofeHistogramWidget widget.
    #
    #     Args:
    #         measurement: A measurement class object.
    #         masses: A masses class object.
    #         icon_manager: An iconmanager class object.
    #     '''
    #     super().__init__()
    #     self.ui = uic.loadUi(join("ui_files", "ui_simulation_depth_profile_widget.ui"), self)
    #     self.measurement = measurement
    #     self.matplotlib = MatplotlibHistogramWidget(self, measurement,
    #                                                 masses, icon_manager)
    #     self.ui.saveCutsButton.clicked.connect(self.matplotlib.save_cuts)
    #     self.ui.loadSelectionsButton.clicked.connect(
    #         self.matplotlib.load_selections)
    #     # self.connect(self.matplotlib, QtCore.SIGNAL("selectionsChanged(PyQt_PyObject)"), self.set_cut_button_enabled)
    #     self.matplotlib.selectionsChanged.connect(self.set_cut_button_enabled)
    #
    #     # self.connect(self.matplotlib, QtCore.SIGNAL("saveCuts(PyQt_PyObject)"), self.__save_cuts)
    #     self.matplotlib.saveCuts.connect(self.__save_cuts)
    #
    #     self.__set_shortcuts()
    #     self.set_cut_button_enabled(measurement.selector.selections)
    #
    #     count = len(self.measurement.data)
    #     self.ui.setWindowTitle(
    #         "ToF-E Histogram - Event count: {0}".format(count))

    def __select_element(self):
        return
        # dialog = SimulationElementSelectionDialog(self.project)

        # if dialog.directory:
        #     self.__close_project()
        #     title = "{0} - Project: {1}".format(self.title, dialog.name)
        #     self.ui.setWindowTitle(title)


    def set_cut_button_enabled(self, selections=None):
        """Enables save cuts button if the given selections list's length is not 0.
        Otherwise disable.

        Args:
            selections: list of Selection objects
        """
        if not selections:
            selections = self.measurement.selector.selections
        if len(selections) == 0:
            self.ui.saveCutsButton.setEnabled(False)
        else:
            self.ui.saveCutsButton.setEnabled(True)
            # self.measurement.project.save_selection(self.measurement)

    def __save_cuts(self, unused_measurement):
        """Connect to saving cuts. Issue it to project for every other measurement.
        """
        # self.measurement.project.save_cuts(self.measurement)

    def __set_shortcuts(self):
        """Set shortcuts for the ToF-E histogram.
        """
        # # X axis
        # self.__sc_comp_x_inc = QtWidgets.QShortcut(self)
        # self.__sc_comp_x_inc.setKey(QtCore.Qt.Key_Q)
        # self.__sc_comp_x_inc.activated.connect(
        #     lambda: self.matplotlib.sc_comp_inc(0))
        # self.__sc_comp_x_dec = QtWidgets.QShortcut(self)
        # self.__sc_comp_x_dec.setKey(QtCore.Qt.Key_W)
        # self.__sc_comp_x_dec.activated.connect(
        #     lambda: self.matplotlib.sc_comp_dec(0))
        # # Y axis
        # self.__sc_comp_y_inc = QtWidgets.QShortcut(self)
        # self.__sc_comp_y_inc.setKey(QtCore.Qt.Key_Z)
        # self.__sc_comp_y_inc.activated.connect(
        #     lambda: self.matplotlib.sc_comp_inc(1))
        # self.__sc_comp_y_dec = QtWidgets.QShortcut(self)
        # self.__sc_comp_y_dec.setKey(QtCore.Qt.Key_X)
        # self.__sc_comp_y_dec.activated.connect(
        #     lambda: self.matplotlib.sc_comp_dec(1))
        # # Both axes
        # self.__sc_comp_inc = QtWidgets.QShortcut(self)
        # self.__sc_comp_inc.setKey(QtCore.Qt.Key_A)
        # self.__sc_comp_inc.activated.connect(
        #     lambda: self.matplotlib.sc_comp_inc(2))
        # self.__sc_comp_dec = QtWidgets.QShortcut(self)
        # self.__sc_comp_dec.setKey(QtCore.Qt.Key_S)
        # self.__sc_comp_dec.activated.connect(
        #     lambda: self.matplotlib.sc_comp_dec(2))
