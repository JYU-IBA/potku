# coding=utf-8
"""
Created on 18.4.2018
Updated on 3.5.2018

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
from PyQt5 import uic
from PyQt5 import QtWidgets
from widgets.matplotlib.simulation.composition import FoilCompositionWidget
from modules.foil import CircularFoil
from modules.foil import RectangularFoil


class FoilDialog(QtWidgets.QDialog):
    """ Class for creating a foil widget for detector settings.
    """
    def __init__(self, tmp_foils, tmp_index, icon_manager):
        """ Initializes the Foil Dialog.
        Args:
            tmp_foils: Foil object list.
            tmp_index: Index of the Foil object in tmp_foils.
            icon_manager: Icon manager for TargetCompositionWidget.
        """
        super().__init__()
        self.ui = uic.loadUi(os.path.join("ui_files",
                                          "ui_composition_dialog.ui"), self)
        self.icon_manager = icon_manager
        self.foils = tmp_foils
        self.index = tmp_index
        self.foil = tmp_foils[tmp_index]
        self.foil_type = None
        self.foil_type_changed = False

        # Add foil types to combobox.
        self.ui.typeComboBox.addItem("circular")
        self.ui.typeComboBox.addItem("rectangular")

        self.dimension_edits = []
        self.first_dimension_edit = QtWidgets.QDoubleSpinBox()
        self.first_dimension_edit.setMaximumWidth(70)
        self.second_dimension_edit = None
        self.dimension_label = QtWidgets.QLabel("Diameter (mm):")

        self.dimension_edits.append(self.first_dimension_edit)
        self.ui.dimensionLayout.addWidget(self.dimension_label)
        self.ui.dimensionLayout.addWidget(self.dimension_edits[0])

        self.show_parameters()

        # This widget adds itself into the matplotlib_layout
        self.composition = FoilCompositionWidget(self, self.foil,
                                                 self.icon_manager)

        self.ui.typeComboBox.currentIndexChanged.connect(
            lambda: self._change_dimensions())

        self.ui.cancelButton.clicked.connect(self.close)
        self.ui.okButton.clicked.connect(lambda:
                                         self._save_foil_info_and_close())

        self.exec_()

    def show_parameters(self):
        """Show foil parameters in dialog.
        """
        self.ui.nameEdit.setText(self.foil.name)
        self.ui.transmissionEdit.setValue(self.foil.transmission)

        if type(self.foils[self.index]) is CircularFoil:
            self.foil_type = CircularFoil
            self.ui.typeComboBox.setCurrentIndex(0)
            self.first_dimension_edit.setValue(self.foil.diameter)
        else:
            self.foil_type = RectangularFoil
            self.ui.typeComboBox.setCurrentIndex(1)
            self.dimension_label.setText("Size (mm):")
            self.second_dimension_edit = QtWidgets.QDoubleSpinBox()
            self.dimension_edits.append(self.second_dimension_edit)
            self.ui.dimensionLayout.addWidget(self.dimension_edits[1])
            self.first_dimension_edit.setValue(self.foil.size[0])
            self.second_dimension_edit.setValue(self.foil.size[1])

    def _change_dimensions(self):
        """Change the view to show diameter for circular foil and sizes x and
           y for rectangular foil.
        """
        if self.ui.typeComboBox.currentText() == "circular":
            # Circular foil
            # Remove the second dimension edit that is used by rectangular type.
            self.dimension_edits.pop()
            self.dimension_label.setText("Diameter (mm):")
            self.ui.dimensionLayout.removeWidget(self.second_dimension_edit)
            self.second_dimension_edit.deleteLater()
            self.second_dimension_edit = None
            self.foil_type_changed = True
            if self.foil_type is RectangularFoil:
                self.foil_type_changed = True
            else:
                self.foil_type_changed = False
        else:
            # Rectangular foil
            self.dimension_label.setText("Size (mm):")
            self.second_dimension_edit = QtWidgets.QDoubleSpinBox()
            self.dimension_edits.append(self.second_dimension_edit)
            self.ui.dimensionLayout.addWidget(self.second_dimension_edit)
            if self.foil_type is CircularFoil:
                self.foil_type_changed = True
            else:
                self.foil_type_changed = False

    def _save_foil_info_and_close(self):
        """Saves foil information and closes dialog."""
        if self.foil_type_changed:
            # If foil type has changed, change object.
            if self.foil_type is CircularFoil:
                new_foil = RectangularFoil(self.ui.nameEdit.text(),
                                           layers=self.foil.layers)
                new_foil.size = (self.first_dimension_edit.value(),
                                 self.second_dimension_edit.value())
            else:
                new_foil = CircularFoil(self.ui.nameEdit.text(),
                                        layers=self.foil.layers)
                new_foil.diameter = self.first_dimension_edit.value()
            new_foil.distance = self.foils[self.index].distance
            self.foils[self.index] = new_foil
        else:
            # Save foil information to the old object.
            self.foil.name = self.ui.nameEdit.text()
            self.foil.transmission = self.ui.transmissionEdit.value()
            if self.foil_type is CircularFoil:
                self.foil.diameter = self.first_dimension_edit.value()
            else:
                self.foil.size = (self.first_dimension_edit.value(),
                                  self.second_dimension_edit.value())
        self.close()
