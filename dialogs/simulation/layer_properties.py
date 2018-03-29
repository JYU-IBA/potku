# coding=utf-8
"""
Created on 28.2.2018
Updated on ...

#TODO Licence and copyright

"""
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä " \
             "\n Sinikka Siironen"
__versio__ = "2.0"

import logging
import os
from PyQt5 import uic, QtWidgets
from modules.layer import Layer


class LayerPropertiesDialog(QtWidgets.QDialog):
    """Dialog creating a new simulation.
    """

    # def __init__(self, parent):
    def __init__(self):
        """Inits a new simulation dialog.
        TODO: Right now only the Cancel button works.
        Args:
            parent: Ibasoft class object.
        """
        super().__init__()
        # self.parent = parent

        self.ui = uic.loadUi(os.path.join("ui_files", "ui_layer_dialog.ui"),
                             self)

        self.ui.addElementButton.clicked.connect(self.__add_element)
        self.ui.okButton.clicked.connect(self.__add_layer)
        self.ui.cancelButton.clicked.connect(self.close)

        self.exec_()

    def __add_layer(self):
        name = self.ui.nameEdit.text()
        # elements =
        thickness = self.ui.thicknessEdit.text()
        density = self.ui.densityEdit.text()
        ion_stopping = self.ui.ionStoppingComboBox.currentText()
        recoil_stopping = self.ui.recoilStoppingComboBox.currentText()
        print(name)
        print(thickness)
        print(density)
        print(ion_stopping)
        print(recoil_stopping)
        self.close()
        # Layer(name, elements, )

    def __add_element(self):
        layout = QtWidgets.QHBoxLayout()
        element = QtWidgets.QPushButton("Si")
        isotope = QtWidgets.QComboBox()
        amount = QtWidgets.QLineEdit("50")
        layout.addWidget(element)
        layout.addWidget(isotope)
        layout.addWidget(amount)
        # widget.addWidget(nappi)
        self.ui.scrollAreaWidgetContents.layout().addLayout(layout)
        print("toimii")


