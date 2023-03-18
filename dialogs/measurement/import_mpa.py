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
        self.files_added = {}
        self.__files_preview = {}

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
        self.__load_files()
        self.__check_if_import_allowed()

    def __load_file_preview(self, file=None, preview_max_len=64,
                            preview_data_max_len=4):
        """Load beginning of the file to preview window.

        Args:
            file: A string representing full path to the file.
            preview_max_len: Maximum amount of lines to show in preview.
            preview_data_max_len: Maximum amount of data lines to show
                in preview.
        """
        if not file:
            self.textEdit.clear()
            self.button_coinc.setEnabled(False)
            return
        self.button_coinc.setEnabled(True)

        preview_file_lines = self.__files_preview[file]
        preview_max_len = min(preview_max_len, len(preview_file_lines))
        data_title_line_index = None

        # Find data title line
        for i in range(preview_max_len):
            line = preview_file_lines[i]
            # Data title line ends with "Timestamp"
            if line.strip()[-9:] == "Timestamp":
                data_title_line_index = i
                break

        if data_title_line_index is not None:
            preview_max_len = \
                min(preview_max_len,
                    data_title_line_index + preview_data_max_len + 1)

        preview_string = f"{file} + \n\n"
        for i in range(preview_max_len):
            line = preview_file_lines[i]
            preview_string += f"{i + 1}: {line}\n"
        preview_string += "...\n"
        self.textEdit.setText(preview_string)

    def __load_files(self):
        """Loads X lines of the data for rough estimation of values.
        """
        skip_length = 10
        self.adc_occurance = {}
        for file in self.files_added:
            with open(file) as in_file:
                self.__files_preview[file] = []
                reading_data = False
                i = 1
                for line in in_file:
                    if i >= 1000:
                        break
                    if not line:
                        continue
                    i += 1
                    # Get ADC values
                    if reading_data:
                        split = line.strip().split("\t")
                        if not split[0] in self.adc_occurance:
                            self.adc_occurance[split[0]] = 1
                        else:
                            self.adc_occurance[split[0]] += 1
                    # Automatically set good skip amount.
                    elif line.strip()[-9:] == "Timestamp":
                        skip_length = i
                        reading_data = True
                    self.__files_preview[file].append(line.strip())
        # Automatically set good values.
        sort_adc_occ = OrderedDict(sorted(self.adc_occurance.items(),
                                          reverse=True))
        adc_keys = sorted(self.adc_occurance.keys())

        self.spin_skiplines.setValue(skip_length)
        self.spin_adctrigger.setMinimum(int(adc_keys[0]))
        self.spin_adctrigger.setMaximum(int(adc_keys[-1]))
        self.spin_adctrigger.setValue(int(tuple(sort_adc_occ.keys())[0]))
        self.spin_adccount.setValue(int(adc_keys[-1]) + 1)
        self.__create_timing_spinbox()
        self.__update_timings()
        self.__insert_import_timings()

    def __check_if_import_allowed(self):
        """Toggle state of import button depending on if it is allowed.
        """
        root = self.treeWidget.invisibleRootItem()
        self.button_import.setEnabled(root.childCount() > 0)

    def __coinc_calc(self):
        """Calculate coincidence for selected
        """
        item = self.treeWidget.currentItem()
        input_file = Path(item.file)

        timing = dict()
        timing_first = "1"
        for coinc_timing in self.__added_timings.values():
            if coinc_timing.is_not_trigger:
                timing[coinc_timing.adc] = (coinc_timing.low.value(),
                                            coinc_timing.high.value())
                timing_first = coinc_timing.adc
        # timing_first = timing.keys().next()
        timing_low = self.__added_timings[timing_first].low
        timing_high = self.__added_timings[timing_first].high
        ImportTimingGraphDialog(
            self, input_file, None, (timing_low, timing_high),
            icon_manager=self.__icon_manager,
            skip_lines=self.spin_skiplines.value(),
            trigger=self.spin_adctrigger.value(),
            adc_count=self.spin_adccount.value(),
            timing=timing,
            coinc_count=self.global_settings.get_import_coinc_count())

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
