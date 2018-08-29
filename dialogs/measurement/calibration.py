# coding=utf-8
"""
Created on 15.4.2013
Updated on 29.8.2018

Potku is a graphical user interface for analyzation and 
visualization of measurement data collected from a ToF-ERD 
telescope. For physics calculations Potku uses external 
analyzation components.  
Copyright (C) 2013-2018 Jarkko Aalto, Severi Jääskeläinen, Samuel Kaiponen,
Timo Konu, Samuli Kärkkäinen, Samuli Rahkonen, Miika Raunio, Heta Rekilä and
Sinikka Siironen

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
"""
__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen \n " \
             "Samuli Rahkonen \n Miika Raunio \n Severi Jääskeläinen \n " \
             "Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"
__version__ = "2.0"

import os
import platform

from modules.cut_file import CutFile
from modules.calibration import TOFCalibration

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5 import uic

from widgets.matplotlib.calibration.curve_fitting \
    import MatplotlibCalibrationCurveFittingWidget
from widgets.matplotlib.calibration.linear_fitting \
    import MatplotlibCalibrationLinearFittingWidget


class CalibrationDialog(QtWidgets.QDialog):
    """A dialog for the time of flight calibration
    """
    def __init__(self, measurements, detector,
                 run, parent_settings_widget=None):
        """Inits the calibration dialog class.
        
        Args:
            measurements: A string list representing measurements files.
            detector: A Detector class object.
            run: Run object.
            parent_settings_widget: A widget this dialog was opened from.
        """
        super().__init__()
        self.measurements = measurements
        self.run = run
        self.detector = detector
        self.__cut_file = CutFile()
        self.__cut_files = {}
        
        self.ui = uic.loadUi(os.path.join("ui_files",
                                          "ui_calibration_dialog.ui"), self)
        self.parent_settings_widget = parent_settings_widget
        self.tof_calibration = TOFCalibration()
        
        # Go through all the measurements and their cut files and list them.
        for measurement in self.measurements:
            item = QtWidgets.QTreeWidgetItem([measurement.name])
            
            cuts, unused_cuts_elemloss = measurement.get_cut_files()
            # May also return a list of cut file's element losses 
            # cut files as one of the list elements
            for cut_file in cuts:
                subitem = QtWidgets.QTreeWidgetItem([cut_file])
                subitem.directory = measurement.directory_cuts
                subitem.file_name = cut_file
                item.addChild(subitem)
                cut_object = CutFile()
                cut_object.load_file(os.path.join(measurement.directory_cuts,
                                                  cut_file))
                self.__cut_files[cut_file] = cut_object
            self.ui.cutFilesTreeWidget.addTopLevelItem(item)
            item.setExpanded(True)
        # Resize columns to fit the content nicely
        for column in range(0, self.ui.cutFilesTreeWidget.columnCount()):
            self.ui.cutFilesTreeWidget.resizeColumnToContents(column)

        self.curveFittingWidget = \
            CalibrationCurveFittingWidget(self,
                                          self.__cut_file,
                                          self.tof_calibration,
                                          self.detector,
                                          self.ui.binWidthSpinBox.value(), 1,
                                          self.run)
        
        old_params = None
        # Get old parameters from the parent dialog
        if parent_settings_widget:
            try:
                f1 = float(self.parent_settings_widget.ui.slopeLineEdit.text())
                f2 = float(self.parent_settings_widget.ui.offsetLineEdit.text())
                old_params = f1, f2
            except:
                m = "Can't get old calibration parameters from the settings " \
                    "dialog."
                print(m)
                
        self.linearFittingWidget = CalibrationLinearFittingWidget(
            self, self.tof_calibration, old_params)
        
        self.ui.fittingResultsLayout.addWidget(self.curveFittingWidget)
        self.ui.calibrationResultsLayout.addWidget(self.linearFittingWidget)        
        
        # Set up connections
        self.ui.cutFilesTreeWidget.itemSelectionChanged.connect(
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

        if platform.system() == "Darwin":
            self.ui.tofSecondsLineEdit.setFixedWidth(170)
            self.ui.tofChannelLineEdit.setFixedWidth(170)
            self.ui.offsetLineEdit.setFixedWidth(170)
            self.ui.slopeLineEdit.setFixedWidth(170)

        if platform.system() == "Linux":
            self.ui.tofSecondsLineEdit.setFixedWidth(190)
            self.ui.tofChannelLineEdit.setFixedWidth(190)
            self.ui.offsetLineEdit.setFixedWidth(190)
            self.ui.slopeLineEdit.setFixedWidth(190)
        self.exec_()

    def remove_selected_points(self):
        """Remove selected items from point tree widget
        """
        removed_something = False
        root = self.ui.pointsTreeWidget.invisibleRootItem()
        for item in self.ui.pointsTreeWidget.selectedItems():
            if item and hasattr(item, "point"):
                removed_something = True
                self.tof_calibration.remove_point(item.point)
            (item.parent() or root).removeChild(item)
        if removed_something:
            self.__change_selected_points()

    def set_calibration_point(self, tof):
        """Set Cut file front edge estimation to specific value.
        
        Args:
            tof: Float representing front edge of linear fit estimation.
        """
        self.curveFittingWidget.matplotlib.set_calibration_point_externally(tof)

    def set_calibration_parameters_to_parent(self):
        """Set calibration parameters to parent dialog's calibration parameters 
        fields.
        """
        if self.parent_settings_widget:
            self.parent_settings_widget.scientific_tof_slope\
                .scientificLineEdit.\
                setText(self.ui.slopeLineEdit.text())
            self.parent_settings_widget.scientific_tof_offset\
                .scientificLineEdit.\
                setText(self.ui.offsetLineEdit.text())
            return True
        return False

    def accept_calibration(self):
        """Accept calibration (parameters).
        """
        calib_ok = "Calibration parameters accepted.\nYou can now close the " \
                   "window."
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
            current_item: QtWidgets.QTreeWidgetItem of CutFile which was
            selected.
        """
        self.__change_accept_point_label("")
        if current_item and hasattr(current_item, "directory") and \
           hasattr(current_item, "file_name"):
            self.__set_current_cut(current_item)        
            self.__update_curve_fit()

    def __set_current_cut(self, current_item):
        """Sets the current open cut file in the calibration dialog.
        
        Args:
            current_item: QtWidgets.QTreeWidgetItem of CutFile which was
            selected.
        """
        self.__cut_file = self.__cut_files[current_item.file_name]

    def __update_curve_fit(self):
        """Redraws everything in the curve fitting graph. Updates the bin width
        too.
        """
        bin_width = self.ui.binWidthSpinBox.value()
        self.curveFittingWidget.matplotlib.change_bin_width(bin_width)
        self.curveFittingWidget.matplotlib.change_cut(self.__cut_file)

    def __set_state_for_point(self, tree_item):
        """Sets if the tof calibration point is drawn to the linear fit graph
        
        Args:
            tree_item: QtWidgets.QTreeWidgetItem
        """
        if tree_item and hasattr(tree_item, "point"):
            tree_item.point.point_used = tree_item.checkState(0)
            self.__change_selected_points()
            self.__enable_accept_calibration_button()

    def __accept_point(self):
        """ Called when 'accept point' button is clicked.
        
        Adds the calibration point to the point set for linear fitting and
        updates the treewidget of points.
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
        """Timeout event method to remove label text.
        """
        self.ui.acceptPointLabel.setText("")
        self.timer.stop()

    def __enable_accept_calibration_button(self):
        """Let press accept calibration only if there are parameters available.
        """
        if self.tof_calibration.slope or self.tof_calibration.offset:
            self.ui.acceptCalibrationButton.setEnabled(True)
        else:
            self.ui.acceptCalibrationButton.setEnabled(False)

    def __add_point_to_tree(self, tof_calibration_point):
        """Adds a ToF Calibration point to the pointsTreeWidget and sets the 
        QTreeWidgetItem's attribute 'point' as the given TOFCalibrationPoint. 
        """
        item = QtWidgets.QTreeWidgetItem([tof_calibration_point.get_name()])
        item.point = tof_calibration_point
        item.setCheckState(0, QtCore.Qt.Checked)
        self.ui.pointsTreeWidget.addTopLevelItem(item)

    def __change_selected_points(self):
        """Redraws the linear fitting graph.
        """
        self.linearFittingWidget.matplotlib.on_draw()  # Redraw
    

class CalibrationCurveFittingWidget(QtWidgets.QWidget):
    """Widget class for holding MatplotlibCalibrationCurveFittingWidget.
    """
    def __init__(self, dialog, cut, tof_calibration,
                 detector, bin_width, column, run):
        """Initializes widget.
        
        Args:
            dialog: Parent dialog.
            cut: CutFile class object.
            tof_calibration: TOFCalibration class object.
            detector: Detector object
            bin_width: Float representing histogram's bin width.
            column: Integer representing which column number is used.
            run: Run object.
        """
        super().__init__()
        self.ui = uic.loadUi(os.path.join("ui_files",
                                          "ui_tof_curve_fitting_widget.ui"),
                             self)
        # NOTE: One of these should always be there. Could probably use "else"
        if hasattr(dialog.parent_settings_widget, "request"):
            self.img_dir = dialog.parent_settings_widget.request.directory
        elif hasattr(dialog.parent_settings_widget, "measurement") and \
                dialog.parent_settings_widget.measurement is not None:
            self.img_dir = dialog.parent_settings_widget.measurement.directory
        self.matplotlib = \
            MatplotlibCalibrationCurveFittingWidget(self, detector,
                                                    tof_calibration,
                                                    cut, run,
                                                    bin_width,
                                                    column,
                                                    dialog)

            
class CalibrationLinearFittingWidget(QtWidgets.QWidget):
    """Widget class for holding MatplotlibCalibrationLinearFittingWidget.
    """
    def __init__(self, dialog, tof_calibration, old_params):
        """Initializes widget.
        
        Args:
            dialog: Parent dialog.
            tof_calibration: TOFCalibration class object.
            old_params: Old calibration parameters in tuple (slope, offset).
        """
        super().__init__()
        self.ui = uic.loadUi(os.path.join("ui_files",
                                          "ui_tof_linear_fitting_widget.ui"),
                             self)
        # NOTE: One of these should always be there. Could probably use "else"
        if hasattr(dialog.parent_settings_widget, "request"):
            self.img_dir = dialog.parent_settings_widget.request.directory
        elif hasattr(dialog.parent_settings_widget, "measurement") and \
                dialog.parent_settings_widget.measurement is not None:
            self.img_dir = dialog.parent_settings_widget.measurement.directory
        self.matplotlib = MatplotlibCalibrationLinearFittingWidget(
            self, tof_calibration, dialog=dialog, old_params=old_params)
