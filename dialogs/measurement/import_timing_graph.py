# coding=utf-8
"""
Created on 6.6.2013
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
__author__ = "Timo Konu \n Severi Jääskeläinne \n Samuel Kaiponen \n Heta " \
             "Rekilä \n Sinikka Siironen"
__version__ = "2.0"

import modules.general_functions as gf
import widgets.gui_utils as gutils

from PyQt5 import uic
from PyQt5 import QtWidgets

from widgets.matplotlib.import_timing import MatplotlibImportTimingWidget


class ImportTimingGraphDialog(QtWidgets.QDialog):
    """Timing graph class for importing measurements.
    """

    def __init__(self, parent, input_file, output_file, adc_timing_spin,
                 icon_manager, skip_lines, trigger, adc_count, timing,
                 coinc_count):
        """Inits timing graph dialog for measurement import.
        
        Args:
            parent: An ImportMeasurementsDialog class object.
            input_file: Path to input file.
            output_file: Path to destination file.
            adc_timing_spin: A tuple of timing QSpinboxes.
            icon_manager: An IconManager class object.
            skip_lines: An integer representing line count to be skipped.
            trigger: An integer representing ADC number.
            adc_count: An integer representing ADC count
            timing: A dictionary of tuples for each ADC.
            coinc_count: An integer representing number of coincidences to be 
                         captured from input_file.
        """
        super().__init__()
        uic.loadUi(gutils.get_ui_dir() / "ui_import_graph_dialog.ui", self)

        self.parent = parent
        self.img_dir = self.parent.request.directory
        self.timing_low = adc_timing_spin[0]
        self.timing_high = adc_timing_spin[1]

        self.button_close.clicked.connect(self.close)
        data = gf.coinc(
            input_file, skip_lines=skip_lines, tablesize=10, trigger=trigger,
            adc_count=adc_count, timing=timing, nevents=coinc_count,
            columns=[3], timediff=True, output_file=output_file)
        if not data:
            QtWidgets.QMessageBox.question(
                self, "No data", "No coincidence events were found.",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            self.close()
        else:
            self.matplotlib = MatplotlibImportTimingWidget(
                self, data, icon_manager, timing)
            self.exec_()
