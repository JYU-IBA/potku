# coding=utf-8
'''
Created on 18.4.2013
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
from PyQt4 import QtGui, QtCore
from PyQt4 import uic

from Widgets.MatplotlibTofeHistogramWidget import MatplotlibHistogramWidget


class TofeHistogramWidget(QtGui.QWidget):
    '''
    HistogramWidget
    
    Used to draw ToF-E Histograms
    '''
    def __init__(self, measurement, icon_manager):
        '''Inits TofeHistogramWidget widget.
        
        Args:
            measurement: Measurement class object.
            icon_manager: IconManager class object.
        '''
        super().__init__()
        self.ui = uic.loadUi(join("ui_files", "ui_histogram_widget.ui"), self)
        self.matplotlib = MatplotlibHistogramWidget(self, measurement, 
                                                    icon_manager)
        self.measurement = measurement
        self.ui.saveCutsButton.clicked.connect(self.measurement.save_cuts)
        self.ui.loadSelectionsButton.clicked.connect(
                                                 self.matplotlib.load_selections)
        self.connect(self.matplotlib, 
                     QtCore.SIGNAL("selectionsChanged(PyQt_PyObject)"), 
                     self.set_cut_button_enabled)
        self.set_cut_button_enabled(measurement.selector.selections)
        
        
    def set_cut_button_enabled(self, selections=None):
        """Enables save cuts button if the given selections list's lenght is not 0.
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
            
        
        