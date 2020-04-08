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

import logging
import os
import re

import dialogs.dialog_functions as df
import modules.general_functions as gf
import widgets.input_validation as iv

from pathlib import Path
from collections import OrderedDict

from dialogs.measurement.import_timing_graph import ImportTimingGraphDialog
from dialogs.file_dialogs import open_files_dialog

from PyQt5 import uic
from PyQt5 import QtCore
from PyQt5 import QtWidgets

from time import clock


class ImportMeasurementsDialog(QtWidgets.QDialog):
    """Measurement importing class. Used to import measurement data
    from detecting unit into potku.
    """
    def __init__(self, request, icon_manager, statusbar, parent):
        """Init measurement import dialog.
        
        Args:
            request: A request class object.
            icon_manager: An IconManager class object.
            statusbar: A QtGui.QMainWindow's QStatusBar.
            parent: A QtGui.QMainWindow of Potku.
        """
        super().__init__()
        uic.loadUi(Path("ui_files", "ui_import_dialog.ui"), self)

        self.request = request
        self.__icon_manager = icon_manager
        self.statusbar = statusbar
        self.parent = parent
        self.global_settings = self.parent.settings
        self.files_added = {}  # Just placeholder
        self.__files_preview = {}
        self.__added_timings = {}  # Placeholder for timing limits
        self.__import_row_count = 0  # Placeholder for adding/removing rows
        self.__initiated_columns = False
        self.imported = False
        
        self.__add_timing_labels()

        self.button_import.clicked.connect(self.__import_files) 
        self.button_cancel.clicked.connect(self.__close) 
        self.button_addimport.clicked.connect(self.__add_file)
        self.button_coinc.clicked.connect(self.__coinc_calc)
        self.button_addColumn.clicked.connect(
                  lambda: self.__add_import_column(self.grid_column.rowCount()))
        #          lambda: self.__add_import_column(self.__import_row_count))
        self.spin_adctrigger.valueChanged.connect(self.__update_timings)
        self.spin_adctrigger.setKeyboardTracking(False)
        
        self.treeWidget.itemClicked.connect(self.__select_file)
        remove_file = QtWidgets.QAction("Delete", self.treeWidget)
        self.treeWidget.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.treeWidget.addAction(remove_file)
        remove_file.triggered.connect(self.__remove_selected)

        self.exec_()

    def __add_file(self):
        """Add a file to list of files to be imported.
        """
        files = open_files_dialog(self,
                                  self.request.directory,
                                  "Select an event collection to be imported",
                                  "Event collection (*.evnt)")
        df.add_imported_files_to_tree(self, files)
        self.__load_files()
        self.__check_if_import_allowed()

    def __add_import_column(self, i, adc="0", removable=True):
        """Add a column to import file.
        
        Args:
            i: An integer representing the row integer.
            adc: An integer representing ADC.
            removable: A boolean representing if row can be removed.
        """
        self.__import_row_count += 1
        label = QtWidgets.QLabel("{0}".format(self.__import_row_count))
        remove_button = QtWidgets.QPushButton("Remove")
        remove_button.clicked.connect(
              lambda: self.__remove_import_column_row(remove_button))
        remove_button.setEnabled(removable)
        self.grid_column.addWidget(label, i, 0)
        self.grid_column.addWidget(self.__create_combobox(adc), i, 1)
        self.grid_column.addWidget(remove_button, i, 2)

    def __add_timing_labels(self):
        """Add timing labels in code side
        """
        label_adc = QtWidgets.QLabel("ADC")
        label_low = QtWidgets.QLabel("Low")
        label_high = QtWidgets.QLabel("High")
        self.grid_timing.addWidget(label_adc, 0, 0)
        self.grid_timing.addWidget(label_low, 1, 0)
        self.grid_timing.addWidget(label_high, 2, 0)

    def __import_files(self):
        """Import listed files with settings defined in the dialog.
        """
        imported_files = {}
        string_columns = []
        for i in range(self.grid_column.rowCount()):
            item = self.grid_column.itemAtPosition(i, 0)
            if not item.isEmpty():
                combo_widget = self.grid_column.itemAtPosition(i, 1).widget()
                # combo_widget = combo_item
                cur_index = combo_widget.currentIndex()
                cur_text = combo_widget.currentText()
                adc = int(re.sub(r"ADC ([0-9]+).*", r"\1", cur_text))
                # + 1 since actual column, not index
                column_index = adc * 2 + cur_index % 2 + 1  
                string_columns.append("${0}".format(column_index))
        string_column = ",".join(string_columns)
        
        self.__remove_temp_file()
        root = self.treeWidget.invisibleRootItem()
        root_child_count = root.childCount()
        timing = dict()
        for coinc_key in self.__added_timings.keys():
            coinc_timing = self.__added_timings[coinc_key]
            if coinc_timing.is_not_trigger:
                timing[coinc_timing.adc] = (coinc_timing.low.value(),
                                            coinc_timing.high.value())
        start_time = clock()
        progress_bar = QtWidgets.QProgressBar()
        self.statusbar.addWidget(progress_bar, 1)
        progress_bar.show()
        progress_bar.setValue(10)
        QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents)
        # Mac requires event processing to show progress bar and its
        # process.
        
        filename_list = []
        for i in range(root_child_count):
            item = root.child(i)
            filename_list.append(item.filename)

            sample = self.request.samples.add_sample()
            self.parent.add_root_item_to_tree(sample)
            item_name = item.name.replace("_", "-")

            regex = "^[A-Za-z0-9-ÖöÄäÅå]*"
            item_name = iv.validate_text_input(item_name, regex)

            measurement = self.parent.add_new_tab("measurement", "",
                                                  sample,
                                                  object_name=item_name,
                                                  import_evnt_or_binary=True)
            output_file = os.path.join(measurement.directory_data, item_name
                                       + ".asc")
            n = 2
            while True:  # Allow import of same named files.
                if not os.path.isfile(output_file):
                    break
                output_file = "{0}-{2}.{1}".format(measurement.directory_data
                 + os.sep + item_name, "asc", n)
                n += 1
            imported_files[sample] = output_file
            gf.coinc(item.file,
                     output_file,
                     skip_lines=self.spin_skiplines.value(),
                     tablesize=10,
                     trigger=self.spin_adctrigger.value(),
                     adc_count=self.spin_adccount.value(),
                     timing=timing,
                     columns=string_column,
                     nevents=self.spin_eventcount.value())
            measurement.measurement_file = output_file

            progress_bar.setValue(10 + (i + 1) / root_child_count * 90)
            QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents)
            # Mac requires event processing to show progress bar and its
            # process.
        
        filenames = ", ".join(filename_list)

        progress_bar.setValue(100)
        QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents)

        self.statusbar.removeWidget(progress_bar)
        progress_bar.hide()
        elapsed = clock() - start_time
        log = "Imported measurements to request: {0}".format(filenames)
        log_var = "Variables used: {0} {1} {2} {3} {4}".format(
            "Skip lines: " + str(self.spin_skiplines.value()),
            "ADC trigger: " + str(self.spin_adctrigger.value()),
            "ADC count: " + str(self.spin_adccount.value()),
            "Timing: " + str(timing),
            "Event count: " + str(self.spin_eventcount.value()))
        log_elapsed = "Importing finished {0} seconds".format(int(elapsed))
        logging.getLogger("request").info(log)
        logging.getLogger("request").info(log_var)
        logging.getLogger("request").info(log_elapsed)
        self.imported = True
        self.close()

    def __insert_import_timings(self):
        """Insert column selection for import to QTableWidget.
        """
        if self.__initiated_columns:
            return
        self.__initiated_columns = True
        keys = tuple(sorted(self.adc_occurance.keys()))
        for i in range(0, len(keys)):
            adc = keys[i]
            self.__add_import_column(i, adc, removable=False)

    def __load_file_preview(self, file=None):
        """Load beginning of the file to preview window.
        
        Args:
            file: A string representing full path to the file.
        """
        if not file:
            self.textEdit.clear()
            self.button_coinc.setEnabled(False)
            return
        self.button_coinc.setEnabled(True)
        string = file + "\r\n\r\n"
        for i in range(1, 31):
            line = self.__files_preview[file][i]
            if line.strip()[-9:] == "Timestamp" or i > 30:
                break
            string += "{0}: {1}\n".format(i, line)
        self.textEdit.setText(string)

    def __load_files(self):
        """Loads X lines of the data for rough estimation of values.
        """
        skip_length = 10
        self.adc_occurance = {}
        for file in self.files_added:
            with open(file) as fp:
                self.__files_preview[file] = []
                reading_data = False
                i = 1
                for line in fp:
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
        self.group_importcolumn.setEnabled(root.childCount() > 0)

    def __close(self):
        """Close dialog.
        """
        self.__remove_temp_file()
        self.close()

    def __coinc_calc(self):
        """Calculate coincidence for selected
        """
        item = self.treeWidget.currentItem()
        input_file = item.file
        request_dir = str(os.path.join(self.request.directory, "import_file"))
        output_file = "{0}.{1}".format(request_dir, "tmp")

        timing = dict()
        timing_first = "1"
        for coinc_key in self.__added_timings.keys():
            coinc_timing = self.__added_timings[coinc_key]
            if coinc_timing.is_not_trigger:
                timing[coinc_timing.adc] = (coinc_timing.low.value(),
                                            coinc_timing.high.value())
                timing_first = coinc_timing.adc
        # TODO: Needs a better solution for more ADCs
        # timing_first = timing.keys().next()
        timing_low = self.__added_timings[timing_first].low
        timing_high = self.__added_timings[timing_first].high
        ImportTimingGraphDialog(self, input_file, output_file,
                                (timing_low, timing_high),
                                icon_manager=self.__icon_manager,
                                skip_lines=self.spin_skiplines.value(),
                                trigger=self.spin_adctrigger.value(),
                                adc_count=self.spin_adccount.value(),
                                timing=timing,
                                coinc_count=self.global_settings
                                .get_import_coinc_count())

    def __create_combobox(self, adc):
        """Create combobox for ADC.
        
        Args:
            adc: An integer representing ADC.        
        """
        adc_keys = sorted(self.adc_occurance.keys())
        combobox = QtWidgets.QComboBox()
        for key in adc_keys:
            combobox.addItem("ADC {0}".format(key))
            if key == adc:
                combobox.setCurrentIndex(combobox.count() - 1)
            combobox.addItem("ADC {0} timediff".format(key))
        combobox.column = self.__import_row_count
        return combobox

    def __create_spinbox(self, default):
        spinbox = QtWidgets.QSpinBox()
        spinbox.stepBy(1)
        spinbox.setMinimum(-1000)
        spinbox.setMaximum(1000)
        spinbox.setValue(int(default))
        return spinbox

    def __create_timing_spinbox(self):
        """Generate timing spinboxes from read files.
        """
        i = 1
        for adc in sorted(self.adc_occurance.keys()):
            if adc in self.__added_timings:  # Do not add multiple times
                continue
            timing = self.global_settings.get_import_timing(adc)
            label = QtWidgets.QLabel("{0}".format(adc))
            spin_low = self.__create_spinbox(timing[0])
            spin_high = self.__create_spinbox(timing[1])
            self.__added_timings[adc] = CoincTiming(adc, spin_low, spin_high)
            self.grid_timing.addWidget(label, 0, i)
            self.grid_timing.addWidget(spin_low, 1, i)
            self.grid_timing.addWidget(spin_high, 2, i)
            i += 1

    def __remove_import_column_row(self, button):
        """Remove row from columns in import data.
        
        Args:
            button: A QtWidgets.QPushButton class object which was pressed.
        """
        index = self.grid_column.indexOf(button)
        row, column, unused_cols, unused_rows = \
            self.grid_column.getItemPosition(index)
        column_count = sorted(range(column + 1), reverse=True)
        # Close all widgets in the row.
        for i in column_count:
            item = self.grid_column.itemAtPosition(row, i)
            item.widget().close()
        # Fix column label text and combobox column number.
        n = 0
        for i in range(self.grid_column.rowCount()):
            item = self.grid_column.itemAtPosition(i, 0)
            if not item.isEmpty():
                n += 1
                widget = item.widget()
                widget.setText(str(n))
                self.__import_row_count -= 1
                # Fix combobox column number.
                combo_item = self.grid_column.itemAtPosition(i, 1)
                combo_widget = combo_item.widget()
                combo_widget.column = n
        self.__import_row_count = n

    def __remove_selected(self):
        """Remove the selected files from import list.
        """
        root = self.treeWidget.invisibleRootItem()
        for item in self.treeWidget.selectedItems():
            (item.parent() or root).removeChild(item)
            self.files_added.pop(item.file)
        self.__check_if_import_allowed()
        self.__load_file_preview()

    def __remove_temp_file(self):
        """Remove tempfile, if it exist, used for timing limit correction.
        """
        request_dir = str(os.path.join(self.request.directory, "import_file"))
        tmp_file = "{0}.{1}".format(request_dir, "tmp")
        try:
            if os.path.isfile(tmp_file):
                os.unlink(tmp_file)
        except:
            pass

    def __select_file(self):
        """Item is selected in treewidget.
        """
        item = self.treeWidget.currentItem()
        self.__load_file_preview(item.file)

    def __update_timings(self):
        """Update spinboxes enabled state based on selected ADC trigger.
        """
        current_adc = str(self.spin_adctrigger.value())
        for coinc_key in self.__added_timings.keys():
            coinc_timing = self.__added_timings[coinc_key]
            coinc_timing.is_not_trigger = coinc_timing.adc != current_adc
            coinc_timing.low.setEnabled(coinc_timing.is_not_trigger)
            coinc_timing.high.setEnabled(coinc_timing.is_not_trigger)


class CoincTiming:
    """Coincidence timing class
    """
    def __init__(self, adc, low, high):
        """Inits coincidence timing class
        
        Args:
            adc: An integer representing ADC.
            low: A QtWidgets.QSpinBox representing spinbox for low value.
            high: A QtWidgets.QSpinBox representing spinbox for high value.
        """
        self.adc = adc
        self.low = low
        self.high = high
        self.is_not_trigger = True
