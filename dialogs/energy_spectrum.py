# coding=utf-8
"""
Created on 25.3.2013
Updated on 23.5.2019

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
import shutil

import dialogs.dialog_functions as df
import widgets.gui_utils as gutils
import modules.cut_file as cut_file
import dialogs.file_dialogs as fdialogs

from pathlib import Path

from widgets.gui_utils import StatusBarHandler
from modules.energy_spectrum import EnergySpectrum
from modules.measurement import Measurement
from modules.get_espe import GetEspe
from modules.enums import OptimizationType

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
                 recoil_widget=None, statusbar=None, spectra_changed=None):
        """Inits energy spectrum dialog.
        
        Args:
            parent: A TabWidget.
            spectrum_type: Whether spectrum is for measurement of simulation.
            element_simulation: ElementSimulation object.
            recoil_widget: RecoilElement widget.
        """
        super().__init__()
        uic.loadUi(Path("ui_files", "ui_energy_spectrum_params.ui"), self)

        self.parent = parent
        self.element_simulation = element_simulation
        self.spectrum_type = spectrum_type
        self.statusbar = statusbar

        locale = QLocale.c()
        self.histogramTicksDoubleSpinBox.setLocale(locale)

        # Connect buttons
        self.pushButton_Cancel.clicked.connect(self.close)

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
        self.histogramTicksDoubleSpinBox.setValue(
            EnergySpectrumParamsDialog.bin_width)

        if isinstance(self.parent.obj, Measurement):
            self.measurement = self.parent.obj
            self.pushButton_OK.clicked.connect(
                lambda: self.__accept_params(spectra_changed=spectra_changed))

            m_name = self.measurement.name
            if m_name not in EnergySpectrumParamsDialog.checked_cuts:
                EnergySpectrumParamsDialog.checked_cuts[m_name] = []

            gutils.fill_cuts_treewidget(
                self.measurement, self.treeWidget, True,
                EnergySpectrumParamsDialog.checked_cuts[m_name])

            self.__update_eff_files()

            self.importPushButton.setVisible(False)
            self.exec_()

        else:
            header_item = QtWidgets.QTreeWidgetItem()
            header_item.setText(0, "Simulated elements")
            self.treeWidget.setHeaderItem(header_item)

            self.tof_list_tree_widget = QtWidgets.QTreeWidget()
            self.tof_list_tree_widget.setSizePolicy(
                QtWidgets.QSizePolicy.Expanding,
                QtWidgets.QSizePolicy.Expanding)

            header = QtWidgets.QTreeWidgetItem()
            header.setText(0, "Pre-calculated elements")

            self.gridLayout_2.addWidget(self.tof_list_tree_widget, 0, 1)

            self.tof_list_tree_widget.setHeaderItem(header)

            self.pushButton_OK.clicked.connect(
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
                            if "opt" in f and "opt" not in rec_name:
                                continue
                            elif "opt" in rec_name and "opt" not in f:
                                continue
                            else:
                                item = QtWidgets.QTreeWidgetItem()
                                item.setText(0, rec_name)
                                if rec_to_check and rec_to_check.prefix + "-" +\
                                   rec_to_check.name == rec_name:
                                    item.setCheckState(0, QtCore.Qt.Checked)
                                else:
                                    item.setCheckState(0, QtCore.Qt.Unchecked)
                                self.treeWidget.addTopLevelItem(item)
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

                        for file_2 in os.listdir(measurement.get_changes_dir()):
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

            self.gridLayout_2.addWidget(self.external_tree_widget, 0, 2)

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
            self.histogramTicksLabel.setText("Simulation and measurement "
                                             "histogram bin width:")

            self.importPushButton.clicked.connect(self.__import_external_file)
            self.exec_()

    def get_selected_measurements(self):
        """Returns a dictionary that contains selected measurements,
        cut files belonging to each measurement, and the corresponding
        result file.
        """
        root_for_tof_list_files = self.tof_list_tree_widget.invisibleRootItem()
        child_count = root_for_tof_list_files.childCount()

        used_measurements = {}

        for i in range(child_count):
            measurement_item = root_for_tof_list_files.child(i)
            mes_child_count = measurement_item.childCount()
            for j in range(mes_child_count):
                item = measurement_item.child(j)
                if item.checkState(0):
                    measurement = item.parent().obj
                    if len(item.text(0).split(".")) < 5:
                        # Normal cut
                        cut_file = Path(measurement.directory_cuts,
                                        f"{item.text(0)}.cut")
                    else:
                        cut_file = Path(
                            measurement.get_changes_dir(),
                            f"{item.text(0)}.cut")
                    result_file = Path(measurement.get_energy_spectra_dir(),
                                       f"{item.text(0)}.no_foil.hist")
                    used_measurements.setdefault(measurement, []).append({
                            "cut_file": cut_file,
                            "result_file": result_file
                        })

        return used_measurements

    def get_selected_simulations(self):
        """Returns a dictionary that contains selected simulations and list
        of recoil elements and corresponding result files.
        """
        root = self.treeWidget.invisibleRootItem()
        child_count = root.childCount()

        used_simulations = {}

        for i in range(child_count):
            # TODO list items should have the recoil data in user role so
            #   we do not have iterate these all over again
            item = root.child(i)
            if item.checkState(0):
                for elem_sim in self.parent.obj.element_simulations:
                    for rec_elem in elem_sim.recoil_elements:
                        rec_elem_name = rec_elem.get_full_name()
                        if rec_elem_name == item.text(0):
                            used_simulations.setdefault(elem_sim, []).append({
                                "recoil_element": rec_elem,
                            })
                            break
                    if elem_sim.is_optimization_finished():
                        for rec_elem in elem_sim.optimization_recoils:
                            rec_elem_name = rec_elem.get_full_name()
                            if rec_elem_name == item.text(0):
                                used_simulations.setdefault(
                                    elem_sim, []).append({
                                        "recoil_element": rec_elem,
                                        "optimization_type":
                                            OptimizationType.RECOIL
                                    })
                                break

        return used_simulations

    def get_selected_external_files(self):
        """Returns a list of selected external files.
        """
        # Add external files to result files
        used_external_files = []
        root_for_ext_files = self.external_tree_widget.invisibleRootItem()
        child_count = root_for_ext_files.childCount()
        for k in range(child_count):
            item = root_for_ext_files.child(k)
            if item.checkState(0):
                ext_file = Path(self.imported_files_folder, item.text(0))
                if ext_file.exists():
                    used_external_files.append(ext_file)

        return used_external_files

    def __calculate_selected_spectra(self):
        """Calculate selected spectra.
        """
        self.close()
        self.bin_width = self.histogramTicksDoubleSpinBox.value()

        sbh = StatusBarHandler(self.statusbar)

        # Get all
        used_simulations = self.get_selected_simulations()
        used_measurements = self.get_selected_measurements()
        used_externals = self.get_selected_external_files()

        sbh.reporter.report(33)

        # Calculate espes for simulations
        for elem_sim, lst in used_simulations.items():
            for d in lst:
                _, espe_file = elem_sim.calculate_espe(**d, ch=self.bin_width)
                self.result_files.append(espe_file)

        sbh.reporter.report(66)

        # Calculate espes for measurements. 'no_foil' parameter is used to
        # make the results comparable with simulation espes. Basically
        # this increases the calculated energy values, shifting the espe
        # histograms to the right on the x axis.
        for mesu, lst in used_measurements.items():
            self.result_files.extend(d["result_file"] for d in lst)
            # TODO use the return values instead of reading the files further
            #   down the execution path
            EnergySpectrum.calculate_measured_spectra(
                mesu, [d["cut_file"] for d in lst], self.bin_width,
                no_foil=True)

        # Add external files
        self.result_files.extend(used_externals)

        sbh.reporter.report(100)

        simulation_name = self.element_simulation.simulation.name
        msg = f"Created Energy Spectrum. " \
              f"Bin width: {self.bin_width} " \
              f"Used files: {', '.join(str(f) for f in self.result_files)}"

        logging.getLogger("request").info(f"[{simulation_name}] {msg}")
        logging.getLogger(simulation_name).info(msg)

    def __accept_params(self, spectra_changed=None):
        """Accept given parameters and cut files.
        """
        width = self.histogramTicksDoubleSpinBox.value()
        use_cuts = []
        root = self.treeWidget.invisibleRootItem()
        child_count = root.childCount()
        m_name = self.measurement.name
        EnergySpectrumParamsDialog.checked_cuts[m_name].clear()
        for i in range(child_count):
            item = root.child(i)
            if item.checkState(0):
                use_cuts.append(Path(item.directory, item.file_name))
                EnergySpectrumParamsDialog.checked_cuts[m_name].append(
                    item.file_name)
            child_count = item.childCount()
            if child_count > 0:  # Elemental Losses
                dir_elo = self.measurement.get_changes_dir()
                for j in range(child_count):
                    item_child = item.child(j)
                    if item_child.checkState(0):
                        use_cuts.append(
                            Path(dir_elo, item_child.file_name))
                        EnergySpectrumParamsDialog.checked_cuts[m_name].append(
                            item_child.file_name)
                EnergySpectrumParamsDialog.bin_width = width
        if use_cuts:
            self.label_status.setText("Please wait. Creating energy spectrum.")
            QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents)
            if self.parent.energy_spectrum_widget:
                self.parent.del_widget(self.parent.energy_spectrum_widget)
            self.parent.energy_spectrum_widget = EnergySpectrumWidget(
                self.parent, spectrum_type=self.spectrum_type,
                use_cuts=use_cuts,
                bin_width=width,
                statusbar=self.statusbar,
                spectra_changed=spectra_changed)

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
                    "Cut files: {0}".format(", ".join(str(cut) for cut
                                                      in use_cuts)))
                logging.getLogger("request").info(msg)
                logging.getLogger(measurement_name).info(
                    "Created Energy Spectrum. Bin width: {0} Cut files: {1}".
                    format(width, ", ".join(str(cut) for cut in use_cuts)))
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
        QtWidgets.QMessageBox.information(
            self, "Notice",
            "The external file needs to have the following format:\n\n"
            "energy count\nenergy count\nenergy count\n...\n\n"
            "to match the simulation and measurement energy spectra files.",
            QtWidgets.QMessageBox.Ok,  QtWidgets.QMessageBox.Ok)
        file_path = fdialogs.open_file_dialog(
            self, self.element_simulation.request.directory,
            "Select a file to import", "")
        if not file_path:
            return

        name = os.path.split(file_path)[1]

        for file in os.listdir(self.imported_files_folder):
            if file == name:
                QtWidgets.QMessageBox.critical(
                    self, "Error",
                    "A file with that name already exists.",
                    QtWidgets.QMessageBox.Ok,
                    QtWidgets.QMessageBox.Ok)
                return

        shutil.copyfile(
            file_path, os.path.join(self.imported_files_folder, name))

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
        detector = self.measurement.get_detector_or_default()
        eff_files = detector.get_efficiency_files()
        df.update_used_eff_file_label(self, eff_files)


class EnergySpectrumWidget(QtWidgets.QWidget):
    """Energy spectrum widget which is added to measurement tab.
    """
    save_file = "widget_energy_spectrum.save"

    def __init__(self, parent, spectrum_type, use_cuts=None, bin_width=0.025,
                 save_file_int=0, statusbar=None, spectra_changed=None):
        """Inits widget.
        
        Args:
            parent: A TabWidget.
            use_cuts: A string list representing Cut files.
            bin_width: A float representing Energy Spectrum histogram's bin
                width.
            save_file_int: n integer to have unique save file names for
                simulation energy spectra combinations.
            spectra_changed: pyqtSignal that indicates a change in energy
                spectra.
        """
        sbh = None
        try:
            super().__init__()
            uic.loadUi(Path("ui_files", "ui_energy_spectrum.ui"), self)

            self.parent = parent
            self.icon_manager = parent.icon_manager
            self.progress_bar = None
            if use_cuts is None:
                use_cuts = []
            self.use_cuts = use_cuts
            self.bin_width = bin_width
            self.energy_spectrum_data = {}
            self.spectrum_type = spectrum_type
            rbs_list = {}

            title = "{0} - Bin Width: {1}".format(self.windowTitle(),
                                                  bin_width)
            self.setWindowTitle(title)

            if isinstance(self.parent.obj, Measurement):
                self.measurement = self.parent.obj
                # Removal is done in the finally block so autoremove
                # is set to False
                sbh = StatusBarHandler(statusbar, autoremove=False)

                # Do energy spectrum stuff on this
                self.energy_spectrum_data = \
                    EnergySpectrum.calculate_measured_spectra(
                        self.measurement, use_cuts, bin_width,
                        progress=sbh.reporter
                    )

                # Check for RBS selections.
                for cut in self.use_cuts:
                    filename = os.path.basename(cut)
                    split = filename.split(".")
                    if cut_file.is_rbs(cut):
                        # This should work for regular cut and split.
                        key = "{0}.{1}.{2}.{3}".format(split[1], split[2],
                                                       split[3], split[4])
                        rbs_list[key] = cut_file.get_scatter_element(cut)

            else:
                self.simulation = self.parent.obj
                self.save_file_int = save_file_int
                self.save_file = "widget_energy_spectrum_" + str(
                    save_file_int) + ".save"
                for file in use_cuts:
                    self.energy_spectrum_data[file] = GetEspe.read_espe_file(
                        file)

            # Graph in matplotlib widget and add to window
            self.matplotlib = MatplotlibEnergySpectrumWidget(
                self, self.energy_spectrum_data, rbs_list, spectrum_type,
                spectra_changed=spectra_changed, channel_width=bin_width
            )
        except (PermissionError, IsADirectoryError, FileNotFoundError) as e:
            # If the file path points to directory, this will either raise
            # PermissionError (Windows) or IsADirectoryError (Mac)
            msg = f"Could not create Energy Spectrum graph: {e}"
            logging.getLogger(self.parent.obj.name).error(msg)

            if hasattr(self, "matplotlib"):
                self.matplotlib.delete()
            self.matplotlib = None
        finally:
            if sbh is not None:
                sbh.remove_progress_bar()

    def update_use_cuts(self):
        """Update used cuts list with new Measurement cuts.
        """
        changes_dir = self.measurement.get_changes_dir()
        df.update_cuts(
            self.use_cuts, self.measurement.directory_cuts, changes_dir)

    def delete(self):
        """Delete variables and do clean up.
        """
        if self.matplotlib is not None:
            self.matplotlib.delete()
        self.matplotlib = None
        self.close()

    def closeEvent(self, evnt):
        """Reimplemented method when closing widget.
        """
        if self.spectrum_type == "simulation":
            file = Path(self.parent.obj.directory, self.save_file)
            try:
                if os.path.isfile(file):
                    os.unlink(file)
            except:
                pass
        self.delete()
        super().closeEvent(evnt)

    def save_to_file(self, measurement=True, update=False):
        """Save object information to file.

        Args:
            measurement: Whether energy spectrum belong to measurement or
                         simulation.
            update: TODO
        """
        if measurement:
            files = "\t".join([os.path.relpath(tmp,
                                               self.measurement.directory)
                               for tmp in self.use_cuts])
            file = os.path.join(self.measurement.get_energy_spectra_dir(),
                                self.save_file)
        else:
            files = "\t".join([str(tmp) for tmp in self.use_cuts])

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
            file = Path(self.simulation.directory, file_name)

        with open(file, "wt") as fh:
            fh.write("{0}\n".format(files))
            fh.write("{0}".format(self.bin_width))
