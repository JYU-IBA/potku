# coding=utf-8
'''
Created on 27.8.2013
Updated on 27.8.2013

Potku is a graphical user interface for analyzation and 
visualization of measurement data collected from a ToF-ERD 
telescope. For physics calculations Potku uses external 
analyzation components.  
Copyright (C) Timo Konu

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
'''
__author__ = "Timo Konu"
__versio__ = "1.0"

from os.path import join
from PyQt5 import QtGui, QtCore, uic, QtWidgets


class GraphIgnoreElements(QtWidgets.QDialog):
    def __init__(self, elements, ignored):
        '''Init the dialog.
        
        Args:
            elements: A list of elements in Depth Profile.
            ignored: A list of elements ignored previously for ratio calculation.
        '''
        super().__init__()
        self.__elements = elements
        self.ignored_elements = ignored
        uic.loadUi(join("ui_files", "ui_graph_ignored_elements.ui"), self)
        self.button_ok.clicked.connect(self.__ok_button) 
        self.button_cancel.clicked.connect(self.close)
        self.__set_values()
        self.exec_()
        
    
    def __set_values(self):
        '''Set elements to tree widget.
        '''
        for element in self.__elements:
            item = QtWidgets.QTreeWidgetItem([str(element)])
            item.element = str(element)
            if not item.element in self.ignored_elements:
                item.setCheckState(0, QtCore.Qt.Checked)
            else:
                item.setCheckState(0, QtCore.Qt.Unchecked)
            self.tree_elements.addTopLevelItem(item)
    
    
    def __ok_button(self):
        '''Accept selected elements to be used in ratio calculation.
        '''
        self.ignored_elements.clear()
        root = self.tree_elements.invisibleRootItem()
        child_count = root.childCount()
        for i in range(child_count): 
            item = root.child(i)
            if not item.checkState(0):
                self.ignored_elements.append(item.element)
        self.close()
        
        
        
        
