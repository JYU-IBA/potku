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

from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5 import uic
from PyQt5 import QtWidgets

from modules.measurement import Measurement
import widgets.gui_utils as gutils
from widgets.base_tab import BaseTab
from widgets.icon_manager import IconManager
from widgets.matplotlib.measurement.tofe_histogram import \
    MatplotlibHistogramWidget


class TofeHistogramWidget(QtWidgets.QWidget):
    """HistogramWidget used to draw ToF-E Histograms.
    """
    saveCutsButton: QtWidgets.QPushButton
    loadSelectionsButton: QtWidgets.QPushButton

    # shortcut keys that adjust compression
    X_INC_COMP = Qt.Key_Q
    X_DEC_COMP = Qt.Key_W
    Y_INC_COMP = Qt.Key_Z
    Y_DEC_COM = Qt.Key_X
    BOTH_INC_COMP = Qt.Key_A
    BOTH_DEC_COMP = Qt.Key_S

    def __init__(
            self,
            measurement: Measurement,
            icon_manager: IconManager,
            tab: BaseTab,
            statusbar: Optional[QtWidgets.QStatusBar] = None):
        """Inits TofeHistogramWidget widget.

        Args:
            measurement: A measurement class object.
            icon_manager: An iconmanager class object.
            tab: A MeasurementTabWidget.
        """
        super().__init__()
        uic.loadUi(gutils.get_ui_dir() / "ui_histogram_widget.ui", self)

        self.measurement = measurement
        self.tab = tab
        self.matplotlib = MatplotlibHistogramWidget(
            self, measurement, icon_manager,
            global_settings=self.measurement.request.global_settings,
            statusbar=statusbar)
        self.saveCutsButton.clicked.connect(self.matplotlib.save_cuts)
        self.loadSelectionsButton.clicked.connect(
            self.matplotlib.load_selections)
        self.matplotlib.selectionsChanged.connect(self.set_cut_button_enabled)

        self.matplotlib.saveCuts.connect(self._save_cuts)

        self._set_shortcuts()
        self.set_cut_button_enabled()

        count = len(self.measurement.data)
        self.setWindowTitle(f"ToF-E Histogram - Event count: {count}")

    def set_cut_button_enabled(self) -> None:
        """Enables save cuts button if Measurement has selections. Otherwise
        disable.
        """
        if not self.measurement.selector.selections:
            self.saveCutsButton.setEnabled(False)
        else:
            self.saveCutsButton.setEnabled(True)

    def _save_cuts(self) -> None:
        """Connect to saving cuts. Issue it to request for every other
        measurement.
        """
        self.measurement.request.save_cuts(self.measurement)

    def _set_shortcuts(self) -> None:
        """Set shortcuts for the ToF-E histogram.
        """
        # X axis
        gutils.assign_shortcut(
            self,
            TofeHistogramWidget.X_INC_COMP,
            lambda: self.matplotlib.increase_compression("x"))
        gutils.assign_shortcut(
            self,
            TofeHistogramWidget.X_DEC_COMP,
            lambda: self.matplotlib.decrease_compression("x"))

        # Y Axis
        gutils.assign_shortcut(
            self,
            TofeHistogramWidget.Y_INC_COMP,
            lambda: self.matplotlib.increase_compression("y"))
        gutils.assign_shortcut(
            self,
            TofeHistogramWidget.Y_DEC_COM,
            lambda: self.matplotlib.decrease_compression("y"))

        # Both
        gutils.assign_shortcut(
            self,
            TofeHistogramWidget.BOTH_INC_COMP,
            lambda: self.matplotlib.increase_compression("xy"))
        gutils.assign_shortcut(
            self,
            TofeHistogramWidget.BOTH_DEC_COMP,
            lambda: self.matplotlib.decrease_compression("xy"))
