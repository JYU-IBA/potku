# coding=utf-8
'''
Created on 5.4.2013
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

import logging
import os
from PyQt5 import QtWidgets, uic
# from PyQt4 import uic

from Modules.DepthFiles import DepthFiles
from Modules.Element import Element
from Widgets.MatplotlibDepthProfileWidget import MatplotlibDepthProfileWidget


class DepthProfileDialog(QtWidgets.QDialog):

    def __init__(self, parent):
        '''Inits depth profile dialog
        
        Args:
            parent: MeasurementTabWidget
        '''
        super().__init__()
        self.parent = parent
        self.ui = uic.loadUi(os.path.join("ui_files", "ui_depth_profile_params.ui"), self)
        self.measurement = parent.measurement
        self.__cut_filepath = self.measurement.directory_cuts
        self.__statusbar = parent.measurement.statusbar

        # Connect buttons
        self.ui.OKButton.clicked.connect(self.__accept_params)
        self.ui.cancelButton.clicked.connect(self.close)

        self.measurement.fill_cuts_treewidget(self.ui.treeWidget, True)
        self.exec_()
        
        
    def __accept_params(self):
        '''Accept given parameters
        '''
        progress_bar = QtWidgets.QProgressBar()
        self.__statusbar.addWidget(progress_bar, 1) 
        progress_bar.show() 
        
        try:
            use_cut = []
            output_dir = os.path.join(self.measurement.directory, 'depthfiles')
            output_files = os.path.join(output_dir, 'depth')
            elements = []
                
            # Make the directory for depth files
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            progress_bar.setValue(10)
            
            # Get the filepaths of the selected items
            root = self.ui.treeWidget.invisibleRootItem()
            child_count = root.childCount()
            for i in range(child_count):  # TODO: Esimerkki turhasta rangettelusta
                item = root.child(i)
                if item.checkState(0):
                    use_cut.append(os.path.join(item.directory, item.file_name))
                    element = Element(item.file_name.split('.')[1])
                    elements.append(element)
                child_count_2 = item.childCount()
                if child_count_2 > 0:  # Elemental Losses
                    for j in range(child_count_2):
                        item_child = item.child(j)
                        if item_child.checkState(0):
                            name = item_child.file_name
                            dir_e = self.parent.measurement.directory_elemloss
                            use_cut.append(os.path.join(dir_e, name))
                            element = Element(item_child.file_name.split('.')[1])
                            elements.append(element)
            progress_bar.setValue(20)
            
            # Get the x-axis unit to be used from the radio buttons
            x_units = 'nm'
            radio_buttons = self.findChildren(QtWidgets.QRadioButton)
            for radio_button in radio_buttons:
                if radio_button.isChecked():
                    x_units = radio_button.text()
            progress_bar.setValue(30)
            
            # If items are selected, proceed to generating the depth profile
            if use_cut:
                self.measurement.generate_tof_in()
                dp = DepthFiles(use_cut, output_files)
                dp.create_depth_files()
                progress_bar.setValue(90)
                
                if self.parent.depth_profile_widget:
                    self.parent.del_widget(self.parent.depth_profile_widget)
                self.parent.depth_profile_widget = DepthProfileWidget(self.parent,
                                                                        output_dir,
                                                                        elements,
                                                                        x_units)
                icon = self.parent.icon_manager.get_icon(
                                                     "depth_profile_icon_2_16.png")
                self.parent.add_widget(self.parent.depth_profile_widget, icon=icon)
                self.close()
            else:
                print("No cuts have been selected for depth profile.")
        except Exception as e:
            error_log = "Unexpected error: {0}".format(str(e))
            logging.getLogger(self.measurement.measurement_name).error(error_log)
        finally:
            self.__statusbar.removeWidget(progress_bar)
            progress_bar.hide()



            
class DepthProfileWidget(QtWidgets.QWidget):
    '''Depth Profile widget which is added to measurement tab.
    '''
    def __init__(self, parent, output_dir, elements, x_units):
        '''Inits widget.
        
        Args:
            parent: MeasurementTabWidget
            output_dir: Directory in which the depth files are located.
            elements: A list of Element objects that are used in depth profile.
            x_units: Units to be used for x-axis of depth profile.
        '''
        super().__init__()
        self.parent = parent
        self.ui = uic.loadUi(os.path.join("ui_files", "ui_depth_profile.ui"), self)
        self.matplotlib = MatplotlibDepthProfileWidget(self, output_dir,
                                                       elements, x_units)


    def delete(self):
        '''Delete variables and do clean up.
        '''
        self.matplotlib.delete()
        self.matplotlib = None
        self.ui.close()
        self.ui = None
        self.close()
