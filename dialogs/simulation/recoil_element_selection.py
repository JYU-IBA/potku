# coding=utf-8
"""
Created on 23.4.2018
Updated on 20.7.2018

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
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n " \
             "Sinikka Siironen"
__version__ = "2.0"

import modules.masses as masses

import os

from dialogs.element_selection import ElementSelectionDialog

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5 import uic


class RecoilElementSelectionDialog(QtWidgets.QDialog):
    """Selection Settings dialog handles showing settings for selection made in
    measurement (in matplotlib graph).
    """

    def __init__(self, recoil_atom_distribution):
        """Inits simulation element selection dialog.
        """
        super().__init__()
        self.ui = uic.loadUi(os.path.join("ui_files",
                                  "ui_recoil_element_selection_dialog.ui"),
                             self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.recoil_atom_distribution = recoil_atom_distribution

        self.element = None
        self.isotope = None
        self.color = None
        self.tmp_element = None
        self.colormap = self.recoil_atom_distribution.simulation.request \
            .global_settings.get_element_colors()

        # Setup connections
        self.ui.element_button.clicked.connect(self.__change_sample_element)
        self.ui.isotope_radio.toggled.connect(self.__toggle_isotope_sample)

        self.ui.OKButton.clicked.connect(self.__accept_settings)
        self.ui.cancelButton.clicked.connect(self.close)
        self.ui.colorPushButton.clicked.connect(self.__change_color)

        # Whether we accept or cancel selection, then remove selection if
        # cancel.
        self.isOk = False
        self.exec_()

    def __set_color_button_color(self, element):
        """Set default color of element to color button.

        Args:
            element: String representing element.
        """
        self.ui.colorPushButton.setEnabled(True)
        if element and element != "Select":
            self.color = QtGui.QColor(self.colormap[element])
            self.__change_color_button_color(element)

    def __change_color(self):
        """
        Change the color of the recoil element.
        """
        dialog = QtWidgets.QColorDialog(self)
        color = dialog.getColor(QtGui.QColor(self.color))
        if color.isValid():
            self.color = color
            self.__change_color_button_color(self.tmp_element)

    def __change_color_button_color(self, element):
        """
        Change color button's color.

        Args:
            element: String representing element name.
        """
        text_color = "black"
        luminance = 0.2126 * self.color.red() + 0.7152 * self.color.green()
        luminance += 0.0722 * self.color.blue()
        if luminance < 50:
            text_color = "white"
        style = "background-color: {0}; color: {1};".format(self.color.name(),
                                                            text_color)
        self.ui.colorPushButton.setStyleSheet(style)

        if self.color.name() == self.colormap[element]:
            self.ui.colorPushButton.setText("Automatic [{0}]".format(element))
        else:
            self.ui.colorPushButton.setText("")

    def __change_sample_element(self):
        """Shows dialog to change selection element.
        """
        self.__change_element(self.ui.element_button,
                              self.ui.isotope_combobox,
                              self.ui.standard_mass_label,
                              self.ui.standard_mass_radio,
                              self.ui.isotope_radio)
        self.__check_if_settings_ok()

    def __change_element(self, button, isotope_combobox, standard_mass_label,
                         standard_mass_radio, isotope_radio, sample=True):
        """Shows dialog to change selection element.

        Args:
            button: QtWidgets.QPushButton (button to select element)
            isotope_combobox: QtWidgets.QComboBox
            standard_mass_radio: QtGui.QRadioButton
            standard_mass_label: QtWidgets.QLabel
            isotope_radio: QtGui.QRadioButton
            sample: Boolean representing if element is sample (and not RBS
                    element).
        """
        dialog = ElementSelectionDialog()
        # Only disable these once, not if you cancel after selecting once.
        if button.text() == "Select":
            isotope_radio.setEnabled(False)
            standard_mass_radio.setEnabled(False)
            standard_mass_label.setEnabled(False)
        # If element was selected, proceed to enable appropriate fields.
        if dialog.element:
            button.setText(dialog.element)
            self.__enable_element_fields(dialog.element, isotope_combobox,
                                         isotope_radio, standard_mass_radio,
                                         standard_mass_label, sample)
            self.__set_color_button_color(dialog.element)
            self.tmp_element = dialog.element

    def __enable_element_fields(self, element, isotope_combobox,
                                isotope_radio, standard_mass_radio,
                                standard_mass_label, sample=True,
                                current_isotope=None):
        """Enable element information fields.

        Args:
            element: String representing element.
            isotope_combobox: QtWidgets.QComboBox
            isotope_radio: QtGui.QRadioButton
            standard_mass_radio: QtGui.QRadioButton
            standard_mass_label: QtWidgets.QLabel
            sample: Boolean representing if element is sample (and not RBS
                    element).
        """
        if element:
            isotope_radio.setEnabled(True)
            standard_mass_radio.setEnabled(True)
            standard_mass_label.setEnabled(True)
            self.__load_isotopes(isotope_combobox,
                                 standard_mass_label,
                                 element,
                                 current_isotope)

    def __load_isotopes(self, combobox, standard_mass_label, element,
                        current_isotope=None):
        """Change isotope information regarding element

        Args:
            combobox: QtWidgets.QComboBox where element's isotopes are loaded
                      to.
            standard_mass_label: QtWidgets.QLabel where element's standard mass
                                 is shown.
            element: String representing element.
            current_isotope: String representing current isotope.
        """
        standard_mass = masses.get_standard_isotope(element)
        standard_mass_label.setText(str(round(standard_mass, 3)))
        masses.load_isotopes(element, combobox, current_isotope)

    def __toggle_isotope_sample(self):
        """Toggle Sample isotope radio button.
        """
        self.ui.isotope_combobox.setEnabled(self.ui.isotope_radio.isChecked())

    def __check_if_settings_ok(self):
        """Check if sample settings are ok, and enable ok button.
        """
        element = self.ui.element_button.text()
        if element:
            self.ui.OKButton.setEnabled(True)
        elif element != "Select" and element:
            self.ui.OKButton.setEnabled(True)
        else:
            self.ui.OKButton.setEnabled(False)

    def __accept_settings(self):
        """Accept settings given in the selection dialog and save these to
        parent.
        """
        self.element = self.ui.element_button.text()

        # For standard isotopes:

        # Check if specific isotope was chosen and use that instead.
        if self.ui.isotope_radio.isChecked():
            isotope_index = self.ui.isotope_combobox.currentIndex()
            isotope_data = self.ui.isotope_combobox.itemData(isotope_index)
            self.isotope = isotope_data[0]

        self.isOk = True
        self.close()
