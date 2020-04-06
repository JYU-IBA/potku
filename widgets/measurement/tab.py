# coding=utf-8
"""
Created on 21.3.2013
Updated on 18.12.2018

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

import dialogs.dialog_functions as df

from pathlib import Path

from dialogs.energy_spectrum import EnergySpectrumParamsDialog
from dialogs.energy_spectrum import EnergySpectrumWidget
from dialogs.measurement.depth_profile import DepthProfileDialog
from dialogs.measurement.depth_profile import DepthProfileWidget
from dialogs.measurement.element_losses import ElementLossesDialog
from dialogs.measurement.element_losses import ElementLossesWidget
from dialogs.measurement.settings import MeasurementSettingsDialog

from modules.element import Element
from modules.ui_log_handlers import CustomLogHandler

from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5 import uic

from widgets.log import LogWidget
from widgets.measurement.tofe_histogram import TofeHistogramWidget
from widgets.gui_utils import StatusBarHandler


class MeasurementTabWidget(QtWidgets.QWidget):
    """Tab widget where measurement stuff is added.
    """

    issueMaster = QtCore.pyqtSignal()

    def __init__(self, tab_id, measurement, icon_manager, statusbar=None):
        """Init measurement tab class.
        Args:
            tab_id: An integer representing ID of the tabwidget.
            measurement: A measurement class object.
            icon_manager: An iconmanager class object.
            statusbar: A QtGui.QMainWindow's QStatusBar.
        """
        super().__init__()
        self.tab_id = tab_id
        self.ui = uic.loadUi(Path("ui_files", "ui_measurement_tab.ui"), self)
        self.obj = measurement
        self.icon_manager = icon_manager

        self.histogram = None
        # self.add_histogram()
        self.elemental_losses_widget = None
        self.energy_spectrum_widget = None
        self.depth_profile_widget = None
        # self.check_previous_state_files()  # For above three.
        self.log = None

        self.ui.saveCutsButton.clicked.connect(self.measurement_save_cuts)

        # TODO
        self.ui.analyzeElementLossesButton.clicked.connect(
            lambda: self.open_element_losses(self))
        self.ui.energySpectrumButton.clicked.connect(
            lambda: self.open_energy_spectrum(self))
        self.ui.createDepthProfileButton.clicked.connect(
            lambda: self.open_depth_profile(self))
        self.ui.command_master.clicked.connect(self.__master_issue_commands)
        self.ui.openSettingsButton.clicked.connect(lambda:
                                                   self.__open_settings())

        self.data_loaded = False

        df.set_up_side_panel(self, "mesu_panel_shown", "right")

        # Enable master button
        self.toggle_master_button()

        self.statusbar = statusbar

    def add_widget(self, widget, minimized=None, has_close_button=True,
                   icon=None):
        """Adds a new widget to current (measurement) tab.

        Args:
            widget: QWidget to be added into measurement tab widget.
            minimized: Boolean representing if widget should be minimized.
            has_close_button: Whether widget has close button or not.
            icon: QtGui.QIcon for the subwindow.
        """
        # QtGui.QMdiArea.addSubWindow(QWidget, flags=0)
        if has_close_button:
            subwindow = self.ui.mdiArea.addSubWindow(widget)
        else:
            subwindow = self.ui.mdiArea.addSubWindow(
                widget, QtCore.Qt.CustomizeWindowHint |
                QtCore.Qt.WindowTitleHint |
                QtCore.Qt.WindowMinMaxButtonsHint)
        if icon:
            subwindow.setWindowIcon(icon)
        subwindow.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        widget.subwindow = subwindow

        if minimized:
            widget.showMinimized()
        else:
            widget.show()
        self.__set_icons()

    def add_histogram(self, progress=None, start=0.0, add=0.0):
        """Adds ToF-E histogram into tab if it doesn't have one already.

        Args:
            progress: ProgressReporter object
            start: Start value of progress bar.
            add: Value added to progress bar.
        """
        self.histogram = TofeHistogramWidget(self.obj,
                                             self.icon_manager,
                                             self,
                                             statusbar=self.statusbar)
        if progress is not None and not start:
            progress.report(40)

        self.obj.set_axes(self.histogram.matplotlib.axes, progress,
                          start, add)

        self.ui.makeSelectionsButton.clicked.connect(
            lambda: self.histogram.matplotlib.elementSelectionButton.setChecked(
                True))
        self.histogram.matplotlib.selectionsChanged.connect(
            self.__set_cut_button_enabled)

        if progress is not None and not add:
            progress.report(60)

        # Draw after giving axes -> selections set properly
        self.histogram.matplotlib.on_draw()

        if not self.obj.selector.is_empty():
            self.histogram.matplotlib.elementSelectionSelectButton.setEnabled(
                True)
        self.add_widget(self.histogram, has_close_button=False)
        self.histogram.set_cut_button_enabled()

        # Check if there are selections in the measurement and enable save cut 
        # button. 
        self.__set_cut_button_enabled(self.obj.selector.selections)

    def add_log(self):
        """Add the measurement log to measurement tab widget.

        Checks also if there's already some logging for this measurement and
        appends the text field of the user interface with this log.
        """
        self.log = LogWidget()
        self.add_widget(self.log, minimized=True, has_close_button=False)
        self.add_ui_logger(self.log)

        # Checks for log file and appends it to the field.
        log_default = os.path.join(self.obj.directory, 'default.log')
        log_error = os.path.join(self.obj.directory, 'errors.log')
        self.__read_log_file(log_default, 1)
        self.__read_log_file(log_error, 0)

    def add_ui_logger(self, log_widget):
        """Adds handlers to measurement logger so the logger can log the events
        to the user interface too.

        log_widget specifies which ui element will handle the logging. That
        should be the one which is added to this MeasurementTabWidget.
        """
        logger = logging.getLogger(self.obj.name)
        defaultformat = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S')
        widgetlogger_default = CustomLogHandler(logging.INFO,
                                                defaultformat,
                                                log_widget)
        logger.addHandler(widgetlogger_default)

    def check_previous_state_files(self, progress_bar=None):
        """Check if saved state for Elemental Losses, Energy Spectrum or Depth
        Profile exists. If yes, load them also.

        Args:
            progress_bar: A QtWidgets.QProgressBar where loading of previous
                          graph can be shown.
        """
        sample_folder_name = "Sample_" + "%02d" % \
                             self.obj.sample.serial_number + "-" + \
                             self.obj.sample.name
        directory_c = self.obj.directory_composition_changes
        self.make_elemental_losses(directory_c, self.obj.name,
                                   self.obj.serial_number,
                                   sample_folder_name)
        progress_bar.setValue(72)
        QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents)
        # Mac requires event processing to show progress bar and its
        # process.
        directory_e = self.obj.directory_energy_spectra
        self.make_energy_spectrum(directory_e, self.obj.name,
                                  self.obj.serial_number,
                                  sample_folder_name)
        progress_bar.setValue(82)
        QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents)
        # Mac requires event processing to show progress bar and its
        # process.
        directory_d = self.obj.directory_depth_profiles
        self.make_depth_profile(directory_d, self.obj.name,
                                self.obj.serial_number,
                                sample_folder_name)
        progress_bar.setValue(98)
        QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents)
        # Mac requires event processing to show progress bar and its
        # process.

    def del_widget(self, widget):
        """Delete a widget from current (measurement) tab.

        Args:
            widget: QWidget to be removed.
        """
        try:
            self.ui.mdiArea.removeSubWindow(widget.subwindow)
            widget.delete()
        except:
            # If window was manually closed, do nothing.
            pass

    def make_depth_profile(self, directory, name, serial_number_m,
                           sample_folder_name):
        """Make depth profile from loaded lines from saved file.
        
        Args:
            directory: A string representing directory to depth files.
            name: A string representing measurement's name.
            serial_number_m: Measurement's serial number.
            sample_folder_name: Sample's serial number.
        """
        file = Path(directory, DepthProfileWidget.save_file)
        lines = self.__load_file(file)
        if not lines:
            return
        m_name = self.obj.name
        try:
            old_folder_prefix = "Measurement_" + "%02d" % serial_number_m
            new_folder_prefix = "Measurement_" + "%02d" % self.obj.serial_number
            new_sample_name = "Sample_" + "%02d" % \
                              self.obj.sample.serial_number + "-" + \
                              self.obj.sample.name
            output_dir = self.__confirm_filepath(lines[0].strip(), name,
                                                 m_name, old_folder_prefix,
                                                 new_folder_prefix,
                                                 sample_folder_name,
                                                 new_sample_name)
            use_cuts = self.__confirm_filepath(
                lines[2].strip().split("\t"), name, m_name, old_folder_prefix,
                new_folder_prefix, sample_folder_name, new_sample_name)
            cut_names = [os.path.basename(cut) for cut in use_cuts]
            elements_string = lines[1].strip().split("\t")
            elements = [Element.from_string(element)
                        for element in elements_string]
            x_unit = lines[3].strip()
            line_zero = False
            line_scale = False
            if len(lines) == 7:  # "Backwards compatibility"
                line_zero = lines[4].strip() == "True"
                line_scale = lines[5].strip() == "True"
                systerr = float(lines[6].strip())
            DepthProfileDialog.x_unit = x_unit
            DepthProfileDialog.checked_cuts[m_name] = cut_names
            DepthProfileDialog.line_zero = line_zero
            DepthProfileDialog.line_scale = line_scale
            DepthProfileDialog.systerr = systerr
            self.depth_profile_widget = DepthProfileWidget(
                self, output_dir, use_cuts, elements, x_unit, line_zero,
                line_scale, systerr)
            icon = self.icon_manager.get_icon("depth_profile_icon_2_16.png")
            self.add_widget(self.depth_profile_widget, icon=icon)
        except:  # We do not need duplicate error logs, log in widget instead
            print(sys.exc_info())  # TODO: Remove this.

    def make_elemental_losses(self, directory, name, serial_number,
                              old_sample_name):
        """Make elemental losses from loaded lines from saved file.
        
        Args:
            directory: A string representing directory.
            name: A string representing measurement's name.
            serial_number: Measurement's serial number.
            old_sample_name: Sample folder of the measurement.
        """
        file = Path(directory, ElementLossesWidget.save_file)
        lines = self.__load_file(file)
        if not lines:
            return
        m_name = self.obj.name
        try:
            old_folder_prefix = "Measurement_" + "%02d" % serial_number
            new_folder_prefix = "Measurement_" + "%02d" % self.obj.serial_number
            new_sample_name = "Sample_" + "%02d" % \
                              self.obj.sample.serial_number + "-" + \
                              self.obj.sample.name
            file_path = lines[0].strip()
            if self.obj.directory in file_path:
                file_path = file_path.replace(file_path + os.sep, "")
            reference_cut = self.__confirm_filepath(file_path,
                                                    name, m_name,
                                                    old_folder_prefix,
                                                    new_folder_prefix,
                                                    old_sample_name,
                                                    new_sample_name)
            checked_cuts = self.__confirm_filepath(
                lines[1].strip().split("\t"), name, m_name, old_folder_prefix,
                new_folder_prefix, old_sample_name, new_sample_name)
            cut_names = [os.path.basename(cut) for cut in checked_cuts]
            split_count = int(lines[2])
            y_scale = int(lines[3])
            ElementLossesDialog.reference_cut[m_name] = \
                os.path.basename(reference_cut)
            ElementLossesDialog.checked_cuts[m_name] = cut_names
            ElementLossesDialog.split_count = split_count
            ElementLossesDialog.y_scale = y_scale
            self.elemental_losses_widget = ElementLossesWidget(
                self, reference_cut, checked_cuts, split_count, y_scale,
                use_progress_bar=False, statusbar=self.statusbar)
            icon = self.icon_manager.get_icon("elemental_losses_icon_16.png")
            self.add_widget(self.elemental_losses_widget, icon=icon)
        except:  # We do not need duplicate error logs, log in widget instead
            print(sys.exc_info())  # TODO: Remove this.

    def make_energy_spectrum(self, directory, name, serial_number,
                             old_sample_name):
        """Make energy spectrum from loaded lines from saved file.
        
        Args:
            directory: A string representing directory.
            name: A string representing measurement's name.
            serial_number: Measurement's serial number.
        """
        file = Path(directory, EnergySpectrumWidget.save_file)
        lines = self.__load_file(file)
        if not lines:
            return
        m_name = self.obj.name
        try:
            old_folder_prefix = "Measurement_" + "%02d" % serial_number
            new_folder_prefix = "Measurement_" + "%02d" % self.obj.serial_number
            new_sample_name = "Sample_" + "%02d" % \
                              self.obj.sample.serial_number + "-" + \
                              self.obj.sample.name
            use_cuts = self.__confirm_filepath(
                lines[0].strip().split("\t"), name, m_name, old_folder_prefix,
                new_folder_prefix, old_sample_name, new_sample_name)
            cut_names = [os.path.basename(cut) for cut in use_cuts]
            width = float(lines[1].strip())
            EnergySpectrumParamsDialog.bin_width = width
            EnergySpectrumParamsDialog.checked_cuts[m_name] = cut_names
            self.energy_spectrum_widget = EnergySpectrumWidget(
                self, spectrum_type="measurement",
                use_cuts=use_cuts,
                bin_width=width)
            icon = self.icon_manager.get_icon("energy_spectrum_icon_16.png")
            self.add_widget(self.energy_spectrum_widget, icon=icon)
        except:  # We do not need duplicate error logs, log in widget instead
            print(sys.exc_info())  # TODO: Remove this.

    def measurement_save_cuts(self):
        """Save measurement selections to cut files.
        """
        sbh = StatusBarHandler(self.statusbar)
        self.obj.save_cuts(progress=sbh.reporter)
        # Do for all slaves if master.
        self.obj.request.save_cuts(self.obj)

    def __open_settings(self):
        """Opens measurement settings dialog.
        """
        MeasurementSettingsDialog(self.obj, self.icon_manager)

    def open_depth_profile(self, parent):
        """Opens depth profile dialog.

        Args:
            parent: MeasurementTabWidget
        """
        previous = self.depth_profile_widget
        DepthProfileDialog(parent, statusbar=self.statusbar)
        if self.depth_profile_widget != previous and \
                type(self.depth_profile_widget) is not None:
            self.depth_profile_widget.save_to_file()

    def open_energy_spectrum(self, parent):
        """Opens energy spectrum dialog.
        
        Args:
            parent: MeasurementTabWidget
        """
        previous = self.energy_spectrum_widget
        EnergySpectrumParamsDialog(parent, spectrum_type="measurement",
                                   statusbar=self.statusbar)
        if self.energy_spectrum_widget != previous and \
                type(self.energy_spectrum_widget) is not None:
            self.energy_spectrum_widget.save_to_file()

    def open_element_losses(self, parent):
        """Opens element losses dialog.
        
        Args:
            parent: MeasurementTabWidget
        """
        previous = self.elemental_losses_widget
        ElementLossesDialog(parent, self.statusbar)
        if self.elemental_losses_widget != previous and \
                type(self.elemental_losses_widget) is not None:
            self.elemental_losses_widget.save_to_file()

    def toggle_master_button(self):
        """Toggle enabled state of the master measurement button in the
        measurementtabwidget.
        """
        measurement_name = self.obj.name
        master = self.obj.request.has_master()
        if master != "":
            master_name = master.name
        else:
            master_name = None
        self.ui.command_master.setEnabled(measurement_name == master_name)

    def __confirm_filepath(self, filepath, name, m_name, old_folder_prefix,
                           new_folder_prefix, old_sample_name, new_sample_name):
        """Confirm whether file path exist and changes it accordingly.

        Args:
            filepath: A string or a collection of strings representing
                      filepaths.
            name: A string representing origin measurement's name.
            m_name: A string representing measurement's name where graph is
            created.
            old_folder_prefix: Folder name of the original measurement.
            new_folder_prefix: Folder prefix of the measurement who will have
            the graph.
            old_sample_name: Sample folder name of the original measurement.
            new_sample_name: Sample folder name of the measurement who will
            have the graph.

        Return:
            either a Path object or a list of Path objects depending on the
            input type.
        """
        if type(filepath) == str:
            # Replace two for measurement and cut file's name. Not all, in case 
            # the request or directories above it have same name.
            file = self.__rreplace(filepath, name, m_name,
                                   old_folder_prefix, new_folder_prefix,
                                   old_sample_name, new_sample_name)
            return self.__validate_file_path(file)
        elif type(filepath) == list:
            newfiles = []
            for file in filepath:
                file = self.__rreplace(file, name, m_name, old_folder_prefix,
                                       new_folder_prefix, old_sample_name,
                                       new_sample_name)
                newfiles.append(self.__validate_file_path(file))
            return newfiles
        raise TypeError("Expected either a string or a list")

    def __validate_file_path(self, file_path):
        """Helper function that checks if the given file_path points to file.
        If it does, returns the file path as it was given, otherwise treats
        the file_path as a relative path and returns an absolute path within
        object's directory.
        """
        if file_path.is_file():
            return file_path
        return Path(self.obj.directory, file_path)

    def __load_file(self, file):
        """Load file

        Args:
            file: A string representing full filepath to the file.
        """
        lines = []
        try:
            with open(file, "rt") as fp:
                for line in fp:
                    lines.append(line)
        except (IOError, UnicodeDecodeError) as e:
            # TODO when opening a widget_safe_file that was saved on another
            #      platform, UnicodeDecodeError is raised. Log this.
            print(e)
        return lines

    def __master_issue_commands(self):
        """Signal that master measurement's command has been issued
        to all slave measurements in the request.
        """
        meas_name = self.obj.name
        master = self.obj.request.has_master()
        if master != "":
            master_name = master.name
        else:
            master_name = None
        if meas_name == master_name:
            self.issueMaster.emit()

    def __read_log_file(self, file, state=1):
        """Read the log file into the log window.

        Args:
            file: A string representing log file.
            state: An integer (0, 1) representing what sort of log we read.
                   0 = error
                   1 = text (default)
        """
        if os.path.exists(file):
            with open(file) as log_file:
                for line in log_file:
                    if state == 0:
                        self.log.add_error(line.strip())
                    else:
                        self.log.add_text(line.strip())

    def __rreplace(self, s, old, new, old_folder_prefix, new_folder_prefix,
                   old_sample_name, new_sample_name):
        """Replace from last occurrence.
        
        http://stackoverflow.com/questions/2556108/how-to-replace-the-last-
        occurence-of-an-expression-in-a-string

        Args:
            s: String to modify.
            old: Old name.
            new: New name.
            old_folder_prefix: Folder prefix of the old name.
            new_folder_prefix: Folder prefix of the new name.
            old_sample_name: Name of the old sample folder.
            new_sample_name: Name of the new sample folder.
        """
        li = s.rsplit(old, 2)
        if old_folder_prefix in li[0]:
            new_f = li[0].replace(old_folder_prefix, new_folder_prefix)
            li[0] = new_f
        if old_sample_name in li[0]:
            new_f = li[0].replace(old_sample_name, new_sample_name)
            li[0] = new_f
        # first = s.split(old_folder_prefix, 1)[0]
        # f_done = first + new_folder_name
        # second = s.rsplit(old, 1)[1]
        # s_done = new + second
        #
        # result = f_done + s_done
        result = new.join(li)
        if "\\" in result and not "/" in result:
            # This is a patch to make it possible to open .cut files made
            # on another os.
            # TODO it would be better to use Path when writing these paths
            #      to file in the first place
            result = result.replace("\\", "/")
        return Path(result)

    def __set_cut_button_enabled(self, selections):
        """Enables save cuts button if the given selections list's lenght is
        not 0.
        Otherwise disable.
        
        Args:
            selections: list of Selection objects
        """
        self.ui.saveCutsButton.setEnabled(len(selections))

    def __set_icons(self):
        """Adds icons to UI elements.
        """
        self.icon_manager.set_icon(self.ui.makeSelectionsButton,
                                   "amarok_edit.svg", size=(30, 30))
        self.icon_manager.set_icon(self.ui.saveCutsButton,
                                   "save_all.svg", size=(30, 30))
        self.icon_manager.set_icon(self.ui.analyzeElementLossesButton,
                                   "elemental_losses_icon.svg", size=(30, 30))
        self.icon_manager.set_icon(self.ui.energySpectrumButton,
                                   "energy_spectrum_icon.svg", size=(30, 30))
        self.icon_manager.set_icon(self.ui.createDepthProfileButton,
                                   "depth_profile.svg", size=(30, 30))
        self.icon_manager.set_icon(self.ui.command_master,
                                   "editcut.svg", size=(30, 30))
