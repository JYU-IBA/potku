# coding=utf-8
"""
Created on 25.3.2013
Updated on 18.6.2018

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
import os
import sys

from PyQt5 import uic
from PyQt5 import QtCore
from PyQt5 import QtWidgets

import modules.masses as masses
from modules.cut_file import is_rbs, get_scatter_element
from modules.element import Element
from modules.energy_spectrum import EnergySpectrum
from modules.general_functions import read_espe_file
from modules.measurement import Measurement
from widgets.matplotlib.measurement.energy_spectrum import \
    MatplotlibEnergySpectrumWidget


class EnergySpectrumParamsDialog(QtWidgets.QDialog):
    """
    An EnergySpectrumParamsDialog.
    """
    checked_cuts = {}

    def __init__(self, parent, spectrum_type, element_simulation=None):
        """Inits energy spectrum dialog.
        
        Args:
            parent: A TabWidget.
            spectrum_type: Whether spectrum is for measurement of simulation.
            element_simulation: ElementSimulation object.
        """
        super().__init__()
        self.parent = parent
        self.spectrum_type = spectrum_type
        self.ui = uic.loadUi(
            os.path.join("ui_files", "ui_energy_spectrum_params.ui"), self)

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
                    element_simulation.channel_width
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
            self.exec_()

        else:
            header_item = QtWidgets.QTreeWidgetItem()
            header_item.setText(0, "Simulated elements")
            self.ui.treeWidget.setHeaderItem(header_item)

            tof_list_tree_widget = QtWidgets.QTreeWidget()
            tof_list_tree_widget.setSizePolicy(
                QtWidgets.QSizePolicy.Expanding,
                QtWidgets.QSizePolicy.Expanding)

            header = QtWidgets.QTreeWidgetItem()
            header.setText(0, "Pre-calculated elements")

            self.ui.gridLayout_2.addWidget(tof_list_tree_widget, 0, 1)

            tof_list_tree_widget.setHeaderItem(header)

            self.ui.pushButton_OK.clicked.connect(
                self.__calculate_selected_spectra)

            self.result_files = []
            elem_sim_prefixes = []  # .rec files of the same simulation are
            # shown as one tree item.
            for file in os.listdir(self.parent.obj.directory):
                if file.endswith(".rec"):
                    sim_name = file.split(".")[0]

                    if sim_name in elem_sim_prefixes:
                        continue

                    elem_sim_prefixes.append(sim_name)
                    item = QtWidgets.QTreeWidgetItem()
                    item.setText(0, sim_name)
                    item.setCheckState(0, QtCore.Qt.Unchecked)
                    self.ui.treeWidget.addTopLevelItem(item)

            # Add calculated tof_list files to tof_list_tree_widget by
            # measurement under the same sample.
            for sample in self.parent.obj.request.samples.samples:
                for measurement in sample.measurements.measurements.values():
                    if element_simulation.sample is measurement.sample:
                        tree_item = QtWidgets.QTreeWidgetItem()
                        tree_item.setText(0, measurement.name)
                        tree_item.obj = measurement
                        tof_list_tree_widget.addTopLevelItem(tree_item)

                        for file in os.listdir(
                                measurement.directory_energy_spectra):
                            if file.endswith("tof_list"):
                                item = QtWidgets.QTreeWidgetItem()
                                file_name_without_suffix = \
                                    file.rsplit('.', 1)[0]
                                item.setText(0, file_name_without_suffix)
                                item.setCheckState(0, QtCore.Qt.Unchecked)
                                tree_item.addChild(item)
                                tree_item.setExpanded(True)
            self.exec_()

    def __calculate_selected_spectra(self):
        """Calculate selected spectra.
        """
        root = self.ui.treeWidget.invisibleRootItem()
        child_count = root.childCount()
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
                            elem_sim.calculate_espe()
                            self.result_files.append(os.path.join(
                                self.parent.obj.directory,
                                rec_elem_prefix_and_name + ".simu"))

        self.bin_width = self.ui.histogramTicksDoubleSpinBox.value()

        self.close()

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
                reply = QtWidgets.QMessageBox.critical(
                    self, "Error",
                    "An error occured while trying to create energy spectrum",
                    QtWidgets.QMessageBox.Ok,
                    QtWidgets.QMessageBox.Ok)

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

    def __init__(self, parent, spectrum_type, use_cuts=None, bin_width=0.1):
        """Inits widget.
        
        Args:
            parent: A TabWidget.
            use_cuts: A string list representing Cut files.
            bin_width: A float representing Energy Spectrum histogram's bin
            width.
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
                for file in use_cuts:
                    self.energy_spectrum_data[file] = read_espe_file(file)

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
            logging.getLogger(self.obj.name).error(msg)
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
        self.parent.energy_spectrum_widget = None
        file = os.path.join(self.parent.obj.directory, self.save_file)
        try:
            if os.path.isfile(file):
                os.unlink(file)
        except:
            pass
        super().closeEvent(evnt)

    def save_to_file(self):
        """Save object information to file.
        """
        files = "\t".join([tmp.replace(self.measurement.directory + "\\",
                                       "")
                           for tmp in self.use_cuts])
        file = os.path.join(self.measurement.directory_energy_spectra,
                            self.save_file)
        fh = open(file, "wt")
        fh.write("{0}\n".format(files))
        fh.write("{0}".format(self.bin_width))
        fh.close()
