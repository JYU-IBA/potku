# coding=utf-8
'''
Created on 30.4.2013
Updated on 23.5.2013

Potku is a graphical user interface for analyzation and 
visualization of measurement data collected from a ToF-ERD 
telescope. For physics calculations Potku uses external 
analyzation components.  
Copyright (C) Jarkko Aalto, Timo Konu, Samuli Kärkkäinen, Samuli Rahkonen and 
Miika Raunio

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
'''
__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen \n Samuli Rahkonen \n Miika Raunio"
__versio__ = "1.0"

from os import path
from PyQt4 import QtCore, uic, QtGui

class GlobalSettingsDialog(QtGui.QDialog):
    def __init__(self, masses, settings):
        '''Constructor for the program
        '''
        super().__init__()
        self.masses = masses
        self.settings = settings
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.ui = uic.loadUi(path.join("ui_files", "ui_global_settings.ui"), self)
        
        # Connect UI buttons
        self.ui.OKButton.clicked.connect(self.__accept_changes)
        self.ui.cancelButton.clicked.connect(self.close)
        self.ui.loadProjectPathButton.clicked.connect(
                                                  self.__change_project_directory)
        buttons = self.ui.findChild(QtGui.QButtonGroup, "elementButtons")
        buttons.buttonClicked.connect(self.__change_element_color)
        self.__set_values()
        self.exec_()
        
    
    def __set_values(self):
        '''Set settings values to dialog.
        '''
        self.ui.projectPathLineEdit.setText(self.settings.get_project_directory())
        for button in self.ui.groupBox_3.findChildren(QtGui.QPushButton):
            self.__set_button_color(button, 
                                    self.settings.get_element_color(button.text()))

        
    def __accept_changes(self):
        '''Accept changed settings and save.
        '''
        self.settings.set_project_directory(self.ui.projectPathLineEdit.text())
        for button in self.ui.groupBox_3.findChildren(QtGui.QPushButton):
            self.settings.set_element_color(button.text(), button.color)
        self.settings.save_config()
        self.close()

    
    def __change_project_directory(self):
        '''Change default project directory.
        '''
        folder = QtGui.QFileDialog.getExistingDirectory(self,
            "Select default project directory",
            directory=self.ui.projectPathLineEdit.text())
        if folder:
            self.ui.projectPathLineEdit.setText(folder)
            
    
    def __change_element_color(self, button):
        '''Change color of element button.
        
        Args:
            button: QPushButton
        '''
        dialog = QtGui.QColorDialog(self)
        self.color = dialog.getColor(QtGui.QColor(button.color),
                                     self,
                                     "Select Color for Element: {0}".format(
                                                                button.text()))
        if self.color.isValid():
            self.__set_button_color(button, self.color.name())
    
    
    def __set_button_color(self, button, color_name):
        '''Change button text color.
        
        Args:
            button: QPushButton
            color_name: String representing color.
        '''
        if not button.isEnabled():
            return
        text_color = "black"
        color = QtGui.QColor(color_name)
        luminance = 0.2126 * color.red() + 0.7152 * color.green()
        luminance += 0.0722 * color.blue()
        if luminance < 50:
            text_color = "white"
        button.color = color.name()
        button.setStyleSheet("background-color: {0}; color: {1};".format(
                                                     color.name(), text_color))
