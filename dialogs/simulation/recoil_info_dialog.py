# coding=utf-8
"""
Created on 3.5.2018
Updated on 9.8.2018

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

import os
import time

from PyQt5 import QtWidgets
from PyQt5 import uic

from modules.general_functions import check_text
from modules.general_functions import set_input_field_red
from modules.general_functions import validate_text_input

from widgets.scientific_spinbox import ScientificSpinBox


class RecoilInfoDialog(QtWidgets.QDialog):
    """Dialog for editing the name, description and reference density
    of a recoil element.
    """

    def __init__(self, recoil_element, colormap, element_simulation):
        """Inits a recoil info dialog.

        Args:
            recoil_element: A RecoilElement object.
            colormap: Colormap for elements.
            element_simulation: Element simulation that has the recoil element.
        """
        super().__init__()
        self.__ui = uic.loadUi(os.path.join("ui_files",
                                            "ui_recoil_info_dialog.ui"),
                               self)

        self.__ui.okPushButton.clicked.connect(self.__accept_settings)
        self.__ui.cancelPushButton.clicked.connect(self.close)
        self.__ui.colorPushButton.clicked.connect(self.__change_color)

        set_input_field_red(self.__ui.nameLineEdit)
        self.text_is_valid = True
        self.__ui.nameLineEdit.textChanged.connect(
            lambda: self.__check_text(self.__ui.nameLineEdit, self))

        self.name = recoil_element.name
        self.__ui.nameLineEdit.setText(recoil_element.name)
        self.__ui.descriptionLineEdit.setPlainText(
            recoil_element.description)

        value = recoil_element.reference_density
        multiplier = recoil_element.multiplier
        self.__scientific_spinbox = ScientificSpinBox(value, multiplier,
                                                            0.01, 99.99e22)
        self.__ui.formLayout.insertRow(4, QtWidgets.QLabel(r"Reference "
                                                           "density "
                                                           "[at./cm"
                                                           "<sup>2</sup>]:"),
                                       self.__scientific_spinbox)
        self.__ui.formLayout.removeRow(self.__ui.widget)

        self.description = recoil_element.description
        self.isOk = False

        self.__ui.dateLabel.setText(time.strftime("%c %z %Z", time.localtime(
            recoil_element.modification_time)))

        self.__ui.nameLineEdit.textEdited.connect(lambda: self.__validate())

        if recoil_element.element.isotope:
            title = "Recoil element: " + str(recoil_element.element.isotope) +\
                    recoil_element.element.symbol
        else:
            title = "Recoil element: " + recoil_element.element.symbol

        self.__ui.infoGroupBox.setTitle(title)

        self.recoil_element = recoil_element
        self.element_simulation = element_simulation

        self.__close = True
        self.color = None
        self.tmp_color = self.recoil_element.color
        self.colormap = colormap

        self.__set_color_button_color(recoil_element.element.symbol)

        self.exec_()

    def __density_valid(self):
        """
        Check if density value is valid and in limits.

        Return:
            True or False.
        """
        if self.__scientific_spinbox.check_min_and_max():
            return True
        return False

    def __accept_settings(self):
        """Function for accepting the current settings and closing the dialog
        window.
        """
        if not self.text_is_valid or not self.__density_valid():
            QtWidgets.QMessageBox.critical(self, "Warning",
                                           "Some of the setting values are "
                                           "invalid.\n" +
                                           "Please input values in fields "
                                           "indicated in red.",
                                           QtWidgets.QMessageBox.Ok,
                                           QtWidgets.QMessageBox.Ok)
            self.__close = False
        else:
            # If current recoil is used in a running simulation
            if self.recoil_element is \
                    self.element_simulation.recoil_elements[0]:
                if self.element_simulation.mcerd_objects and self.name != \
                        self.__ui.nameLineEdit.text():
                    reply = QtWidgets.QMessageBox.question(
                        self, "Recoil used in simulation",
                        "This recoil is used in a simulation that is "
                        "currently running.\nIf you change the name of "
                        "the recoil, the running simulation will be "
                        "stopped.\n\n"
                        "Do you want to save changes anyway?",
                        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No |
                        QtWidgets.QMessageBox.Cancel,
                        QtWidgets.QMessageBox.Cancel)
                    if reply == QtWidgets.QMessageBox.No or reply == \
                            QtWidgets.QMessageBox.Cancel:
                        self.__close = False
                    else:
                        self.element_simulation.controls.stop_simulation()
                        self.__update_values()
                else:
                    self.__update_values()
            else:
                self.__update_values()
        if self.__close:
            self.close()

    def __update_values(self):
        """
        Update values in the dialog to be accessed outside of the dialog.
        """
        self.name = self.__ui.nameLineEdit.text()
        self.description = self.__ui.descriptionLineEdit.toPlainText()
        self.reference_density = self.__scientific_spinbox.value
        self.multiplier = self.__scientific_spinbox.multiplier
        self.color = self.tmp_color
        self.isOk = True
        self.__close = True

    def __change_color(self):
        """
        Change the color of the recoil element.
        """
        dialog = QtWidgets.QColorDialog(self)
        color = dialog.getColor(self.tmp_color)
        if color.isValid():
            self.tmp_color = color
            self.__change_color_button_color(self.recoil_element.element.symbol)

    def __change_color_button_color(self, element):
        """
        Change color button's color.

        Args:
            element: String representing element name.
        """
        text_color = "black"
        luminance = 0.2126 * self.tmp_color.red() + 0.7152 * \
            self.tmp_color.green()
        luminance += 0.0722 * self.tmp_color.blue()
        if luminance < 50:
            text_color = "white"
        style = "background-color: {0}; color: {1};".format(
            self.tmp_color.name(), text_color)
        self.__ui.colorPushButton.setStyleSheet(style)

        if self.tmp_color.name() == self.colormap[element]:
            self.__ui.colorPushButton.setText("Automatic [{0}]".format(element))
        else:
            self.__ui.colorPushButton.setText("")

    @staticmethod
    def __check_text(input_field, settings):
        """Checks if there is text in given input field.

        Args:
            input_field: Input field the contents of which are checked.
            settings: Settings dialog.
        """
        settings.fields_are_valid = check_text(input_field)

    def __set_color_button_color(self, element):
        """Set default color of element to color button.

        Args:
            element: String representing element.
        """
        self.__ui.colorPushButton.setEnabled(True)
        self.tmp_color = self.recoil_element.color
        self.__change_color_button_color(element)

    def __validate(self):
        """
        Validate the recoil name.
        """
        text = self.__ui.nameLineEdit.text()
        regex = "^[A-Za-z0-9-ÖöÄäÅå]*"
        valid_text = validate_text_input(text, regex)

        self.__ui.nameLineEdit.setText(valid_text)
