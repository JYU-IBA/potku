# coding=utf-8
'''
Created on 21.3.2013
Updated on 27.8.2013

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

from PyQt4 import QtGui

from Dialogs.GraphIgnoreElements import GraphIgnoreElements
from Modules.Element import Element
from Widgets.MatplotlibWidget import MatplotlibWidget


class MatplotlibElementLossesWidget(MatplotlibWidget):
    '''Energy spectrum widget
    '''
    def __init__(self, parent, split, legend=True, y_scale=0, rbs_list={}):
        '''Inits Energy Spectrum widget.
        
        Args:
            parent: An ElementLossesWidget class object.
            split: A list of counted split counts for each element.
            legend: A boolean representing whether to draw legend or not.
            y_scale: An integer flag representing Y axis scaling mode.
            rbs_list: A dictionary of RBS selection elements containing 
                      scatter elements.
        '''
        super().__init__(parent)
        super().fork_toolbar_buttons()
        self.draw_legend = legend
        self.split = split
        self.y_scale = y_scale
        self.__rbs_list = rbs_list
        self.__masses = parent.parent.masses
        self.__icon_manager = parent.icon_manager
        self.selection_colors = parent.measurement.selector.get_colors()
        
        self.__initiated_box = False
        self.__ignore_elements = []
        self.__scale_mode = 0  # 0 default, 1 log, 2 scale (to 100)
        self.__icons = {0:'elemloss_scale_default.png',
                        1:'elemloss_scale_log.png',
                        2:'elemloss_scale_to100.png'}
        self.canvas.manager.set_title("Elemental Losses")
        self.axes.fmt_xdata = lambda x: "{0:1.0f}".format(x)
        self.axes.fmt_ydata = lambda y: "{0:1.0f}".format(y)
        
        # Add button to toggle scaling of the graph
        self.mpl_toolbar.addSeparator()
        self.__button_scale = QtGui.QToolButton(self)
        self.__button_scale.clicked.connect(self.__toggle_scaling)
        self.__button_scale.setToolTip("Toggle scaling mode for the graph " + \
                                       "default, log and 100%.")
        self.__icon_manager.set_icon(self.__button_scale,
                                     self.__icons[self.__scale_mode])
        self.mpl_toolbar.addWidget(self.__button_scale)
        
        # Add button to ignore elements.
        self.__button_ignores = QtGui.QToolButton(self)
        self.__button_ignores.clicked.connect(self.__ignore_elements_from_graph)
        self.__button_ignores.setToolTip("Select elements which are included in" + \
                                         " the graph.")
        self.__icon_manager.set_icon(self.__button_ignores, "gear.svg")
        self.mpl_toolbar.addWidget(self.__button_ignores)
        
        self.on_draw()
        
        
    def __sortt(self, key):
        cut_file = key.split('.')
        element_object = Element(cut_file[0].strip())
        element, isotope = element_object.get_element_and_isotope()
        mass = str(isotope)
        if not mass:
            mass = self.__masses.get_standard_isotope(element)
        else:
            mass = float(mass)
        return mass
    
    
    def on_draw(self):
        '''Draw method for matplotlib.
        '''
        self.axes.clear()  # Clear old stuff
        
        # keys = sorted(self.split.keys())
        keys = [item[0] for item in sorted(self.split.items(),
                                           key=lambda x: self.__sortt(x[0]))]
        for key in keys:
            cut_file = key.split('.')
            element_object = Element(cut_file[0].strip())
            element, isotope = element_object.get_element_and_isotope()
            if key in self.__ignore_elements:
                continue
            # Check RBS selection
            rbs_string = ""
            if len(cut_file) == 2:
                if key + ".cut" in self.__rbs_list.keys():
                    element_object = self.__rbs_list[key + ".cut"]
                    element, isotope = element_object.get_element_and_isotope()
                    rbs_string = "*"
            else:
                if key + cut_file[2] in self.__rbs_list.keys():
                    element_object = self.__rbs_list[key + cut_file[2]]
                    element, isotope = element_object.get_element_and_isotope()
                    rbs_string = "*"
            
            # Get color for selection
            color_string = "{0}{1}{2}".format(isotope, element, cut_file[1])
            if not color_string in self.selection_colors:
                color = "red"
            else:
                color = self.selection_colors[color_string]
            
            # Set label text
            if len(cut_file) == 2:
                label = r"$^{" + str(isotope) + "}$" + element + rbs_string
            else: 
                label = r"$^{" + str(isotope) + "}$" + element + rbs_string \
                        + "$_{split: " + cut_file[2] + "}$"
            # Modify data if scaled to 100.
            data = self.split[key]
            if self.__scale_mode == 2:
                modifier = 100 / self.split[key][0]
                data = [i * modifier for i in data]
            self.axes.plot(data,
                           color=color,
                           label=label)
 
        if self.draw_legend:
            if not self.__initiated_box:
                self.fig.tight_layout(pad=0.5)
                box = self.axes.get_position()
                self.axes.set_position([box.x0, box.y0,
                                        box.width * 0.9, box.height])
                self.__initiated_box = True
            
            handles, labels = self.axes.get_legend_handles_labels()
            leg = self.axes.legend(handles,
                                   labels,
                                   loc=3,
                                   bbox_to_anchor=(1, 0),
                                   borderaxespad=0,
                                   prop={'size':12})
            for handle in leg.legendHandles:
                handle.set_linewidth(3.0)
        
        # Scale based on values
        x_min, x_max = self.axes.get_xlim()
        y_min, y_max = self.axes.get_ylim()
        
        # Y-axis scaling option, 0 = 0-max, 1 = min-max
        if self.y_scale == 0:
            y_min = 0
        
        # Set limits accordingly
        self.axes.set_ylim([y_min, y_max]) 
        self.axes.set_xlim([x_min, x_max])
        
        # Scale for log
        if self.__scale_mode == 1:
            self.axes.set_yscale('symlog')
        else:
            self.axes.set_yscale('linear')
        
        # Set axes names
        if self.__scale_mode == 2:
            self.axes.set_ylabel("Scaled count")
        else:
            self.axes.set_ylabel("Count")
        self.axes.set_xlabel("Split")
             
        # Remove axis ticks
        self.remove_axes_ticks()
        self.canvas.draw()
        
        
    def __ignore_elements_from_graph(self):
        '''Ignore elements from elements ratio calculation.
        '''
        elements = [item[0] for item in sorted(self.split.items(),
                                           key=lambda x: self.__sortt(x[0]))]
        dialog = GraphIgnoreElements(elements, self.__ignore_elements)
        self.__ignore_elements = dialog.ignored_elements
        self.on_draw()
        
        
    def __toggle_scaling(self):
        """Toggle scaling mode for the graph default, log and 100%.
        """
        self.__scale_mode = (self.__scale_mode + 1) % len(self.__icons)
        self.__icon_manager.set_icon(self.__button_scale,
                                     self.__icons[self.__scale_mode])
        self.on_draw()
