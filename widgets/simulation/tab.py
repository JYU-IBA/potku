# coding=utf-8
"""
Created on 1.3.2018
Updated on 27.5.2019

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2018 Severi Jääskeläinen, Samuel Kaiponen, Heta Rekilä and
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
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä " \
             "\n Sinikka Siironen"
__version__ = "2.0"

import logging
import os

from collections import Counter

from dialogs.energy_spectrum import EnergySpectrumWidget
from dialogs.simulation.optimization import OptimizationDialog
from dialogs.simulation.settings import SimulationSettingsDialog

from modules.ui_log_handlers import CustomLogHandler

from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5 import uic

from widgets.log import LogWidget
from widgets.simulation.optimized_fluence import OptimizedFluenceWidget
from widgets.simulation.optimized_recoils import OptimizedRecoilsWidget
from widgets.simulation.target import TargetWidget


class SimulationTabWidget(QtWidgets.QWidget):
    """Tab widget where simulation stuff is added.
    """
    def __init__(self, request, tab_id, simulation, icon_manager):
        """ Init simulation tab class.
        
        Args:
            request: Request that has the simulation object.
            tab_id: An integer representing ID of the tab widget.
            simulation: A simulation class object.
            icon_manager: An icon manager class object.
        """
        super().__init__()
        self.request = request
        self.tab_id = tab_id
        self.simulation = simulation
        self.ui = uic.loadUi(os.path.join("ui_files", "ui_simulation_tab.ui"),
                             self)
        self.obj = simulation
        self.icon_manager = icon_manager

        self.simulation_target = None
        self.energy_spectrum_widgets = []
        self.log = None

        self.data_loaded = False
        self.panel_shown = True
        self.ui.hidePanelButton.clicked.connect(lambda: self.hide_panel())
        self.ui.openSettingsButton.clicked.connect(lambda:
                                                   self.__open_settings())
        self.ui.optimizeButton.clicked.connect(lambda:
                                               self.__open_optimization_dialog())

        self.optimization_result_widget = None

    def add_widget(self, widget, minimized=None, has_close_button=True,
                   icon=None):
        """ Adds a new widget to current simulation tab.
        
        Args:
            widget: QWidget to be added into simulation tab widget.
            minimized: Boolean representing if widget should be minimized.
            has_close_button: Will the widget have a close button or not.
            icon: QtGui.QIcon for the sub window.
        """
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

    def add_simulation_target_and_recoil(self, progress_bar=None):
        """ Add target widget for modifying the target and recoils into tab.
        Args:
            progress_bar: A progress bar used when opening an existing
            simulation.
        """
        self.simulation_target = TargetWidget(self, self.obj, self.obj.target,
                                              self.icon_manager, progress_bar)
        self.add_widget(self.simulation_target, has_close_button=False)

    def add_optimization_results_widget(self, elem_sim, measurement_elem,
                                        mode_recoil):
        """
        Add a widget that holds progress and results of optimization.

        Args:
            elem_sim: Element simulation that is being optimized.
            measurement_elem: Measured element used in optimization.
            mode_recoil: Whether recoil result widget is shown or fluence
            result widget.
        """
        if mode_recoil:
            self.optimization_result_widget = OptimizedRecoilsWidget(
                elem_sim, measurement_elem, self.obj.target)
        else:
            self.optimization_result_widget = OptimizedFluenceWidget(elem_sim)
        elem_sim.optimization_widget = self.optimization_result_widget
        icon = self.icon_manager.get_icon("potku_icon.ico")
        self.add_widget(self.optimization_result_widget)
        return self.optimization_result_widget

    def add_log(self):        
        """ Add the simulation log to simulation tab widget.
        
        Checks also if there's already some logging for this simulation
        and appends the text field of the user interface with this log.
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
        """ Adds handlers to simulation logger so the logger can log the events
        to the user interface too.
        
        log_widget specifies which ui element will handle the logging. That
        should be the one which is added to this SimulationTabWidget.
        """
        logger = logging.getLogger(self.obj.name)
        defaultformat = logging.Formatter(
                                  '%(asctime)s - %(levelname)s - %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
        widgetlogger_default = CustomLogHandler(logging.INFO,
                                                defaultformat,
                                                log_widget)
        logger.addHandler(widgetlogger_default)
    
    def check_previous_state_files(self, progress_bar):
        """Check if saved state for Energy Spectra exist.
        If yes, make widgets.

        Args:
            progress_bar: A QtWidgets.QProgressBar where loading of previous
                          graph can be shown.
        """
        self.make_energy_spectra()
        # Show optimized results if there are any
        used_measured_element = ""
        for element_simulation in self.simulation.element_simulations:
            if element_simulation.optimization_recoils:
                # Find file that contains measurement element name used in
                # optimization
                for file in os.listdir(element_simulation.directory):
                    if file.startswith(element_simulation.name_prefix) and \
                            file.endswith(".measured"):
                        with open(os.path.join(element_simulation.directory,
                                               file)) as m_f:
                            used_measured_element = m_f.readline()
                        break
                self.optimization_result_widget = OptimizedRecoilsWidget(
                    element_simulation, used_measured_element, self.obj.target)
                element_simulation.optimization_done = True
                element_simulation.optimization_widget = \
                    self.optimization_result_widget
                icon = self.icon_manager.get_icon("potku_icon.ico")
                self.add_widget(self.optimization_result_widget, icon=icon)
                break
            elif element_simulation.optimized_fluence:
                self.optimization_result_widget = OptimizedFluenceWidget(
                    element_simulation)
                element_simulation.optimization_done = True
                element_simulation.optimization_widget = \
                    self.optimization_result_widget
                icon = self.icon_manager.get_icon("potku_icon.ico")
                self.add_widget(self.optimization_result_widget, icon=icon)
                break

        progress_bar.setValue(82)
        QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents)
        # Mac requires event processing to show progress bar and its
        # process.

    def make_energy_spectra(self):
        """
        Make corresponding energy spectra for each save file in simulation
        directory.
        """
        save_energy_spectrum = False
        for file in os.listdir(self.simulation.directory):
            if file.endswith(".save"):
                file_path = os.path.join(self.simulation.directory, file)
                save_file_int = file.rsplit('_', 1)[1].split(".save")[0]
                lines = []
                with open(file_path, 'r') as save_file:
                    lines = save_file.readlines()
                if not lines:
                    return
                used_files = lines[0].strip().split("\t")
                used_files_confirmed = []
                for u_f in used_files:
                    if os.path.exists(u_f):
                        used_files_confirmed.append(u_f)
                if Counter(used_files) != Counter(used_files_confirmed):
                    save_energy_spectrum = True
                bin_width = float(lines[1].strip())
                icon = self.icon_manager.get_icon("energy_spectrum_icon_16.png")
                energy_spectrum_widget = EnergySpectrumWidget(
                    self, "simulation", used_files_confirmed, bin_width,
                    save_file_int)
                self.energy_spectrum_widgets.append(energy_spectrum_widget)
                self.add_widget(energy_spectrum_widget, icon=icon)

                if save_energy_spectrum:
                    energy_spectrum_widget.save_to_file(measurement=False,
                                                        update=True)
            
    def del_widget(self, widget):
        """Delete a widget from current tab.

        Args:
            widget: QWidget to be removed.
        """
        try:
            self.ui.mdiArea.removeSubWindow(widget.subwindow)
            widget.delete()
        except:
            # If window was manually closed, do nothing.
            pass
    
    def hide_panel(self, enable_hide=None):
        """Sets the frame (including all the tool buttons) visible.
        
        Args:
            enable_hide: If True, sets the frame visible and vice versa. 
                         If not given, sets the frame visible or hidden 
                         depending its previous state.
        """
        if enable_hide is not None:
            self.panel_shown = enable_hide
        else:
            self.panel_shown = not self.panel_shown    
        if self.panel_shown:
            self.ui.hidePanelButton.setText('>')
        else:
            self.ui.hidePanelButton.setText('<')

        self.ui.frame.setVisible(self.panel_shown)

    def __open_settings(self):
        SimulationSettingsDialog(self, self.simulation, self.icon_manager)

    def __open_optimization_dialog(self):
        OptimizationDialog(self.simulation, self)

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
