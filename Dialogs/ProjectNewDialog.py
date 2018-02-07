
# coding=utf-8
'''
Created on 11.4.2013
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

import logging
import os
from PyQt5 import QtGui, QtWidgets
from PyQt5 import uic


class ProjectNewDialog(QtWidgets.QDialog):
    '''Dialog creating a new project.
    '''
    def __init__(self, parent):
        '''Inits energy spectrum dialog.
        
        Args:
            parent: Ibasoft class object.
        '''
        super().__init__()
        self.parent = parent
        self.folder = None  # Temporary for browsing folder
        self.directory = None
        
        self.ui = uic.loadUi(os.path.join("ui_files", "ui_new_project.ui"), self)
        self.default_directory_used = True
        self.ui.projectDirectoryLineEdit.setText(
                                     self.parent.settings.get_project_directory())
        
        # Connect buttons
        self.ui.pushOk.clicked.connect(self.__create_project) 
        self.ui.pushCancel.clicked.connect(self.close) 
        self.ui.browseFolderButton.clicked.connect(self.__browser_folder)
        self.ui.useDefaultCheckBox.clicked.connect(self.__change_directory)
        
        self.exec_()
    
    
    def __change_directory(self):
        self.default_directory_used = not self.default_directory_used 
        if self.default_directory_used:
            self.ui.projectDirectoryLineEdit.setText(
                                     self.parent.settings.get_project_directory())
    
    
    def __browser_folder(self):
        folder = QtGui.QFileDialog.getExistingDirectory(self,
                                     self.ui.browseFolderButton.text())
        if folder:
            self.folder = folder
            self.ui.projectDirectoryLineEdit.setText(folder)
        
        
    def __create_project(self):
        self.folder = self.ui.projectDirectoryLineEdit.text()
        self.name = self.ui.projectNameLineEdit.text()
        # TODO: check for valid folder needed
        # TODO: Get rid of print -> message window perhaps
        if not self.folder:  
            print("Project folder required!")
            return
        if not self.name: 
            print("Project name required!")
            return
        try:
            directory = os.path.join(self.folder, self.name)
            if not os.path.exists(directory):
                os.makedirs(directory)
                self.directory = directory
                logging.getLogger("project").info("Created the project.")
            else:
                print("Folder already exists: {0}".format(directory))
                return
            self.close()
        except:
            print("We've done something wrong. Most likely invalid project name.")
