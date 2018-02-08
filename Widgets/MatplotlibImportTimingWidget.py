# coding=utf-8
'''
Created on 6.6.2013
Updated on 29.8.2013

Potku is a graphical user interface for analyzation and 
visualization of measurement data collected from a ToF-ERD 
telescope. For physics calculations Potku uses external 
analyzation components.  
Copyright (C) Timo Konu

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
__author__ = "Timo Konu"
__versio__ = "1.0"

from PyQt4 import QtGui

from Widgets.MatplotlibWidget import MatplotlibWidget


class MatplotlibImportTimingWidget(MatplotlibWidget):
    def __init__(self, parent, output_file, icon_manager, timing):
        '''Inits import timings widget
        
        Args:
            parent: An ImportTimingGraphDialog class object.
            output_file: A string representing file to be graphed.
            icon_manager: An IconManager class object.
            timing: A tuple representing low & high timing limits.
        '''
        super().__init__(parent)
        super().fork_toolbar_buttons()
        self.canvas.manager.set_title("Import coincidence timing")
        self.icon_manager = icon_manager
        # TODO: Multiple timings ?
        timing_key = list(timing.keys())[0]
        self.__limit_low, self.__limit_high = timing[timing_key] 
        self.__title = self.main_frame.windowTitle()
        self.__fork_toolbar_buttons()
        self.canvas.mpl_connect('button_press_event', self.on_click)
        self.main_frame.setWindowTitle("{0} - Timing: ADC {3} ({1},{2})".format(
                                                       self.__title,
                                                       self.__limit_low,
                                                       self.__limit_high,
                                                       timing_key))
        self.__limit_prev = 0
        self.data = []
        with open(output_file) as fp:
            for line in fp:
                if not line:  # Can still result in empty lines at the end, skip.
                    continue
                split = line.strip().split("\t")
                time_diff = int(split[3])
                # if time_diff < 0:
                #    time_diff *= -1
                self.data.append(time_diff)
        self.data = sorted(self.data) 
        self.on_draw()
        
        
    def on_draw(self):
        '''Draws the timings graph
        '''
        self.axes.clear()
        
        self.axes.hist(self.data, 200, facecolor='green', histtype='stepfilled')
        self.axes.set_yscale('log', nonposy='clip')
        
        self.axes.set_xlabel("Timedifference (µs?)")
        self.axes.set_ylabel("Count (?)")    
            
        if self.__limit_low:
            self.axes.axvline(self.__limit_low, linestyle="--")
        if self.__limit_high:
            self.axes.axvline(self.__limit_high, linestyle="--")
            
        self.remove_axes_ticks()
        self.canvas.draw_idle()
        
    
    def on_click(self, event):
        '''Handles clicks on the graph.
        
        Args:
            event: A click event on the graph
        '''
        if event.button == 1 and self.limButton.isChecked():
            value = int(event.xdata)
            if value == self.__limit_high or value == self.__limit_low:
                return
            if self.__limit_prev:
                self.__limit_high = value
                self.__limit_prev = 0
            else:
                self.__limit_low = value
                self.__limit_prev = 1
            
            # Check these values are correctly ordered
            if self.__limit_high < self.__limit_low:
                self.__limit_low, self.__limit_high = \
                self.__limit_high, self.__limit_low

            # Set values to parent dialog (main_frame = ImportTimingGraphDialog)
            self.main_frame.timing_low.setValue(self.__limit_low)
            self.main_frame.timing_high.setValue(self.__limit_high)
            self.main_frame.setWindowTitle("{0} - Timing: ({1},{2})".format(
                                                       self.__title,
                                                       self.__limit_low,
                                                       self.__limit_high))
            self.on_draw()


    def __fork_toolbar_buttons(self):
        '''Custom toolbar buttons be here.
        '''
        self.__tool_label = self.mpl_toolbar.children()[24]
        self.__button_drag = self.mpl_toolbar.children()[12]
        self.__button_zoom = self.mpl_toolbar.children()[14]
        self.__button_drag.clicked.connect(self.__uncheck_custom_buttons)
        self.__button_zoom.clicked.connect(self.__uncheck_custom_buttons)
        
        self.limButton = QtGui.QToolButton(self)
        self.limButton.clicked.connect(self.__limit_button_click)
        self.limButton.setCheckable(True)
        self.limButton.setToolTip("Change timing's low and high limits for more accurate coincidence reading.")
        self.icon_manager.set_icon(self.limButton, "amarok_edit.svg")
        self.mpl_toolbar.addWidget(self.limButton)


    def __limit_button_click(self):
        '''Click event on limit button.
        '''
        if self.limButton.isChecked():
            self.__uncheck_built_in_buttons()
            self.__tool_label.setText("timing limit tool")
            self.mpl_toolbar.mode = "timing limit tool"
        else:
            self.__tool_label.setText("")
            self.mpl_toolbar.mode = ""


    def __uncheck_custom_buttons(self):
        self.limButton.setChecked(False)
    
    
    def __uncheck_built_in_buttons(self):
        self.__button_drag.setChecked(False)
        self.__button_zoom.setChecked(False)
        self.__tool_label.setText("")
        self.mpl_toolbar.mode = ""
