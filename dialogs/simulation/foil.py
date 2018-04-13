# coding=utf-8
"""
Created on 13.4.2018
"""
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"
__version__ = "2.0"

import os
from PyQt5 import uic
from PyQt5 import QtWidgets
from widgets.matplotlib.simulation.target_composition import TargetCompositionWidget


class FoilDialog(QtWidgets.QDialog):
    """ Class for creating a foil widget for detector settings.
    """
    def __init__(self, icon_manager):
        super().__init__()
        self.ui = uic.loadUi(os.path.join("ui_files", "ui_composition_dialog.ui"), self)
        self.icon_manager = icon_manager
        # This widget adds itself into the matplotlib_layout
        self.composition = TargetCompositionWidget(self, self.icon_manager)

        self.ui.typeComboBox.addItem("circular")  # This is put as the current text
        self.ui.typeComboBox.addItem("rectangular")

        self.dimension_label = QtWidgets.QLabel("Diameter:")
        self.dimension_edits = []
        self.first_dimension_edit = QtWidgets.QLineEdit()
        self.second_dimension_edit = None
        self.dimension_edits.append(self.first_dimension_edit)
        self.ui.dimensionLayout.addWidget(self.dimension_label)
        self.ui.dimensionLayout.addWidget(self.dimension_edits[0])

        self.ui.typeComboBox.currentIndexChanged.connect(lambda: self._change_dimensions())

        self.ui.cancelButton.clicked.connect(self.close)

        self.exec_()

    def _change_dimensions(self):
        if self.ui.typeComboBox.currentText() == "circular":
            self.dimension_label.setText("Diameter:")
            self.dimension_edits.pop()  # removes the second dimension edit that is only needed by rectangular type
            self.ui.dimensionLayout.removeWidget(self.second_dimension_edit)
            self.second_dimension_edit.deleteLater()
            self.second_dimension_edit = None
        else:
            self.dimension_label.setText("Size:")
            self.second_dimension_edit = QtWidgets.QLineEdit()
            self.dimension_edits.append(self.second_dimension_edit)
            self.ui.dimensionLayout.addWidget(self.second_dimension_edit)
