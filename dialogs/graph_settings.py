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
Sinikka Siironen, 2020 Juhani Sundell, Tuomas Pitkänen

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
             "Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen" \
             "Juhani Sundell \n Tuomas Pitkänen"
__version__ = "2.0"

import widgets.binding as bnd
import widgets.gui_utils as gutils

from PyQt5 import QtCore
from PyQt5 import uic
from PyQt5 import QtWidgets


class TofeGraphSettingsWidget(QtWidgets.QDialog):
    """Graph settings dialog for the ToF-E histogram graph.
    """
    color_scheme = bnd.bind("colorbox")

    def __init__(self, parent):
        """Inits ToF-E graph histogram graph settings dialog.
        
        Args:
            parent: MatplotlibHistogramWidget which settings are being changed.
        """
        super().__init__()
        uic.loadUi(gutils.get_ui_dir() / "ui_tofe_graph_settings.ui", self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.parent = parent

        gutils.set_min_max_handlers(
            self.spin_range_x_min, self.spin_range_x_max
        )
        gutils.set_min_max_handlers(
            self.spin_range_y_min, self.spin_range_y_max
        )

        self.parent.show_yourself(self)

        # Connect and show
        self.OKButton.clicked.connect(self.accept_settings)
        self.cancelButton.clicked.connect(self.close)
        self.radio_range_manual.clicked.connect(lambda: self.toggle_manual(True))
        self.radio_range_auto.clicked.connect(lambda: self.toggle_manual(False))
        
        if self.radio_range_auto.isChecked():
            self.toggle_manual(False)
           
        elif self.radio_range_manual.isChecked():
            self.toggle_manual(True)
 
        self.exec_()
    
    def toggle_manual(self, is_manual):
        # if manual is on, spinboxes are enabled
        is_disabled = not is_manual
        self.spin_range_x_min.setDisabled(is_disabled)
        self.spin_range_x_max.setDisabled(is_disabled)
        self.spin_range_y_min.setDisabled(is_disabled)
        self.spin_range_y_max.setDisabled(is_disabled) 

    def accept_settings(self):
        """Accept changed settings and save them.
        """
        self.parent.compression_x = self.bin_x.value()
        self.parent.compression_y = self.bin_y.value()
        self.parent.invert_X = \
            self.invert_x.checkState() == QtCore.Qt.Checked
        self.parent.invert_Y = \
            self.invert_y.checkState() == QtCore.Qt.Checked
        self.parent.show_axis_ticks = \
            self.axes_ticks.checkState() == QtCore.Qt.Checked
        self.parent.transpose_axes = \
            self.transposeAxesCheckBox.checkState() == QtCore.Qt.Checked
        self.parent.color_scheme = self.color_scheme
        
        if self.radio_range_auto.isChecked(): 
            self.parent.axes_range_mode = 0    

        elif self.radio_range_manual.isChecked():
            self.parent.axes_range_mode = 1
            x_range_min = self.spin_range_x_min.value()
            x_range_max = self.spin_range_x_max.value()
            y_range_min = self.spin_range_y_min.value()
            y_range_max = self.spin_range_y_max.value()
            self.parent.axes_range = [(x_range_min, x_range_max),
                                      (y_range_min, y_range_max)]  

        self.parent.on_draw()
        self.close()
