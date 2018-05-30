# coding=utf-8
"""
Created on 21.3.2013
Updated on 30.5.2018

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
__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen" \
             " \n Samuli Rahkonen \n Miika Raunio \n Severi Jääskelänen \n " \
             "Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"
__version__ = "2.0"
import os

from PyQt5 import QtCore, uic, QtWidgets


class TofeGraphSettingsWidget(QtWidgets.QDialog):
    """Graph settings dialog for the ToF-E histogram graph.
    """

    def __init__(self, parent):
        """Inits ToF-E graph histogram graph settings dialog.
        
        Args:
            parent: MatplotlibHistogramWidget which settings are being changed.
        """
        super().__init__()
        self.parent = parent
        self.ui = uic.loadUi(os.path.join("ui_files",
                                          "ui_tofe_graph_settings.ui"),
                             self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.parent.show_yourself(self.ui)

        # Connect and show
        self.ui.OKButton.clicked.connect(self.accept_settings)
        self.ui.cancelButton.clicked.connect(self.close)

        self.exec_()

    def accept_settings(self):
        """Accept changed settings and save them.
        """
        self.parent.compression_x = self.ui.bin_x.value()
        self.parent.compression_y = self.ui.bin_y.value()
        self.parent.invert_X = \
            self.ui.invert_x.checkState() == QtCore.Qt.Checked
        self.parent.invert_Y = \
            self.ui.invert_y.checkState() == QtCore.Qt.Checked
        self.parent.show_axis_ticks = \
            self.ui.axes_ticks.checkState() == QtCore.Qt.Checked
        self.parent.transpose_axes = \
            self.ui.transposeAxesCheckBox.checkState() == QtCore.Qt.Checked
        self.parent.measurement.color_scheme = self.ui.colorbox.currentText()
        if self.ui.radio_range_auto.isChecked():
            self.parent.axes_range_mode = 0
        elif self.ui.radio_range_manual.isChecked():
            self.parent.axes_range_mode = 1
        x_range_min = self.ui.spin_range_x_min.value()
        x_range_max = self.ui.spin_range_x_max.value()
        y_range_min = self.ui.spin_range_y_min.value()
        y_range_max = self.ui.spin_range_y_max.value()
        if x_range_min > x_range_max: x_range_min
        if y_range_min > y_range_max: y_range_min
        self.parent.axes_range = [(x_range_min, x_range_max),
                                  (y_range_min, y_range_max)]
        self.parent.on_draw()
        self.close()
