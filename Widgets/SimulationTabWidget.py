# coding=utf-8
'''
Created on 1.3.2018
Updated on 15.3.2018
'''
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"

import os, logging, sys
from os.path import join
from PyQt5 import QtCore, uic, QtWidgets

from Dialogs.ElementLossesDialog import ElementLossesDialog, ElementLossesWidget
from Dialogs.DepthProfileDialog import DepthProfileDialog, DepthProfileWidget
from Modules.Element import Element
from Modules.Null import Null
from Modules.UiLogHandlers import customLogHandler
from Widgets.LogWidget import LogWidget
from Widgets.SimulationDepthProfileWidget import SimulationDepthProfileWidget
from Widgets.SimulationEnergySpectrumWidget import SimulationEnergySpectrumWidget
from Modules.Functions import read_espe_file

class SimulationTabWidget(QtWidgets.QWidget):
    """Tab widget where simulation stuff is added.
    """
    issueMaster = QtCore.pyqtSignal()

    def __init__(self, project, tab_id, simulation, masses, icon_manager):
        """ Init simulation tab class.
        
        Args:
            tab_id: An integer representing ID of the tabwidget.
            simulation: A simulation class object.
            masses: A masses class object.
            icon_manager: An iconmanager class object.
        """
        super().__init__()
        self.project = project
        self.tab_id = tab_id
        self.ui = uic.loadUi(os.path.join("ui_files", "ui_simulation_tab.ui"), self)
        self.simulation = simulation
        self.masses = masses
        self.icon_manager = icon_manager

        self.simulation_depth_profile = Null()
        self.energy_spectrum_widget = Null()
        self.log = Null()
        
        # Hide the simulation specific settings buttons
        self.ui.settingsFrame.setVisible(False)
        
        self.data_loaded = False
        self.panel_shown = True
        self.ui.hidePanelButton.clicked.connect(lambda: self.hide_panel())

        # Set up settings and energy spectra connections within the tab UI
        self.ui.detectorSettingsButton.clicked.connect(self.open_detector_settings)
        self.ui.mcSimulationButton.clicked.connect(lambda: self.start_mcsimulation(self))

    def add_widget(self, widget, minimized=None, has_close_button=True, icon=None):
        """ Adds a new widget to current simulation tab.
        
        Args:
            widget: QWidget to be added into simulation tab widget.
            minimized: Boolean representing if widget should be minimized.
            icon: QtGui.QIcon for the subwindow. 
        """
        if has_close_button:
            subwindow = self.ui.mdiArea.addSubWindow(widget)
        else:
            subwindow = self.ui.mdiArea.addSubWindow(widget, QtCore.Qt.CustomizeWindowHint | QtCore.Qt.WindowTitleHint |
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

    def add_simulation_depth_profile(self):
        """ Adds depth profile for modifying the elements into tab if it doesn't have one already.
        """
        self.simulation_depth_profile = SimulationDepthProfileWidget(self.simulation, self.masses, self.icon_manager)
        self.add_widget(self.simulation_depth_profile, has_close_button=False)
        # TODO: Do all the necessary operations so that the widget can be used.

    def add_log(self):        
        """ Add the simulation log to simulation tab widget.
        
        Checks also if there's already some logging for this measurement and appends 
        the text field of the user interface with this log.
        """
        # TODO: Perhaps add a simulation log.
        self.log = LogWidget()
        self.add_widget(self.log, minimized=True, has_close_button=False)
        self.add_UI_logger(self.log)
        
        # Checks for log file and appends it to the field.
        log_default = os.path.join(self.simulation.directory, 'default.log')
        log_error = os.path.join(self.simulation.directory, 'errors.log')
        self.__read_log_file(log_default, 1)
        self.__read_log_file(log_error, 0)
    
    def add_UI_logger(self, log_widget):
        """ Adds handlers to simulation logger so the logger can log the events to
        the user interface too.
        
        log_widget specifies which ui element will handle the logging. That should 
        be the one which is added to this SimulationTabWidget.
        """
        logger = logging.getLogger(self.simulation.simulation_name)
        defaultformat = logging.Formatter(
                                  '%(asctime)s - %(levelname)s - %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
        widgetlogger_default = customLogHandler(logging.INFO,
                                                defaultformat,
                                                log_widget)
        logger.addHandler(widgetlogger_default)
    
    def check_previous_state_files(self, progress_bar=Null(), directory=None):
        '''Check if saved state for Elemental Losses, Energy Spectrum or Depth 
        Profile exists. If yes, load them also.
        
        Args:
            progress_bar: A QtWidgets.QProgressBar where loading of previous
                          graph can be shown.
        '''
        if not directory:
            directory = self.simulation.directory
        self.make_elemental_losses(directory, self.simulation.simulation_name)
        progress_bar.setValue(66)
        QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents)
        # Mac requires event processing to show progress bar and its
        # process.
        self.make_energy_spectrum(directory, self.simulation.simulation_name)
        progress_bar.setValue(82)
        QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents)
        # Mac requires event processing to show progress bar and its
        # process.
        self.make_depth_profile(directory, self.simulation.simulation_name)
        progress_bar.setValue(98)
        QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents)
        # Mac requires event processing to show progress bar and its
        # process.

    def start_mcsimulation(self, parent):
        """ Start the Monte Carlo simulation and draw energy spectrum based on it.
        Args:
            parent: Parent of the energy spectrum widget.
        """
        directory = 'Sample-data/'
        espe_file = 'LiMnO_O.simu'
        self.make_energy_spectrum(directory, espe_file)
        self.add_widget(self.energy_spectrum_widget)
            
    def del_widget(self, widget):
        '''Delete a widget from current (measurement) tab.
        
        Args:
            widget: QWidget to be removed.
        '''
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
    
    def make_energy_spectrum(self, directory, name):
        """Make energy spectrum from loaded lines from saved file.

        Args:
            directory: A string representing directory.
            name: A string representing measurement's name.
        """
        try:
            data = read_espe_file(directory, name)
            self.energy_spectrum_widget = SimulationEnergySpectrumWidget(self, data)
            icon = self.icon_manager.get_icon("energy_spectrum_icon_16.png")
        except:  # We do not need duplicate error logs, log in widget instead
            print(sys.exc_info())  # TODO: Remove this.

    def open_detector_settings(self):
        """ Open the detector settings dialog.
        """
        QtWidgets.QMessageBox.critical(self, "Error", "Detector or other settings dialogs not yet implemented!",
                                           QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
    
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

    def __set_icons(self):
        """Adds icons to UI elements.
        """
        # TODO Add icons.


