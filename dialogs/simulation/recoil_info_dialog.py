# coding=utf-8
"""
Created on 3.5.2018
Updated on 30.10.2018

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

import widgets.binding as bnd
import widgets.input_validation as iv

from widgets.gui_utils import QtABCMeta

from PyQt5 import QtWidgets
from PyQt5 import uic
from PyQt5.QtGui import QColor

from widgets.scientific_spinbox import ScientificSpinBox


class RecoilInfoDialog(QtWidgets.QDialog, bnd.PropertyBindingWidget,
                       metaclass=QtABCMeta):
    """Dialog for editing the name, description and reference density
    of a recoil element.
    """
    # TODO possibly track name changes
    name = bnd.bind("nameLineEdit")
    description = bnd.bind("descriptionLineEdit")
    reference_density = bnd.bind("scientific_spinbox")

    @property
    def multiplier(self):
        return self.scientific_spinbox.multiplier

    @property
    def color(self):
        return self.tmp_color.name()

    def __init__(self, recoil_element, colormap, element_simulation):
        """Inits a recoil info dialog.

        Args:
            recoil_element: A RecoilElement object.
            colormap: Colormap for elements.
            element_simulation: Element simulation that has the recoil element.
        """
        super().__init__()
        uic.loadUi(os.path.join("ui_files", "ui_recoil_info_dialog.ui"), self)

        self.okPushButton.clicked.connect(self.__accept_settings)
        self.cancelPushButton.clicked.connect(self.close)
        self.colorPushButton.clicked.connect(self.__change_color)

        self.name = recoil_element.name
        self.description = recoil_element.description
        value = recoil_element.reference_density
        multiplier = recoil_element.multiplier
        self.scientific_spinbox = ScientificSpinBox(value, multiplier,
                                                    0.01, 99.99e22)
        self.formLayout.insertRow(
            4,
            QtWidgets.QLabel(r"Reference density [at./cm<sup>3</sup>]:"),
            self.scientific_spinbox)
        self.formLayout.removeRow(self.widget)

        self.description = recoil_element.description
        self.isOk = False

        self.dateLabel.setText(time.strftime("%c %z %Z", time.localtime(
            recoil_element.modification_time)))

        self.fields_are_valid = True
        iv.set_input_field_red(self.nameLineEdit)
        self.nameLineEdit.textChanged.connect(
            lambda: iv.check_text(self.nameLineEdit, qwidget=self))
        self.nameLineEdit.textEdited.connect(self.__validate)

        title = f"Recoil element: " \
                f"{recoil_element.element.get_prefix()}"

        self.infoGroupBox.setTitle(title)

        self.recoil_element = recoil_element
        self.element_simulation = element_simulation

        self.tmp_color = QColor(self.recoil_element.color)
        self.colormap = colormap

        self.__set_color_button_color(recoil_element.element.symbol)

        self.exec_()

    def __density_valid(self):
        """
        Check if density value is valid and in limits.

        Return:
            True or False.
        """
        if self.scientific_spinbox.check_min_and_max():
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
            return

        if self.name != self.recoil_element.name:
            # Check that the new name is not already in use
            if self.name in (r.name for r in
                             self.element_simulation.recoil_elements):
                QtWidgets.QMessageBox.critical(
                    self, "Warning",
                    "Name of the recoil element is "
                    "already in use. Please use a "
                    "different name",
                    QtWidgets.QMessageBox.Ok,
                    QtWidgets.QMessageBox.Ok)
                return

        # If current recoil is used in a running simulation
        if self.recoil_element is \
                self.element_simulation.recoil_elements[0]:
            if self.element_simulation.mcerd_objects and self.name != \
                    self.recoil_element.name:
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
                    return
                else:
                    self.element_simulation.stop()

        self.isOk = True
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
        self.colorPushButton.setStyleSheet(style)

        if self.tmp_color.name() == self.colormap[element]:
            self.colorPushButton.setText("Automatic [{0}]".format(element))
        else:
            self.colorPushButton.setText("")

    def __set_color_button_color(self, element):
        """Set default color of element to color button.

        Args:
            element: String representing element.
        """
        self.colorPushButton.setEnabled(True)
        self.tmp_color = QColor(self.recoil_element.color)
        self.__change_color_button_color(element)

    def __validate(self):
        """
        Validate the recoil name.
        """
        text = self.name
        regex = "^[A-Za-z0-9-ÖöÄäÅå]*"
        valid_text = iv.validate_text_input(text, regex)

        self.name = valid_text
