# coding=utf-8
"""
Created on 25.3.2013
Updated on 10.4.2018

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
"""
__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen \n Samuli Rahkonen \n Miika Raunio \n" \
             "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"
__version__ = "2.0"

import logging, os, sys
from PyQt5 import uic, QtCore, QtWidgets

from modules.cut_file import is_rbs, get_scatter_element
from modules.element import Element
from modules.energy_spectrum import EnergySpectrum
from modules.null import Null
from widgets.matplotlib.measurement.energy_spectrum import MatplotlibEnergySpectrumWidget


class EnergySpectrumParamsDialog(QtWidgets.QDialog):
    checked_cuts = {}
    bin_width = 0.1
    def __init__(self, parent):
        """Inits energy spectrum dialog.
        
        Args:
            parent: MeasurementTabWidget
        """
        super().__init__()
        self.parent = parent
        self.measurement = self.parent.measurement
        self.__global_settings = self.measurement.request.global_settings
        self.ui = uic.loadUi(os.path.join("ui_files", "ui_energy_spectrum_params.ui"), self)
        
        # Connect buttons
        self.ui.pushButton_OK.clicked.connect(self.__accept_params) 
        self.ui.pushButton_Cancel.clicked.connect(self.close) 
        
        m_name = self.parent.measurement.measurement_name
        if not m_name in EnergySpectrumParamsDialog.checked_cuts.keys():
            EnergySpectrumParamsDialog.checked_cuts[m_name] = []
        parent.measurement.fill_cuts_treewidget(
            self.ui.treeWidget,
            True,
            EnergySpectrumParamsDialog.checked_cuts[m_name])
        
        width = EnergySpectrumParamsDialog.bin_width
        self.ui.histogramTicksDoubleSpinBox.setValue(width)
        
        self.__update_eff_files()
        
        if not hasattr(self.measurement, "measurement_settings"):
            QtWidgets.QMessageBox.question(self, "Warning",
                                           "Settings have not been set. Please set settings before continuing.",
                                           QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
        else:
            if not self.measurement.measurement_settings.has_been_set():
                reply = QtWidgets.QMessageBox.question(self, "Warning",
                                                       "Not all settings have been set. Do you want to continue?",
                                                       QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                                       QtWidgets.QMessageBox.No)
                if reply == QtWidgets.QMessageBox.No:
                    self.close()
                    return
            self.exec_()

    def __accept_params(self):
        """Accept given parameters and cut files.
        """
        width = self.ui.histogramTicksDoubleSpinBox.value()
        use_cuts = []
        root = self.ui.treeWidget.invisibleRootItem()
        child_count = root.childCount()
        m_name = self.parent.measurement.measurement_name
        EnergySpectrumParamsDialog.checked_cuts[m_name].clear()
        for i in range(child_count):
            item = root.child(i)
            if item.checkState(0):
                use_cuts.append(os.path.join(item.directory, item.file_name))
                EnergySpectrumParamsDialog.checked_cuts[m_name].append(
                                                                     item.file_name)
            child_count = item.childCount()
            if child_count > 0:  # Elemental Losses
                dir_elo = self.parent.measurement.directory_composition_changes
                for i in range(child_count):
                    item_child = item.child(i)
                    if item_child.checkState(0):
                        use_cuts.append(os.path.join(dir_elo, item_child.file_name))
                        EnergySpectrumParamsDialog.checked_cuts[m_name].append(
                                                               item_child.file_name)
        EnergySpectrumParamsDialog.bin_width = width
        if use_cuts:
            self.ui.label_status.setText("Please wait. Creating energy spectrum.")
            QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents)
            if self.parent.energy_spectrum_widget:
                self.parent.del_widget(self.parent.energy_spectrum_widget)
            self.parent.energy_spectrum_widget = EnergySpectrumWidget(self.parent,
                                                                      use_cuts,
                                                                      width)

            # Check that matplotlib attribute exists after creation of energy spectrum widget.
            # If it doesn't exists, that means that the widget hasn't been initialized properly
            # and the program should show an error dialog.
            if hasattr(self.parent.energy_spectrum_widget, "matplotlib"):
                icon = self.parent.icon_manager.get_icon("energy_spectrum_icon_16.png")
                self.parent.add_widget(self.parent.energy_spectrum_widget, icon=icon)
            
                measurement_name = self.parent.measurement.measurement_name
                msg = "[{0}] Created Energy Spectrum. {1} {2}".format(
                    measurement_name,
                    "Bin width: {0}".format(width),
                    "Cut files: {0}".format(", ".join(use_cuts))
                    )
                logging.getLogger("request").info(msg)
                logging.getLogger(measurement_name).info(
                    "Created Energy Spectrum. Bin width: {0} Cut files: {1}".format(
                                                             width,
                                                             ", ".join(use_cuts)))
                log_info = "Energy Spectrum graph points:\n"
                data = self.parent.energy_spectrum_widget.energy_spectrum_data
                splitinfo = "\n".join(["{0}: {1}".format(key,", ".join("({0};{1})".format(round(v[0], 2), v[1]) \
                                           for v in data[key])) for key in data.keys()])
                logging.getLogger(measurement_name).info(log_info + splitinfo)
                self.close()
            else:
                self.close()
                reply = QtWidgets.QMessageBox.critical(self, "Error",
                                                       "An error occured while trying to create energy spectrum",
                                                       QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)

    def __update_eff_files(self):
        """Update efficiency files to UI which are used.
        """
        # This is probably not the most effective way, or practical for 
        # that matter, to get all efficiency files from directory defined
        # in global settings that match the cut files of measurements.
        eff_files = self.__global_settings.get_efficiencies()
        masses = self.measurement.request.masses
        eff_files_used = []
        root = self.ui.treeWidget.invisibleRootItem()
        child_count = root.childCount()
        for eff in eff_files:
            str_element, unused_ext = eff.split(".")
            element = Element(str_element)
            for i in range(child_count): 
                item = root.child(i)
                # TODO: Perhaps make this update every time a cut file is
                # selected so user knows exactly what files are used instead
                # of what files match all the cut files.
                # if not item.checkState(0): continue
                cut_element = Element(item.file_name.split(".")[1])
                mass = cut_element.isotope.mass
                if not mass:
                    mass = round(masses.get_standard_isotope(cut_element.name),
                                 0)
                if cut_element.name == element.name \
                and mass == element.isotope.mass:
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
    
    def __init__(self, parent, use_cuts, width):
        """Inits widget.
        
        Args:
            parent: A MeasurementTabWidget.
            use_cuts: A string list representing Cut files.
            width: A float representing Energy Spectrum histogram's bin width.
        """
        try:
            super().__init__()
            self.parent = parent
            self.icon_manager = parent.icon_manager
            self.measurement = self.parent.measurement
            self.use_cuts = use_cuts
            self.width = width
            if self.measurement.statusbar:
                self.progress_bar = QtWidgets.QProgressBar()
                self.measurement.statusbar.addWidget(self.progress_bar, 1) 
                self.progress_bar.show()
                QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents)
                # Mac requires event processing to show progress bar and its 
                # process.
            else:
                self.progress_bar = None
            self.ui = uic.loadUi(os.path.join("ui_files",
                                              "ui_energy_spectrum.ui"),
                                 self)
            title = "{0} - Bin Width: {1}".format(self.ui.windowTitle(), width)
            self.ui.setWindowTitle(title)
            
            # Generate new tof.in file for external programs
            self.measurement.generate_tof_in()
            # Do energy spectrum stuff on this
            self.energy_spectrum = EnergySpectrum(self.measurement,
                                                  use_cuts,
                                                  width,
                                                  progress_bar=self.progress_bar)
            self.energy_spectrum_data = self.energy_spectrum.calculate_spectrum()
            
            # Check for RBS selections.
            rbs_list = {}
            for cut in self.use_cuts:
                filename = os.path.basename(cut)
                split = filename.split(".")
                if is_rbs(cut):
                    # This should work for regular cut and split.
                    key = "{0}.{1}.{2}".format(split[1], split[2], split[3])
                    rbs_list[key] = get_scatter_element(cut)
            
            # Graph in matplotlib widget and add to window
            self.matplotlib = MatplotlibEnergySpectrumWidget(
                                                 self,
                                                 self.energy_spectrum_data,
                                                 rbs_list)
        except:
            import traceback
            msg = "Could not create Energy Spectrum graph. "
            err_file = sys.exc_info()[2].tb_frame.f_code.co_filename
            str_err = ", ".join([sys.exc_info()[0].__name__ + ": " + traceback._some_str(sys.exc_info()[1]), err_file,
                                str(sys.exc_info()[2].tb_lineno)])
            msg += str_err
            logging.getLogger(self.measurement.measurement_name).error(msg)
            if hasattr(self, "matplotlib"):
                self.matplotlib.delete()
        finally:
            if self.progress_bar:
                self.measurement.statusbar.removeWidget(self.progress_bar)
                self.progress_bar.hide()

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
        self.parent.energy_spectrum_widget = Null()
        file = os.path.join(self.parent.measurement.directory, self.save_file)
        try:
            if os.path.isfile(file):
                os.unlink(file)
        except:
            pass
        super().closeEvent(evnt)

    def save_to_file(self):
        """Save object information to file.
        """
        files = "\t".join([tmp.replace(self.parent.measurement.directory + "\\",
                                       "") 
                           for tmp in self.use_cuts])
        file = os.path.join(self.parent.measurement.directory_energy_spectra, self.save_file)
        fh = open(file, "wt")
        fh.write("{0}\n".format(files))
        fh.write("{0}".format(self.width))
        fh.close()
