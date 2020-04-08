# coding=utf-8
"""
Created on 27.8.2013
Updated on 1.6.2018

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

MatplotlibDepthProfileWidget handles the drawing and operation of the 
depth profile graph.
"""
__author__ = "Timo Konu \n Severi Jääskeläinen \n Samuel Kaiponen \n Heta " \
             "Rekilä \n Sinikka Siironen"
__version__ = "1.0"

from pathlib import Path

from PyQt5 import QtCore, uic
from PyQt5 import QtWidgets


class GraphIgnoreElements(QtWidgets.QDialog):
    """
    A dialog for ignoring elements in a graph.
    """
    def __init__(self, elements, ignored):
        """Init the dialog.
        
        Args:
            elements: A list of elements in Depth Profile.
            ignored: A set of elements ignored previously for ratio
            calculation.
        """
        super().__init__()
        uic.loadUi(Path("ui_files", "ui_graph_ignored_elements.ui"), self)

        self.__elements = elements
        self.ignored_elements = set(ignored)
        self.button_ok.clicked.connect(self.__ok_button)
        self.button_cancel.clicked.connect(self.close)
        self.__set_values()
        self.exec_()

    def __set_values(self):
        """Set elements to tree widget.
        """
        for element in self.__elements:
            item = QtWidgets.QTreeWidgetItem([str(element)])
            item.element = str(element)
            if item.element not in self.ignored_elements:
                item.setCheckState(0, QtCore.Qt.Checked)
            else:
                item.setCheckState(0, QtCore.Qt.Unchecked)
            self.tree_elements.addTopLevelItem(item)

    def __ok_button(self):
        """Accept selected elements to be used in ratio calculation.
        """
        self.ignored_elements.clear()
        root = self.tree_elements.invisibleRootItem()
        child_count = root.childCount()
        for i in range(child_count):
            item = root.child(i)
            if not item.checkState(0):
                self.ignored_elements.add(item.element)
        self.close()
