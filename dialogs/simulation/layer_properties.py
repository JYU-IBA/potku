# coding=utf-8
"""
Created on 28.2.2018
Updated on 17.7.2018

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
import os
import modules.masses as masses

from dialogs.element_selection import ElementSelectionDialog

from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5 import uic
from PyQt5.QtCore import QLocale

from modules.element import Element
from modules.general_functions import check_text
from modules.general_functions import set_input_field_red
from modules.general_functions import validate_text_input
from modules.layer import Layer


class LayerPropertiesDialog(QtWidgets.QDialog):
    """Dialog for adding a new layer or editing an existing one.
    """

    def __init__(self, layer=None, modify=False, simulation=None):
        """Inits a layer dialog.

        Args:
            layer: Layer object to be modified. None if creating a new layer.
            modify: If dialog is used to modify a layer.
            simulation: A Simulation object.
        """
        super().__init__()
        self.__ui = uic.loadUi(os.path.join("ui_files", "ui_layer_dialog.ui"),
                               self)
        self.layer = layer
        self.ok_pressed = False
        self.simulation = simulation

        set_input_field_red(self.__ui.nameEdit)
        self.fields_are_valid = False
        self.__ui.nameEdit.textChanged.connect(
            lambda: self.__check_text(self.__ui.nameEdit, self))

        # Connect buttons to events
        self.__ui.addElementButton.clicked.connect(self.__add_element_layout)
        self.__ui.okButton.clicked.connect(self.__save_layer)
        self.__ui.cancelButton.clicked.connect(self.close)

        self.__element_layouts = []
        if self.layer:
            self.__show_layer_info()
        else:
            self.__add_element_layout()

        self.__ui.nameEdit.textEdited.connect(lambda: self.__validate())
        self.__close = True

        self.__ui.thicknessEdit.setLocale(QLocale.c())
        self.__ui.densityEdit.setLocale(QLocale.c())

        if modify:
            self.__ui.groupBox_2.hide()

        self.placement_under = True

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
        self.__ui.nameEdit.setText(self.layer.name)
        self.__ui.thicknessEdit.setValue(self.layer.thickness)
        self.__ui.densityEdit.setValue(self.layer.density)

        for elem in self.layer.elements:
            self.__add_element_layout(elem)

    def __check_if_settings_ok(self):
        """Check that all the settings are okay.

        Return:
             True if the settings are okay and false if some required fields
             are empty.
        """
        help_sum = 0

        # Check if 'scrollArea' is empty (no elements).
        if self.__ui.scrollAreaWidgetContents.layout().isEmpty():
            set_input_field_red(self.__ui.scrollArea)
            self.fields_are_valid = False

        # Check if 'thicknessEdit' is empty.
        if not self.__ui.thicknessEdit.value():
            set_input_field_red(self.__ui.thicknessEdit)
            self.fields_are_valid = False

        # Check if 'densityEdit' is empty.
        if not self.__ui.densityEdit.text():
            set_input_field_red(self.__ui.densityEdit)
            self.fields_are_valid = False

        # Check that the element specific settings are okay.
        for child in self.__ui.scrollAreaWidgetContents.children():
            if type(child) is QtWidgets.QPushButton:
                if child.text() == "Select":
                    set_input_field_red(child)
                    self.fields_are_valid = False
            if type(child) is QtWidgets.QLineEdit:
                if child.isEnabled():
                    if child.text():
                        help_sum += float(child.text())
                    else:
                        set_input_field_red(child)
                        self.fields_are_valid = False

    @staticmethod
    def __check_text(input_field, dialog):
        """Checks if there is text in given input field.

        Args:
            input_field: Input field the contents of which are checked.
            dialog: Layer dialog.
        """
        dialog.fields_are_valid = check_text(input_field)

    def __accept_settings(self):
        """Function for accepting the current settings and closing the dialog
        window.
        """
        if not self.fields_are_valid:
            QtWidgets.QMessageBox.critical(self, "Warning",
                                           "Some of the parameter values have"
                                           " not been set.\n" +
                                           "Please input values in fields "
                                           "indicated in red.",
                                           QtWidgets.QMessageBox.Ok,
                                           QtWidgets.QMessageBox.Ok)
            self.__close = False
            self.fields_are_valid = True
            return

        simulations_run = self.check_if_simulations_run()
        simulations_running = self.simulations_running()

        if simulations_run and simulations_running:
            reply = QtWidgets.QMessageBox.question(
                self, "Simulated and running simulations",
                "There are simulations that use the current target, "
                "and either have been simulated or are currently running."
                "\nIf you save changes, the running simulations "
                "will be stopped, and the result files of the simulated "
                "and stopped simulations are deleted.\n\nDo you want to "
                "save changes anyway?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No |
                QtWidgets.QMessageBox.Cancel, QtWidgets.QMessageBox.Cancel)
            if reply == QtWidgets.QMessageBox.No or reply == \
                    QtWidgets.QMessageBox.Cancel:
                self.__close = False
                return
            else:
                # Stop simulations
                tmp_sims = copy.copy(self.simulation.running_simulations)
                for elem_sim in tmp_sims:
                    elem_sim.stop()
                    elem_sim.controls.state_label.setText("Stopped")
                    elem_sim.controls.run_button.setEnabled(True)
                    elem_sim.controls.stop_button.setEnabled(False)
                # TODO: Delete files
        elif simulations_running:
            reply = QtWidgets.QMessageBox.question(
                self, "Simulations running",
                "There are simulations running that use the current "
                "target.\nIf you save changes, the running "
                "simulations will be stopped, and their result files "
                "deleted.\n\nDo you want to save changes anyway?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No |
                QtWidgets.QMessageBox.Cancel, QtWidgets.QMessageBox.Cancel)
            if reply == QtWidgets.QMessageBox.No or reply == \
                    QtWidgets.QMessageBox.Cancel:
                self.__close = False
                return
            else:
                # Stop simulations
                tmp_sims = copy.copy(self.simulation.running_simulations)
                for elem_sim in tmp_sims:
                    elem_sim.stop()
                    elem_sim.controls.state_label.setText("Stopped")
                    elem_sim.controls.run_button.setEnabled(True)
                    elem_sim.controls.stop_button.setEnabled(False)
                # TODO: Delete files
        elif simulations_run:
            reply = QtWidgets.QMessageBox.question(
                self, "Simulated simulations",
                "There are simulations that use the current target, "
                "and have been simulated.\nIf you save changes,"
                " the result files of the simulated simulations are "
                "deleted.\n\nDo you want to save changes anyway?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No |
                QtWidgets.QMessageBox.Cancel, QtWidgets.QMessageBox.Cancel)
            if reply == QtWidgets.QMessageBox.No or reply == \
                    QtWidgets.QMessageBox.Cancel:
                self.__close = False
                return
            else:
                pass
                # TODO: Delete files

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
            try:
                elem_isotope = int(children[i].currentText().split(" ")[0])
            except ValueError:
                elem_isotope = masses.get_standard_isotope(elem_symbol)
            i += 1
            elem_amount = children[i].value()
            elements.append(Element(elem_symbol, elem_isotope, elem_amount))
            i += 2

        if self.layer:
            self.layer.name = name
            self.layer.elements = elements
            self.layer.thickness = thickness
            self.layer.density = density
        else:
            self.layer = Layer(name, elements, thickness, density)
        if self.__ui.comboBox.currentText().startswith("Under"):
            self.placement_under = True
        else:
            self.placement_under = False
        self.ok_pressed = True
        self.__close = True

    def check_if_simulations_run(self):
        """
        Check if simulation have been run.

        Return:
             True or False.
        """
        if not self.simulation:
            return False
        for elem_sim in self.simulation.element_simulations:
            if elem_sim.simulations_done and \
               elem_sim.use_default_settings:
                return True
        return False

    def simulations_running(self):
        """
        Check if there are any simulations running.

        Return:
            True or False.
        """
        if not self.simulation:
            return False
        for elem_sim in self.simulation.element_simulations:
            if elem_sim in self.simulation.request.running_simulations:
                return True
            elif elem_sim in self.simulation.running_simulations:
                return True
        return False

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
        self.__ui.scrollArea.setStyleSheet("")
        self.__element_layouts.append(ElementLayout(
            self.__ui.scrollAreaWidgetContents, element))

    def __validate(self):
        """
        Validate the layer name.
        """
        text = self.__ui.nameEdit.text()
        regex = "^[A-Za-z0-9-ÖöÄäÅå]*"
        valid_text = validate_text_input(text, regex)

        self.__ui.nameEdit.setText(valid_text)


class ElementLayout(QtWidgets.QHBoxLayout):
    """ElementLayout that holds element information input fields."""

    def __init__(self, parent, element):
        """Initializes the layout.
        Args:
            parent: A QWidget into which the layout is added.
            element: Element object whose info is shown. None adding a
            default layout.
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

        self.isotope_combobox = QtWidgets.QComboBox()
        self.isotope_combobox.setFixedWidth(120)
        self.isotope_combobox.setEnabled(enabled)

        self.amount_spinbox = QtWidgets.QDoubleSpinBox()
        self.amount_spinbox.setMaximum(9999.00)
        self.amount_spinbox.setDecimals(3)
        self.amount_spinbox.setEnabled(enabled)
        self.amount_spinbox.valueChanged\
            .connect(lambda: self.amount_spinbox.setStyleSheet(""))
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

    def __load_isotopes(self, current_isotope=None):
        """Loads isotopes of the element into the combobox.
        """
        masses.load_isotopes(self.element_button.text(), self.isotope_combobox,
                             current_isotope)
