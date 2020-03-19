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

import os

import widgets.gui_utils as gutils
import widgets.binding as bnd
import dialogs.dialog_functions as df

from widgets.simulation.settings import SimulationSettingsWidget

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

        uic.loadUi(os.path.join("ui_files", "ui_specific_settings.ui"), self)
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

        self.set_spinbox_maximums()

        self.__close = True
        self.exec_()

    def get_original_property_values(self):
        """Returns the original values of the properties that this widget
        has."""
        return self.__original_property_values

    def set_spinbox_maximums(self):
        """Set maximum values to spinbox components."""
        # TODO find out if element simulation settings should have different
        #      maxima than request settings.
        #      If not, this can be moved to SimulationSettingsWidget
        int_max = 2147483647
        float_max = 1000000000000000013287555072.00
        self.sim_widget.numberOfIonsSpinBox.setMaximum(int_max)
        self.sim_widget.numberOfPreIonsSpinBox.setMaximum(int_max)
        self.sim_widget.seedSpinBox.setMaximum(int_max)
        self.sim_widget.numberOfRecoilsSpinBox.setMaximum(int_max)
        self.sim_widget.numberOfScalingIonsSpinBox.setMaximum(int_max)
        self.sim_widget.minimumScatterAngleDoubleSpinBox.setMaximum(float_max)
        self.sim_widget.minimumMainScatterAngleDoubleSpinBox.setMaximum(
            float_max)
        self.sim_widget.minimumEnergyDoubleSpinBox.setMaximum(float_max)

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

        # If there are running simulation that use the same seed as the
        # new one, stop them
        # TODO this seems unnecessary. The seed is automatically incremented
        #   to a unique value when a new simulation is run, so why should this
        #   require stopping?
        # seed = self.sim_widget.seedSpinBox.value()
        # if self.is_seed_used(seed):
        #     reply = QtWidgets.QMessageBox.question(
        #         self, "Running simulations",
        #         "There is a simulation process that has the same seed "
        #         "number as the new one.\nIf you save changes, this "
        #         "simulation process will be stopped (but its results will "
        #         "not be deleted).\n\nDo you want save changes anyway?",
        #         QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No |
        #         QtWidgets.QMessageBox.Cancel,
        #         QtWidgets.QMessageBox.Cancel)
        #     if reply == QtWidgets.QMessageBox.No or reply == \
        #             QtWidgets.QMessageBox.Cancel:
        #         self.__close = False
        #         return
        #     else:
        #         # Stop the running simulation's mcerd process
        #         # that corresponds to seed
        #         self.element_simulation.mcerd_objects[seed].stop_process()
        #         del self.element_simulation.mcerd_objects[seed]

        self.sim_widget.update_settings()
        self.element_simulation.use_default_settings = self.use_default_settings
        self.element_simulation.to_file(
                os.path.join(self.element_simulation.directory,
                             self.element_simulation.get_full_name()
                             + ".mcsimu"))

        # TODO remove files with old name, if name has changed

        self.__close = True

    # def is_seed_used(self, seed):
    #     """
    #     Check if element simulation has man mcerd process with the given seed.
    #
    #     Args:
    #         seed: Seed number.
    #
    #     Return:
    #         Whether seed is being used
    #     """
    #     # TODO function of element simulation
    #     return seed in self.element_simulation.mcerd_objects
