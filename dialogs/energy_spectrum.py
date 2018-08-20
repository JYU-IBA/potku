# coding=utf-8
"""
Created on 25.3.2013
Updated on 20.8.2018

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

__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen " \
             "\n Samuli Rahkonen \n Miika Raunio \n Severi Jääskeläinen \n " \
             "Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"
__version__ = "2.0"

import logging
import modules.masses as masses
import os
import shutil
import sys

from modules.cut_file import is_rbs, get_scatter_element
from modules.element import Element
from modules.energy_spectrum import EnergySpectrum
from modules.general_functions import open_file_dialog
from modules.general_functions import calculate_spectrum
from modules.general_functions import read_espe_file
from modules.general_functions import read_tof_list_file
from modules.measurement import Measurement

from PyQt5 import uic
from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5.QtCore import QLocale

from widgets.matplotlib.measurement.energy_spectrum import \
    MatplotlibEnergySpectrumWidget


class EnergySpectrumParamsDialog(QtWidgets.QDialog):
    """
    An EnergySpectrumParamsDialog.
    """
    checked_cuts = {}

    def __init__(self, parent, spectrum_type, element_simulation=None,
                 recoil_widget=None):
        """Inits energy spectrum dialog.
        
        Args:
            parent: A TabWidget.
            spectrum_type: Whether spectrum is for measurement of simulation.
            element_simulation: ElementSimulation object.
            recoil_widget: RecoilElement widget.
        """
        super().__init__()
        self.parent = parent
        self.element_simulation = element_simulation
        self.spectrum_type = spectrum_type
        self.ui = uic.loadUi(
            os.path.join("ui_files", "ui_energy_spectrum_params.ui"), self)

        locale = QLocale.c()
        self.ui.histogramTicksDoubleSpinBox.setLocale(locale)

        # Connect buttons
        self.ui.pushButton_Cancel.clicked.connect(self.close)

        if not self.parent.obj.detector:  # Request settings are used.
            EnergySpectrumParamsDialog.bin_width = \
                self.parent.obj.request.default_measurement.channel_width
        else:
            if type(self.parent.obj) is Measurement:
                EnergySpectrumParamsDialog.bin_width = \
                    self.parent.obj.channel_width
            else:
                EnergySpectrumParamsDialog.bin_width = \
                    self.element_simulation.channel_width
        self.ui.histogramTicksDoubleSpinBox.setValue(
            EnergySpectrumParamsDialog.bin_width)

        if isinstance(self.parent.obj, Measurement):
            self.measurement = self.parent.obj
            self.ui.pushButton_OK.clicked.connect(self.__accept_params)

            m_name = self.measurement.name
            if m_name not in EnergySpectrumParamsDialog.checked_cuts.keys():
                EnergySpectrumParamsDialog.checked_cuts[m_name] = []
            self.measurement.fill_cuts_treewidget(
                self.ui.treeWidget,
                True,
                EnergySpectrumParamsDialog.checked_cuts[m_name])

            self.__update_eff_files()

            self.ui.importPushButton.setVisible(False)
            self.exec_()

        else:
            header_item = QtWidgets.QTreeWidgetItem()
            header_item.setText(0, "Simulated elements")
            self.ui.treeWidget.setHeaderItem(header_item)

            self.tof_list_tree_widget = QtWidgets.QTreeWidget()
            self.tof_list_tree_widget.setSizePolicy(
                QtWidgets.QSizePolicy.Expanding,
                QtWidgets.QSizePolicy.Expanding)

            header = QtWidgets.QTreeWidgetItem()
            header.setText(0, "Pre-calculated elements")

            self.ui.gridLayout_2.addWidget(self.tof_list_tree_widget, 0, 1)

            self.tof_list_tree_widget.setHeaderItem(header)

            self.ui.pushButton_OK.clicked.connect(
                self.__calculate_selected_spectra)

            # Find the corresponding recoil element to recoil widget
            rec_to_check = None
            for rec_element in self.element_simulation.recoil_elements:
                if rec_element.widgets[0] is recoil_widget:
                    rec_to_check = rec_element

            self.result_files = []
            for file in os.listdir(self.parent.obj.directory):
                if file.endswith(".rec") or file.endswith(".sct"):
                    rec_name = file.split(".")[0]

                    for f in os.listdir(self.parent.obj.directory):
                        rec_prefix = rec_name.split('-')[0]
                        if f.startswith(rec_prefix) and f.endswith(".erd"):
                            item = QtWidgets.QTreeWidgetItem()
                            item.setText(0, rec_name)
                            if rec_to_check and rec_to_check.prefix + "-" + \
                               rec_to_check.name == rec_name:
                                item.setCheckState(0, QtCore.Qt.Checked)
                            else:
                                item.setCheckState(0, QtCore.Qt.Unchecked)
                            self.ui.treeWidget.addTopLevelItem(item)
                            break

            # Add calculated tof_list files to tof_list_tree_widget by
            # measurement under the same sample.

            for sample in self.parent.obj.request.samples.samples:
                for measurement in sample.measurements.measurements.values():
                    if self.element_simulation.sample is measurement.sample:

                        all_cuts = []

                        tree_item = QtWidgets.QTreeWidgetItem()
                        tree_item.setText(0, measurement.name)
                        tree_item.obj = measurement
                        tree_item.obj = measurement
                        self.tof_list_tree_widget.addTopLevelItem(tree_item)

                        for file in os.listdir(
                                measurement.directory_cuts):
                            if file.endswith(".cut"):
                                file_name_without_suffix = \
                                    file.rsplit('.', 1)[0]
                                all_cuts.append(file_name_without_suffix)

                        for file_2 in os.listdir(
                                os.path.join(
                                    measurement.directory_composition_changes,
                                    "Changes")):
                            if file_2.endswith(".cut"):
                                file_name_without_suffix = \
                                    file_2.rsplit('.', 1)[0]
                                all_cuts.append(file_name_without_suffix)

                        all_cuts.sort()

                        for cut in all_cuts:
                            item = QtWidgets.QTreeWidgetItem()
                            item.setText(0, cut)
                            item.setCheckState(0, QtCore.Qt.Unchecked)
                            tree_item.addChild(item)
                            tree_item.setExpanded(True)

            # Add a view for adding external files to draw
            self.external_tree_widget = QtWidgets.QTreeWidget()
            self.external_tree_widget.setSizePolicy(
                QtWidgets.QSizePolicy.Expanding,
                QtWidgets.QSizePolicy.Expanding)

            header = QtWidgets.QTreeWidgetItem()
            header.setText(0, "External files")

            self.ui.gridLayout_2.addWidget(self.external_tree_widget, 0, 2)

            self.external_tree_widget.setHeaderItem(header)

            self.imported_files_folder = \
                os.path.join(self.element_simulation.request.directory,
                             "Imported_files")
            if not os.path.exists(self.imported_files_folder):
                os.makedirs(self.imported_files_folder)

            # Add possible external files to view
            for ext_file in os.listdir(self.imported_files_folder):
                item = QtWidgets.QTreeWidgetItem()
                item.setText(0, ext_file)
                item.setCheckState(0, QtCore.Qt.Unchecked)
                self.external_tree_widget.addTopLevelItem(item)

            # Change the bin width label text
            self.ui.histogramTicksLabel.setText("Simulation and measurement "
                                                "histogram bin width:")

            self.ui.importPushButton.clicked.connect(
                self.__import_external_file)
            self.exec_()

    def __calculate_selected_spectra(self):
        """Calculate selected spectra.
        """
        self.close()
        root = self.ui.treeWidget.invisibleRootItem()
        child_count = root.childCount()

        if self.parent.obj.statusbar:
            progress_bar = QtWidgets.QProgressBar()
            self.parent.obj.statusbar.addWidget(progress_bar, 1)
            progress_bar.show()
            QtCore.QCoreApplication.processEvents(
                QtCore.QEventLoop.AllEvents)
            # Mac requires event processing to show progress bar and its
            # process.
        else:
            progress_bar = None
        dirtyinteger = 0

        for i in range(child_count):
            item = root.child(i)
            if item.checkState(0):
                for elem_sim in self.parent.obj.element_simulations:
                    for rec_elem in elem_sim.recoil_elements:
                        rec_elem_prefix_and_name = rec_elem.prefix + "-"\
                                                   + rec_elem.name
                        if rec_elem_prefix_and_name == item.text(0):
                            elem_sim.channel_width = self.ui.\
                                histogramTicksDoubleSpinBox.value()
                            elem_sim.calculate_espe(rec_elem)
                            self.result_files.append(os.path.join(
                                self.parent.obj.directory,
                                rec_elem_prefix_and_name + ".simu"))
                        dirtyinteger += 1
                        progress_bar.setValue((dirtyinteger / child_count) * 33)
                        QtCore.QCoreApplication.processEvents(
                            QtCore.QEventLoop.AllEvents)

        if child_count == 0:
            progress_bar.setValue(33)
            QtCore.QCoreApplication.processEvents(
                QtCore.QEventLoop.AllEvents)

        root_for_tof_list_files = self.tof_list_tree_widget.invisibleRootItem()
        child_count = root_for_tof_list_files.childCount()

        cut_files = {}
        item_texts = []
        used_measurements = []

        for i in range(child_count):
            measurement_item = root_for_tof_list_files.child(i)
            mes_child_count = measurement_item.childCount()
            for j in range(mes_child_count):
                item = measurement_item.child(j)
                if item.checkState(0):
                    measurement = item.parent().obj
                    if measurement not in cut_files.keys():
                        cut_files[measurement] = []
                    used_measurements.append(measurement)
                    # Calculate energy spectra for cut
                    item_texts.append(item.text(0))
                    if len(item.text(0).split('.')) < 4:
                        # Normal cut
                        cut_file = os.path.join(measurement.directory_cuts,
                                                item.text(0)) + ".cut"
                    else:
                        cut_file = os.path.join(
                            measurement.directory_composition_changes,
                            "Changes", item.text(0)) + ".cut"
                    cut_files[measurement].append(cut_file)
            dirtyinteger += 1
            progress_bar.setValue((dirtyinteger / child_count) * 33)
            QtCore.QCoreApplication.processEvents(
                QtCore.QEventLoop.AllEvents)

        if child_count == 0:
            progress_bar.setValue(66)
            QtCore.QCoreApplication.processEvents(
                QtCore.QEventLoop.AllEvents)

        length = len(used_measurements)
        # Hist all selected cut files
        for measurement in used_measurements:
            es = EnergySpectrum(measurement, cut_files[measurement],
                                self.ui.histogramTicksDoubleSpinBox.value(),
                                None)
            es.calculate_spectrum()
            # Add result files
            for name in item_texts:
                file_path = os.path.join(
                    measurement.directory_energy_spectra, name + ".hist")
                if os.path.exists(file_path):
                    if file_path in self.result_files:
                        continue
                    self.result_files.append(file_path)
                    dirtyinteger += 1
                    progress_bar.setValue((dirtyinteger / length) * 33)
                    QtCore.QCoreApplication.processEvents(
                        QtCore.QEventLoop.AllEvents)

        root_for_ext_files = self.external_tree_widget.invisibleRootItem()
        child_count = root_for_ext_files.childCount()

        # Add external files to result files
        for k in range(child_count):
            item = root_for_ext_files.child(k)
            if item.checkState(0):
                for ext in os.listdir(self.imported_files_folder):
                    if ext == item.text(0):
                        self.result_files.append(
                            os.path.join(self.imported_files_folder, ext))
                        break

        progress_bar.setValue(100)
        QtCore.QCoreApplication.processEvents(
            QtCore.QEventLoop.AllEvents)

        if progress_bar:
            self.parent.obj.statusbar.removeWidget(progress_bar)
            progress_bar.hide()

        self.bin_width = self.ui.histogramTicksDoubleSpinBox.value()

        simulation_name = self.element_simulation.simulation.name
        msg = "[{0}] Created Energy Spectrum. {1} {2}".format(
            simulation_name,
            "Bin width: {0}".format(self.bin_width),
            "Used files: {0}".format(", ".join(self.result_files))
        )
        logging.getLogger("request").info(msg)
        logging.getLogger(simulation_name).info(
            "Created Energy Spectrum. Bin width: {0} Used files: {1}".format(
                self.bin_width, ", ".join(self.result_files)))

    def __accept_params(self):
        """Accept given parameters and cut files.
        """
        width = self.ui.histogramTicksDoubleSpinBox.value()
        use_cuts = []
        root = self.ui.treeWidget.invisibleRootItem()
        child_count = root.childCount()
        m_name = self.measurement.name
        EnergySpectrumParamsDialog.checked_cuts[m_name].clear()
        for i in range(child_count):
            item = root.child(i)
            if item.checkState(0):
                use_cuts.append(os.path.join(item.directory, item.file_name))
                EnergySpectrumParamsDialog.checked_cuts[m_name].append(
                    item.file_name)
            child_count = item.childCount()
            if child_count > 0:  # Elemental Losses
                dir_elo = os.path.join(
                    self.measurement.directory_composition_changes, "Changes")
                for j in range(child_count):
                    item_child = item.child(j)
                    if item_child.checkState(0):
                        use_cuts.append(
                            os.path.join(dir_elo, item_child.file_name))
                        EnergySpectrumParamsDialog.checked_cuts[m_name].append(
                            item_child.file_name)
                EnergySpectrumParamsDialog.bin_width = width
        if use_cuts:
            self.ui.label_status.setText(
                "Please wait. Creating energy spectrum.")
            QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents)
            if self.parent.energy_spectrum_widget:
                self.parent.del_widget(self.parent.energy_spectrum_widget)
            self.parent.energy_spectrum_widget = EnergySpectrumWidget(
                self.parent, spectrum_type=self.spectrum_type,
                use_cuts=use_cuts,
                bin_width=width)

            # Check that matplotlib attribute exists after creation of energy
            # spectrum widget.
            # If it doesn't exists, that means that the widget hasn't been
            # initialized properly and the program should show an error dialog.
            if hasattr(self.parent.energy_spectrum_widget, "matplotlib_layout"):
                icon = self.parent.icon_manager.get_icon(
                    "energy_spectrum_icon_16.png")
                self.parent.add_widget(self.parent.energy_spectrum_widget,
                                       icon=icon)

                measurement_name = self.measurement.name
                msg = "[{0}] Created Energy Spectrum. {1} {2}".format(
                    measurement_name,
                    "Bin width: {0}".format(width),
                    "Cut files: {0}".format(", ".join(use_cuts))
                )
                logging.getLogger("request").info(msg)
                logging.getLogger(measurement_name).info(
                    "Created Energy Spectrum. Bin width: {0} Cut files: {1}".
                    format(
                        width,
                        ", ".join(use_cuts)))
                log_info = "Energy Spectrum graph points:\n"
                data = self.parent.energy_spectrum_widget.energy_spectrum_data
                splitinfo = "\n".join(["{0}: {1}".format(key, ", ".join(
                    "({0};{1})".format(round(v[0], 2), v[1])
                    for v in data[key])) for key in data.keys()])
                logging.getLogger(measurement_name).info(log_info + splitinfo)
                self.close()
            else:
                self.close()
                QtWidgets.QMessageBox.critical(
                    self, "Error",
                    "An error occurred while trying to create energy spectrum.",
                    QtWidgets.QMessageBox.Ok,
                    QtWidgets.QMessageBox.Ok)

    def __import_external_file(self):
        """
        Import an external file that matches the format of hist and simu files.
        """
        QtWidgets.QMessageBox.information(self, "Notice",
                                          "The external file needs to have the "
                                          "following format:\n\nenergy count\n"
                                          "energy count\nenergy count\n...\n\n"
                                          "to match the simulation and "
                                          "measurement energy spectra files.",
                                          QtWidgets.QMessageBox.Ok,
                                          QtWidgets.QMessageBox.Ok)
        file_path = open_file_dialog(
            self, self.element_simulation.request.directory, "Select a file "
                                                             "to import", "")

        name = os.path.split(file_path)[1]

        for file in os.listdir(self.imported_files_folder):
            if file == name:
                QtWidgets.QMessageBox.critical(
                    self, "Error",
                    "A file with that name already exists.",
                    QtWidgets.QMessageBox.Ok,
                    QtWidgets.QMessageBox.Ok)
                return

        shutil.copyfile(file_path, os.path.join(self.imported_files_folder,
                                                    name))

        item = QtWidgets.QTreeWidgetItem()
        item.setText(0, name)
        item.setCheckState(0, QtCore.Qt.Checked)
        self.external_tree_widget.addTopLevelItem(item)

    def __update_eff_files(self):
        """Update efficiency files to UI which are used.
        """
        # This is probably not the most effective way, or practical for 
        # that matter, to get all efficiency files from directory defined
        # in global settings that match the cut files of measurements.
        if self.measurement.detector:
            eff_files = self.measurement.detector.get_efficiency_files()
        else:
            eff_files = self.measurement.request.default_detector.\
                get_efficiency_files()
        eff_files_used = []
        root = self.ui.treeWidget.invisibleRootItem()
        child_count = root.childCount()
        for eff in eff_files:
            str_element, unused_ext = eff.split(".")
            element = Element.from_string(str_element)
            for i in range(child_count):
                item = root.child(i)
                # TODO: Perhaps make this update every time a cut file is
                # selected so user knows exactly what files are used instead
                # of what files match all the cut files.
                # if not item.checkState(0): continue
                if not hasattr(item, "file_name"):
                    continue
                cut_element = Element.from_string(item.file_name.split(".")[1])
                mass = cut_element.isotope
                if not mass:
                    mass = round(
                        masses.get_standard_isotope(cut_element.symbol),
                        0)
                if cut_element.symbol == element.symbol \
                        and mass == element.isotope:
                    eff_files_used.append(eff)
        if eff_files_used:
            self.ui.label_efficiency_files.setText(
                "Efficiency files used: {0}".format(", ".join(eff_files_used)))
        else:
            self.ui.label_efficiency_files.setText("No efficiency files.")


class EnergySpectrumWidget(QtWidgets.QWidget):
    """Energy spectrum widget which is added to measurement tab.
    """
    save_file = "widget_energy_spectrum.save"

    def __init__(self, parent, spectrum_type, use_cuts=None, bin_width=0.025,
                 save_file_int=0):
        """Inits widget.
        
        Args:
            parent: A TabWidget.
            use_cuts: A string list representing Cut files.
            bin_width: A float representing Energy Spectrum histogram's bin
            width.
            save_file_int: n integer to have unique save file names for
            simulation energy spectra combinations.
        """
        try:
            super().__init__()
            self.parent = parent
            self.icon_manager = parent.icon_manager
            self.progress_bar = None
            if use_cuts is None:
                use_cuts = []
            self.use_cuts = use_cuts
            self.bin_width = bin_width
            self.energy_spectrum_data = {}
            rbs_list = {}

            self.ui = uic.loadUi(os.path.join("ui_files",
                                              "ui_energy_spectrum.ui"),
                                 self)
            title = "{0} - Bin Width: {1}".format(self.ui.windowTitle(),
                                                  bin_width)
            self.ui.setWindowTitle(title)

            if isinstance(self.parent.obj, Measurement):
                self.measurement = self.parent.obj
                if self.measurement.statusbar:
                    self.progress_bar = QtWidgets.QProgressBar()
                    self.measurement.statusbar.addWidget(self.progress_bar, 1)
                    self.progress_bar.show()
                    QtCore.QCoreApplication.processEvents(
                        QtCore.QEventLoop.AllEvents)
                    # Mac requires event processing to show progress bar and its
                    # process.
                else:
                    self.progress_bar = None

                # Generate new tof.in file for external programs
                self.measurement.generate_tof_in()
                # Do energy spectrum stuff on this
                self.energy_spectrum = EnergySpectrum(
                    self.measurement,
                    use_cuts,
                    bin_width,
                    progress_bar=self.progress_bar)
                self.energy_spectrum_data = self.energy_spectrum.\
                    calculate_spectrum()

                # Check for RBS selections.
                for cut in self.use_cuts:
                    filename = os.path.basename(cut)
                    split = filename.split(".")
                    if is_rbs(cut):
                        # This should work for regular cut and split.
                        key = "{0}.{1}.{2}".format(split[1], split[2], split[3])
                        rbs_list[key] = get_scatter_element(cut)

            else:
                self.simulation = self.parent.obj
                self.save_file_int = save_file_int
                self.save_file = "widget_energy_spectrum_" + str(
                    save_file_int) + ".save"
                for file in use_cuts:
                    self.energy_spectrum_data[file] = read_espe_file(
                        file)

            # Graph in matplotlib widget and add to window
            self.matplotlib = MatplotlibEnergySpectrumWidget(
                self,
                self.energy_spectrum_data,
                rbs_list, spectrum_type)
        except:
            import traceback
            msg = "Could not create Energy Spectrum graph. "
            err_file = sys.exc_info()[2].tb_frame.f_code.co_filename
            str_err = ", ".join([sys.exc_info()[
                                     0].__name__ + ": " + traceback._some_str(
                sys.exc_info()[1]), err_file,
                                 str(sys.exc_info()[2].tb_lineno)])
            msg += str_err
            logging.getLogger(self.parent.obj.name).error(msg)
            if hasattr(self, "matplotlib"):
                self.matplotlib.delete()
        finally:
            if self.progress_bar:
                self.measurement.statusbar.removeWidget(self.progress_bar)
                self.progress_bar.hide()

    def update_use_cuts(self):
        """
        Update used cuts list with new Measurement cuts.
        """
        for file in os.listdir(self.parent.obj.directory_cuts):
            for i in range(len(self.use_cuts)):
                cut = self.use_cuts[i]
                cut_split = cut.split('.')  # There is one dot more (.potku)
                file_split = file.split('.')
                if cut_split[2] == file_split[1] and cut_split[3] == \
                        file_split[2] and cut_split[4] == file_split[3]:
                    cut_file = os.path.join(self.parent.obj.directory_cuts,
                                            file)
                    self.use_cuts[i] = cut_file

        changes_dir = os.path.join(
            self.parent.obj.directory_composition_changes, "Changes")
        if os.path.exists(changes_dir):
            for file in os.listdir(changes_dir):
                for i in range(len(self.use_cuts)):
                    cut = self.use_cuts[i]
                    cut_split = cut.split('.')  # There is one dot more (.potku)
                    file_split = file.split('.')
                    if cut_split[2] == file_split[1] and cut_split[3] == \
                            file_split[2] and cut_split[4] == file_split[3]:
                        cut_file = os.path.join(changes_dir, file)
                        self.use_cuts[i] = cut_file

    def delete(self):
        """Delete variables and do clean up.
        """
        self.energy_spectrum = None
        self.progress_bar = None
        self.matplotlib.delete()
        self.matplotlib = None
        self.ui.close()
        self.ui = None
        self.close()

    def closeEvent(self, evnt):
        """Reimplemented method when closing widget.
        """
        file = os.path.join(self.parent.obj.directory, self.save_file)
        try:
            if os.path.isfile(file):
                os.unlink(file)
        except:
            pass
        super().closeEvent(evnt)

    def save_to_file(self, measurement=True, update=False):
        """Save object information to file.

        Args:
            measurement: Whether energy spectrum belong to measurement or
            simulation.
        """
        if measurement:
            files = "\t".join([tmp.replace(self.measurement.directory + "\\",
                                           "")
                               for tmp in self.use_cuts])
            file = os.path.join(self.measurement.directory_energy_spectra,
                                self.save_file)
        else:
            files = "\t".join([tmp for tmp in self.use_cuts])

            file_name_start = "widget_energy_spectrum_"
            i = self.save_file_int
            file_name_end = ".save"
            file_name = file_name_start + str(i) + file_name_end
            if self.save_file_int == 0 or not update:
                i = 1
                file_name = file_name_start + str(i) + file_name_end
                while os.path.exists(os.path.join(self.simulation.directory,
                                                  file_name)):
                    file_name = file_name_start + str(i) + file_name_end
                    i += 1
                self.save_file_int = i
            self.save_file = file_name
            file = os.path.join(self.simulation.directory, file_name)
        fh = open(file, "wt")
        fh.write("{0}\n".format(files))
        fh.write("{0}".format(self.bin_width))
        fh.close()
