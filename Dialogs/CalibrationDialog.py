# coding=utf-8
'''
Created on 15.4.2013
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
from PyQt5 import QtCore, QtWidgets
from PyQt5 import QtGui
from PyQt5 import uic

from Modules.CutFile import CutFile
from Modules.Calibration import TOFCalibration
from Widgets.MatplotlibCalibrationCurveFittingWidget \
import MatplotlibCalibrationCurveFittingWidget
from Widgets.MatplotlibCalibrationLinearFittingWidget \
import MatplotlibCalibrationLinearFittingWidget

class CalibrationDialog(QtWidgets.QDialog):
    """A dialog for the time of flight calibration
    """
    def __init__(self, measurements, settings, masses, parent_settings_dialog=None):
        """Inits the calibration dialog class
        
        Args:
            measurements: String list representing measurements files.
            settings: Settings object
            masses: Reference to Masses class object.
            parent_settings_dialog: Representing from which dialog this was opened 
                                    from.
        """
        super().__init__()
        self.measurements = measurements  # List
        # TODO: Settings should be loaded from the measurement depending on is the 
        # calibration dialog opened from the project settings (measurement's 
        # project settings is loaded) or the measurement specific settings
        # (measurement's measurement settings is loaded). This has to be done for
        # better architecture.
        self.settings = settings 
        self.cuts = []

        self.ui = uic.loadUi(os.path.join("ui_files",
                                          "ui_calibration_dialog.ui"), self)
        self.parent_settings_dialog = parent_settings_dialog 
        self.tof_calibration = TOFCalibration()
        
        measurement = None
        
        # Go through all the measurements and their cut files and list them.
        for measurement in self.measurements:
            item = QtGui.QTreeWidgetItem([measurement.measurement_name])
            
            cuts, unused_cuts_elemloss = measurement.get_cut_files()
            # May also return a list of cut file's element losses 
            # cut files as one of the list elements
            for cut_file in cuts:
                subitem = QtGui.QTreeWidgetItem([cut_file])
                subitem.directory = measurement.directory_cuts
                subitem.file_name = cut_file
                item.addChild(subitem)
            self.ui.cutFilesTreeWidget.addTopLevelItem(item)
            item.setExpanded(True)
        # Resize columns to fit the content nicely
        for column in range(0, self.ui.cutFilesTreeWidget.columnCount()):
            self.ui.cutFilesTreeWidget.resizeColumnToContents(column)

            
        self.cut_file = CutFile()
        self.curveFittingWidget = CalibrationCurveFittingWidget(self, self.cut_file,
                                                    self.tof_calibration,
                                                    self.settings,
                                                    self.ui.binWidthSpinBox.value(),
                                                    1,
                                                    masses)
        
        old_params = None
        if parent_settings_dialog:  # Get old parameters from the parent dialog
            try:
                f1 = float(self.parent_settings_dialog.ui.slopeLineEdit.text())
                f2 = float(self.parent_settings_dialog.ui.offsetLineEdit.text())
                old_params = f1, f2
            except:
                m = "Can't get old calibration parameters from the settings dialog."
                print(m)
                
        self.linearFittingWidget = CalibrationLinearFittingWidget(self,
                                                      self.tof_calibration,
                                                      old_params)
        
        self.ui.fittingResultsLayout.addWidget(self.curveFittingWidget)
        self.ui.calibrationResultsLayout.addWidget(self.linearFittingWidget)        
        
        # Set up connections
        self.ui.cutFilesTreeWidget.itemClicked.connect(
            lambda: self.change_current_cut(
                self.ui.cutFilesTreeWidget.currentItem()))
        self.ui.pointsTreeWidget.itemClicked.connect(self.__set_state_for_point)
        self.ui.acceptPointButton.clicked.connect(self.__accept_point)
        self.ui.binWidthSpinBox.valueChanged.connect(self.__update_curve_fit)
        self.ui.binWidthSpinBox.setKeyboardTracking(False)
        self.ui.acceptCalibrationButton.clicked.connect(self.accept_calibration)
        self.ui.cancelButton.clicked.connect(self.close)
        self.ui.removePointButton.clicked.connect(self.remove_selected_points)
        self.ui.tofChannelLineEdit.editingFinished.connect(
            lambda: self.set_calibration_point(
                float(self.ui.tofChannelLineEdit.text())))
        
        # Set the validator for lineEdit so user can't give invalid values
        double_validator = QtGui.QDoubleValidator()
        self.ui.tofChannelLineEdit.setValidator(double_validator)
        
        self.timer = QtCore.QTimer(interval=1500, timeout=self.timeout)
        self.exec_()
    
    
    def remove_selected_points(self):
        '''Remove selected items from point tree widget
        '''
        removed_something = False
        root = self.ui.pointsTreeWidget.invisibleRootItem()
        for item in self.ui.pointsTreeWidget.selectedItems():
            if item and hasattr(item, 'point'):
                removed_something = True
                self.tof_calibration.remove_point(item.point)
            (item.parent() or root).removeChild(item)
        if removed_something:
            self.__change_selected_points()
            
    
    def set_calibration_point(self, tof):
        '''Set Cut file front edge estimation to specific value.
        
        Args:
            tof: Float representing front edge of linear fit estimation.
        '''
        self.curveFittingWidget.matplotlib.set_calibration_point_externally(tof)
    
    
    def set_calibration_parameters_to_parent(self):
        '''Set calibration parameters to parent dialog's calibration parameters 
        fields.
        '''
        if self.parent_settings_dialog:
            self.parent_settings_dialog.ui.slopeLineEdit.setText(
                                                 self.ui.slopeLineEdit.text())
            self.parent_settings_dialog.ui.offsetLineEdit.setText(
                                                 self.ui.offsetLineEdit.text())
            return True
        return False
    
    
    def accept_calibration(self):
        '''Accept calibration (parameters).
        '''
        calib_ok = "Calibration parameters accepted.\nYou can now close the window."
        calib_no = "Couldn't set parameters to\nthe settings dialog."
        calib_inv = "Invalid calibration parameters."
        results = self.tof_calibration.get_fit_parameters()
        if results[0] and results[1]:
            if self.set_calibration_parameters_to_parent():
                self.ui.acceptCalibrationLabel.setText(calib_ok)
            else:
                self.ui.acceptCalibrationLabel.setText(calib_no)
        else:
            self.ui.acceptCalibrationLabel.setText(calib_inv)
        
        
    def change_current_cut(self, current_item):
        """Changes the current cut file drawn to the curve fitting widget.
        
        Args:
            current_item: QtGui.QTreeWidgetItem of CutFile which was selected. 
        """
        self.__change_accept_point_label("")
        if current_item and hasattr(current_item, 'directory') and \
        hasattr(current_item, 'file_name'):
            self.__set_current_cut(current_item)        
            self.__update_curve_fit()
        
    
    
    def __set_current_cut(self, current_item):
        """Sets the current open cut file in the calibration dialog.
        
        Args:
            current_item: QtGui.QTreeWidgetItem of CutFile which was selected. 
        """
        # TODO: Do not read cut files every time. 
        # Read them once and then switch here.
        self.cut_file = CutFile()
        self.cut_file.load_file(os.path.join(current_item.directory,
                                             current_item.file_name))
    
    
    def __update_curve_fit(self):
        """Redraws everything in the curve fitting graph. Updates the bin width too.
        """
        bin_width = self.ui.binWidthSpinBox.value()
        self.curveFittingWidget.matplotlib.change_bin_width(bin_width)
        self.curveFittingWidget.matplotlib.change_cut(self.cut_file)
    
    
    def __set_state_for_point(self, tree_item):
        """Sets if the tof calibration point is drawn to the linear fit graph
        
        Args:
            tree_item: QtGui.QTreeWidgetItem
        """
        if tree_item and hasattr(tree_item, 'point'):
            tree_item.point.point_used = tree_item.checkState(0)
            self.__change_selected_points()
            self.__enable_accept_calibration_button()
        
    
    def __accept_point(self):
        """ Called when 'accept point' button is clicked.
        
        Adds the calibration point to the point set for linear fitting and updates
        the treewidget of points.
        """
        point = self.curveFittingWidget.matplotlib.tof_calibration_point
        if point and not self.tof_calibration.point_exists(point):
            self.tof_calibration.add_point(point)
            self.__add_point_to_tree(point)
            self.__change_selected_points()
            self.__enable_accept_calibration_button()      
            self.__change_accept_point_label("Point accepted.")
        else:
            self.__change_accept_point_label("Point already exists.")
    
    
    def __change_accept_point_label(self, text):
        """Sets text for the 'acceptPointLabel' label 
        and starts timer.
        
        Args:
            text: String to be set to the label.
        """
        self.ui.acceptPointLabel.setText(text)
        self.timer.start()
        
        
    def timeout(self):
        '''Timeout eventmethod to remove label text.
        '''
        self.ui.acceptPointLabel.setText("")
        self.timer.stop()
    
    
    def __enable_accept_calibration_button(self):
        # Let press accept calibration only if there are parameters available.
        if self.tof_calibration.slope or self.tof_calibration.offset: 
            self.ui.acceptCalibrationButton.setEnabled(True)
        else:
            self.ui.acceptCalibrationButton.setEnabled(False)
    
    
    def __add_point_to_tree(self, tof_calibration_point):
        """Adds a ToF Calibration point to the pointsTreeWidget and sets the 
        QTreeWidgetItem's attribute 'point' as the given TOFCalibrationPoint. 
        """
        item = QtGui.QTreeWidgetItem([tof_calibration_point.get_name()])
        item.point = tof_calibration_point
        item.setCheckState(0, QtCore.Qt.Checked)
        self.ui.pointsTreeWidget.addTopLevelItem(item)

    
    def __change_selected_points(self):
        """Redraws the linear fitting graph.
        """
        self.linearFittingWidget.matplotlib.on_draw()  # Redraw
    
        


class CalibrationCurveFittingWidget(QtWidgets.QWidget):
    '''Widget class for holding MatplotlibCalibrationCurveFittingWidget.
    '''
    def __init__(self, dialog, cut, tof_calibration,
                 settings, bin_width, column, masses):
        '''Inits widget.
        
        Args:
            dialog: Parent dialog.
            cut: CutFile class object.
            tof_calibration: TOFCalibration class object.
            settings: Settings object
            bin_width: Float representing histogram's bin width.
            column: Integer representing which column number is used.
            masses: Reference to Masses class object.
        '''
        super().__init__()
        self.ui = uic.loadUi(os.path.join("ui_files",
                                          "ui_tof_curve_fitting_widget.ui"), self)
        self.matplotlib = MatplotlibCalibrationCurveFittingWidget(self,
                                                                  settings,
                                                                  tof_calibration,
                                                                  cut, masses,
                                                                  bin_width,
                                                                  column,
                                                                  dialog)
        
        
        
            
class CalibrationLinearFittingWidget(QtWidgets.QWidget):
    '''Widget class for holding MatplotlibCalibrationLinearFittingWidget.
    '''
    def __init__(self, dialog, tof_calibration, old_params):
        '''Inits widget.
        
        Args:
            dialog: Parent dialog.
            tof_calibration: TOFCalibration class object.
            old_params: Old calibration parameters in tuple (slope, offset).
        '''
        super().__init__()
        self.ui = uic.loadUi(os.path.join("ui_files",
                                          "ui_tof_linear_fitting_widget.ui"), self)
        self.matplotlib = MatplotlibCalibrationLinearFittingWidget(self,
                                                           tof_calibration,
                                                           dialog=dialog,
                                                           old_params=old_params)
    
