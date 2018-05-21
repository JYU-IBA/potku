# coding=utf-8
"""
Created on 1.3.2018
Updated on 21.5.2018
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
        dialog = EnergySpectrumParamsDialog(self.parent)
        if dialog.result_files:
            self.parent.energy_spectrum_widget = EnergySpectrumWidget(
                parent=self.parent, use_cuts=dialog.result_files,
                bin_width=dialog.bin_width)
            self.parent.add_widget(self.parent.energy_spectrum_widget)
