# coding=utf-8
"""
Created on 15.3.2013
Updated on 17.12.2018

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
__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen " \
             "\n Samuli Rahkonen \n Miika Raunio \n Severi Jääskeläinen \n " \
             "Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"
__version__ = "2.0"

import platform

import modules.masses as masses

import widgets.input_validation as iv
import widgets.gui_utils as gutils

from pathlib import Path

from dialogs.element_selection import ElementSelectionDialog

from modules.element import Element

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import uic
from PyQt5 import QtWidgets


class SelectionSettingsDialog(QtWidgets.QDialog):
    """Selection Settings dialog handles showing settings for selection made in 
    measurement (in matplotlib graph).
    """
    def __init__(self, selection):
        """Inits selection settings dialog.
        
        Args:
            selection: Selection class object.
        """
        super().__init__()
        uic.loadUi(Path("ui_files", "ui_selection_settings.ui"), self)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.selection = selection
        self.measurement = self.selection.measurement
        self.element_colormap = self.selection.element_colormap
        self.__set_isotope_weight_factor()

        # Setup connections
        self.sampleType.currentIndexChanged.connect(self.__change_type)
        self.sample_element_button.clicked.connect(self.__change_sample_element)
        self.sample_isotope_radio.toggled.connect(self.__toggle_isotope_sample)
        self.sample_isotope_combobox.currentIndexChanged.connect(
            lambda: self.__set_isotope_weight_factor(
                self.sample_isotope_combobox))
        self.rbs_element_button.clicked.connect(self.__change_rbs_element)
        self.rbs_isotope_radio.toggled.connect(self.__toggle_isotope_rbs)
        self.rbs_isotope_combobox.currentIndexChanged.connect(
            lambda: self.__set_isotope_weight_factor(
                self.rbs_isotope_combobox))
        self.colorButton.clicked.connect(self.__click_color_button)
        self.OKButton.clicked.connect(self.__accept_settings)
        self.cancelButton.clicked.connect(self.close)

        self.sampleIsotopeInfoLabel.setVisible(False)
        self.rbsIsotopeInfoLabel.setVisible(False)

        if platform.system() == "Darwin":
            self.setMinimumWidth(425)
        
        # Set current values to UI and show
        self.__set_values_to_dialog()
        # Whether we accept or cancel selection, then remove selection if
        # cancel.
        self.isOk = False
        self.exec_()

    def __set_values_to_dialog(self):
        """Set parent's values into the dialog.
        """
        if self.selection.type == "ERD":
            element = self.selection.element
            isotope = self.selection.element.isotope

            self.groupBox_sample.setEnabled(True)
            self.groupBox_rbs.setVisible(False)

            if isotope:
                self.sample_isotope_radio.setChecked(True)
                self.sample_isotope_combobox.setEnabled(True)

            self.__enable_element_fields(element.symbol,
                                         self.sample_isotope_combobox,
                                         self.sample_isotope_radio,
                                         self.sample_standard_mass_radio,
                                         self.sample_standard_mass_label,
                                         current_isotope=isotope)

            # Recoil Element
            if element.symbol:
                self.sample_element_button.setText(element.symbol)
                self.colorButton.setText(
                    "Automatic [{0}]".format(element.symbol))

        elif self.selection.type == "RBS":
            rbs_element = self.selection.element_scatter
            rbs_isotope = self.selection.element_scatter.isotope

            self.groupBox_rbs.setEnabled(True)
            self.groupBox_sample.setVisible(False)

            if rbs_isotope:
                self.rbs_isotope_radio.setChecked(True)
                self.rbs_isotope_combobox.setEnabled(True)

            self.__enable_element_fields(rbs_element.symbol,
                                         self.rbs_isotope_combobox,
                                         self.rbs_isotope_radio,
                                         self.rbs_standard_mass_radio,
                                         self.rbs_standard_mass_label,
                                         current_isotope=rbs_isotope)

            if rbs_element.symbol:
                self.rbs_element_button.setText(rbs_element.symbol)
                self.colorButton.setText(
                    "Automatic [{0}]".format(rbs_element.symbol))

        else:
            raise ValueError("Invalid values")

        # Set proper type (ERD / RBS) of the element
        for i in range(self.sampleType.count()):
            if self.sampleType.itemText(i) == self.selection.type:
                self.sampleType.setCurrentIndex(i)

        if self.selection.type == "ERD":
            if not self.selection.element.isotope:
                self.rbs_standard_mass_radio.setChecked(True)

        else:
            if not self.selection.element_scatter.isotope:
                self.sample_standard_mass_radio.setChecked(True)

        self.sampleWeightFactor.setValue(self.selection.weight_factor)

        self.__check_if_settings_ok()

    def __change_sample_element(self):
        """Shows dialog to change selection element.
        """
        self.__change_element(self.sample_element_button,
                              self.sample_isotope_combobox,
                              self.sample_standard_mass_label,
                              self.sample_standard_mass_radio,
                              self.sample_isotope_radio,
                              self.sampleIsotopeInfoLabel)
        self.__check_if_settings_ok()

    def __change_rbs_element(self):
        """Shows dialog to change selection element.
        """
        self.__change_element(self.rbs_element_button,
                              self.rbs_isotope_combobox,
                              self.rbs_standard_mass_label,
                              self.rbs_standard_mass_radio,
                              self.rbs_isotope_radio,
                              self.rbsIsotopeInfoLabel,
                              sample=False)
        self.__check_if_settings_ok()

    def __change_element(self, button, isotope_combobox, standard_mass_label,
                         standard_mass_radio, isotope_radio, isotope_info_label,
                         sample=True):
        """Shows dialog to change selection element.
        
        Args:
            button: QtWidgets.QPushButton (button to select element)
            isotope_combobox: QtWidgets.QComboBox
            isotope_radio: QtGui.QRadioButton
            standard_mass_radio: QtGui.QRadioButton
            standard_mass_label: QtWidgets.QLabel
            isotope_info_label: Label that shows if element doesn't have any
            natural isotopes.
            sample: Whether the element is from sample or rbs.
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
                                         standard_mass_label)

            if isotope_combobox.count() == 0:
                isotope_info_label.setVisible(True)
                iv.set_input_field_red(isotope_combobox)
            else:
                isotope_info_label.setVisible(False)
                isotope_combobox.setStyleSheet("background-color: %s" % "None")

    def __enable_element_fields(self, element, isotope_combobox,
                                isotope_radio, standard_mass_radio,
                                standard_mass_label,
                                current_isotope=None):
        """Enable element information fields.
        
        Args:
            element: String representing element.
            isotope_combobox: QtWidgets.QComboBox
            isotope_radio: QtGui.QRadioButton
            standard_mass_radio: QtGui.QRadioButton
            standard_mass_label: QtWidgets.QLabel
        """
        if element and element != "Select":
            isotope_radio.setEnabled(True)
            standard_mass_radio.setEnabled(True)
            standard_mass_label.setEnabled(True)
            self.__load_isotopes(isotope_combobox,
                                 standard_mass_label,
                                 element,
                                 current_isotope)
            self.__set_color_button_color(element)

    def __set_color_button_color(self, element):
        """Set default color of element to color button.
        
        Args:
            element: String representing element.
        """
        self.groupBox_coloring.setEnabled(True)
        if element and element != "Select":
            self.color = QtGui.QColor(self.element_colormap[element])
            if self.selection.is_closed:
                self.color = QtGui.QColor(self.selection.default_color)
            self.__change_color_button_color(element)

    def __set_isotope_weight_factor(self, isotope_combobox=None):
        """Set a specific isotope's weight factor to label.
        
        Args:
            isotope_combobox: A QtWidgets.QComboBox element of isotopes.
        """
        if not isotope_combobox or not isotope_combobox.isEnabled():
            self.isotope_specific_weight_factor_label.setText("")
        else:
            isotope_index = isotope_combobox.currentIndex()
            unused_isotope, propability = isotope_combobox.itemData(
                isotope_index)
            isotope_weightfactor = 100.0 / float(propability)
            text = "%.3f for specific isotope" % isotope_weightfactor
            self.isotope_specific_weight_factor_label.setText(text)

    def __click_color_button(self):
        """Shows dialog to change selection color.
        """
        dialog = QtWidgets.QColorDialog(self)
        self.color = dialog.getColor(QtGui.QColor(self.color))
        if self.color.isValid():
            if self.selection.element_scatter != "":
                element = self.selection.element_scatter.symbol
            elif self.rbs_element_button.text() != "Select":
                element = self.rbs_element_button.text()
            else:
                element = self.sample_element_button.text()
            self.__change_color_button_color(element)

    def __change_color_button_color(self, element):
        """Change color button's color.
        
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
        self.colorButton.setStyleSheet(style)

        if self.color.name() == self.element_colormap[element]:
            self.colorButton.setText("Automatic [{0}]".format(element))
        else:
            self.colorButton.setText("")

    def __load_isotopes(self, combobox, standard_mass_label,
                        element, current_isotope=None):
        """Change isotope information regarding element
        
        Args:
            combobox: QtWidgets.QComboBox where element's isotopes are loaded
            to.
            standard_mass_label: QtWidgets.QLabel where element's standard mass
            is shown.
            element: String representing element.
            current_isotope: String representing current isotope.
        """
        # TODO move to gutils
        standard_mass = masses.get_standard_isotope(element)
        standard_mass_label.setText(str(round(standard_mass, 3)))
        gutils.load_isotopes(element, combobox, current_isotope)

    def __change_type(self):
        """Toggle ERD/RBS type change.
        """
        if self.sampleType.currentText() == "RBS":
            self.__change_type_to_rbs()
        elif self.sampleType.currentText() == "ERD":
            self.__change_type_to_erd()

    def __change_type_to_rbs(self):
        """Change sample settings to RBS mode.
        """
        self.rbs_isotope_combobox.clear()
        current_isotope = None
        # Put current sample settings to RBS
        if self.sample_element_button.text() != "Select":
            self.rbs_element_button.setText(self.sample_element_button.text())
            self.rbs_isotope_radio.setChecked(
                self.sample_isotope_radio.isChecked())
            self.rbs_isotope_combobox.setEnabled(
                self.sample_isotope_radio.isChecked())
            self.rbs_standard_mass_radio.setChecked(
                self.sample_standard_mass_radio.isChecked())

            if self.sample_isotope_radio.isChecked():
                mass_index = self.sample_isotope_combobox.currentIndex()
                isotope_data = self.sample_isotope_combobox.itemData(mass_index)
                if isotope_data:
                    current_isotope = isotope_data[0]
                    self.rbsIsotopeInfoLabel.setVisible(False)
                    self.rbs_isotope_combobox.setStyleSheet(
                        "background-color: %s" % "None")
                else:
                    current_isotope = None
                    iv.set_input_field_red(self.rbs_isotope_combobox)
                    self.rbsIsotopeInfoLabel.setVisible(True)
            else:
                if self.sampleIsotopeInfoLabel.isVisible():
                    current_isotope = None
                    iv.set_input_field_red(self.rbs_isotope_combobox)
                    self.rbsIsotopeInfoLabel.setVisible(True)
                else:
                    self.rbsIsotopeInfoLabel.setVisible(False)
                    self.rbs_isotope_combobox.setStyleSheet(
                        "background-color: %s" % "None")
            self.__enable_element_fields(self.sample_element_button.text(),
                                         self.rbs_isotope_combobox,
                                         self.rbs_isotope_radio,
                                         self.rbs_standard_mass_radio,
                                         self.rbs_standard_mass_label,
                                         current_isotope=current_isotope)
        # Put Scatter Element settings to dialog
        else:
            if self.selection.element_scatter != "":
                self.rbs_element_button.setText(
                    self.selection.element_scatter.symbol)
            else:
                self.rbs_element_button.setText("Select")
            if self.selection.element_scatter and \
                    self.selection.element_scatter.isotope:
                self.rbs_isotope_radio.setChecked(True)
                self.rbs_isotope_combobox.setEnabled(True)
                self.rbs_standard_mass_radio.setChecked(False)

                current_isotope = self.selection.element_scatter.isotope
            else:
                self.rbs_isotope_radio.setChecked(False)
                self.rbs_isotope_combobox.setEnabled(False)
                if self.selection.element_scatter:
                    self.rbs_standard_mass_radio.setChecked(True)
                else:
                    self.rbs_standard_mass_radio.setChecked(False)

            self.__enable_element_fields(self.rbs_element_button.text(),
                                         self.rbs_isotope_combobox,
                                         self.rbs_isotope_radio,
                                         self.rbs_standard_mass_radio,
                                         self.rbs_standard_mass_label,
                                         current_isotope=current_isotope)

        self.sample_standard_mass_radio.setEnabled(False)
        self.sample_standard_mass_label.setEnabled(False)

        self.sample_isotope_radio.setChecked(True)
        self.sample_isotope_radio.setEnabled(False)
        self.sample_isotope_combobox.setEnabled(False)

        self.__set_color_button_color(self.rbs_element_button.text())
        if current_isotope:
            self.__set_isotope_weight_factor(self.rbs_isotope_combobox)

        self.groupBox_sample.setEnabled(False)
        self.groupBox_sample.setVisible(False)
        self.groupBox_rbs.setEnabled(True)
        self.groupBox_rbs.setVisible(True)

    def __change_type_to_erd(self):
        """Change sample settings to ERD mode.
        """
        # Put RBS information to sample settings.
        self.sample_isotope_combobox.clear()
        self.sample_element_button.setText(self.rbs_element_button.text())
        self.sample_isotope_radio.setChecked(
            self.rbs_isotope_radio.isChecked())
        self.sample_isotope_combobox.setEnabled(
            self.rbs_isotope_radio.isChecked())
        self.sample_standard_mass_radio.setChecked(
            self.rbs_standard_mass_radio.isChecked())
        self.sample_standard_mass_label.setText(
            self.rbs_standard_mass_label.text())
        current_isotope = None
        if self.rbs_element_button.text() != "Select":
            if self.sample_isotope_radio.isChecked():
                mass_index = self.rbs_isotope_combobox.currentIndex()
                isotope_data = self.rbs_isotope_combobox.itemData(mass_index)
                if isotope_data:
                    current_isotope = isotope_data[0]
                    self.sampleIsotopeInfoLabel.setVisible(False)
                    self.sample_isotope_combobox.setStyleSheet(
                        "background-color: %s" % "None")
                else:
                    iv.set_input_field_red(self.sample_isotope_combobox)
                    self.sampleIsotopeInfoLabel.setVisible(True)
            else:
                if self.rbsIsotopeInfoLabel.isVisible():
                    iv.set_input_field_red(self.sample_isotope_combobox)
                    self.sampleIsotopeInfoLabel.setVisible(True)
                else:
                    self.sample_isotope_combobox.setStyleSheet(
                        "background-color: %s" % "None")
                    self.sampleIsotopeInfoLabel.setVisible(False)
            self.__enable_element_fields(self.rbs_element_button.text(),
                                         self.sample_isotope_combobox,
                                         self.sample_isotope_radio,
                                         self.sample_standard_mass_radio,
                                         self.sample_standard_mass_label,
                                         current_isotope=current_isotope)
        if self.sample_element_button.text() == "Select":
            self.sample_standard_mass_label.setEnabled(False)
            self.sample_standard_mass_radio.setEnabled(False)
            self.sample_isotope_radio.setEnabled(False)
            self.colorButton.setStyleSheet("")  # Clear style
            self.colorButton.setText("Automatic")
        
        # Clear RBS area.
        self.rbs_element_button.setText("Select")
        self.rbs_standard_mass_label.setText("0")
        self.rbs_isotope_combobox.clear()
        # Switch to this by default.
        self.rbs_standard_mass_radio.setChecked(True)
        if current_isotope:
            self.__set_isotope_weight_factor(self.sample_isotope_combobox)

        self.groupBox_rbs.setEnabled(False)
        self.groupBox_rbs.setVisible(False)
        self.groupBox_sample.setEnabled(True)
        self.groupBox_sample.setVisible(True)

    def __toggle_isotope_sample(self):
        """Toggle Sample isotope radio button.
        """
        self.__change_to_specific_isotope(self.sample_isotope_radio,
                                          self.sample_isotope_combobox)

    def __toggle_isotope_rbs(self):
        """Toggle RBS isotope radio button.
        """
        self.__change_to_specific_isotope(self.rbs_isotope_radio,
                                          self.rbs_isotope_combobox)

    def __change_to_specific_isotope(self, radio, combobox):
        """Toggle combobox visibility depending on if radio button is checked.
        
        Args:
            radio: A QtGui.QRadioButton element.
            combobox: A QtWidgets.QComboBox element.
        """
        combobox.setEnabled(radio.isChecked())
        # self.__set_isotope_weight_factor()
        if radio.isChecked():
            self.__set_isotope_weight_factor(combobox)
        else:
            self.__set_isotope_weight_factor()

    def __check_if_settings_ok(self):
        """Check if sample settings are ok, and enable ok button.
        """
        selection_type = self.sampleType.currentText()
        rbs_element = self.rbs_element_button.text()
        sample_element = self.sample_element_button.text()
        if selection_type == "RBS" and rbs_element != "Select" and rbs_element \
           and rbs_element and not self.rbsIsotopeInfoLabel.isVisible():
            self.OKButton.setEnabled(True)
        elif selection_type == "ERD" and sample_element != "Select" and \
                sample_element and not \
                self.sampleIsotopeInfoLabel.isVisible():
            self.OKButton.setEnabled(True)
        else:
            self.OKButton.setEnabled(False)

    def __accept_settings(self):
        """Accept settings given in the selection dialog and save these to
        parent.
        """
        self.selection.type = self.sampleType.currentText()

        # For standard isotopes:
        isotope = None
        rbs_isotope = None

        symbol = self.sample_element_button.text()
        if self.selection.type == "ERD":
            if self.sample_isotope_radio.isChecked():
                isotope_index = self.sample_isotope_combobox.currentIndex()
                isotope_data = self.sample_isotope_combobox.itemData(
                    isotope_index)
                isotope = int(isotope_data[0])

            self.selection.element_scatter = Element("")
            self.selection.element = Element(symbol, isotope)

        else:
            rbs_element = self.rbs_element_button.text()
            if self.rbs_isotope_radio.isChecked():
                isotope_index = self.rbs_isotope_combobox.currentIndex()
                isotope_data = self.rbs_isotope_combobox.itemData(
                    isotope_index)
                rbs_isotope = int(isotope_data[0])

            self.selection.element_scatter = Element(rbs_element,
                                                     rbs_isotope)
            if self.measurement.run:
                self.selection.element = self.measurement.run.beam.ion
            else:
                self.selection.element = \
                    self.measurement.request.default_measurement.run.beam.ion

        self.selection.type = self.sampleType.currentText()
        self.selection.weight_factor = self.sampleWeightFactor.value()

        self.selection.default_color = self.color.name()
        self.selection.reset_color()
        self.isOk = True
        self.close()
