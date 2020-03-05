# coding=utf-8
"""
Created on 28.2.2018
Updated on 24.5.2019

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

import copy
import modules.masses as masses
import os
import platform

import dialogs.dialog_functions as df
import widgets.input_validation as iv

from dialogs.element_selection import ElementSelectionDialog

from modules.element import Element
from modules.general_functions import delete_simulation_results
from modules.layer import Layer

from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5 import uic
from PyQt5.QtCore import QLocale


class LayerPropertiesDialog(QtWidgets.QDialog):
    """Dialog for adding a new layer or editing an existing one.
    """

    def __init__(self, tab, layer=None, modify=False, simulation=None,
                 first_layer=False):
        """Inits a layer dialog.

        Args:
            tab: A SimulationTabWidget
            layer: Layer object to be modified. None if creating a new layer.
            modify: If dialog is used to modify a layer.
            simulation: A Simulation object.
            first_layer: Whether the dialog is used to add the first layer.
        """
        super().__init__()
        self.ui = uic.loadUi(os.path.join("ui_files", "ui_layer_dialog.ui"),
                             self)
        self.tab = tab
        self.layer = layer
        self.ok_pressed = False
        self.simulation = simulation

        iv.set_input_field_red(self.ui.nameEdit)
        iv.set_input_field_red(self.ui.thicknessEdit)
        iv.set_input_field_red(self.ui.densityEdit)
        self.fields_are_valid = True
        self.amount_mismatch = False
        self.ui.nameEdit.textChanged.connect(
            lambda: self.check_text(self.ui.nameEdit, self))

        # Connect buttons to events
        self.ui.addElementButton.clicked.connect(self.__add_element_layout)
        self.ui.okButton.clicked.connect(self.__save_layer)
        self.ui.cancelButton.clicked.connect(self.close)

        self.ui.thicknessEdit.valueChanged.connect(
            lambda: self.validate_spinbox(self.ui.thicknessEdit))
        self.ui.densityEdit.valueChanged.connect(lambda:
                                                   self.validate_spinbox(
                                                       self.ui.densityEdit))

        self.__element_layouts = []
        if self.layer:
            self.__show_layer_info()
        else:
            self.__add_element_layout()

        if first_layer:
            self.ui.groupBox_2.hide()

        self.ui.nameEdit.textEdited.connect(lambda: self.__validate())
        self.__close = True

        self.ui.thicknessEdit.setLocale(QLocale.c())
        self.ui.densityEdit.setLocale(QLocale.c())

        if modify:
            self.ui.groupBox_2.hide()

        self.placement_under = True

        if platform.system() == "Darwin":
            self.setMinimumWidth(450)

        if platform.system() == "Linux":
            self.setMinimumWidth(470)

        self.exec_()

    def __save_layer(self):
        """Function for adding a new layer with given settings.
        """
        self.__check_if_settings_ok()
        self.__accept_settings()
        if self.__close:
            self.close()

    def __show_layer_info(self):
        """
        Show information of the current layer.
        """
        self.ui.nameEdit.setText(self.layer.name)
        self.ui.thicknessEdit.setValue(self.layer.thickness)
        self.ui.densityEdit.setValue(self.layer.density)

        for elem in self.layer.elements:
            self.__add_element_layout(elem)

    def __check_if_settings_ok(self):
        """Check that all the settings are okay.

        Return:
             True if the settings are okay and false if some required fields
             are empty.
        """
        help_sum = 0
        spinboxes = []

        # Check if 'scrollArea' is empty (no elements).
        if self.ui.scrollAreaWidgetContents.layout().isEmpty():
            iv.set_input_field_red(self.ui.scrollArea)
            self.fields_are_valid = False

        # Check if 'thicknessEdit' is empty.
        if not self.ui.thicknessEdit.value():
            iv.set_input_field_red(self.ui.thicknessEdit)
            self.fields_are_valid = False

        # Check if 'densityEdit' is empty.
        if not self.ui.densityEdit.value():
            iv.set_input_field_red(self.ui.densityEdit)
            self.fields_are_valid = False

        # Check that the element specific settings are okay.
        for child in self.ui.scrollAreaWidgetContents.children():
            if type(child) is QtWidgets.QPushButton:
                if child.text() == "Select":
                    iv.set_input_field_red(child)
                    self.fields_are_valid = False
            if type(child) is QtWidgets.QDoubleSpinBox:
                if child.isEnabled():
                    if child.value():
                        help_sum += child.value()
                        spinboxes.append(child)
                    else:
                        iv.set_input_field_red(child)
                        self.fields_are_valid = False

        if help_sum != 1.0 and help_sum != 100.0:
            for sb in spinboxes:
                iv.set_input_field_red(sb)
            self.fields_are_valid = False
            self.amount_mismatch = True
        else:
            for sb in spinboxes:
                iv.set_input_field_white(sb)
            self.amount_mismatch = False

    @staticmethod
    def check_text(input_field, dialog):
        """Checks if there is text in given input field.

        Args:
            input_field: Input field the contents of which are checked.
            dialog: Layer dialog.
        """
        dialog.fields_are_valid = iv.check_text(input_field)

    def validate_spinbox(self, spinbox):
        """
        Check if given spinbox has a proper value.

        Args:
            spinbox: Spinbox to check.
        """
        if spinbox.value() == 0.0:
            self.fields_are_valid = False
            iv.set_input_field_red(spinbox)
        else:
            self.fields_are_valid = True
            iv.set_input_field_white(spinbox)

    def values_changed(self):
        """
        Check if layer's values have been changed.

        Return:
            True or False.
        """
        if self.layer.name != self.ui.nameEdit.text():
            return True
        if self.layer.thickness != self.ui.thicknessEdit.value():
            return True
        if self.layer.density != self.ui.densityEdit.value():
            return True
        if self.elements_changed():
            return True
        return False

    def elements_changed(self):
        """
        Check if elements have been changed in the layer.
        """
        new_elements = []
        self.find_elements(new_elements)
        if len(self.layer.elements) != len(new_elements):
            return True
        for i in range(len(self.layer.elements)):
            elem1 = self.layer.elements[i]
            elem2 = new_elements[i]
            if elem1 != elem2:
                return True
        return False

    def find_elements(self, lst):
        """
        Find all the layer's element from the dialog.

        Args:
            lst: List to append the elements to.
        """
        children = self.ui.scrollAreaWidgetContents.children()

        # TODO: Explain the following. Maybe better implementation?
        # TODO this could be a bit shaky. Got an AttributeError once
        #      as isotope was being read from a PushButton instead of
        #      a combobox
        i = 1
        while i < len(children):
            # Get symbol from PushButton
            elem_symbol = children[i].text()
            i += 1
            try:
                # Get isotope from Combobox
                # The value is a string representation of a floating point
                # number so we need to convert it to float before converting
                # to int.
                elem_isotope = int(float(
                    children[i].currentText().split(" ")[0]))
            except ValueError as e:
                elem_isotope = None
            i += 1
            # Get amount from DoubleSpinBox
            elem_amount = children[i].value()
            lst.append(Element(elem_symbol, elem_isotope, elem_amount))
            i += 3

    def __accept_settings(self):
        """Function for accepting the current settings and closing the dialog
        window.
        """
        if not self.fields_are_valid:
            if self.amount_mismatch:
                hint = "(Hint: element amounts need to sum up to either 1 or " \
                       "100.)"
            else:
                hint = ""
            QtWidgets.QMessageBox.critical(self, "Warning",
                                           "Some of the parameter values have"
                                           " not been set.\n\n" +
                                           "Please input values in fields "
                                           "indicated in red.\n" + hint,
                                           QtWidgets.QMessageBox.Ok,
                                           QtWidgets.QMessageBox.Ok)
            self.__close = False
            self.fields_are_valid = True
            return

        if self.layer and not self.values_changed():
            self.__close = True
            self.fields_are_valid = True
            self.ok_pressed = False  # No update needed
            return

        if self.simulation is not None:
            if not df.delete_element_simulations(self, self.tab,
                                                 self.simulation,
                                                 msg_str="target"):
                self.__close = False
                return

        name = self.ui.nameEdit.text()
        thickness = self.ui.thicknessEdit.value()
        density = self.ui.densityEdit.value()
        elements = []
        self.find_elements(elements)

        if self.layer:
            self.layer.name = name
            self.layer.elements = elements
            self.layer.thickness = thickness
            self.layer.density = density
        else:
            self.layer = Layer(name, elements, thickness, density)
        if self.ui.comboBox.currentText().startswith("Under"):
            self.placement_under = True
        else:
            self.placement_under = False
        self.ok_pressed = True
        self.__close = True

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

    def __add_element_layout(self, element=None):
        """Add element widget into view.
        """
        self.ui.scrollArea.setStyleSheet("")
        self.__element_layouts.append(ElementLayout(
            self.ui.scrollAreaWidgetContents, element, self))

    def __validate(self):
        """
        Validate the layer name.
        """
        text = self.ui.nameEdit.text()
        regex = "^[A-Za-z0-9-ÖöÄäÅå]*"
        valid_text = iv.validate_text_input(text, regex)

        self.ui.nameEdit.setText(valid_text)


class ElementLayout(QtWidgets.QVBoxLayout):
    """ElementLayout that holds element information input fields."""

    def __init__(self, parent, element, dialog):
        """Initializes the layout.
        Args:
            parent: A QWidget into which the layout is added.
            element: Element object whose info is shown. None adding a
            default layout.
            dialog: LayerPropertiesDialog.
        """
        parent.parentWidget().setStyleSheet("")

        super().__init__()

        if not element:
            btn_txt = "Select"
            enabled = False
        else:
            btn_txt = element.symbol
            enabled = True
        self.element_button = QtWidgets.QPushButton(btn_txt)
        self.element_button.setFixedWidth(60)

        self.dialog = dialog

        self.isotope_combobox = QtWidgets.QComboBox()
        self.isotope_combobox.setFixedWidth(120)
        self.isotope_combobox.setEnabled(enabled)

        if platform.system() == "Darwin" or platform.system() == "Linux":
            self.isotope_combobox.setFixedWidth(150)

        self.amount_spinbox = QtWidgets.QDoubleSpinBox()
        self.amount_spinbox.setMaximum(9999.00)
        self.amount_spinbox.setDecimals(3)
        self.amount_spinbox.setEnabled(enabled)
        self.amount_spinbox.valueChanged\
            .connect(lambda: dialog.validate_spinbox(self.amount_spinbox))
        self.amount_spinbox.setLocale(QLocale.c())

        if enabled:
            self.__load_isotopes(element.isotope)
            self.amount_spinbox.setValue(element.amount)

        self.delete_button = QtWidgets.QPushButton("")
        self.delete_button.setIcon(QtGui.QIcon("ui_icons/potku/del.png"))
        self.delete_button.setFixedWidth(28)
        self.delete_button.setFixedHeight(28)

        self.element_button.clicked.connect(self.__select_element)
        self.delete_button.clicked.connect(self.__delete_element_layout)

        self.isotope_info_label = QtWidgets.QLabel()

        self.horizontal_layout = QtWidgets.QHBoxLayout()
        self.horizontal_layout.addWidget(self.element_button)
        self.horizontal_layout.addWidget(self.isotope_combobox)
        self.horizontal_layout.addWidget(self.amount_spinbox)
        self.horizontal_layout.addWidget(self.delete_button)

        self.addLayout(self.horizontal_layout)
        self.addWidget(self.isotope_info_label)
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

    def __select_element(self):
        """Opens a dialog to select an element.
        """
        dialog = ElementSelectionDialog()

        if dialog.element:
            self.element_button.setStyleSheet("")
            self.element_button.setText(dialog.element)
            self.__load_isotopes()
            self.isotope_combobox.setEnabled(True)
            self.amount_spinbox.setEnabled(True)
            if not self.amount_spinbox.value():
                iv.set_input_field_red(self.amount_spinbox)

            # Check if no isotopes
            if self.isotope_combobox.currentText().startswith("0.0"):
                iv.set_input_field_red(self.isotope_combobox)
                self.dialog.fields_are_valid = False
                self.isotope_info_label.setText(
                    "If you wish to use this element, please modify masses.dat "
                    "file\nand change the natural abundance to 100 % on your\n"
                    "preferred isotope and restart the application.")
            else:
                self.dialog.check_text(self.dialog.ui.nameEdit, self.dialog)
                self.isotope_combobox.setStyleSheet(
                    "background-color: %s" % "None")
                self.isotope_info_label.setText("")

    def __load_isotopes(self, current_isotope=None):
        """Loads isotopes of the element into the combobox.
        """
        masses.load_isotopes(self.element_button.text(), self.isotope_combobox,
                             current_isotope)
        standard_isotope = masses.get_standard_isotope(
            self.element_button.text())
        self.isotope_combobox.insertItem(0,
                                         "{0} (st. mass)".format(
                                             round(standard_isotope, 3)))
        self.isotope_combobox.setCurrentIndex(0)
