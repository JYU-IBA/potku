# coding=utf-8
'''
Created on 16.4.2013
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

from os.path import join
from PyQt5 import QtWidgets, QtCore, uic
# from PyQt4 import uic
# from PyQt4 import QtCore

class LogWidget(QtWidgets.QWidget):
    '''Log widget which displays the log. This widget handles the loghandlers emits.    
    '''   
    
    def __init__(self):
        '''Initializes the loghandler widget.
        '''        
        super().__init__()
        # This is used to ensure that the window can't be closed.        
        self.want_to_close = False
        self.ui = uic.loadUi(join("ui_files", "ui_log_widget.ui"), self)
        self.ui.hideButton.clicked.connect(self.minimize_window)    
    
    
    def add_text(self, message):
        '''Adds the specified message to the log field.
        
        Args:
            message: the message which will be displayed.            
        '''
        self.ui.defaultLogText.append(message)       
    
    
    def add_error(self, message):
        '''Adds the specified message to the error field.
        
        Args:
            message: the message which will be displayed.            
        '''
        self.ui.errorLogText.append(message)


    def closeEvent(self, evnt):  # Inherited
        '''Event which happens when the windows is closing.
        
        Instead of closing, minimize the window. This is because the disabling of
        the close button isn't implemented yet. 
        
        Args:
            envt: Close event
        '''
        if self.want_to_close:
            super(LogWidget, self).closeEvent(evnt)
        else:
            evnt.ignore()
            self.minimize_window()


    def minimize_window(self):
        '''Minimize the window.
        '''
        self.setWindowState(QtCore.Qt.WindowMinimized)
