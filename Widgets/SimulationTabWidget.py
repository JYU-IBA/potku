# coding=utf-8
'''
Created on 1.3.2018
Updated on 5.3.2018
'''
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"

import os, logging, sys
from PyQt5 import QtCore, uic, QtWidgets

from Dialogs.ElementLossesDialog import ElementLossesDialog, ElementLossesWidget
from Dialogs.EnergySpectrumDialog import EnergySpectrumParamsDialog, EnergySpectrumWidget
from Dialogs.DepthProfileDialog import DepthProfileDialog, DepthProfileWidget
from Modules.Element import Element
from Modules.Null import Null
from Modules.UiLogHandlers import customLogHandler
from Widgets.LogWidget import LogWidget
from Widgets.SimulationDepthProfileWidget import SimulationDepthProfileWidget
from Widgets.SimulationEnergySpectrumWidget import SimulationEnergySpectrumWidget

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
        #self.simulation_depth_profile = SimulationDepthProfileWidget(self.simulation, self.masses, self.icon_manager)
        self.simulation_depth_profile = SimulationDepthProfileWidget(self.simulation, self.masses, self.icon_manager)
        self.add_widget(self.simulation_depth_profile, has_close_button=False)
        # TODO: Do all the necessary operations so that the widget can be used.
        # self.simulation.set_axes(self.simulation_depth_profile.matplotlib.axes)
        # self.ui.makeSelectionsButton.clicked.connect(
        #    lambda: self.simulation_depth_profile.matplotlib.elementSelectionButton.setChecked(True))
        # self.simulation_depth_profile.matplotlib.selectionsChanged.connect(self.__set_cut_button_enabled)

        # Draw after giving axes -> selections set properly
        # self.simulation_depth_profile.matplotlib.on_draw()
        # if not self.measurement.selector.is_empty():
        #    self.simulation_depth_profile.matplotlib.elementSelectionSelectButton.setEnabled(True)
        # self.add_widget(self.simulation_depth_profile, has_close_button=False)
        # self.simulation_depth_profile.set_cut_button_enabled()
                
        # Check if there are selections in the measurement and enable save cut 
        # button. 
        # self.__set_cut_button_enabled(self.measurement.selector.selections)
    
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
        """ Start the Monte Catrlo simulation and draw energy spectrum based on it.
        Args:
            parent: Parent of the energy spectrum widget.
        """
        self.energy_spectrum_widget = SimulationEnergySpectrumWidget(self)
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
        if enable_hide != None:
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
        m_name = self.simulation.simulation_name
        try:
            output_dir = self.__confirm_filepath(lines[0].strip(), name, m_name)
            use_cuts = self.__confirm_filepath(
                                   lines[2].strip().split("\t"), name, m_name)
            cut_names = [os.path.basename(cut) for cut in use_cuts]
            elements_string = lines[1].strip().split("\t")
            elements = [Element(element) for element in elements_string]
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
        m_name = self.simulation.simulation_name
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
        file = os.path.join(directory, EnergySpectrumWidget.save_file)
        lines = self.__load_file(file)
        if not lines:
            return
        m_name = self.simulation.simulation_name
        try:
            use_cuts = self.__confirm_filepath(
                                   lines[0].strip().split("\t"), name, m_name)
            cut_names = [os.path.basename(cut) for cut in use_cuts]
            width = float(lines[1].strip())
            EnergySpectrumParamsDialog.bin_width = width
            EnergySpectrumParamsDialog.checked_cuts[m_name] = cut_names
            self.energy_spectrum_widget = EnergySpectrumWidget(self,
                                                               use_cuts,
                                                               width)
            icon = self.icon_manager.get_icon("energy_spectrum_icon_16.png")
            self.add_widget(self.energy_spectrum_widget, icon=icon)
        except:  # We do not need duplicate error logs, log in widget instead
            print(sys.exc_info())  # TODO: Remove this.

    # def open_energy_spectrum(self, parent):
    #     """Opens energy spectrum dialog.
    #
    #     Args:
    #         parent: MeasurementTabWidget
    #     """
    #     previous = self.energy_spectrum_widget
    #     EnergySpectrumParamsDialog(parent)
    #     if self.energy_spectrum_widget != previous and \
    #         type(self.energy_spectrum_widget) != Null:
    #         self.energy_spectrum_widget.save_to_file()

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
            # the project or directories above it have same name.
            filepath = self.__rreplace(filepath, name, m_name, 2)
            try:
                with open(filepath):
                    pass
                return filepath
            except:
                return os.path.join(self.simulation.directory, filepath)
        elif type(filepath) == list:
            newfiles = []
            for file in filepath:
                file = self.__rreplace(file, name, m_name, 2)
                try:
                    with open(file):
                        pass
                    newfiles.append(file)
                except:
                    newfiles.append(os.path.join(self.simulation.directory, file))
            return newfiles

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
        except:
            pass
        return lines

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
        # self.icon_manager.set_icon(self.ui.measuringUnitSettingsButton,
        #                            "measuring_unit_settings.svg")
        # self.icon_manager.set_icon(self.ui.calibrationSettingsButton,
        #                            "calibration_settings.svg")
        # self.icon_manager.set_icon(self.ui.depthProfileSettingsButton, "gear.svg")
        # self.icon_manager.set_icon(self.ui.makeSelectionsButton,
        #                            "amarok_edit.svg", size=(30, 30))
        # self.icon_manager.set_icon(self.ui.saveCutsButton,
        #                            "save_all.svg", size=(30, 30))
        # self.icon_manager.set_icon(self.ui.analyzeElementLossesButton,
        #                            "elemental_losses_icon.svg", size=(30, 30))
        # self.icon_manager.set_icon(self.ui.energySpectrumButton,
        #                            "energy_spectrum_icon.svg", size=(30, 30))
        # self.icon_manager.set_icon(self.ui.createDepthProfileButton,
        #                            "depth_profile.svg", size=(30, 30))
        # self.icon_manager.set_icon(self.ui.hideShowSettingsButton,
        #                            "show_icon.svg", size=(30, 30))



