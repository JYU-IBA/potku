# coding=utf-8
'''
Created on 21.3.2013
Updated on 23.5.2013

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
'''
__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen \n Samuli Rahkonen \n Miika Raunio"
__versio__ = "1.0"

import os
import logging

from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5 import uic

from Dialogs.ElementLossesDialog import ElementLossesDialog
from Dialogs.EnergySpectrumDialog import EnergySpectrumParamsDialog
from Dialogs.DepthProfileDialog import DepthProfileDialog
from Dialogs.MeasurementSettingsDialogs import CalibrationSettings
from Dialogs.MeasurementSettingsDialogs import DepthProfileSettings
from Dialogs.MeasurementSettingsDialogs import MeasurementUnitSettings
from Modules.Null import Null
from Modules.UiLogHandlers import customLogHandler
from Widgets.LogWidget import LogWidget
from Widgets.TofeHistogramWidget import TofeHistogramWidget


class MeasurementTabWidget(QtWidgets.QWidget):
    '''Tab widget where measurement stuff is added.
    '''
    def __init__(self, tab_id, measurement, icon_manager):
        '''Init measurement tab class.
        
        Args:
            tab_id: Integer representing ID of the tabwidget.
            measurement: Measurement class object.
            icon_manager: IconManager class object.
        '''
        super().__init__()
        self.tab_id = tab_id
        self.ui = uic.loadUi(os.path.join("ui_files",
                                          "ui_measurement_tab.ui"), self)
        self.measurement = measurement
        self.icon_manager = icon_manager
        
        self.histogram = Null()
        self.add_histogram()
        self.elemental_losses_widget = Null()
        self.energy_spectrum_widget = Null()
        self.depth_profile_widget = Null()
        
        self.ui.settingsFrame.setVisible(False)  # Hide the measurement specific settings buttons
        
        self.ui.makeSelectionsButton.clicked.connect(
             lambda: self.histogram.matplotlib.elementSelectionButton.setChecked(
                                                                             True))
        self.ui.saveCutsButton.clicked.connect(self.measurement_save_cuts)
        self.ui.analyzeElementLossesButton.clicked.connect(
             lambda: self.open_element_losses(self))
        self.ui.energySpectrumButton.clicked.connect(
             lambda: self.open_energy_spectrum(self))
        self.ui.createDepthProfileButton.clicked.connect(
             lambda: self.open_depth_profile(self))
        self.ui.measuringUnitSettingsButton.clicked.connect(
             self.open_measuring_unit_settings)
        self.ui.depthProfileSettingsButton.clicked.connect(
             self.open_depth_profile_settings)
        self.ui.calibrationSettingsButton.clicked.connect(
             self.open_calibration_settings)
        
        
        #self.connect(self.histogram.matplotlib, QtCore.pyqtSignal("selectionsChanged(PyQt_PyObject)"), self.__set_cut_button_enabled)
        self.histogram.matplotlib.selectionsChanged.connect(self.__set_cut_button_enabled)
        # Check if there are selections in the measurement and enable save cut 
        # button. 
        self.__set_cut_button_enabled(self.measurement.selector.selections)
        
        self.panel_shown = True
        self.ui.hidePanelButton.clicked.connect(lambda: self.hide_panel())
    
    
    
    def __set_cut_button_enabled(self, selections):
        """Enables save cuts button if the given selections list's lenght is not 0.
        Otherwise disable.
        
        Args:
            selections: list of Selection objects
        """
        if len(selections) == 0:
            self.ui.saveCutsButton.setEnabled(False)
        else:
            self.ui.saveCutsButton.setEnabled(True)
    
    
    
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

        self.ui.frame.setShown(self.panel_shown)
    
    
    def measurement_save_cuts(self):
        '''Save measurement selections to cut files.
        '''
        self.measurement.save_cuts()
        
    
    def open_measuring_unit_settings(self):
        '''Opens measurement settings dialog.
        '''
        MeasurementUnitSettings(self.measurement.measurement_settings, self.measurement.project.masses)
        
        
    def open_depth_profile_settings(self):
        '''Opens depth profile settings dialog.
        '''
        DepthProfileSettings(self.measurement.measurement_settings)
    
    
    def open_calibration_settings(self):
        '''Opens calibration settings dialog.
        '''
        CalibrationSettings(self.measurement)
    
    
    def open_depth_profile(self, parent):
        '''Opens depth profile dialog.
        
        Args:
            parent: MeasurementTabWidget
        '''
        DepthProfileDialog(parent)
    
    
    def open_energy_spectrum(self, parent):
        """Opens energy spectrum dialog.
        
        Args:
            parent: MeasurementTabWidget
        """
        EnergySpectrumParamsDialog(parent)
     
    
    def open_element_losses(self, parent):
        """Opens element losses dialog.
        
        Args:
            parent: MeasurementTabWidget
        """
        ElementLossesDialog(parent)
    
    
    def add_widget(self, widget, minimized=None, has_close_button=True, icon=None):
        '''Adds a new widget to current (measurement) tab.
        
        Args:
            widget: QWidget to be added into measurement tab widget.
            minimized: Boolean representing if widget should be minimized.
            icon: QtGui.QIcon for the subwindow. 
        '''
        # QtGui.QMdiArea.addSubWindow(QWidget, flags=0)
        if has_close_button:
            subwindow = self.ui.mdiArea.addSubWindow(widget)
        else:
            subwindow = self.ui.mdiArea.addSubWindow(widget,
                                             QtCore.Qt.CustomizeWindowHint \
                                             | QtCore.Qt.WindowTitleHint \
                                             | QtCore.Qt.WindowMinMaxButtonsHint)
        if icon:
            subwindow.setWindowIcon(icon)
        subwindow.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        widget.subwindow = subwindow
        
        if minimized:
            widget.showMinimized()         
        else: 
            widget.show()
        self.__set_icons()
    
    
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
    
    
    def add_histogram(self):
        '''Adds ToF-E histogram into tab if it doesn't have one already.
        '''
        self.histogram = TofeHistogramWidget(self.measurement, self.icon_manager)
        self.measurement.set_axes(self.histogram.matplotlib.axes)
        # Draw after giving axes -> selections set properly
        self.histogram.matplotlib.on_draw()  
        if not self.measurement.selector.is_empty():
            self.histogram.matplotlib.elementSelectionSelectButton.setEnabled(True)
        self.add_widget(self.histogram, has_close_button=False)
        self.histogram.set_cut_button_enabled()
    
    
    def add_log(self):        
        '''Add the measurement log to measurement tab widget.
        
        Checks also if there's already some logging for this measurement and appends 
        the text field of the user interface with this log.
        '''
        self.log = LogWidget()
        self.add_widget(self.log, minimized=True, has_close_button=False)
        self.add_UI_logger(self.log)        
        
        # Checks for log file and appends it to the field.
        if os.path.join(self.measurement.directory, 'default.log'):
            if os.path.exists(os.path.join(self.measurement.directory,
                                           'default.log')):
                with open(os.path.join(self.measurement.directory,
                                       'default.log')) as existinglog:
                    for line in existinglog:
                        self.log.add_text(line.strip())        
        
        # Checks the error log file and appends it to the field.
        if os.path.join(self.measurement.directory, 'errors.log'):
            if os.path.exists(os.path.join(self.measurement.directory,
                                           'errors.log')):
                with open(os.path.join(self.measurement.directory,
                                       'errors.log')) as existingerrors:
                    for line in existingerrors:
                        self.log.add_error(line.strip())
    
    
    def add_UI_logger(self, log_widget):
        '''Adds handlers to measurement logger so the logger can log the events to 
        the user interface too.
        
        log_widget specifies which ui element will handle the logging. That should 
        be the one which is added to this MeasurementTabWidget.
        '''
        logger = logging.getLogger(self.measurement.measurement_name)
        defaultformat = logging.Formatter(
                                  '%(asctime)s - %(levelname)s - %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
        widgetlogger_default = customLogHandler(logging.INFO,
                                                defaultformat,
                                                log_widget)
        logger.addHandler(widgetlogger_default)
        

    def __set_icons(self):
        """Adds icons to UI elements.
        """
        self.icon_manager.set_icon(self.ui.measuringUnitSettingsButton, "measuring_unit_settings.svg")
        self.icon_manager.set_icon(self.ui.calibrationSettingsButton, "calibration_settings.svg")
        self.icon_manager.set_icon(self.ui.depthProfileSettingsButton, "gear.svg")
        self.icon_manager.set_icon(self.ui.makeSelectionsButton, "amarok_edit.svg", size=(30, 30))
        self.icon_manager.set_icon(self.ui.saveCutsButton, "save_all.svg", size=(30, 30))
        self.icon_manager.set_icon(self.ui.analyzeElementLossesButton, "elemental_losses_icon.svg", size=(30, 30))
        self.icon_manager.set_icon(self.ui.energySpectrumButton, "energy_spectrum_icon.svg", size=(30, 30))
        self.icon_manager.set_icon(self.ui.createDepthProfileButton, "depth_profile.svg", size=(30, 30))
        self.icon_manager.set_icon(self.ui.hideShowSettingsButton, "show_icon.svg", size=(30, 30))

