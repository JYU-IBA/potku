# coding=utf-8
'''
Created on 13.4.2013
Updated on 23.5.2013

Potku is a graphical user interface for analyzation and 
visualization of measurement data collected from a ToF-ERD 
telescope. For physics calculations Potku uses external 
analyzation components.  
Copyright (C) Jarkko Aalto, Timo Konu, Samuli Kärkkäinen, Samuli Rahkonen and 
Miika Raunio

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
'''
__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen \n Samuli Rahkonen \n Miika Raunio"
__versio__ = "1.0"

from os.path import join
from PyQt4 import uic, QtGui

class MeasurementInfoWidget(QtGui.QWidget):
    """Class for creating an info tab widget
    """
    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi(join("ui_files",
                                  "ui_create_measurement_info_widget.ui"), self)
        bg = "url(images/background.svg)"
        self.ui.setStyleSheet("QWidget#measurementInfoTab {border-image: " + bg + ";}")
