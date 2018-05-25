# coding=utf-8
"""
Created on 28.2.2018
Updated on 30.4.2018

#TODO Licence and copyright

"""
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n " \
             "Sinikka Siironen"
__version__ = "2.0"

import os
from PyQt5 import uic, QtGui, QtWidgets
from dialogs.element_selection import ElementSelectionDialog
from modules.element import Element
from modules.layer import Layer
import modules.masses as masses
import enum
import random


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

        # TODO: Check if negative or zero values are given.

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
            elem_amount = float(children[i].text())
            elements.append(Element(elem_symbol, elem_isotope, elem_amount))
            i += 2

        self.layer = Layer(name, elements, thickness, density)
        self.close()

    def __missing_information_message(self, empty_fields):
        # TODO: Add docstring.
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
        # TODO: Add docstring.
        self.__ui.scrollArea.setStyleSheet("")
        self.__element_layouts.append(ElementLayout(
            self.__ui.scrollAreaWidgetContents))


class ElementLayout(QtWidgets.QHBoxLayout):
    # TODO: Add docstring and more comments.

    def __init__(self, parent):
        parent.parentWidget().setStyleSheet("")

        super().__init__()

        self.element = QtWidgets.QPushButton("Select")
        self.element.setFixedWidth(60)

        self.isotope = QtWidgets.QComboBox()
        self.isotope.setFixedWidth(120)
        self.isotope.setEnabled(False)

        self.amount_spinbox = QtWidgets.QDoubleSpinBox()
        self.amount_spinbox.setEnabled(False)
        self.amount_spinbox.valueChanged\
            .connect(lambda: self.amount_spinbox.setStyleSheet(""))

        self.delete_button = QtWidgets.QPushButton("")
        self.delete_button.setIcon(QtGui.QIcon("ui_icons/potku/del.png"))
        self.delete_button.setFixedWidth(28)
        self.delete_button.setFixedHeight(28)

        self.element.clicked.connect(self.__select_element)
        self.delete_button.clicked.connect(self.__delete_element_layout)

        self.addWidget(self.element)
        self.addWidget(self.isotope)
        self.addWidget(self.amount_spinbox)
        self.addWidget(self.delete_button)
        self.insertStretch(-1, 0)
        parent.layout().addLayout(self)

    def __delete_element_layout(self):
        # TODO: Add docstring.
        self.element.deleteLater()
        self.isotope.deleteLater()
        self.amount_spinbox.deleteLater()
        self.delete_button.deleteLater()
        self.deleteLater()

    def __select_element(self, button):
        # TODO: Add docstring.
        dialog = ElementSelectionDialog()

        if dialog.element:
            self.element.setStyleSheet("")
            self.element.setText(dialog.element)
            self.__load_isotopes()
            self.isotope.setEnabled(True)
            self.amount_spinbox.setEnabled(True)

    def __load_isotopes(self):
        # TODO: Change the path.
        masses.load_isotopes(self.element.text(), self.isotope, None)
