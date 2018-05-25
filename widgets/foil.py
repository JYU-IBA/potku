# coding=utf-8
"""
Created on 18.4.2018
Updated on 18.5.2018
"""
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä " \
             "\n Sinikka Siironen"
__version__ = "2.0"

import os
from PyQt5 import uic, QtWidgets


class FoilWidget(QtWidgets.QWidget):
    """Class for creating a foil widget for detector settings.
    """
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.ui = uic.loadUi(os.path.join("ui_files", "ui_foil_widget.ui"),
                             self)
        self.ui.deleteButton.clicked.connect(lambda: self._delete_foil())
        self.ui.distanceDoubleSpinBox.valueChanged.connect(lambda:
                                              self.__calculate_distance())

    def _delete_foil(self):
        confirm_box = QtWidgets.QMessageBox()
        confirm_box.setIcon(QtWidgets.QMessageBox.Warning)
        yes_button = confirm_box.addButton(QtWidgets.QMessageBox.Yes)
        confirm_box.addButton(QtWidgets.QMessageBox.Cancel)
        confirm_box.setText("Are you sure you want to delete the foil?")
        confirm_box.setWindowTitle("Confirm")

        confirm_box.exec()

        if confirm_box.clickedButton() == yes_button:
            self.parent.delete_foil(self)
            self.parent.calculate_distance()

    def __calculate_distance(self):
        self.parent.calculate_distance()
