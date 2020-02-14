# coding=utf-8
"""
Created on 6.6.2013
Updated on 22.8.2018

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
__author__ = "Timo Konu \n Severi Jääskeläinen \n Samuel Kaiponen \n Heta " \
             "Rekilä \n Sinikka Siironen"
__version__ = "2.0"

import numpy
import os
import struct

import dialogs.dialog_functions as df
from dialogs.file_dialogs import open_files_dialog
from modules.general_functions import validate_text_input

from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5 import uic


class ImportDialogBinary(QtWidgets.QDialog):
    """Binary measurement importing class.
    """
    def __init__(self, request, icon_manager, statusbar, parent):
        """Init binary measurement import dialog.
        """
        super().__init__()
        self.request = request
        self.__icon_manager = icon_manager
        self.__statusbar = statusbar
        self.parent = parent
        self.__global_settings = self.parent.settings
        uic.loadUi(os.path.join("ui_files", "ui_import_dialog_binary.ui"), self)
        self.imported = False
        self.files_added = {}  # Dictionary of files to be imported.
        
        self.button_import.clicked.connect(self.__import_files) 
        self.button_cancel.clicked.connect(self.close) 
        self.button_addimport.clicked.connect(self.__add_file)
        
        remove_file = QtWidgets.QAction("Remove selected files",
                                        self.treeWidget)
        remove_file.triggered.connect(self.__remove_selected)
        self.treeWidget.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.treeWidget.addAction(remove_file)
        
        self.exec_()

    def __add_file(self):
        """Add a file to list of files to be imported.
        """
        files = open_files_dialog(self,
                                  self.request.directory,
                                  "Select binary files to be imported",
                                  "Binary format (*.lst)")
        df.add_imported_files_to_tree(self, files)
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
        imported_files = {}
        progress_bar = QtWidgets.QProgressBar()
        self.__statusbar.addWidget(progress_bar, 1)
        progress_bar.show()
        progress_bar.setValue(10)
        QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents)
        
        root = self.treeWidget.invisibleRootItem()
        root_child_count = root.childCount()

        for i in range(root_child_count):
            item = root.child(i)
            input_file = item.file

            sample = self.request.samples.add_sample()
            self.parent.add_root_item_to_tree(sample)
            item_name = item.name.replace("_", "-")

            regex = "^[A-Za-z0-9-ÖöÄäÅå]*"
            item_name = validate_text_input(item_name, regex)

            measurement = self.parent.add_new_tab("measurement", "",
                                                  sample,
                                                  object_name=item_name,
                                                  import_evnt_or_binary=True)
            output_file = "{0}.{1}".format(measurement.directory_data +
                                           os.sep + item_name, "asc")
            n = 2
            while True:  # Allow import of same named files.
                if not os.path.isfile(output_file):
                    break
                output_file = "{0}-{2}.{1}".format(measurement.directory_data
                 + os.sep + item_name, "asc", n)
                n += 1
            imported_files[sample] = output_file
            self.__convert_file(input_file, output_file)
            measurement.measurement_file = output_file

            percentage = 10 + (i + 1 / root_child_count) * 90
            progress_bar.setValue(percentage)
            QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents)

        progress_bar.setValue(100)
        QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents)

        self.__statusbar.removeWidget(progress_bar)
        progress_bar.hide()
        self.imported = True

        self.close()

    def __remove_selected(self):
        """Remove the selected files from import list.
        """
        root = self.treeWidget.invisibleRootItem()
        for item in self.treeWidget.selectedItems():
            (item.parent() or root).removeChild(item)
            self.files_added.pop(item.file)
        self.__check_if_import_allowed()
