# coding=utf-8
'''
Created on 18.4.2013
Updated on 5.7.2013

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

from PyQt5 import QtGui, QtWidgets

from modules.calibration import TOFCalibrationPoint, TOFCalibrationHistogram
from widgets.matplotlib.base import MatplotlibWidget


class MatplotlibCalibrationCurveFittingWidget(MatplotlibWidget):
    '''Energy spectrum widget
    '''
    def __init__(self, parent, settings, tof_calibration, cut, masses,
                 bin_width=2.0, column=1, dialog=None):
        '''Inits Energy Spectrum widget.
        
        Args:
            parent: CalibrationCurveFittingWidget
            settings: Settings class object.
            tof_calibration: TOFCalibration class object.
            cut: CutFile class object.
            masses: Reference to element masses object of main program.
            bin_width: Histograms bin width
            column: Which column of the CutFile's data is used to create a 
                    histogram.
            dialog: parent's parent dialog.
        '''
        super().__init__(parent)
        super().fork_toolbar_buttons()
        self.canvas.manager.set_title("ToF-E Calibration - curve fitting")
        self.__fork_toolbar_buttons()
        self.dialog = dialog
        self.settings = settings
        self.cut = cut
        self.masses = masses
        self.cut_standard_mass = 0
        self.cut_standard_scatter_mass = 0
        self.bin_width = bin_width
        self.use_column = column
        
        self.tof_histogram = None
        self.tof_calibration_point = None 
        self.selection_given_manually = False
        self.canvas.mpl_connect('button_press_event', self.onclick)
        self.on_draw()

        
    def onclick(self, event):
        ''' Handles clicks on the graph
        
        Args:
            event: Mouse click event.
        '''
        if not self.selection_given_manually:
            return
        if event.button == 1:
            self.__set_calibration_point(event.xdata)                                       
            
            
            
    def __set_calibration_point(self, tof):
        self.selected_tof = tof
        self.tof_calibration_point = TOFCalibrationPoint(self.selected_tof,
                                                         self.cut,
                                                         self.masses,
                                                         self.settings)
        self.__update_dialog_values()
        self.on_draw()
        
        
    def set_calibration_point_externally(self, tof):
        '''Set calibration point.
        
        Args:
            tof: Integer representing x axis value Time of Flight [Channel].
        '''
        state = self.selection_given_manually
        self.selection_given_manually = True
        self.__set_calibration_point(tof)
        self.selection_given_manually = state
            
            
    def __update_dialog_values(self):
        """Updates the parent dialog's fields with the calculated values.
        """
        tof_channel = self.tof_calibration_point.get_tof_channel()
        tof_seconds = self.tof_calibration_point.get_tof_seconds()
        self.dialog.ui.acceptPointButton.setEnabled(True)
        if not tof_channel:
            tof_channel = "Invalid cut file parameters."
            self.dialog.ui.acceptPointButton.setEnabled(False)
        if not tof_seconds:
            tof_seconds = "Invalid cut file parameters."
            self.dialog.ui.acceptPointButton.setEnabled(False)
        self.dialog.ui.tofChannelLineEdit.setText(str(tof_channel))
        self.dialog.ui.tofSecondsLineEdit.setText(str(tof_seconds))
    
    def change_cut(self, cut):
        """Changes the cut file to be drawn and analyzed
        """
        if self.cut != cut:
            self.cut = cut 
            self.selectButton.setChecked(False)
            self.selection_given_manually = False
            self.cut_standard_mass = self.masses.get_standard_isotope(
                                                          self.cut.element.symbol)
        self.on_draw()
        
        
    def change_bin_width(self, bin_width):
        '''Change histogram bin width.
        
        Args:
            bin_width: Float representing graph bin width.
        '''
        self.bin_width = bin_width
        
    
    def on_draw(self):
        '''Draw method for matplotlib.
        '''
        self.axes.clear()
        
        if self.selection_given_manually:
            self.axes.axvline(x=self.selected_tof)

        if self.cut.element:
            self.tof_histogram = TOFCalibrationHistogram(self.cut,
                                                         self.bin_width,
                                                         self.use_column)          
            self.axes.plot(self.tof_histogram.histogram_x,
                           self.tof_histogram.histogram_y)
            
            # Get some value between the cut data's both edges.
            # middle = self.tof_histogram.find_middle()
            # params = self.tof_histogram.get_error_function_parameters(middle)
            err_start, err_end = self.tof_histogram.find_leading_edge_borders()
            params = self.tof_histogram.get_error_function_parameters(err_end,
                                                                      err_start)
            
            # Generate points for the fitted curve to be drawn.
            fit_points_x, fit_points_y = self.tof_histogram.get_curve_fit_points(
                                                                         params,
                                                                         2000)
            self.axes.plot(fit_points_x, fit_points_y, "-")
            
            
            if not self.selection_given_manually:
                # Set the now selected point to the generated one.
                # x0 is the middle point of the rising curve.
                self.selected_tof = params[0]  
                self.tof_calibration_point = TOFCalibrationPoint(self.selected_tof,
                                                                 self.cut,
                                                                 self.masses,
                                                                 self.settings)
                # Update dialog and draw a vertical line
                self.__update_dialog_values()
                self.axes.axvline(x=self.selected_tof, color="red")
            
            # TODO: Unnecessary limits?
            x_min, x_max = self.axes.get_xlim()
            y_min, y_max = self.axes.get_ylim()          
            
            # Set limits accordingly
            self.axes.set_ylim([y_min, y_max])
            self.axes.set_xlim([x_min, x_max])
        
        self.axes.set_ylabel("Intensity [Counts]")
        self.axes.set_xlabel("Time of Flight [Channel]")
         
        # Remove axis ticks
        self.remove_axes_ticks()

        # Draw magic
        self.canvas.draw()
        
        
    def toggle_clicks(self):
        '''Toggle between manual ToF channel (x axis) selection.
        '''
        self.selection_given_manually = not self.selection_given_manually
        
        
    def __fork_toolbar_buttons(self):
        '''Custom toolbar buttons be here.
        '''
        self.selectButton = QtWidgets.QToolButton(self)
        self.selectButton.clicked.connect(self.toggle_clicks)
        self.selectButton.setCheckable(True)
        self.selectButton.setIcon(QtGui.QIcon("ui_icons/reinhardt/amarok_edit.svg"))  # TODO: Make this the new way
        self.selectButton.setToolTip("Select the point manually.")
        self.mpl_toolbar.addWidget(self.selectButton)
