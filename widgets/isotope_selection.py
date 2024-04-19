# coding=utf-8
"""
Created on 13.04.2020

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2020 Juhani Sundell

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
__author__ = "Juhani Sundell"
__version__ = "2.0"


import widgets.gui_utils as gutils
import widgets.input_validation as iv

from modules.element import Element

from dialogs.element_selection import ElementSelectionDialog

from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QDoubleSpinBox
from PyQt5.QtCore import QObject
from PyQt5.QtCore import pyqtSignal


class IsotopeSelectionWidget(QObject):
    """IsotopeSelectionWidget is a helper class for selecting isotopes in
    GUI.

    Currently it has no corresponding 'ui' file nor does it dynamically add
    any GUI elements to the screen. Instead, GUI elements are provided as
    parameters when the IsotopeSelectionWidget is initialized.
    """
    DEFAULT_BTN_TXT = "Select"
    MISSING_ISOTOPE_TXT = "If you wish to use this element, please modify " \
                          "abundances.dat file\nand change the natural abundance " \
                          "of your\npreferred isotope to 1.0 and restart " \
                          "the application."

    # Signal that is emitted when isotope selection has changed
    selection_changed = pyqtSignal()

    def __init__(self, symbol_input: QPushButton,
                 isotope_input: QComboBox, amount_input: QDoubleSpinBox = None,
                 st_mass_input: QWidget = None, info_label: QLabel = None,
                 parent: QWidget = None):
        """Initializes a new IsotopeSelectionWidget.
        """
        super().__init__()
        self._symbol_input = symbol_input
        self._isotope_input = isotope_input
        self._amount_input = amount_input
        self._st_mass_input = st_mass_input
        self._info_label = info_label
        self._parent = parent

        self._symbol_input.setText(IsotopeSelectionWidget.DEFAULT_BTN_TXT)
        self._symbol_input.setStyleSheet("")
        self._symbol_input.setEnabled(True)
        self._symbol_input.clicked.connect(self.show_element_dialog)

        self._isotope_input.setEnabled(False)

    def show_element_dialog(self):
        """Opens up the ElementSelectionDialog that allows user
        to choose the element.
        """
        dialog = ElementSelectionDialog()

        if dialog.element:
            self.set_element(dialog.element)

    def set_element(self, element: Element):
        """Sets currently selected element.
        """
        if not isinstance(element, Element):
            try:
                element = Element.from_string(element)
            except (ValueError, AttributeError):
                self._isotope_input.clear()
                self.validate()
                self.selection_changed.emit()
                return

        show_st_mass_in_combobox = self._st_mass_input is None

        self._symbol_input.setText(element.symbol)
        gutils.load_isotopes(element.symbol, self._isotope_input,
                             show_std_mass=show_st_mass_in_combobox,
                             current_isotope=element.isotope)

        if self._amount_input is not None and element.amount:
            self._amount_input.setValue(element.amount)

        self.validate()
        self.selection_changed.emit()

    def validate(self):
        """Validates the contents of the Widget, setting background colors
        and error messages if necessary.
        """
        valid_selection = bool(self.get_element())
        self._isotope_input.setEnabled(valid_selection)

        if valid_selection:
            self._isotope_input.setStyleSheet(
                "background-color: %s" % "None")
            if self._info_label is not None:
                self._info_label.setText("")
        else:
            iv.set_input_field_red(self._isotope_input)
            self._symbol_input.setText("Select")
            if self._info_label is not None:
                self._info_label.setText(
                    IsotopeSelectionWidget.MISSING_ISOTOPE_TXT)
            if self._parent is not None:
                self._parent.fields_are_valid = False

    def get_element(self) -> Element:
        """Returns the selected element.
        """
        element: Element = None
        data = self._isotope_input.currentData()
        if data is not None:
            element = data["element"]

        if element is not None and self._amount_input is not None:
            element.amount = self._amount_input.value()

        return element

