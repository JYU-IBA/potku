# coding=utf-8
'''
Created on 27.3.2013
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
from PyQt4 import QtGui
from PyQt4 import uic

from Modules.ElementLosses import ElementLosses
from Widgets.MatplotlibElementLossesWidget import MatplotlibElementLossesWidget


class ElementLossesDialog(QtGui.QDialog):
    """Class to handle element losses dialogs.
    """
    def __init__(self, parent):
        """Inits element losses class.
        
         Args:
            parent: MeasurementTabWidget
        """
        super().__init__()
        self.parent = parent
        self.cuts = []

        self.ui = uic.loadUi(os.path.join("ui_files", 
                                          "ui_element_losses_params.ui"), self)
        
        self.ui.OKButton.clicked.connect(self.__accept_params)
        self.ui.cancelButton.clicked.connect(self.close)  
        # self.ui.referenceCut.currentIndexChanged.connect(self.__load_targets) # Annoying

        # TODO: Read cut files twice. Requires Refactor.
        cuts, unused_elemloss = parent.measurement.get_cut_files()
        for cut in cuts:
            self.cuts.append(cut)
            self.ui.referenceCut.addItem(cut)

        parent.measurement.fill_cuts_treewidget(self.ui.targetCutTree, True)
        self.exec_()
    

    def __accept_params(self):
        """Called when OK button is pressed. Creates a elementlosses widget and
        adds it to the parent (mdiArea).
        """
        cut_dir = self.parent.measurement.directory_cuts
        cut_elo = self.parent.measurement.directory_elemloss
        y_axis_0_scale = self.ui.radioButton_0max.isChecked()
        unused_y_axis_min_scale = self.ui.radioButton_minmax.isChecked()
        reference_cut = os.path.join(cut_dir, self.ui.referenceCut.currentText())
        partition_count = self.ui.partitionCount.value()
        checked_cuts = []
        root = self.ui.targetCutTree.invisibleRootItem()
        root_child_count = root.childCount()
        for i in range(root_child_count):
            item = root.child(i)
            if item.checkState(0):
                checked_cuts.append(os.path.join(cut_dir, item.file_name))
            child_count = item.childCount()
            if child_count > 0:  # Elemental Losses
                for i in range(child_count):
                    item_child = item.child(i)
                    if item_child.checkState(0):
                        checked_cuts.append(os.path.join(cut_elo,
                                                         item_child.file_name))

        if y_axis_0_scale:
            y_scale = 0
        else:
            y_scale = 1
        
        if checked_cuts:
            msg = "Created Element Losses. Splits: {0} {1} {2}".format(
                    partition_count,
                    "Reference cut: {0}".format(reference_cut),
                    "List of cuts: {0}".format(checked_cuts))
            logging.getLogger(self.parent.measurement.measurement_name
                ).info(msg)
            self.close()
            if self.parent.elemental_losses_widget:
                self.parent.del_widget(self.parent.elemental_losses_widget)
            self.parent.elemental_losses_widget = ElementLossesWidget(self.parent,
                                                                  reference_cut,
                                                                  checked_cuts,
                                                                  partition_count,
                                                                  y_scale)
            icon = self.parent.icon_manager.get_icon("elemental_losses_icon_16.png")
            self.parent.add_widget(self.parent.elemental_losses_widget, icon=icon)
                                                    


        
class ElementLossesWidget(QtGui.QWidget):
    '''Element losses widget which is added to measurement tab.
    '''
    def __init__(self, parent, reference_cut_file, checked_cuts, 
                 partition_count, y_scale):
        '''Inits widget.
        
        Args:
            parent: MeasurementTabWidget
            reference_cut_file: String representing reference cut file.
            checked_cuts: String list representing cut files.
            partition_count: Integer representing how many splits cut files 
                             are divided to.
            y_scale: Integer flag representing how Y axis is scaled.
        '''
        super().__init__()
        self.parent = parent
        # TODO: Use Null with GUI ProgresBar.
        if self.parent.measurement.statusbar:
            self.progress_bar = QtGui.QProgressBar()
            self.parent.measurement.statusbar.addWidget(self.progress_bar, 1) 
            self.progress_bar.show()
        else:
            self.progress_bar = None
        
        self.ui = uic.loadUi(os.path.join("ui_files", "ui_element_losses.ui"), self)
        title = "{0} - Reference cut: {1}".format(self.ui.windowTitle(), 
                                              os.path.basename(reference_cut_file))
        self.ui.setWindowTitle(title)
        
        # Calculate elemental losses
        self.losses = ElementLosses(parent.measurement.directory_cuts,
                                    parent.measurement.directory_elemloss,
                                    reference_cut_file,
                                    checked_cuts,
                                    partition_count,
                                    progress_bar=self.progress_bar)
        split_counts = self.losses.count_element_cuts()
        
        # Connect buttons
        self.ui.splitSaveButton.clicked.connect(self.__save_splits) 
        
        self.matplotlib = MatplotlibElementLossesWidget(self,
                                                        split_counts,
                                                        legend=True,
                                                        y_scale=y_scale) 
        if self.progress_bar:
            self.parent.measurement.statusbar.removeWidget(self.progress_bar)
            self.progress_bar.hide()

        
    def delete(self):
        '''Delete variables and do clean up.
        '''
        self.losses = None
        self.progress_bar = None
        self.matplotlib.delete()
        self.matplotlib = None
        self.ui.close()
        self.ui = None
        self.close()


    def __save_splits(self): # TODO: Use Null with GUI ProgresBar.
        if self.progress_bar:
            self.progress_bar = QtGui.QProgressBar()
            self.parent.measurement.statusbar.addWidget(self.progress_bar, 1) 
            self.progress_bar.show()
        else:
            self.progress_bar = None
        self.losses.progress_bar = self.progress_bar  # Update this     
        self.losses.save_splits()
        if self.progress_bar:
            self.parent.measurement.statusbar.removeWidget(self.progress_bar)
            self.progress_bar.hide()

    
