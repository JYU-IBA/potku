# coding=utf-8
"""
Created on 3.5.2018
Updated on 3.8.2018

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
from PyQt5.QtCore import QLocale

from modules.general_functions import check_text
from modules.general_functions import set_input_field_red
from modules.general_functions import validate_text_input

from widgets.scientific_spinbox import ScientificDoubleSpinBox

from modules.input_validator import InputValidator


class RecoilInfoDialog(QtWidgets.QDialog):
    """Dialog for editing the name, description and reference density
    of a recoil element.
    """

    def __init__(self, recoil_element, colormap):
        """Inits a recoil info dialog.

        Args:
            recoil_element: A RecoilElement object.
            colormap: Colormap for elements.
        """
        super().__init__()
        self.__ui = uic.loadUi(os.path.join("ui_files",
                                            "ui_recoil_info_dialog.ui"),
                               self)

        locale = QLocale.c()
        self.__ui.referenceDensityDoubleSpinBox.setLocale(locale)

        self.__ui.okPushButton.clicked.connect(self.__accept_settings)
        self.__ui.cancelPushButton.clicked.connect(self.close)
        self.__ui.colorPushButton.clicked.connect(self.__change_color)

        set_input_field_red(self.__ui.nameLineEdit)
        self.fields_are_valid = False
        self.__ui.nameLineEdit.textChanged.connect(
            lambda: self.__check_text(self.__ui.nameLineEdit, self))

        self.name = ""
        self.__ui.nameLineEdit.setText(recoil_element.name)
        self.__ui.descriptionLineEdit.setPlainText(
            recoil_element.description)
        self.__ui.referenceDensityDoubleSpinBox.setValue(
            recoil_element.reference_density)
        self.__ui.formLayout.addWidget(ScientificDoubleSpinBox())
        self.description = ""
        self.isOk = False

        self.__ui.dateLabel.setText(time.strftime("%c %z %Z", time.localtime(
            recoil_element.modification_time)))

        self.__ui.nameLineEdit.textEdited.connect(lambda: self.__validate())

        self.__ui.infoGroupBox.setTitle("Recoil element: " +
                                        str(recoil_element.element.isotope) +
                                        recoil_element.element.symbol)

        self.recoil_element = recoil_element

        self.__close = True
        self.color = None
        self.tmp_color = self.recoil_element.color
        self.colormap = colormap

        self.__set_color_button_color(recoil_element.element.symbol)

        self.exec_()

    def __accept_settings(self):
        """Function for accepting the current settings and closing the dialog
        window.
        """
        if not self.fields_are_valid:
            QtWidgets.QMessageBox.critical(self, "Warning",
                                           "Some of the setting values have"
                                           " not been set.\n" +
                                           "Please input values in fields "
                                           "indicated in red.",
                                           QtWidgets.QMessageBox.Ok,
                                           QtWidgets.QMessageBox.Ok)
            self.__close = False
        else:
            self.name = self.__ui.nameLineEdit.text()
            self.description = self.__ui.descriptionLineEdit.toPlainText()
            self.reference_density = self.__ui.referenceDensityDoubleSpinBox\
                .value()
            self.color = self.tmp_color
            self.isOk = True
            self.__close = True
        if self.__close:
            self.close()

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
