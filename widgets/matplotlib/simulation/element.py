# coding=utf-8
"""
Created on 1.3.2018
Updated on 2.8.2018

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
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n " \
             "Sinikka Siironen"
__version__ = "2.0"

import copy
import modules.general_functions as general

from dialogs.energy_spectrum import EnergySpectrumParamsDialog
from dialogs.energy_spectrum import EnergySpectrumWidget
from dialogs.simulation.element_simulation_settings import \
    ElementSimulationSettingsDialog

from collections import Counter

from modules.recoil_element import RecoilElement

from PyQt5 import QtGui
from PyQt5 import QtWidgets

from widgets.simulation.circle import Circle
from widgets.simulation.recoil_element import RecoilElementWidget


class ElementWidget(QtWidgets.QWidget):
    """Class for creating an element widget for the recoil atom distribution.
        """

    def __init__(self, parent, element, parent_tab, element_simulation, color):
        """
        Initializes the ElementWidget.

        Args:
            parent: A RecoilAtomDistributionWidget.
            element: An Element object.
            parent_tab: A SimulationTabWidget.
            element_simulation: ElementSimulation object.
            color: Color for the circle.
        """
        super().__init__()

        self.parent = parent
        self.parent_tab = parent_tab
        self.element_simulation = element_simulation

        horizontal_layout = QtWidgets.QHBoxLayout()
        horizontal_layout.setContentsMargins(0, 0, 0, 0)

        self.radio_button = QtWidgets.QRadioButton()

        if element.isotope:
            isotope_superscript = general.to_superscript(str(element.isotope))
            button_text = isotope_superscript + " " + element.symbol
        else:
            button_text = element.symbol

        self.radio_button.setText(button_text)

        # Circle for showing the recoil color
        self.circle = Circle(color)

        draw_spectrum_button = QtWidgets.QPushButton()
        draw_spectrum_button.setIcon(QtGui.QIcon(
            "ui_icons/potku/energy_spectrum_icon.svg"))
        draw_spectrum_button.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                                           QtWidgets.QSizePolicy.Fixed)
        draw_spectrum_button.clicked.connect(self.plot_spectrum)
        draw_spectrum_button.setToolTip("Draw energy spectra")

        settings_button = QtWidgets.QPushButton()
        settings_button.setIcon(QtGui.QIcon("ui_icons/reinhardt/gear.svg"))
        settings_button.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                                      QtWidgets.QSizePolicy.Fixed)
        settings_button.clicked.connect(
            self.open_element_simulation_settings)
        settings_button.setToolTip("Edit element simulation settings")

        add_recoil_button = QtWidgets.QPushButton()
        add_recoil_button.setIcon(QtGui.QIcon(
            "ui_icons/reinhardt/edit_add.svg"))
        add_recoil_button.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                                        QtWidgets.QSizePolicy.Fixed)
        add_recoil_button.clicked.connect(self.add_new_recoil)
        add_recoil_button.setToolTip("Add a new recoil to element")

        horizontal_layout.addWidget(self.radio_button)
        horizontal_layout.addWidget(self.circle)
        horizontal_layout.addWidget(draw_spectrum_button)
        horizontal_layout.addWidget(settings_button)
        horizontal_layout.addWidget(add_recoil_button)

        self.setLayout(horizontal_layout)

        self.running_int_recoil = 1

    def add_new_recoil(self):
        """
        Add new recoil to element simulation.
        """
        points = copy.deepcopy(self.element_simulation.recoil_elements[
                                   0].get_points())

        element = copy.copy(self.element_simulation.recoil_elements[0].element)
        name = "Default-" + str(self.running_int_recoil)

        color = self.element_simulation.recoil_elements[0].color

        if self.element_simulation.simulation_type == "ERD":
            rec_type = "rec"
        else:
            rec_type = "sct"

        recoil_element = RecoilElement(element, points, color, name,
                                       rec_type=rec_type)
        self.running_int_recoil = self.running_int_recoil + 1
        recoil_widget = RecoilElementWidget(self.parent, element,
                                            self.parent_tab, self,
                                            self.element_simulation,
                                            color)
        recoil_element.widgets.append(recoil_widget)
        self.element_simulation.recoil_elements.append(recoil_element)

        self.parent.radios.addButton(recoil_widget.radio_button)
        # Add recoil widget under ite element simulation's element widget
        for i in range(self.parent.recoil_vertical_layout.count()):
            if self.parent.recoil_vertical_layout.itemAt(i).widget() == self:
                self.parent.recoil_vertical_layout.insertWidget(i + 1,
                                                                recoil_widget)
                break
        recoil_widget.radio_button.setChecked(True)

        # Save recoil element
        self.element_simulation.recoil_to_file(
            self.element_simulation.directory, recoil_element)

    def open_element_simulation_settings(self):
        """
        Open element simulation settings.
        """
        ElementSimulationSettingsDialog(self.element_simulation,
                                        self.parent_tab)

    def plot_spectrum(self):
        """
        Plot an energy spectrum and show it in a widget.
        """
        dialog = EnergySpectrumParamsDialog(
            self.parent_tab, spectrum_type="simulation",
            element_simulation=self.element_simulation, recoil_widget=self)
        if dialog.result_files:
            energy_spectrum_widget = EnergySpectrumWidget(
                parent=self.parent_tab, use_cuts=dialog.result_files,
                bin_width=dialog.bin_width, spectrum_type="simulation")

            # Check all energy spectrum widgets, if one has the same
            # elements, delete it
            for e_widget in self.parent_tab.energy_spectrum_widgets:
                keys = e_widget.energy_spectrum_data.keys()
                if Counter(keys) == Counter(
                        energy_spectrum_widget.energy_spectrum_data.keys()):
                    self.parent_tab.energy_spectrum_widgets.remove(e_widget)
                    self.parent_tab.del_widget(e_widget)
                    break

            self.parent_tab.energy_spectrum_widgets.append(
                energy_spectrum_widget)
            self.parent_tab.add_widget(energy_spectrum_widget)
