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

from Modules.Element import Element
from Widgets.MatplotlibWidget import MatplotlibWidget

class MatplotlibEnergySpectrumWidget(MatplotlibWidget):
    '''Energy spectrum widget
    '''
    def __init__(self, parent, histed_files, legend=True):
        '''Inits Energy Spectrum widget.
        
        Args:
            parent: EnergySpectrumWidget class object.
            histed_files: List of calculated energy spectrum files.
            legend: Boolean representing whether to draw legend or not.
        '''
        super().__init__(parent)
        super().fork_toolbar_buttons()
        self.draw_legend = legend
        self.histed_files = histed_files
        self.selection_colors = parent.parent.measurement.selector.get_colors()
        self.on_draw()

        
    def on_draw(self):
        '''Draw method for matplotlib.
        '''
        # Values for zoom
        x_min, x_max = self.axes.get_xlim()
        y_min, y_max = self.axes.get_ylim()
        
        self.axes.clear()  # Clear old stuff
        
        element_counts = {}
        keys = sorted(self.histed_files.keys())
        # for cut in self.cuts:
        for key in keys:
            cut_file = key.split('.')
            cut = self.histed_files[key]
            element_object = Element(cut_file[0])  # Yeah...
            element, isotope = element_object.get_element_and_isotope()

            x = tuple(float(pair[0]) for pair in cut)
            y = tuple(float(pair[1]) for pair in cut)
            
            dirtyinteger = 0
            while "{0}{1}{2}".format(isotope, element, dirtyinteger) in element_counts:
                dirtyinteger += 1
                
            color_string = "{0}{1}{2}".format(isotope, element, dirtyinteger)
            element_counts[color_string] = 1
            if not color_string in self.selection_colors:
                color = "red"
            else:
                color = self.selection_colors[color_string]
            
            if len(cut_file) == 2:
                label = r"$^{" + str(isotope) + "}$" + element
            else: 
                label = r"$^{" + str(isotope) + "}$" + element + "$_{split " \
                        + cut_file[2] + "}$"
            self.axes.plot(x, y,
                           color=color,
                           label=label)
            
        if self.draw_legend:
            box = self.axes.get_position()
            self.axes.set_position([box.x0, box.y0, box.width * 0.8, box.height])
            
            handles, labels = self.axes.get_legend_handles_labels()
            leg = self.axes.legend(handles, labels, loc=3, bbox_to_anchor=(1.05, 0))
            for handle in leg.legendHandles:
                handle.set_linewidth(3.0)
        
        if x_max > 0.09 and x_max < 1.01:  # This works...
            x_max = self.axes.get_xlim()[1]
        if y_max > 0.09 and y_max < 1.01:
            y_max = self.axes.get_ylim()[1]
        
        # Set limits accordingly
        self.axes.set_ylim([y_min, y_max])
        self.axes.set_xlim([x_min, x_max])
        
        self.axes.set_ylabel("Yield (counts)")
        self.axes.set_xlabel("Energy (MeV)")
         
        # Remove axis ticks
        self.remove_axes_ticks()

        # Draw magic
        self.canvas.draw()

