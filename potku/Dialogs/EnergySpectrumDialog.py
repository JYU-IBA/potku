# coding=utf-8
'''
Created on 25.3.2013
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

import logging
from os.path import join
from PyQt4 import QtGui
from PyQt4 import uic

from Modules.EnergySpectrum import EnergySpectrum
from Widgets.MatplotlibEnergySpectrumWidget import MatplotlibEnergySpectrumWidget


class EnergySpectrumParamsDialog(QtGui.QDialog):
    def __init__(self, parent):
        '''Inits energy spectrum dialog.
        
        Args:
            parent: MeasurementTabWidget
        '''
        super().__init__()
        self.parent = parent
        self.ui = uic.loadUi(join("ui_files", "ui_energy_spectrum_params.ui"), self)
        
        # Connect buttons
        self.ui.pushButton_OK.clicked.connect(self.__accept_params) 
        self.ui.pushButton_Cancel.clicked.connect(self.close) 
        
        parent.measurement.fill_cuts_treewidget(self.ui.treeWidget, True)
        self.exec_()


    def __accept_params(self):
        '''Accept given parameters and cut files.
        '''
        width = self.ui.histogramTicksDoubleSpinBox.value()
        use_cuts = []
        root = self.ui.treeWidget.invisibleRootItem()
        child_count = root.childCount()
        for i in range(child_count):
            item = root.child(i)
            if item.checkState(0):
                use_cuts.append(join(item.directory, item.file_name))
            child_count = item.childCount()
            if child_count > 0:  # Elemental Losses
                dir_elo = self.parent.measurement.directory_elemloss
                for i in range(child_count):
                    item_child = item.child(i)
                    if item_child.checkState(0):
                        use_cuts.append(join(dir_elo, item_child.file_name))
        if use_cuts:
            if self.parent.energy_spectrum_widget:
                self.parent.del_widget(self.parent.energy_spectrum_widget)
            self.parent.energy_spectrum_widget = EnergySpectrumWidget(self.parent,
                                                                      use_cuts,
                                                                      width)
            icon = self.parent.icon_manager.get_icon("energy_spectrum_icon_16.png")
            self.parent.add_widget(self.parent.energy_spectrum_widget, icon=icon)
        self.close()




class EnergySpectrumWidget(QtGui.QWidget):
    '''Energy spectrum widget which is added to measurement tab.
    '''
    def __init__(self, parent, use_cuts, width):
        '''Inits widget.
        
        Args:
            parent: MeasurementTabWidget
            use_cuts: String list representing CutFiles
            width: Float representing Energy Spectrum histogram's bin width.
        '''
        super().__init__()
        self.parent = parent
        if self.parent.measurement.statusbar:
            self.progress_bar = QtGui.QProgressBar()
            self.parent.measurement.statusbar.addWidget(self.progress_bar, 1) 
            self.progress_bar.show()
        else:
            self.progress_bar = None
        self.ui = uic.loadUi(join("ui_files", "ui_energy_spectrum.ui"), self)
        title = "{0} - Width: {1}".format(self.ui.windowTitle(), width)
        self.ui.setWindowTitle(title)
        
        # Generate new tof.in file for external programs
        self.parent.measurement.generate_tof_in()
        
        # Do energy spectrum stuff on this
        self.energy_spectrum = EnergySpectrum(use_cuts,
                                              width,
                                              progress_bar=self.progress_bar)
        energy_spectrum_data = self.energy_spectrum.calculate_spectrum()
        # print(energy_spectrum_data)
        # Graph in matplotlib widget and add to window
        self.matplotlib = MatplotlibEnergySpectrumWidget(self, energy_spectrum_data)
        if self.progress_bar:
            self.parent.measurement.statusbar.removeWidget(self.progress_bar)
            self.progress_bar.hide()
        
        msg = "[{0}] Created Energy Spectrum. \n{1} {2}".format(
            self.parent.measurement.measurement_name,
            "Bin width: {0}".format(width),
            "Cut files: {0}".format(", ".join(use_cuts))
            )
        logging.getLogger("project").info(msg)
        logging.getLogger(self.parent.measurement.measurement_name).info(
            "Created Energy Spectrum. \nBin width:{0} Cut files: {1}".format(width,
                                                             ', '.join(use_cuts)))
        # TODO: logger: Created energy spectrum with X parameters.
        
    
    def delete(self):
        '''Delete variables and do clean up.
        '''
        self.energy_spectrum = None
        self.progress_bar = None
        self.matplotlib.delete()
        self.matplotlib = None
        self.ui.close()
        self.ui = None
        self.close()

