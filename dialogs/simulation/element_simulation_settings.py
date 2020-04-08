# coding=utf-8
"""
Created on 4.4.2018
Updated on 24.5.2019

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
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä " \
             "\n Sinikka Siironen"

import widgets.gui_utils as gutils
import widgets.binding as bnd
import dialogs.dialog_functions as df

from widgets.simulation.settings import SimulationSettingsWidget
from pathlib import Path

from PyQt5 import uic
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDesktopWidget
from PyQt5.QtWidgets import QApplication


class ElementSimulationSettingsDialog(QtWidgets.QDialog,
                                      bnd.PropertyTrackingWidget,
                                      metaclass=gutils.QtABCMeta):
    """Class for creating an element simulation settings tab.
    """
    use_default_settings = bnd.bind("defaultSettingsCheckBox",
                                    track_change=True)

    def __init__(self, element_simulation, tab):
        """
        Initializes the dialog.

        Args:
            element_simulation: An ElementSimulation object.
            tab: A SimulationTabWidget.
        """
        super().__init__()
        uic.loadUi(Path("ui_files", "ui_specific_settings.ui"), self)
        self.setWindowTitle("Element Settings")

        self.element_simulation = element_simulation
        self.tab = tab

        self.sim_widget = SimulationSettingsWidget(
            self.element_simulation)
        self.tabs.addTab(self.sim_widget, "Element Settings")
        self.tabs.setEnabled(True)
        self.tabs.setTabBarAutoHide(True)
        screen_geometry = QDesktopWidget \
            .availableGeometry(QApplication.desktop())
        self.resize(self.geometry().width(),
                    screen_geometry.size().height() * 0.8)

        self.OKButton.clicked.connect(self.update_settings_and_close)
        self.applyButton.clicked.connect(self.update_settings)
        self.cancelButton.clicked.connect(self.close)
        self.defaultSettingsCheckBox.stateChanged.connect(
            self.toggle_settings)

        self.__original_property_values = {}
        self.use_default_settings = self.element_simulation.use_default_settings

        self.__close = True
        self.exec_()

    def get_original_property_values(self):
        """Returns the original values of the properties that this widget
        has."""
        return self.__original_property_values

    def toggle_settings(self):
        """If request settings checkbox is checked, disables settings in dialog.
        Otherwise enables settings.
        """
        if self.use_default_settings:
            self.tabs.setEnabled(False)
            self.sim_widget.setEnabled(False)
        else:
            self.tabs.setEnabled(True)
            self.sim_widget.setEnabled(True)

    def update_settings_and_close(self):
        """Updates settings and closes the dialog."""
        self.update_settings()
        if self.__close:
            self.close()

    def update_settings(self):
        """Delete existing file.
        If default settings are used, put them to element simulation and save
        into a file.
        If default settings are not used, read settings from dialog,
        put them to element simulation and save them to file.
        """
        if not self.sim_widget.fields_are_valid:
            QtWidgets.QMessageBox.critical(self, "Warning",
                                           "Some of the setting values have"
                                           " not been set.\n" +
                                           "Please input values in fields "
                                           "indicated in red.",
                                           QtWidgets.QMessageBox.Ok,
                                           QtWidgets.QMessageBox.Ok)
            self.__close = False
            return

        # TODO could compare default element simulation and this element
        #  simulation to see if reset is actually needed
        if self.sim_widget.are_values_changed() or self.are_values_changed():
            simulation = self.element_simulation.simulation

            if self.use_default_settings:
                msg = "request settings"
            else:
                msg = "element specific settings"

            if not df.delete_element_simulations(
                self, self.tab, simulation,
                element_simulation=self.element_simulation,
                msg_str=msg
            ):
                self.__close = False
                return

        if self.element_simulation.name != self.sim_widget.name:
            # Remove current simu file if name has been changed
            self.element_simulation.remove_file()

        self.sim_widget.update_settings()

        self.element_simulation.use_default_settings = self.use_default_settings
        self.element_simulation.to_file()

        # TODO remove files with old name, if name has changed

        self.__close = True
