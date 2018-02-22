# coding=utf-8
'''
Created on 17.4.2013
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

MatplotlibDepthProfileWidget handles the drawing and operation of the 
depth profile graph.
'''
__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen \n Samuli Rahkonen \n Miika Raunio"
__versio__ = "1.0"

from PyQt4 import QtGui
from Widgets.MatplotlibWidget import MatplotlibWidget
import Modules.DepthFiles as df
import os
import re

class MatplotlibDepthProfileWidget(MatplotlibWidget):
    '''
    Depth profile widget
    '''
    def __init__(self, parent, depth_dir, elements, x_units='nm', legend=True):
        '''
        Inits depth profile widget.
        
        Args:
            depth_dir: Directory where depth files are located.
            elements: List of Element objects.
            x_units: Unit to be used as x-axis.
            legend: Boolean of whether to show the legend.
        '''
        super().__init__(parent)
        super().fork_toolbar_buttons()
        self.x_units = x_units
        self.draw_legend = legend
        self.elements = elements
        self.depth_dir = depth_dir
        self.depth_files = df.get_depth_files(self.elements, self.depth_dir)
        self.read_files = []
        self.rel_files = []
        self.hyb_files = []
        self.selection_colors = parent.parent.measurement.selector.get_colors()
        self.icon_manager = parent.parent.icon_manager
        self.lim_a = float
        self.lim_b = float
        self.lim_icons = {'a':'depth_profile_lim_all.svg', 
                          'b':'depth_profile_lim_in.svg', 
                          'c':'depth_profile_lim_ex.svg'}
        self.lim_mode = 'a'
        self.canvas.mpl_connect('button_press_event', self.onclick)
        self.__files_read = False
        self.__limits_set = False
        self.__position_set = False
        self.__rel_graph = False
        self.__show_limits = False
        self.__enable_norm_over_range = False
        self.__use_limit = self.__limit()
        self.__fork_toolbar_buttons()
        self.on_draw()
        
        
    def onclick(self, event):
        '''
        Handles clicks on the graph
        
        Args:
            event: A click event on the graph
        '''
        if event.button == 1 and self.__show_limits:
            if self.__use_limit.get() == 'a':
                self.lim_a = event.xdata
                self.__use_limit.switch()
            elif self.__use_limit.get() == 'b':
                self.lim_b = event.xdata
                self.__use_limit.switch()
            else:
                self.lim_b = event.xdata
                self.__use_limit.switch()
            if self.lim_a > self.lim_b:
                self.__use_limit.switch()
                tmp = self.lim_a
                self.lim_a = self.lim_b
                self.lim_b = tmp
            self.on_draw()
                
    
    def on_draw(self):
        '''
        Draws the depth profile graph
        '''
        self.axes.clear()
        
        # Select the units of the x-axis and what columns to read 
        # from the depth files
        y_column = 3
        if self.x_units == 'nm':
            x_column = 2
        else:
            x_column = 0
        self.axes.set_xlabel('Depth (%s)'%(self.x_units))
        self.axes.set_ylabel('Concentration (at.%)')
        
        # If files have not been read before, they are now
        if not self.__files_read:
            full_paths = []
            for file in self.depth_files:
                full_path = os.path.join(self.depth_dir,file)
                full_paths.append(full_path)
            self.read_files = df.extract_from_depth_files(full_paths, self.elements, x_column, y_column)
            self.__files_read = True
            self.rel_files = df.create_relational_depth_files(self.read_files)
            if not self.__limits_set:
                self.lim_a = self.read_files[0][1][0]
                self.lim_b = self.read_files[0][1][-1]
            self.__limits_set = not self.__limits_set
        
        # Determine what files to use for plotting
        if not self.__rel_graph:
            files_to_use = self.read_files
        elif self.lim_mode == 'a':
            files_to_use = self.rel_files
        else:
            tmp_a = list
            tmp_b = list
            if self.lim_mode == 'b':
                tmp_a = self.read_files
                tmp_b = self.rel_files
            else:
                tmp_a = self.rel_files
                tmp_b = self.read_files
            self.hyb_files = df.merge_files_in_range(tmp_a, tmp_b, self.lim_a, self.lim_b)
            files_to_use = self.hyb_files
        
        
        # Plot the limits a and b
        if self.__show_limits:
            self.axes.axvline(x=self.lim_a)
            self.axes.axvline(x=self.lim_b)
        
        # Plot the lines
        i = 0
        for file in files_to_use:
            element = re.sub("\d+", "", file[0])
            isotope = re.sub("\D", "", file[0])
            axe1 = file[1]
            axe2 = file[2]
            if file[0] == 'total':
                # You can plot the total-line here, if you want
                pass #TODO: continue else ei tarvitse tai if not
            else:
                #TODO This'll crash if not there are multiple of same element
                if isotope == '':
                    color_key = element + '0'
                else:
                    color_key = isotope + element + '0'
                self.axes.plot(axe1, axe2, label=r"$^{" + isotope + "}$" + element, 
                               color=self.selection_colors[color_key])
                        
        # Set up the legend
        if self.draw_legend:
            box = self.axes.get_position()
            if not self.__position_set:
                self.axes.set_position([box.x0, box.y0, box.width * 0.8, box.height]) 
                self.__position_set = True
            handles, labels = self.axes.get_legend_handles_labels()
            percentages = df.integrate_lists(self.read_files, self.lim_a, self.lim_b)
            labels_w_percentages = []
            i = 1
            for label in labels:
                labels_w_percentages.append('%s %.3f%%'%(label,percentages[i]))
                i += 1
            leg = self.axes.legend(handles, labels_w_percentages, 
                                   loc=3, bbox_to_anchor=(1, 0))
            for handle in leg.legendHandles:
                handle.set_linewidth(3.0)
                
        self.remove_axes_ticks()
        
        self.canvas.draw()
        
    def __fork_toolbar_buttons(self):
        '''
        Custom toolbar buttons be here
        '''
        
        # But first, let's play around with the existing MatPlotLib buttons.
        self.__button_drag = self.mpl_toolbar.children()[12]
        self.__button_zoom = self.mpl_toolbar.children()[14]
        self.__button_drag.clicked.connect(self.__uncheck_custom_buttons)
        self.__button_zoom.clicked.connect(self.__uncheck_custom_buttons)
        
        self.limButton = QtGui.QToolButton(self)
        self.limButton.clicked.connect(self.__toggle_lim_lines)
        self.limButton.setCheckable(True)
        self.limButton.setToolTip("Toggle the view of the limit lines on and off")
        self.icon_manager.set_icon(self.limButton, "amarok_edit.svg")
        self.mpl_toolbar.addWidget(self.limButton)

        self.modeButton = QtGui.QToolButton(self)
        self.modeButton.clicked.connect(self.__toggle_lim_mode)
        self.modeButton.setEnabled(False)
        self.modeButton.setToolTip("Toggles between selecting the entire histogram, area included in the limits and areas included of the limits")
        self.icon_manager.set_icon(self.modeButton, "depth_profile_lim_all.svg")
        self.mpl_toolbar.addWidget(self.modeButton)
        
        self.viewButton = QtGui.QToolButton(self)
        self.viewButton.clicked.connect(self.__toggle_rel)
        #self.viewButton.setCheckable(True)
        self.viewButton.setToolTip("Switch between relative and absolute view")
        self.icon_manager.set_icon(self.viewButton, "depth_profile_abs.svg")
        self.mpl_toolbar.addWidget(self.viewButton)
        
    def __uncheck_custom_buttons(self):
        if self.__show_limits:
            self.limButton.setChecked(False)
            self.__toggle_lim_lines()
            
    def __uncheck_built_in_buttons(self):
        self.__button_drag.setChecked(False)
        self.__button_zoom.setChecked(False)
        
    def __toggle_lim_mode(self):
        self.__switch_lim_mode()
        self.axes.clear()
        self.on_draw()
        
    def __switch_lim_mode(self, mode=''):
        '''
        Switch between the three modes:
        a = enable relative view throughout the histogram
        b = enable relative view only within limits
        c = enable relative view only outside limits
        '''
        if mode != '': self.lim_mode = mode
        elif self.lim_mode == 'a': self.lim_mode = 'b'
        elif self.lim_mode == 'b': self.lim_mode = 'c'
        else: self.lim_mode = 'a'
        self.icon_manager.set_icon(self.modeButton, self.lim_icons[self.lim_mode])
        
    def __toggle_lim_lines(self):
        '''
        Toggles the usage of limit lines.
        '''
        self.__toggle_drag_zoom
        self.__switch_lim_mode('a')
        self.__show_limits = not self.__show_limits
        self.modeButton.setEnabled(self.__show_limits)
        if self.__show_limits:
            self.__uncheck_built_in_buttons()
            self.mpl_toolbar.mode = "Limit setting tool"
        else:
            self.mpl_toolbar.mode = ""
        self.__enable_norm_over_range = False
        self.axes.clear()
        self.on_draw()
    
    
    def __toggle_rel(self):
        '''
        Toggles between the absolute and relative views.
        '''
        self.__rel_graph = not self.__rel_graph
        if self.__rel_graph:
            self.icon_manager.set_icon(self.viewButton, "depth_profile_rel.svg")
        else:
            self.icon_manager.set_icon(self.viewButton, "depth_profile_abs.svg")
        self.axes.clear()
        self.on_draw()
        
        
    def __toggle_drag_zoom(self):
        self.__tool_label.setText("")
        if self.__button_drag.isChecked():
            self.mpl_toolbar.pan()
        if self.__button_zoom.isChecked():
            self.mpl_toolbar.zoom()
        self.__button_drag.setChecked(False)
        self.__button_zoom.setChecked(False)
        
        
    class __limit:
        '''
        Simple object to control when setting the integration 
        limits in Depth Profile.
        '''
        def __init__(self):
            '''
            Inits __limit
            '''
            self.limit = 'b'
        def switch(self):
            '''
            Switches limit between a and b.
            '''
            if self.limit == 'b':
                self.limit = 'a'
            else:
                self.limit = 'b'
        def get(self):
            '''
            Returns the current limit.
            
            Return:
                The current limit a or b.
            '''
            return self.limit