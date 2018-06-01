# coding=utf-8
"""
Created on 5.8.2013
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
__version__ = "2.0"

import os
from PyQt5 import QtCore, uic, QtWidgets


class DepthProfileIgnoreElements(QtWidgets.QDialog):
    """
    Dialog for ignoring elements in a depth profile.
    """
    def __init__(self, elements, ignored_graph, ignored_ratio):
        """Init the dialog.
        
        Args:
            elements: A list of elements in Depth Profile.
            ignored_graph: A list of elements ignored previously for the graph.
            ignored_ratio: A list of elements ignored previously for ratio
                           calculation.
        """
        super().__init__()
        self.__elements = elements
        self.ignore_from_graph = ignored_graph
        self.ignore_from_ratio = ignored_ratio
        uic.loadUi(os.path.join("ui_files", "ui_depth_profile_ignored.ui"),
                   self)
        self.button_ok.clicked.connect(self.__ok_button)
        self.button_cancel.clicked.connect(self.close)
        self.tree_elements.itemChanged.connect(self.__element_toggle_graph)
        self.__set_values()
        self.exec_()

    def __element_toggle_graph(self, item, col):
        """Catch item changed event from element tree.
        """
        if col != 0:
            return
        root = self.tree_ratio.invisibleRootItem()
        child_count = root.childCount()
        for i in range(child_count):
            ratio_element = root.child(i)
            if ratio_element.element != item.element:
                continue
            ratio_element.setHidden(not item.checkState(0))
            ratio_element.setCheckState(0, item.checkState(0))

    def __set_values(self):
        """Set elements to tree widget.
        """
        for element in self.__elements:
            element_str = str(element)
            # Add to graph list
            item = QtWidgets.QTreeWidgetItem([element_str])
            item.element = element_str
            if item.element not in self.ignore_from_graph:
                item.setCheckState(0, QtCore.Qt.Checked)
            else:
                item.setCheckState(0, QtCore.Qt.Unchecked)
            self.tree_elements.addTopLevelItem(item)
            # Add to ratio list
            item2 = QtWidgets.QTreeWidgetItem([element_str])
            item2.element = element_str
            if item2.element not in self.ignore_from_ratio and \
                    item2.element not in self.ignore_from_graph:
                item2.setCheckState(0, QtCore.Qt.Checked)
            else:
                item2.setCheckState(0, QtCore.Qt.Unchecked)
            self.tree_ratio.addTopLevelItem(item2)
            if element_str in self.ignore_from_graph:
                item2.setHidden(True)

    def __ok_button(self):
        """Accept selected elements to be used in ratio calculation.
        """
        self.ignore_from_graph.clear()
        self.ignore_from_ratio.clear()
        # Graph
        root = self.tree_elements.invisibleRootItem()
        child_count = root.childCount()
        for i in range(child_count):
            item = root.child(i)
            if not item.checkState(0):
                self.ignore_from_graph.append(item.element)
                self.ignore_from_ratio.append(item.element)  # Since no graph.
        # Ratio
        root = self.tree_ratio.invisibleRootItem()
        child_count = root.childCount()
        for i in range(child_count):
            item = root.child(i)
            if not item.checkState(0) and \
                    item.element not in self.ignore_from_ratio:
                self.ignore_from_ratio.append(item.element)
        self.close()
