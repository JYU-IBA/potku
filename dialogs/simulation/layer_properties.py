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

import platform
import itertools

import dialogs.dialog_functions as df
import widgets.input_validation as iv
import widgets.gui_utils as gutils
import widgets.binding as bnd

from pathlib import Path

from widgets.isotope_selection import IsotopeSelectionWidget

from modules.element import Element
from modules.layer import Layer

from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5 import uic
from PyQt5.QtCore import QLocale


class LayerPropertiesDialog(QtWidgets.QDialog, bnd.PropertyTrackingWidget,
                            metaclass=gutils.QtABCMeta):
    """Dialog for adding a new layer or editing an existing one.
    """
    name = bnd.bind("nameEdit", track_change=True)
    thickness = bnd.bind("thicknessEdit", track_change=True)
    density = bnd.bind("densityEdit", track_change=True)

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
        uic.loadUi(Path("ui_files", "ui_layer_dialog.ui"), self)

        self.tab = tab
        self.layer = layer
        self.ok_pressed = False
        self.simulation = simulation
        self.amount_mismatch = True

        self.fields_are_valid = True
        iv.set_input_field_red(self.nameEdit)
        self.nameEdit.textChanged.connect(
            lambda: iv.check_text(self.nameEdit, self))
        self.nameEdit.textEdited.connect(
            lambda: iv.sanitize_file_name(self.nameEdit))

        # Connect buttons to events
        self.addElementButton.clicked.connect(self.__add_element_layout)
        self.okButton.clicked.connect(self.__save_layer)
        self.cancelButton.clicked.connect(self.close)

        self.thicknessEdit.setMinimum(0.01)
        self.densityEdit.setMinimum(0.01)

        self.__original_properties = {}

        if self.layer:
            self.__show_layer_info()
        else:
            self.__add_element_layout()

        if first_layer:
            self.groupBox_2.hide()

        self.__close = True

        self.thicknessEdit.setLocale(QLocale.c())
        self.densityEdit.setLocale(QLocale.c())

        if modify:
            self.groupBox_2.hide()

        self.placement_under = True

        if platform.system() == "Darwin":
            self.setMinimumWidth(450)

        if platform.system() == "Linux":
            self.setMinimumWidth(470)

        self.exec_()

    def get_original_property_values(self):
        """Returns the original values of the properties.
        """
        return self.__original_properties

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
        self.set_properties(name=self.layer.name, thickness=self.layer.thickness,
                            density=self.layer.density)

        for elem in self.layer.elements:
            self.__add_element_layout(elem)

    def get_element_widgets(self):
        """Returns all ElementLayout child objects that the widget has."""
        return [
            child
            for child in self.scrollAreaWidgetContents.layout().children()
            if isinstance(child, ElementLayout)
        ]

    def __check_if_settings_ok(self):
        """Check that all the settings are okay.

        Return:
             True if the settings are okay and false if some required fields
             are empty.
        """
        settings_ok = True
        help_sum = 0
        elem_widgets = self.get_element_widgets()

        # Check if 'scrollArea' is empty (no elements).
        if not elem_widgets:
            iv.set_input_field_red(self.scrollArea)
            settings_ok = False

        # Check that the element specific settings are okay.
        for widget in elem_widgets:
            elem = widget.get_selected_element()
            if elem is None:
                settings_ok = False
            else:
                help_sum += elem.amount

        if help_sum != 1.0 and help_sum != 100.0:
            for widget in elem_widgets:
                iv.set_input_field_red(widget.amount_spinbox)
            settings_ok = False
            self.amount_mismatch = True
        else:
            for widget in elem_widgets:
                iv.set_input_field_white(widget.amount_spinbox)
            self.amount_mismatch = False
        self.fields_are_valid = settings_ok

    def elements_changed(self):
        """
        Check if elements have been changed in the layer.
        """
        return not all(e1 == e2 for e1, e2 in itertools.zip_longest(
            self.find_elements(), self.layer.elements
        ))

    def find_elements(self):
        """
        Find all the layer's element from the dialog.
        """
        return [
            child.get_selected_element()
            for child in self.get_element_widgets()
        ]

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
            return

        if self.layer and not (self.are_values_changed() or
                               self.elements_changed()):
            self.__close = True
            self.fields_are_valid = True
            self.ok_pressed = False  # No update needed
            return

        if self.simulation is not None:
            if not df.delete_element_simulations(self,
                                                 self.simulation,
                                                 tab=self.tab,
                                                 msg="target"):
                self.__close = False
                return

        elements = self.find_elements()

        if self.layer:
            self.layer.name = self.name
            self.layer.elements = elements
            self.layer.thickness = self.thickness
            self.layer.density = self.density
        else:
            self.layer = Layer(self.name, elements, self.thickness,
                               self.density)
        if self.comboBox.currentText().startswith("Under"):
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
        el = ElementLayout(self.scrollAreaWidgetContents, element, self)
        el.selection_changed.connect(self.__check_if_settings_ok)
        self.scrollArea.setStyleSheet("")
        self.scrollAreaWidgetContents.layout().addLayout(el)


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
        self.dialog = dialog

        self.element_button = QtWidgets.QPushButton("")
        self.element_button.setFixedWidth(60)

        self.isotope_combobox = QtWidgets.QComboBox()
        self.isotope_combobox.setFixedWidth(130)

        if platform.system() == "Darwin" or platform.system() == "Linux":
            self.isotope_combobox.setFixedWidth(150)

        self.amount_spinbox = QtWidgets.QDoubleSpinBox()
        self.amount_spinbox.setMinimum(0.001)
        self.amount_spinbox.setMaximum(9999.00)
        self.amount_spinbox.setDecimals(3)
        self.amount_spinbox.setLocale(QLocale.c())

        self.delete_button = QtWidgets.QPushButton("")
        self.delete_button.setIcon(QtGui.QIcon("ui_icons/potku/del.png"))
        self.delete_button.setFixedWidth(28)
        self.delete_button.setFixedHeight(28)

        self.delete_button.clicked.connect(self.__delete_element_layout)

        self.isotope_info_label = QtWidgets.QLabel()

        self.horizontal_layout = QtWidgets.QHBoxLayout()
        self.horizontal_layout.addWidget(self.element_button)
        self.horizontal_layout.addWidget(self.isotope_combobox)
        self.horizontal_layout.addWidget(self.amount_spinbox)
        self.horizontal_layout.addWidget(self.delete_button)

        self.isotope_selection_widget = IsotopeSelectionWidget(
            self.element_button, self.isotope_combobox,
            info_label=self.isotope_info_label,
            amount_input=self.amount_spinbox,
            parent=self.dialog
        )
        self.isotope_selection_widget.set_element(element)
        self.selection_changed = self.isotope_selection_widget.selection_changed

        self.addLayout(self.horizontal_layout)
        self.addWidget(self.isotope_info_label)
        self.insertStretch(-1, 0)

    def __delete_element_layout(self):
        """Deletes element layout.
        """
        self.element_button.deleteLater()
        self.isotope_combobox.deleteLater()
        self.amount_spinbox.deleteLater()
        self.delete_button.deleteLater()
        self.deleteLater()

    def get_selected_element(self) -> Element:
        """Returns the selected element object.
        """
        return self.isotope_selection_widget.get_element()
