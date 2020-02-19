# coding=utf-8
"""
Created on 5.3.2018
Updated on 30.5.2018

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2018 Severi Jääskeläinen, Samuel Kaiponen, Heta Rekilä and
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
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä " \
             "\n Sinikka Siironen"
__version__ = "2.0"

from PyQt5 import QtWidgets
from PyQt5 import uic
import sys
import logging
import os
from widgets.matplotlib.simulation.energy_spectrum \
    import MatplotlibSimulationEnergySpectrumWidget


class SimulationEnergySpectrumWidget(QtWidgets.QWidget):
    """ Simulation energy spectrum widget which is added to the simulation tab.
    """

    def __init__(self, parent, data, statusbar=None):
        """ Initialize the energy spectrum widget.
        Args:
            parent: Parent of the energy spectrum widget (SimulationTabWidget)
        """
        try:
            super().__init__()
            self.parent = parent
            self.icon_manager = parent.icon_manager
            self.ui = uic.loadUi(os.path.join("ui_files",
                                              "ui_energy_spectrum_simu.ui"),
                                 self)
            self.icon_manager = parent.icon_manager

            # TODO progress_bar is doing nothing in here
            progress_bar = None
            title = str(self.ui.windowTitle())
            self.ui.setWindowTitle(title)
            self.simulation = parent.simulation
            self.ui.saveSimuEnergySpectraButton.clicked.connect(
                self.save_spectra)
            self.energy_spectrum_data = data

            # Graph in matplotlib widget and add to window
            self.matplotlib = MatplotlibSimulationEnergySpectrumWidget(
                self,
                self.energy_spectrum_data)
        except:
            import traceback
            msg = "Could not create Energy Spectrum graph. "
            err_file = sys.exc_info()[2].tb_frame.f_code.co_filename
            str_err = ", ".join([sys.exc_info()[0].__name__ + ": " +
                                 traceback._some_str(sys.exc_info()[1]),
                                 err_file,
                                 str(sys.exc_info()[2].tb_lineno)])
            msg += str_err
            logging.getLogger(self.simulation.name).error(msg)
            if hasattr(self, "matplotlib"):
                self.matplotlib.delete()
        finally:
            if progress_bar is not None:
                statusbar.removeWidget(progress_bar)
                progress_bar.hide()

    def save_spectra(self):
        """ Save the created energy spectra.
        """
        QtWidgets.QMessageBox.critical(self, "Error", "Not implemented",
                                       QtWidgets.QMessageBox.Ok,
                                       QtWidgets.QMessageBox.Ok)
