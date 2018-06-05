# coding=utf-8
"""
Created on 1.3.2018
Updated on 5.6.2018

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

from PyQt5 import QtWidgets
from PyQt5.QtGui import QIcon
from dialogs.energy_spectrum import EnergySpectrumParamsDialog, \
    EnergySpectrumWidget
import modules.general_functions as general


class ElementWidget(QtWidgets.QWidget):
    """Class for creating an element widget for the recoil atom distribution.

        Args:
            parent: A SimulationTabWidget.
        """

    def __init__(self, parent, element, icon_manager):
        """
        Initializes the ElementWidget.

        Args:
            parent: Parent widget.
            element: An Element object.
            icon_manager: IconManager object.
        """
        super().__init__()

        self.parent = parent

        horizontal_layout = QtWidgets.QHBoxLayout()

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

        horizontal_layout.addWidget(self.radio_button)
        horizontal_layout.addWidget(draw_spectrum_button)

        self.setLayout(horizontal_layout)

    def plot_spectrum(self):
        """
        Plot an energy spectrum.
        """
        self.element_simulation.calculate_espe()
        dialog = EnergySpectrumParamsDialog(self.parent,
                                            spectrum_type="simulation")
        if dialog.result_files:
            self.parent.energy_spectrum_widget = EnergySpectrumWidget(
                parent=self.parent, use_cuts=dialog.result_files,
                bin_width=dialog.bin_width, spectrum_type="simulation")
            self.parent.add_widget(self.parent.energy_spectrum_widget)
