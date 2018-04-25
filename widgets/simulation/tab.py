# coding=utf-8
"""
Created on 1.3.2018
Updated on 11.4.2018
"""
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"
__version__ = "2.0"

import os, logging, sys
from PyQt5 import QtCore, uic, QtWidgets

from dialogs.measurement.element_losses import ElementLossesDialog, ElementLossesWidget
from dialogs.measurement.depth_profile import DepthProfileDialog, DepthProfileWidget
from widgets.simulation.target import TargetWidget
from modules.element import Element
from modules.general_functions import read_espe_file
from modules.null import Null
from modules.ui_log_handlers import customLogHandler
from modules.simulation import CallMCERD, CallGetEspe
from widgets.log import LogWidget
from widgets.simulation.energy_spectrum import SimulationEnergySpectrumWidget


class SimulationTabWidget(QtWidgets.QWidget):
    """Tab widget where simulation stuff is added.
    """
    issueMaster = QtCore.pyqtSignal()

    def __init__(self, request, tab_id, simulation, icon_manager):
        """ Init simulation tab class.
        
        Args:
            tab_id: An integer representing ID of the tabwidget.
            simulation: A simulation class object.
            icon_manager: An iconmanager class object.
        """
        super().__init__()
        self.request = request
        self.tab_id = tab_id
        self.ui = uic.loadUi(os.path.join("ui_files", "ui_simulation_tab.ui"), self)
        self.obj = simulation
        self.icon_manager = icon_manager

        self.simulation_depth_profile = None
        self.energy_spectrum_widget = None
        self.log = None

        # Hide the simulation specific settings buttons
        self.ui.settingsFrame.setVisible(False)
        
        self.data_loaded = False
        self.panel_shown = True
        self.ui.hidePanelButton.clicked.connect(lambda: self.hide_panel())

        # Set up settings and energy spectra connections within the tab UI
        self.ui.detectorSettingsButton.clicked.connect(self.open_detector_settings)
        self.ui.mcSimulationButton.clicked.connect(lambda: self.start_mcsimulation(self))

        self.simulation_started = False
        self.stop_simulation_button = None

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
        self.simulation_depth_profile = TargetWidget(self, self.icon_manager)
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
        log_default = os.path.join(self.obj.directory, 'default.log')
        log_error = os.path.join(self.obj.directory, 'errors.log')
        self.__read_log_file(log_default, 1)
        self.__read_log_file(log_error, 0)
    
    def add_UI_logger(self, log_widget):
        """ Adds handlers to simulation logger so the logger can log the events to
        the user interface too.
        
        log_widget specifies which ui element will handle the logging. That should 
        be the one which is added to this SimulationTabWidget.
        """
        logger = logging.getLogger(self.obj.simulation.name)
        defaultformat = logging.Formatter(
                                  '%(asctime)s - %(levelname)s - %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
        widgetlogger_default = customLogHandler(logging.INFO,
                                                defaultformat,
                                                log_widget)
        logger.addHandler(widgetlogger_default)
    
    def check_previous_state_files(self, progress_bar=Null(), directory=None):
        """Check if saved state for Elemental Losses, Energy Spectrum or Depth
        Profile exists. If yes, load them also.

        Args:
            progress_bar: A QtWidgets.QProgressBar where loading of previous
                          graph can be shown.
        """
        if not directory:
            directory = self.obj.directory
        self.make_elemental_losses(directory, self.obj.name)
        progress_bar.setValue(66)
        QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents)
        # Mac requires event processing to show progress bar and its
        # process.
        self.make_energy_spectrum(directory, self.obj.name)
        progress_bar.setValue(82)
        QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents)
        # Mac requires event processing to show progress bar and its
        # process.
        self.make_depth_profile(directory, self.obj.name)
        progress_bar.setValue(98)
        QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents)
        # Mac requires event processing to show progress bar and its
        # process.

    def start_mcsimulation(self, parent):
        """ Start the Monte Carlo simulation and draw energy spectrum based on it.
        Args:
            parent: Parent of the energy spectrum widget.
        """
        if self.simulation_started:
            return
        mcerd_path = os.path.join(self.request.directory, "35Cl-85-LiMnO_Li")
        self.obj.callMCERD = CallMCERD(mcerd_path)
        self.obj.callMCERD.run_simulation()
        self.simulation_started = True

        self.stop_simulation_button = QtWidgets.QPushButton("Stop the simulation")
        self.stop_simulation_button.clicked.connect(self.stop_mcsimulation)
        self.ui.verticalLayout_6.addWidget(self.stop_simulation_button)

    def stop_mcsimulation(self):
        self.obj.callMCERD.stop_simulation()
        self.simulation_started = False

        self.ui.verticalLayout_6.removeWidget(self.stop_simulation_button)
        self.stop_simulation_button.deleteLater()

        self.obj.call_get_espe = CallGetEspe(self.request.directory)
        self.obj.call_get_espe.run_get_espe()

        self.make_energy_spectrum(self.request.directory, self.obj.call_get_espe.output_file)
        # TODO: if there is already an energy spectrum, it should be removed
        self.add_widget(self.energy_spectrum_widget)
            
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
    
    def make_depth_profile(self, directory, name):
        """Make depth profile from loaded lines from saved file.
        
        Args:
            directory: A string representing directory.
            name: A string representing measurement's name.
        """
        file = os.path.join(directory, DepthProfileWidget.save_file)
        lines = self.__load_file(file)
        if not lines:
            return
        m_name = self.obj.name
        try:
            output_dir = self.__confirm_filepath(lines[0].strip(), name, m_name)
            use_cuts = self.__confirm_filepath(
                                   lines[2].strip().split("\t"), name, m_name)
            cut_names = [os.path.basename(cut) for cut in use_cuts]
            elements_string = lines[1].strip().split("\t")
            elements = [Element.from_string(element) for element in elements_string]
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
            self.depth_profile_widget = DepthProfileWidget(self,
                                                           output_dir,
                                                           use_cuts,
                                                           elements,
                                                           x_unit,
                                                           line_zero,
                                                           line_scale,
                                                           systerr)
            icon = self.icon_manager.get_icon("depth_profile_icon_2_16.png")
            self.add_widget(self.depth_profile_widget, icon=icon)
        except:  # We do not need duplicate error logs, log in widget instead
            print(sys.exc_info())  # TODO: Remove this.

    def make_elemental_losses(self, directory, name):
        """Make elemental losses from loaded lines from saved file.

        Args:
            directory: A string representing directory.
            name: A string representing measurement's name.
        """
        file = os.path.join(directory, ElementLossesWidget.save_file)
        lines = self.__load_file(file)
        if not lines:
            return
        m_name = self.obj.name
        try:
            reference_cut = self.__confirm_filepath(lines[0].strip(), name, m_name)
            checked_cuts = self.__confirm_filepath(
                                        lines[1].strip().split("\t"), name, m_name)
            cut_names = [os.path.basename(cut) for cut in checked_cuts]
            split_count = int(lines[2])
            y_scale = int(lines[3])
            ElementLossesDialog.reference_cut[m_name] = \
                                                os.path.basename(reference_cut)
            ElementLossesDialog.checked_cuts[m_name] = cut_names
            ElementLossesDialog.split_count = split_count
            ElementLossesDialog.y_scale = y_scale
            self.elemental_losses_widget = ElementLossesWidget(self,
                                                               reference_cut,
                                                               checked_cuts,
                                                               split_count,
                                                               y_scale)
            icon = self.icon_manager.get_icon("elemental_losses_icon_16.png")
            self.add_widget(self.elemental_losses_widget, icon=icon)
        except:  # We do not need duplicate error logs, log in widget instead
            print(sys.exc_info())  # TODO: Remove this.

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
    
    def __confirm_filepath(self, filepath, name, m_name):
        """Confirm whether filepath exist and changes it accordingly.
        
        Args:
            filepath: A string representing a filepath.
            name: A string representing origin measurement's name.
            m_name: A string representing measurement's name where graph is created.
        """
        if type(filepath) == str:
            # Replace two for measurement and cut file's name. Not all, in case 
            # the request or directories above it have same name.
            filepath = self.__rreplace(filepath, name, m_name, 2)
            try:
                with open(filepath):
                    pass
                return filepath
            except:
                return os.path.join(self.obj.directory, filepath)
        elif type(filepath) == list:
            newfiles = []
            for file in filepath:
                file = self.__rreplace(file, name, m_name, 2)
                try:
                    with open(file):
                        pass
                    newfiles.append(file)
                except:
                    newfiles.append(os.path.join(self.obj.directory, file))
            return newfiles

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

    def __rreplace(self, s, old, new, occurrence):
        """Replace from last occurrence.
        
        http://stackoverflow.com/questions/2556108/how-to-replace-the-last-
        occurence-of-an-expression-in-a-string
        """
        li = s.rsplit(old, occurrence)
        return new.join(li)

    def __set_icons(self):
        """Adds icons to UI elements.
        """
        # TODO: Add icons.


