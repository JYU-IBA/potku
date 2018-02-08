# coding=utf-8
'''
Created on 6.6.2013
Updated on 12.8.2013

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
'''
__author__ = "Timo Konu"
__versio__ = "1.0"

import struct, numpy
from os.path import join, isfile, split, splitext
from PyQt4 import QtGui, uic, QtCore

from Modules.Functions import open_files_dialog


class ImportDialogBinary(QtGui.QDialog):
    """Binary measurement importing class.
    """
    def __init__(self, project, icon_manager, statusbar, parent):
        """Init binary measurement import dialog.
        """
        super().__init__()
        self.__project = project
        self.__icon_manager = icon_manager
        self.__statusbar = statusbar
        self.__parent = parent
        self.__global_settings = self.__parent.settings
        uic.loadUi(join("ui_files", "ui_import_dialog_binary.ui"), self)
        self.imported = False
        self.__files_added = {}  # Dictionary of files to be imported.
        
        self.button_import.clicked.connect(self.__import_files) 
        self.button_cancel.clicked.connect(self.close) 
        self.button_addimport.clicked.connect(self.__add_file)
        
        remove_file = QtGui.QAction("Remove selected files", self.treeWidget)
        remove_file.triggered.connect(self.__remove_selected)
        self.treeWidget.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.treeWidget.addAction(remove_file)
        
        self.exec_()


    def __add_file(self):
        '''Add a file to list of files to be imported.
        '''
        files = open_files_dialog(self,
                                  self.__project.directory,
                                  "Select binary files to be imported",
                                  "Binary format (*.lst)")
        for file in files:
            if file in self.__files_added:
                continue
            directoty, filename = split(file)
            name, unused_ext = splitext(filename)
            item = QtGui.QTreeWidgetItem([name]) 
            item.file = file
            item.name = name
            item.filename = filename
            item.directory = directoty
            self.__files_added[file] = file
            self.treeWidget.addTopLevelItem(item)
        self.__check_if_import_allowed()
    
    
    def __check_if_import_allowed(self):
        """Toggle state of import button depending on if it is allowed.
        """
        root = self.treeWidget.invisibleRootItem()
        self.button_import.setEnabled(root.childCount() > 0)
        
        
    def __convert_file(self, input_file, output_file):
        """Convert binary file into ascii file.
        
        Args:
            input_file: A string representing input binary file.
            output_file: A string representing output ascii file.
        """
        data = []
        with open(input_file, "rb") as f:
            byte = f.read(4)
            while byte:
                # Second column is actually unsigned, but Python is broken
                # in regard to unpacking it properly (treats it as signed 
                # regardless) therefore we've to manually "make" it unsigned.
                cols = struct.unpack("<hh", byte)
                row = [cols[0], cols[1] - 8192]
                data.append(row)
                byte = f.read(4)
        numpy_array = numpy.array(data)
        numpy.savetxt(output_file, numpy_array, delimiter=" ", fmt="%d %d")  
        
        
    def __import_files(self):
        """Import binary files.
        """
        imported_files = []
        progress_bar = QtGui.QProgressBar()
        self.__statusbar.addWidget(progress_bar, 1)
        progress_bar.show()
        
        root = self.treeWidget.invisibleRootItem()
        root_child_count = root.childCount()
        for i in range(root_child_count):
            progress_bar.setValue(i / root_child_count)
            item = root.child(i)
            input_file = item.file
            output_file = "{0}.{1}".format(
               join(self.__project.directory, item.name), "asc")
            n = 2
            while True:  # Allow import of same named files.
                if not isfile(output_file):
                    break
                output_file = "{0}-{2}.{1}".format(
                   join(self.__project.directory, item.name),
                   "asc", n)
                n += 1
            imported_files.append(output_file)
            self.__convert_file(input_file, output_file)
        self.__statusbar.removeWidget(progress_bar)
        progress_bar.hide()
        self.imported = True
        self.__parent.load_project_measurements(imported_files)
        self.close()
        
        
    def __remove_selected(self):
        """Remove the selected files from import list.
        """
        root = self.treeWidget.invisibleRootItem()
        for item in self.treeWidget.selectedItems():
            (item.parent() or root).removeChild(item)
            self.__files_added.pop(item.file)
        self.__check_if_import_allowed()
