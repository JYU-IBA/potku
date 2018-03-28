# coding=utf-8
'''
Created on 21.3.2013
Updated on 7.6.2013

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

from os.path import join
from PyQt5 import QtWidgets
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
#from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar

import modules.navigation_toolbar as NavigationToolbar

class MatplotlibWidget(QtWidgets.QWidget):
    '''Base class for matplotlib widgets
    '''
    def __init__(self, parent):
        '''Inits matplotlib widget.
        
        Args:
            parent: A Parent class object.
        '''
        super().__init__()
        self.main_frame = parent
        self.dpi = 75
        self.show_axis_ticks = True
        self.__create_frame()


    def __create_frame(self):
        self.fig = Figure((5.0, 3.0), dpi=self.dpi)
        self.fig.patch.set_facecolor("white")
        self.canvas = FigureCanvas(self.fig)
        self.canvas.manager = MockManager(self.main_frame)
        self.canvas.setParent(self.main_frame)
        self.axes = self.fig.add_subplot(111)

        self.mpl_toolbar = NavigationToolbar.NavigationToolBar2QTView(
            self.canvas, self.main_frame)

        if hasattr(self.main_frame.ui, "matplotlib_layout"):
            self.main_frame.ui.matplotlib_layout.addWidget(self.canvas)
            self.main_frame.ui.matplotlib_layout.addWidget(self.mpl_toolbar)
        if hasattr(self.main_frame.ui, "stackedWidget"):
            frame = QtWidgets.QWidget()
            layout = QtWidgets.QVBoxLayout()
            layout.addWidget(self.canvas)
            layout.addWidget(self.mpl_toolbar)
            frame.setLayout(layout)
            self.main_frame.ui.stackedWidget.addWidget(frame)


    def fork_toolbar_buttons(self):
        '''Remove figure options & subplot config that might not work properly.
        '''
        try:
            self.mpl_toolbar.removeAction(self.mpl_toolbar.children()[21]) 
            self.mpl_toolbar.removeAction(self.mpl_toolbar.children()[17])
        except:
            pass  # Already removed
    
    
    def remove_axes_ticks(self):
        '''Remove ticks from axes.
        '''
        if not self.show_axis_ticks:
            for tick in self.axes.yaxis.get_major_ticks():
                tick.label1On = False
                tick.label2On = False
            for tick in self.axes.xaxis.get_major_ticks():
                tick.label1On = False
                tick.label2On = False
                
                
    def delete(self):
        '''Delete matplotlib objects.
        '''
        self.axes.clear()  # Might be useless with fig.clf()
        self.canvas.close()
        self.fig.clf()
        self.close()
        
        del self.fig
        del self.canvas
        del self.axes
        
        import gc
        gc.collect()


class MockManager:
    '''MockManager class to force matplotlib's figure (image) saving directory.
    '''
    def __init__(self, parent):
        '''Init the mock manager class to be used when saving figure.
        
        Args:
            parent: A parent object which has measurement object.
        '''
        if hasattr(parent, "measurement"):
            self.directory = parent.measurement.directory
        elif hasattr(parent, "img_dir"):
            self.directory = parent.img_dir
        else:
            self.directory = None
        self.title = "image"
        
    def get_window_title(self):
        '''Get full path to the file (no extension).
        '''
        if self.directory:
            return join(self.directory, self.title)
        return self.title

    def set_title(self, title):
        '''Set file name.
        '''
        self.title = title
