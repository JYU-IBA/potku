# coding=utf-8
"""
Created on 18.4.2013
Updated on 22.8.2018

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2013-2018 Jarkko Aalto, Severi Jääskeläinen, Samuel Kaiponen,
Timo Konu, Samuli Kärkkäinen, Samuli Rahkonen, Miika Raunio, Heta Rekilä and
Sinikka Siironen

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program (file named 'LICENCE').
"""
__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen \n " \
             "Samuli Rahkonen \n Miika Raunio \n Severi Jääskeläinen \n " \
             "Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"
__version__ = "2.0"

import os

from PyQt5 import QtCore
from PyQt5 import uic
from PyQt5 import QtWidgets

from widgets.matplotlib.measurement.tofe_histogram import \
    MatplotlibHistogramWidget


class TofeHistogramWidget(QtWidgets.QWidget):
    """HistogramWidget used to draw ToF-E Histograms.
    """

    def __init__(self, measurement, icon_manager, tab):
        """Inits TofeHistogramWidget widget.

        Args:
            measurement: A measurement class object.
            icon_manager: An iconmanager class object.
            tab: A MeasurementTabWidget.
        """
        super().__init__()
        self.ui = uic.loadUi(os.path.join("ui_files",
                                          "ui_histogram_widget.ui"),
                             self)
        self.measurement = measurement
        self.tab = tab
        self.matplotlib = MatplotlibHistogramWidget(self, measurement,
                                                    icon_manager)
        self.ui.saveCutsButton.clicked.connect(self.matplotlib.save_cuts)
        self.ui.loadSelectionsButton.clicked.connect(
            self.matplotlib.load_selections)
        self.matplotlib.selectionsChanged.connect(self.set_cut_button_enabled)

        self.matplotlib.saveCuts.connect(self.__save_cuts)

        self.__set_shortcuts()
        self.set_cut_button_enabled(measurement.selector.selections)

        count = len(self.measurement.data)
        self.ui.setWindowTitle(
            "ToF-E Histogram - Event count: {0}".format(count))

    def set_cut_button_enabled(self, selections=None):
        """Enables save cuts button if the given selections list's length is
        not 0.
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
            # self.measurement.request.save_selection(self.measurement)

    def __save_cuts(self):
        """Connect to saving cuts. Issue it to request for every other
        measurement.
        """
        self.measurement.request.save_cuts(self.measurement)

    def __set_shortcuts(self):
        """Set shortcuts for the ToF-E histogram.
        """
        # X axis
        self.__sc_comp_x_inc = QtWidgets.QShortcut(self)
        self.__sc_comp_x_inc.setKey(QtCore.Qt.Key_Q)
        self.__sc_comp_x_inc.activated.connect(
            lambda: self.matplotlib.sc_comp_inc(0))
        self.__sc_comp_x_dec = QtWidgets.QShortcut(self)
        self.__sc_comp_x_dec.setKey(QtCore.Qt.Key_W)
        self.__sc_comp_x_dec.activated.connect(
            lambda: self.matplotlib.sc_comp_dec(0))
        # Y axis
        self.__sc_comp_y_inc = QtWidgets.QShortcut(self)
        self.__sc_comp_y_inc.setKey(QtCore.Qt.Key_Z)
        self.__sc_comp_y_inc.activated.connect(
            lambda: self.matplotlib.sc_comp_inc(1))
        self.__sc_comp_y_dec = QtWidgets.QShortcut(self)
        self.__sc_comp_y_dec.setKey(QtCore.Qt.Key_X)
        self.__sc_comp_y_dec.activated.connect(
            lambda: self.matplotlib.sc_comp_dec(1))
        # Both axes
        self.__sc_comp_inc = QtWidgets.QShortcut(self)
        self.__sc_comp_inc.setKey(QtCore.Qt.Key_A)
        self.__sc_comp_inc.activated.connect(
            lambda: self.matplotlib.sc_comp_inc(2))
        self.__sc_comp_dec = QtWidgets.QShortcut(self)
        self.__sc_comp_dec.setKey(QtCore.Qt.Key_S)
        self.__sc_comp_dec.activated.connect(
            lambda: self.matplotlib.sc_comp_dec(2))
