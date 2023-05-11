# coding=utf-8
"""
Created on 2.7.2018
Updated on 13.4.2023

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2018 Heta Rekilä

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
__author__ = "Heta Rekilä"
__version__ = "2.0"

import platform

import dialogs.dialog_functions as df
import widgets.icon_manager as icons

from modules.recoil_element import RecoilElement
from modules.element_simulation import ElementSimulation

from collections import Counter

from dialogs.energy_spectrum import EnergySpectrumParamsDialog
from dialogs.energy_spectrum import EnergySpectrumWidget

from PyQt5 import QtWidgets

from widgets.simulation.circle import Circle


class RecoilElementWidget(QtWidgets.QWidget):
    """
    Class that shows a recoil element that is connected to an ElementSimulation.
    """
    # TODO this class should be refactored together with simulation/element.py
    #   module
    def __init__(self, parent, parent_tab, parent_element_widget,
                 element_simulation: ElementSimulation, color,
                 recoil_element: RecoilElement, statusbar=None,
                 spectra_changed=None, recoil_name_changed=None):
        """
        Initialize the widget.

        Args:
            parent: A RecoilAtomDistributionWidget.
            parent_tab: A SimulationTabWidget.
            parent_element_widget: An ElementWidget.
            element_simulation: ElementSimulation object.
            color: Color for the circle.
            recoil_element: RecoilElement object.
            statusbar: QStatusBar object
            spectra_changed: signal that indicates that a recoil element
                distribution has changed and spectra needs to be updated.
            recoil_name_changed: signal that indicates that a recoil name
                has changed.
        """
        super().__init__()

        self.parent = parent
        self.tab = parent_tab
        self.element_simulation = element_simulation
        self.parent_element_widget = parent_element_widget
        self.recoil_element = recoil_element
        self.statusbar = statusbar

        horizontal_layout = QtWidgets.QHBoxLayout()
        horizontal_layout.setContentsMargins(12, 0, 0, 0)

        self.radio_button = QtWidgets.QRadioButton()

        # TODO full name takes a bit too much room. They layout could use
        #   some fixing.
        self.radio_button.setText(self.recoil_element.name)
        self.radio_button.setMaximumWidth(85)

        # Circle for showing the recoil color
        self.circle = Circle(color)

        draw_spectrum_button = QtWidgets.QPushButton()
        draw_spectrum_button.setIcon(
            icons.get_potku_icon("energy_spectrum_icon.svg"))
        draw_spectrum_button.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                                           QtWidgets.QSizePolicy.Fixed)
        draw_spectrum_button.clicked.connect(
            lambda: self.plot_spectrum(spectra_changed))
        draw_spectrum_button.setToolTip("Draw energy spectra")

        remove_recoil_button = QtWidgets.QPushButton()
        remove_recoil_button.setIcon(icons.get_reinhardt_icon(
            "edit_delete.svg"))
        remove_recoil_button.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                                           QtWidgets.QSizePolicy.Fixed)
        remove_recoil_button.clicked.connect(self.remove_recoil)
        remove_recoil_button.setToolTip("Remove recoil element")

        if platform.system() == "Darwin":
            draw_spectrum_button.setMaximumWidth(30)
            remove_recoil_button.setMaximumWidth(30)

        horizontal_layout.addWidget(self.radio_button)
        horizontal_layout.addWidget(self.circle)
        horizontal_layout.addWidget(draw_spectrum_button)
        horizontal_layout.addWidget(remove_recoil_button)

        self.setLayout(horizontal_layout)

        self.recoil_name_changed = recoil_name_changed
        if self.recoil_name_changed is not None:
            self.recoil_name_changed.connect(self._set_name)

    def closeEvent(self, event):
        try:
            self.recoil_name_changed.disconnect(self._set_name)
        except (TypeError, ValueError):
            pass
        super().closeEvent(event)

    def _set_name(self, _, rec_elem):
        if rec_elem is self.recoil_element:
            self.radio_button.setText(
                self.recoil_element.name)

    def plot_spectrum(self, spectra_changed=None):
        """Plot an energy spectrum and show it in a widget.
        """
        previous = None
        dialog = EnergySpectrumParamsDialog(
            self.tab,
            spectrum_type=EnergySpectrumWidget.SIMULATION,
            element_simulation=self.element_simulation,
            simulation=self.tab.obj,
            recoil_widget=self,
            statusbar=self.statusbar)
        if dialog.result_files:
            energy_spectrum_widget = EnergySpectrumWidget(
                parent=self.tab,
                use_cuts=dialog.result_files,
                bin_width=dialog.bin_width,
                spectrum_type=EnergySpectrumWidget.SIMULATION,
                spectra_changed=spectra_changed)

            # Check all energy spectrum widgets, if one has the same
            # elements, delete it
            for e_widget in self.tab.energy_spectrum_widgets:
                keys = e_widget.energy_spectrum_data.keys()
                if Counter(keys) == Counter(
                        energy_spectrum_widget.energy_spectrum_data.keys()):
                    previous = e_widget
                    self.tab.energy_spectrum_widgets.remove(e_widget)
                    self.tab.del_widget(e_widget)
                    break

            self.tab.energy_spectrum_widgets.append(
                energy_spectrum_widget)
            icon = self.parent.element_manager.icon_manager.get_icon(
                "energy_spectrum_icon_16.png")
            self.tab.add_widget(energy_spectrum_widget, icon=icon)

            if previous and energy_spectrum_widget is not None:
                energy_spectrum_widget.save_file_int = previous.save_file_int
                energy_spectrum_widget.save_to_file(measurement=False,
                                                    update=True)
            elif not previous and energy_spectrum_widget is not None:
                energy_spectrum_widget.save_to_file(measurement=False,
                                                    update=False)

    def remove_recoil(self):
        """Remove recoil from element simulation.
        """
        reply = QtWidgets.QMessageBox.question(
            self.parent.parent, "Confirmation",
            "Deleting selected recoil element will delete possible energy "
            "spectra data calculated from it.\n\n"
            "Are you sure you want to delete selected recoil element anyway?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No |
            QtWidgets.QMessageBox.Cancel, QtWidgets.QMessageBox.Cancel)
        if reply == QtWidgets.QMessageBox.No or reply == \
                QtWidgets.QMessageBox.Cancel:
            return  # If clicked Yes, then continue normally
        self.parent.remove_recoil_element(self)

        # Delete energy spectra that use recoil
        df.delete_recoil_espe(self.tab, self.recoil_element.get_full_name())
