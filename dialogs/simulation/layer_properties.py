# coding=utf-8
"""
Created on 28.2.2018
Updated on 30.4.2018

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

from PyQt5 import uic, QtGui, QtWidgets

import modules.masses as masses
from dialogs.element_selection import ElementSelectionDialog
from modules.element import Element
from modules.layer import Layer


class LayerPropertiesDialog(QtWidgets.QDialog):
    """Dialog for adding a new layer or editing an existing one.
    """

    def __init__(self):
        """Inits a layer dialog.
        """
        super().__init__()
        self.__ui = uic.loadUi(os.path.join("ui_files", "ui_layer_dialog.ui"),
                               self)
        self.layer = None

        # Some border of widgets might be displaying red, because information
        # is missing. Remove the red border by reseting the style sheets, for
        # example when user changes the text in line edit.
        self.__ui.nameEdit.textChanged.connect(
            lambda: self.__ui.nameEdit.setStyleSheet(""))
        self.__ui.thicknessEdit.valueChanged.connect(
            lambda: self.__ui.thicknessEdit.setStyleSheet(""))
        self.__ui.densityEdit.valueChanged.connect(
            lambda: self.__ui.densityEdit.setStyleSheet(""))

        # Connect buttons to events
        self.__ui.addElementButton.clicked.connect(self.__add_element_layout)
        self.__ui.okButton.clicked.connect(self.__add_layer)
        self.__ui.cancelButton.clicked.connect(self.close)

        self.__element_layouts = []
        self.__add_element_layout()

        self.exec_()

    def __add_layer(self):
        """Function for adding a new layer with given settings.
        """
        if self.__check_if_settings_ok():
            self.__accept_settings()

    def __check_if_settings_ok(self):
        """Check that all the settings are okay.

        Return:
             True if the settings are okay and false if some required fields
             are empty.
        """
        failed_style = "background-color: #FFDDDD"
        empty_fields = []
        help_sum = 0

        # Check if 'nameEdit' is empty.
        if not self.__ui.nameEdit.text():
            self.__ui.nameEdit.setStyleSheet(failed_style)
            empty_fields.append("Name")

        # Check if 'scrollArea' is empty (no elements).
        if self.__ui.scrollAreaWidgetContents.layout().isEmpty():
            self.__ui.scrollArea.setStyleSheet(failed_style)
            empty_fields.append("Elements")

        # Check if 'thicknessEdit' is empty.
        if not self.__ui.thicknessEdit.value():
            self.__ui.thicknessEdit.setStyleSheet(failed_style)
            empty_fields.append("Thickness")

        # Check if 'densityEdit' is empty.
        if not self.__ui.densityEdit.text():
            self.__ui.densityEdit.setStyleSheet(failed_style)
            empty_fields.append("Density")

        # Check that the element specific settings are okay.
        one_or_more_empty = False
        for child in self.__ui.scrollAreaWidgetContents.children():
            if type(child) is QtWidgets.QPushButton:
                if child.text() == "Select":
                    child.setStyleSheet(failed_style)
                    one_or_more_empty = True
            if type(child) is QtWidgets.QLineEdit:
                if child.isEnabled():
                    if child.text():
                        help_sum += float(child.text())
                    else:
                        child.setStyleSheet(failed_style)
                        one_or_more_empty = True

        if one_or_more_empty:
            empty_fields.append("Elements")

        # If there are any empty fields, create a message box telling which
        # of the fields are empty.
        if empty_fields:
            self.__missing_information_message(empty_fields)
            return False
        return True  # If everything is ok, return true.

    def __accept_settings(self):
        """Function for accepting the current settings and closing the dialog
        window.
        """
        name = self.__ui.nameEdit.text()
        thickness = self.__ui.thicknessEdit.value()
        density = self.__ui.densityEdit.value()
        elements = []
        children = self.__ui.scrollAreaWidgetContents.children()

        # TODO: Explain the following. Maybe better implementation?
        i = 1
        while i < len(children):
            elem_symbol = children[i].text()
            i += 1
            elem_isotope = int(children[i].currentText().split(" ")[0])
            # TODO: Some elements don't have isotope values. Figure out why.
            i += 1
            elem_amount = children[i].value()
            elements.append(Element(elem_symbol, elem_isotope, elem_amount))
            i += 2

        self.layer = Layer(name, elements, thickness, density)
        self.close()

    def __missing_information_message(self, empty_fields):
        """Show the user a message about missing information.

        Args:
            empty_fields: Input fields that are empty.
        """
        fields = ""
        for field in empty_fields:
            fields += "  • " + field + "\n"
        QtWidgets.QMessageBox.critical(
            self.parent(),
            "Required information missing",
            "The following fields are still empty:\n\n" + fields +
            "\nFill out the required information in order to continue.",
            QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)

    def __add_element_layout(self):
        """Add element widget into view.
        """
        self.__ui.scrollArea.setStyleSheet("")
        self.__element_layouts.append(ElementLayout(
            self.__ui.scrollAreaWidgetContents))


class ElementLayout(QtWidgets.QHBoxLayout):
    """ElementLayout that holds element information input fields."""

    def __init__(self, parent):
        """Initializes the layout.
        Args:
            parent: A QWidget into which the layout is added.
        """
        parent.parentWidget().setStyleSheet("")

        super().__init__()

        self.element_button = QtWidgets.QPushButton("Select")
        self.element_button.setFixedWidth(60)

        self.isotope_combobox = QtWidgets.QComboBox()
        self.isotope_combobox.setFixedWidth(120)
        self.isotope_combobox.setEnabled(False)

        self.amount_spinbox = QtWidgets.QDoubleSpinBox()
        self.amount_spinbox.setMaximum(9999.00)
        self.amount_spinbox.setDecimals(3)
        self.amount_spinbox.setEnabled(False)
        self.amount_spinbox.valueChanged\
            .connect(lambda: self.amount_spinbox.setStyleSheet(""))

        self.delete_button = QtWidgets.QPushButton("")
        self.delete_button.setIcon(QtGui.QIcon("ui_icons/potku/del.png"))
        self.delete_button.setFixedWidth(28)
        self.delete_button.setFixedHeight(28)

        self.element_button.clicked.connect(self.__select_element)
        self.delete_button.clicked.connect(self.__delete_element_layout)

        self.addWidget(self.element_button)
        self.addWidget(self.isotope_combobox)
        self.addWidget(self.amount_spinbox)
        self.addWidget(self.delete_button)
        self.insertStretch(-1, 0)
        parent.layout().addLayout(self)

    def __delete_element_layout(self):
        """Deletes element layout.
        """
        self.element_button.deleteLater()
        self.isotope_combobox.deleteLater()
        self.amount_spinbox.deleteLater()
        self.delete_button.deleteLater()
        self.deleteLater()

    def __select_element(self, button):
        """Opens a dialog to select an element.
        """
        dialog = ElementSelectionDialog()

        if dialog.element:
            self.element_button.setStyleSheet("")
            self.element_button.setText(dialog.element)
            self.__load_isotopes()
            self.isotope_combobox.setEnabled(True)
            self.amount_spinbox.setEnabled(True)

    def __load_isotopes(self):
        """Loads isotopes of the element into the combobox.
        """
        masses.load_isotopes(self.element_button.text(), self.isotope_combobox,
                             None)
