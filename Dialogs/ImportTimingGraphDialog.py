# coding=utf-8
'''
Created on 6.6.2013
Updated on 29.8.2013

Potku is a graphical user interface for analyzation and 
visualization of measurement data collected from a ToF-ERD 
telescope. For physics calculations Potku uses external 
analyzation components.  
Copyright (C) Timo Konu

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
__author__ = "Timo Konu"
__versio__ = "1.0"

from os import path, stat
from PyQt5 import uic, QtWidgets

from Modules.Functions import coinc
from Widgets.MatplotlibImportTimingWidget import MatplotlibImportTimingWidget


class ImportTimingGraphDialog(QtWidgets.QDialog):
    '''Timing graph class for importing measurements.
    '''
    def __init__(self, parent, input_file, output_file, adc_timing_spin,
                 icon_manager, skip_lines, trigger, adc_count, timing,
                 coinc_count):
        '''Inits timing graph dialog for measurement import.
        
        Args:
            parent: An ImportMeasurementsDialog class object.
            input_file: A string representing input file.
            output_file: A string representing destination file.
            adc_timing_spin: A tuple of timing QSpinboxes.
            icon_manager: An IconManager class object.
            skip_lines: An integer representing line count to be skipped.
            trigger: An integer representing ADC number.
            adc_count: An integer representing ADC count
            timing: A dictionary of tuples for each ADC.
            coinc_count: An integer representing number of coincidences to be 
                         captured from input_file.
        '''
        super().__init__()
        self.parent = parent
        self.img_dir = self.parent.project.directory
        self.__input_file = input_file
        self.__output_file = output_file
        self.timing_low = adc_timing_spin[0]
        self.timing_high = adc_timing_spin[1]
        self.ui = uic.loadUi(path.join("ui_files", "ui_import_graph_dialog.ui"), self)
        self.button_close.clicked.connect(self.close)
        coinc(self.__input_file, self.__output_file, skip_lines=skip_lines,
              tablesize=10, trigger=trigger, adc_count=adc_count, timing=timing,
              nevents=coinc_count, temporary=True)
        if not stat(self.__output_file).st_size:
            unused_reply = QtWidgets.QMessageBox.question(self,
                "Empty File",
                "No coincidence events were found.",
                QtWidgets.QMessageBox.Ok)
            self.close()  # Just in case.
        else:
            self.matplotlib = MatplotlibImportTimingWidget(self,
                                                           self.__output_file,
                                                           icon_manager,
                                                           timing)
            self.exec_()

