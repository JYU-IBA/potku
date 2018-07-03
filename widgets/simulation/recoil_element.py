# coding=utf-8
"""
Created on 2.7.2018
Updated on 3.7.2018

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

import modules.general_functions

from dialogs.energy_spectrum import EnergySpectrumParamsDialog
from  dialogs.energy_spectrum import EnergySpectrumWidget

from PyQt5 import QtWidgets
from PyQt5.QtGui import QIcon


class RecoilElementWidget(QtWidgets.QWidget):
    """
    Class that shows a recoil element that is connected to an ElementSimulation.
    """
    def __init__(self, parent, element, parent_tab, parent_element_widget,
        element_simulation):
        """
        Initialize the widget.

        Args:
            parent: A RecoilAtomDistributionWidget.
            element: An Element object.
            parent_tab: A SimulationTabWidget.
            parent_element_widget: An ElementWidget.
            element_simulation: ElementSimulation object.
        """
        super().__init__()

        self.parent = parent
        self.parent_tab = parent_tab
        self.element_simulation = element_simulation
        self.parent_element_widget = parent_element_widget

        horizontal_layout = QtWidgets.QHBoxLayout()
        horizontal_layout.setContentsMargins(12, 0, 0, 0)

        self.radio_button = QtWidgets.QRadioButton()

        if element.isotope:
            isotope_superscript = modules.general_functions.to_superscript(
                str(element.isotope))
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

        remove_recoil_button = QtWidgets.QPushButton()
        remove_recoil_button.setIcon(QIcon("ui_icons/reinhardt/edit_delete.svg"))
        remove_recoil_button.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                                           QtWidgets.QSizePolicy.Fixed)
        remove_recoil_button.clicked.connect(self.remove_recoil)
        remove_recoil_button.setToolTip("Add a new recoil to element")

        horizontal_layout.addWidget(self.radio_button)
        horizontal_layout.addWidget(draw_spectrum_button)
        horizontal_layout.addWidget(remove_recoil_button)

        self.setLayout(horizontal_layout)

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

    def remove_recoil(self):
        """
        Remove recoil from element simulation.
        """
        pass
