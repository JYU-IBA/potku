# coding=utf-8
"""
Created on 15.3.2023

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
import struct

import dialogs.dialog_functions as df
import widgets.gui_utils as gutils
import dialogs.file_dialogs as fdialogs

from widgets.gui_utils import StatusBarHandler
from widgets.icon_manager import IconManager

from modules.request import Request

from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5 import uic


class ImportDialogMPA(QtWidgets.QDialog):
    """MPA measurement importing class.
    """

    def __init__(self, request: Request, icon_manager: IconManager,
                 statusbar: QtWidgets.QStatusBar, parent: "Potku"):
        """Init MPA measurement import dialog.
        """
        super().__init__()
        uic.loadUi(gutils.get_ui_dir() / "ui_import_dialog_mpa.ui", self)

        self.request = request
        self.__icon_manager = icon_manager
        self.__statusbar = statusbar
        self.parent = parent
        self.__global_settings = self.parent.settings
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
        files = fdialogs.open_files_dialog(
            self, self.request.directory,
            "Select binary files to be imported",
            "MPA format (*.lst)")
        df.add_imported_files_to_tree(self, files)
        self.__check_if_import_allowed()

    def __check_if_import_allowed(self):
        """Toggle state of import button depending on if it is allowed.
        """
        root = self.treeWidget.invisibleRootItem()
        self.button_import.setEnabled(root.childCount() > 0)

    @staticmethod
    def __convert_file(input_file, output_file):
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
        """Import MPA files.
        """
        sbh = StatusBarHandler(self.__statusbar)
        sbh.reporter.report(10)

        root = self.treeWidget.invisibleRootItem()
        root_child_count = root.childCount()

        for i in range(root_child_count):
            item = root.child(i)
            input_file = item.file

            output_file = df.import_new_measurement(
                self.request, self.parent, item)
            self.__convert_file(input_file, output_file)

            sbh.reporter.report(10 + (i + 1 / root_child_count) * 90)

        sbh.reporter.report(100)
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
