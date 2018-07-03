# coding=utf-8
"""
Created on 1.3.2018
Updated on 3.7.2018

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

from PyQt5 import QtWidgets
from PyQt5.QtGui import QIcon

from dialogs.energy_spectrum import EnergySpectrumParamsDialog, \
    EnergySpectrumWidget
from dialogs.simulation.element_simulation_settings import \
    ElementSimulationSettingsDialog

from modules.recoil_element import RecoilElement
from modules.point import Point

from widgets.simulation.recoil_element import RecoilElementWidget


class ElementWidget(QtWidgets.QWidget):
    """Class for creating an element widget for the recoil atom distribution.
        """

    def __init__(self, parent, element, parent_tab, element_simulation):
        """
        Initializes the ElementWidget.

        Args:
            parent: A RecoilAtomDistributionWidget.
            element: An Element object.
            parent_tab: A SimulationTabWidget.
            element_simulation: ElementSimulation object.
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

        draw_spectrum_button = QtWidgets.QPushButton()
        draw_spectrum_button.setIcon(QIcon(
            "ui_icons/potku/energy_spectrum_icon.svg"))
        draw_spectrum_button.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                                           QtWidgets.QSizePolicy.Fixed)
        draw_spectrum_button.clicked.connect(self.plot_spectrum)
        draw_spectrum_button.setToolTip("Draw energy spectra")

        settings_button = QtWidgets.QPushButton()
        settings_button.setIcon(QIcon("ui_icons/reinhardt/gear.svg"))
        settings_button.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                                      QtWidgets.QSizePolicy.Fixed)
        settings_button.clicked.connect(
            self.open_element_simulation_settings)
        settings_button.setToolTip("Edit element simulation settings")

        add_recoil_button = QtWidgets.QPushButton()
        add_recoil_button.setIcon(QIcon("ui_icons/reinhardt/edit_add.svg"))
        add_recoil_button.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                                        QtWidgets.QSizePolicy.Fixed)
        add_recoil_button.clicked.connect(self.add_new_recoil)
        add_recoil_button.setToolTip("Add a new recoil to element")

        horizontal_layout.addWidget(self.radio_button)
        horizontal_layout.addWidget(draw_spectrum_button)
        horizontal_layout.addWidget(settings_button)
        horizontal_layout.addWidget(add_recoil_button)

        self.setLayout(horizontal_layout)

    def add_element_simulation_reference(self, element_simulation):
        """
        Add reference to an Element Simulation object.
        """
        self.element_simulation = element_simulation

    def add_new_recoil(self):
        """
        Add new recoil to element simulation.
        """
        xs = [0.00, 35.00]
        ys = [1.0, 1.0]
        xys = list(zip(xs, ys))
        points = []
        for xy in xys:
            points.append(Point(xy))

        element = copy.copy(self.element_simulation.recoil_elements[0].element)
        recoil_element = RecoilElement(element, points)
        recoil_widget = RecoilElementWidget(self.parent, element,
                                            self.parent_tab, self,
                                            self.element_simulation)
        recoil_element.widgets.append(recoil_widget)
        self.element_simulation.recoil_elements.append(recoil_element)

        self.parent.radios.addButton(recoil_widget.radio_button)
        # Add recoil widget under ite element simulation's element widget
        for i in range(self.parent.recoil_vertical_layout.count()):
            if self.parent.recoil_vertical_layout.itemAt(i).widget() == self:
                self.parent.recoil_vertical_layout.insertWidget(i + 1,
                                                                recoil_widget)
                break

    def open_element_simulation_settings(self):
        """
        Open element simulation settings.
        """
        ElementSimulationSettingsDialog(self.element_simulation)

    def plot_spectrum(self):
        """
        Plot an energy spectrum.
        """
        # self.element_simulation.calculate_espe()
        dialog = EnergySpectrumParamsDialog(
            self.parent_tab, spectrum_type="simulation",
            element_simulation=self.element_simulation)
        if dialog.result_files:
            self.parent_tab.energy_spectrum_widget = EnergySpectrumWidget(
                parent=self.parent_tab, use_cuts=dialog.result_files,
                bin_width=dialog.bin_width, spectrum_type="simulation")
            self.parent_tab.add_widget(self.parent_tab.energy_spectrum_widget)
