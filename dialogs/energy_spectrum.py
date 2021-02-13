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
Sinikka Siironen, 2020 Juhani Sundell

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
             "Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen \n " \
             "Juhani Sundell"
__version__ = "2.0"

import os
import shutil

import dialogs.dialog_functions as df
import widgets.gui_utils as gutils
import modules.cut_file as cut_file
import dialogs.file_dialogs as fdialogs
import widgets.binding as bnd

from pathlib import Path
from typing import Optional

from widgets.gui_utils import StatusBarHandler
from widgets.base_tab import BaseTab
from modules.energy_spectrum import EnergySpectrum
from modules.measurement import Measurement
from modules.get_espe import GetEspe
from modules.enums import OptimizationType
from modules.element_simulation import ElementSimulation
from modules.simulation import Simulation

from PyQt5 import uic
from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5.QtCore import QLocale

from widgets.matplotlib.measurement.energy_spectrum import \
    MatplotlibEnergySpectrumWidget

_MESU = "measurement"
_SIMU = "simulation"


class EnergySpectrumParamsDialog(QtWidgets.QDialog):
    """An EnergySpectrumParamsDialog.
    """

    checked_cuts = {}
    bin_width = 0.025

    use_efficiency = bnd.bind("use_eff_checkbox")
    status_msg = bnd.bind("label_status")
    measurement_cuts = bnd.bind("treeWidget")
    used_bin_width = bnd.bind("histogramTicksDoubleSpinBox")

    external_files = bnd.bind("external_tree_widget")
    tof_list_files = bnd.bind("tof_list_tree_widget")
    used_recoil = bnd.bind("treeWidget")

    def __init__(self, parent: BaseTab, spectrum_type: str = _MESU,
                 element_simulation: Optional[ElementSimulation] = None,
                 simulation: Optional[Simulation] = None,
                 measurement: Optional[Measurement] = None,
                 recoil_widget=None,
                 statusbar: Optional[QtWidgets.QStatusBar] = None,
                 spectra_changed=None):
        """Inits energy spectrum dialog.
        
        Args:
            parent: A TabWidget.
            spectrum_type: Whether spectrum is for measurement of simulation.
            element_simulation: ElementSimulation object.
            recoil_widget: RecoilElement widget.
            statusbar: QStatusBar
            spectra_changed: pyQtSignal that is emitted when recoil atom
                distribution is changed.
        """
        super().__init__()
        uic.loadUi(gutils.get_ui_dir() / "ui_energy_spectrum_params.ui", self)

        self.parent = parent
        if spectrum_type == EnergySpectrumWidget.MEASUREMENT:
            if measurement is None:
                raise ValueError(
                    f"Must provide a Measurement when spectrum type is "
                    f"{spectrum_type}")
        elif spectrum_type is EnergySpectrumWidget.SIMULATION:
            if simulation is None:
                raise ValueError(
                    f"Must provide a Simulation when spectrum type is "
                    f"{spectrum_type}")
            if element_simulation is None:
                raise ValueError(
                    f"Must provide an ElementSimulation when spectrum is "
                    f"{spectrum_type}"
                )
        else:
            raise ValueError(f"Unexpected spectrum type: {spectrum_type}")

        self.spectrum_type = spectrum_type
        self.measurement = measurement
        self.simulation = simulation
        self.element_simulation = element_simulation
        self.statusbar = statusbar
        self.result_files = []

        self.use_eff_checkbox.stateChanged.connect(
            lambda *_: self.label_efficiency_files.setEnabled(
                self.use_efficiency))
        self.use_efficiency = True

        locale = QLocale.c()
        self.histogramTicksDoubleSpinBox.setLocale(locale)

        # Connect buttons
        self.pushButton_Cancel.clicked.connect(self.close)

        self.external_tree_widget = QtWidgets.QTreeWidget()

        if self.spectrum_type == EnergySpectrumWidget.MEASUREMENT:
            EnergySpectrumParamsDialog.bin_width = \
                self.measurement.profile.channel_width
            self.pushButton_OK.clicked.connect(
                lambda: self.__accept_params(spectra_changed=spectra_changed))

            m_name = self.measurement.name
            if m_name not in EnergySpectrumParamsDialog.checked_cuts:
                EnergySpectrumParamsDialog.checked_cuts[m_name] = set()

            gutils.fill_cuts_treewidget(
                self.measurement, self.treeWidget.invisibleRootItem(),
                use_elemloss=True)
            self.measurement_cuts = \
                EnergySpectrumParamsDialog.checked_cuts[m_name]

            self.importPushButton.setVisible(False)
        else:
            EnergySpectrumParamsDialog.bin_width = \
                self.element_simulation.channel_width

            self._set_simulation_files(recoil_widget)
            self._set_measurement_files()
            self._set_external_files()

            # Change the bin width label text
            self.histogramTicksLabel.setText(
                "Simulation and measurement histogram bin width:")

            self.pushButton_OK.clicked.connect(
                self.__calculate_selected_spectra)
            self.importPushButton.clicked.connect(self.__import_external_file)

        self.used_bin_width = EnergySpectrumParamsDialog.bin_width
        # FIXME .eff files not shown in sim mode
        self.__update_eff_files()
        self.exec_()

    def showEvent(self, event):
        """Adjust size after dialog has been shown.
        """
        self.adjustSize()
        super().showEvent(event)

    def _set_simulation_files(self, recoil_widget):
        """Sets up the simulation files in a QTreeWidget.
        """
        header_item = QtWidgets.QTreeWidgetItem()
        header_item.setText(0, "Simulated element (observed atoms)")
        self.treeWidget.setHeaderItem(header_item)

        for elem_sim in self.simulation.element_simulations:
            root = QtWidgets.QTreeWidgetItem([
                f"{elem_sim.get_full_name()} ({elem_sim.get_atom_count()})"
            ])
            gutils.fill_tree(
                root, elem_sim.recoil_elements,
                data_func=lambda rec: (elem_sim, rec, None),
                text_func=lambda rec: rec.get_full_name()
            )
            if elem_sim.is_optimization_finished():
                gutils.fill_tree(
                    root, elem_sim.optimization_recoils,
                    data_func=lambda rec: (
                        elem_sim, rec, OptimizationType.RECOIL),
                    text_func=lambda rec: rec.get_full_name()
                )
            self.treeWidget.addTopLevelItem(root)
            root.setExpanded(True)

        self.used_recoil = {(
            recoil_widget.element_simulation, recoil_widget.recoil_element, None
        )}

    def _set_measurement_files(self):
        """Sets up the .cut file list.
        """
        self.tof_list_tree_widget = QtWidgets.QTreeWidget()
        self.tof_list_tree_widget.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding)
        header = QtWidgets.QTreeWidgetItem()
        header.setText(0, "Pre-calculated elements")
        self.gridLayout_2.addWidget(self.tof_list_tree_widget, 0, 1)
        self.tof_list_tree_widget.setHeaderItem(header)

        # Add calculated tof_list files to tof_list_tree_widget by
        # measurement under the same sample.
        for measurement in self.simulation.sample.get_measurements():
            root = QtWidgets.QTreeWidgetItem([measurement.name])

            cuts, elem_loss = measurement.get_cut_files()
            gutils.fill_tree(
                root, cuts, data_func=lambda c: (c, measurement),
                text_func=lambda c: c.name)

            self.tof_list_tree_widget.addTopLevelItem(root)

            elem_loss_root = QtWidgets.QTreeWidgetItem(["Element losses"])
            gutils.fill_tree(
                elem_loss_root, elem_loss, data_func=lambda c: (c, measurement),
                text_func=lambda c: c.name
            )
            root.addChild(elem_loss_root)
            root.setExpanded(True)

        self.tof_list_files = {}

    def _set_external_files(self):
        """Sets up the external file QTreeWidget.
        """
        # Add a view for adding external files to draw
        self.external_tree_widget.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding)
        header = QtWidgets.QTreeWidgetItem()
        header.setText(0, "External files")
        self.gridLayout_2.addWidget(self.external_tree_widget, 0, 2)
        self.external_tree_widget.setHeaderItem(header)

        gutils.fill_tree(
            self.external_tree_widget.invisibleRootItem(),
            self.simulation.request.get_imported_files(),
            text_func=lambda fp: fp.name
        )

        self.external_files = {}

    def get_selected_measurements(self):
        """Returns a dictionary that contains selected measurements,
        cut files belonging to each measurement, and the corresponding
        result file.
        """
        mesus = self.tof_list_files
        used_measurements = {}
        # TODO result file is probably not needed here
        for c, m in mesus:
            used_measurements.setdefault(m, []).append({
                "cut_file": c,
                "result_file": Path(
                    m.get_energy_spectra_dir(), f"{c.stem}.no_foil.hist")
            })
        return used_measurements

    def get_selected_simulations(self):
        """Returns a dictionary that contains selected simulations and list
        of recoil elements and corresponding result files.
        """
        used_simulations = {}
        for elem_sim, rec, optim in self.used_recoil:
            # TODO optim type may not be necessary
            used_simulations.setdefault(elem_sim, []).append({
                "recoil_element": rec,
                "optimization_type": optim
            })
        return used_simulations

    @gutils.disable_widget
    def __calculate_selected_spectra(self, *_):
        """Calculate selected spectra.
        """
        EnergySpectrumParamsDialog.bin_width = self.used_bin_width

        sbh = StatusBarHandler(self.statusbar)

        # Get all
        used_simulations = self.get_selected_simulations()
        used_measurements = self.get_selected_measurements()
        used_externals = self.external_files

        sbh.reporter.report(33)

        # Calculate espes for simulations
        for elem_sim, lst in used_simulations.items():
            for d in lst:
                _, espe_file = elem_sim.calculate_espe(
                    **d, write_to_file=True, ch=self.bin_width)
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
                use_efficiency=self.use_efficiency, no_foil=True)

        # Add external files
        self.result_files.extend(used_externals)

        sbh.reporter.report(100)

        msg = f"Created Energy Spectrum. " \
              f"Bin width: {self.bin_width} " \
              f"Used files: {', '.join(str(f) for f in self.result_files)}"

        self.element_simulation.simulation.log(msg)
        self.simulation.log(msg)
        self.close()

    @gutils.disable_widget
    def __accept_params(self, spectra_changed=None):
        """Accept given parameters and cut files.
        """
        self.status_msg = ""
        width = self.used_bin_width
        m_name = self.measurement.name
        selected_cuts = self.measurement_cuts
        EnergySpectrumParamsDialog.checked_cuts[m_name] = set(
            self.measurement_cuts)
        EnergySpectrumParamsDialog.bin_width = width

        if selected_cuts:
            self.status_msg = "Please wait. Creating energy spectrum."
            if self.parent.energy_spectrum_widget:
                self.parent.del_widget(self.parent.energy_spectrum_widget)
            self.parent.energy_spectrum_widget = EnergySpectrumWidget(
                self.parent, spectrum_type=self.spectrum_type,
                use_cuts=selected_cuts, bin_width=width,
                use_efficiency=self.use_efficiency,
                statusbar=self.statusbar, spectra_changed=spectra_changed)

            # Check that matplotlib attribute exists after creation of energy
            # spectrum widget.
            # If it doesn't exists, that means that the widget hasn't been
            # initialized properly and the program should show an error dialog.
            if hasattr(self.parent.energy_spectrum_widget, "matplotlib_layout"):
                icon = self.parent.icon_manager.get_icon(
                    "energy_spectrum_icon_16.png")
                self.parent.add_widget(self.parent.energy_spectrum_widget,
                                       icon=icon)

                cuts = ", ".join(str(cut) for cut in selected_cuts)
                msg = f"Created Energy Spectrum. " \
                      f"Bin width: {width}. " \
                      f"Cut files: {cuts}"
                self.measurement.log(msg)
                log_info = "Energy Spectrum graph points:\n"
                data = self.parent.energy_spectrum_widget.energy_spectrum_data
                splitinfo = "\n".join(["{0}: {1}".format(key, ", ".join(
                    "({0};{1})".format(round(v[0], 2), v[1])
                    for v in data[key])) for key in data.keys()])
                self.measurement.log(log_info + splitinfo)
            else:
                QtWidgets.QMessageBox.critical(
                    self, "Error",
                    "An error occurred while trying to create energy spectrum.",
                    QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            self.close()
        else:
            self.status_msg = "Please select .cut file[s] to create energy " \
                              "spectra."

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

        file_path = Path(file_path)
        name = file_path.name

        new_file_name = \
            self.element_simulation.request.get_imported_files_folder() / name

        if new_file_name.exists():
            QtWidgets.QMessageBox.critical(
                self, "Error", "A file with that name already exists.",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return

        shutil.copyfile(file_path, new_file_name)

        item = QtWidgets.QTreeWidgetItem()
        item.setText(0, new_file_name.name)
        item.setData(0, QtCore.Qt.UserRole, new_file_name)
        item.setCheckState(0, QtCore.Qt.Checked)
        self.external_tree_widget.addTopLevelItem(item)

    def __update_eff_files(self):
        """Update efficiency files to UI which are used.
        """
        if self.spectrum_type == _SIMU:
            # Simulation energy spectrum can contain cut files from multiple
            # Measurements which each can have different Detector an thus
            # different efficiency files
            label_txt = df.get_multi_efficiency_text(
                self.tof_list_tree_widget,
                self.simulation.sample.get_measurements(),
                data_func=lambda tpl: tpl[0])
        else:
            detector = self.measurement.get_detector_or_default()
            label_txt = df.get_efficiency_text(self.treeWidget, detector)

        self.label_efficiency_files.setText(label_txt)


class EnergySpectrumWidget(QtWidgets.QWidget):
    """Energy spectrum widget which is added to measurement tab.
    """
    MEASUREMENT = _MESU
    SIMULATION = _SIMU

    save_file = "widget_energy_spectrum.save"

    def __init__(self, parent: BaseTab,
                 spectrum_type: str = MEASUREMENT,
                 use_cuts=None, bin_width=0.025, use_efficiency=False,
                 save_file_int=0, statusbar=None, spectra_changed=None):
        """Inits widget.
        
        Args:
            parent: A TabWidget.
            use_cuts: A string list representing Cut files.
            bin_width: A float representing Energy Spectrum histogram's bin
                width.
            use_efficiency: whether efficiency is taken into account when
                measured spectra is calculated
            save_file_int: n integer to have unique save file names for
                simulation energy spectra combinations.
            spectra_changed: pyqtSignal that indicates a change in energy
                spectra.
        """
        sbh = None
        super().__init__()
        uic.loadUi(gutils.get_ui_dir() / "ui_energy_spectrum.ui", self)
        try:
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

            title = f"{self.windowTitle()} - Bin Width: {bin_width}"
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
                        progress=sbh.reporter, use_efficiency=use_efficiency
                    )

                # Check for RBS selections.
                rbs_list = cut_file.get_rbs_selections(self.use_cuts)
            else:
                self.simulation = self.parent.obj
                self.save_file_int = save_file_int
                self.save_file = f"widget_energy_spectrum_{save_file_int}.save"
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
            self.parent.obj.log_error(msg)

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
            self.use_cuts, self.measurement.get_cuts_dir(), changes_dir)

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
        if self.spectrum_type == EnergySpectrumWidget.SIMULATION:
            file = Path(self.parent.obj.directory, self.save_file)
            try:
                file.unlink()
            except OSError:
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
            files = "\t".join([
                os.path.relpath(tmp, self.measurement.directory)
                for tmp in self.use_cuts])
            file = Path(
                self.measurement.get_energy_spectra_dir(), self.save_file)
        else:
            files = "\t".join([str(tmp) for tmp in self.use_cuts])

            file_name = f"widget_energy_spectrum_{self.save_file_int}.save"
            if self.save_file_int == 0 or not update:
                i = 1
                file_name = f"widget_energy_spectrum_{i}.save"
                while Path(self.simulation.directory, file_name).exists():
                    i += 1
                    file_name = f"widget_energy_spectrum_{i}.save"
                self.save_file_int = i
            self.save_file = file_name
            file = Path(self.simulation.directory, file_name)

        try:
            with file.open("w") as fh:
                fh.write("{0}\n".format(files))
                fh.write("{0}".format(self.bin_width))
        except OSError:
            pass
