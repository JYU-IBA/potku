# coding=utf-8
"""
Created on 15.4.2013
Updated on 20.11.2018

Potku is a graphical user interface for analyzation and 
visualization of measurement data collected from a ToF-ERD 
telescope. For physics calculations Potku uses external 
analyzation components.  
Copyright (C) 2013-2018 Jarkko Aalto, Severi Jääskeläinen, Samuel Kaiponen,
Timo Konu, Samuli Kärkkäinen, Samuli Rahkonen, Miika Raunio, Heta Rekilä and
Sinikka Siironen, 2020 Juhani Sundell

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
             "Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen \n" \
             "Juhani Sundell"
__version__ = "2.0"

import pickle
from typing import List

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5 import uic

import widgets.binding as bnd
import widgets.gui_utils as gutils
from modules.calibration import TOFCalibration
from modules.cut_file import CutFile
from modules.detector import Detector
from modules.measurement import Measurement
from modules.run import Run
from widgets.matplotlib.calibration.curve_fitting \
    import MatplotlibCalibrationCurveFittingWidget
from widgets.matplotlib.calibration.linear_fitting \
    import MatplotlibCalibrationLinearFittingWidget


class TofCalibrationDialog(QtWidgets.QDialog):
    """A dialog for the time of flight calibration
    """
    bin_width = bnd.bind("binWidthSpinBox")
    selected_cut_file = bnd.bind(
        "cutFilesTreeWidget", fget=bnd.get_selected_tree_item,
        fset=bnd.set_selected_tree_item)
    POINTS_OBJECT_FILENAME = 'points.pkl'

    def __init__(self, measurements: List[Measurement], detector: Detector,
                 run: Run, parent_settings_widget=None):
        """Inits the calibration dialog class.
        
        Args:
            measurements: A string list representing measurements files.
            detector: A Detector class object.
            run: Run object.
            parent_settings_widget: A widget this dialog was opened from.
        """
        super().__init__()
        uic.loadUi(gutils.get_ui_dir() / "ui_tof_calibration_dialog.ui", self)

        self.measurements = measurements
        self.run = run
        self.detector = detector

        self.parent_settings_widget = parent_settings_widget
        self.tof_calibration = TOFCalibration()

        # Go through all the measurements and their cut files and list them.
        for measurement in self.measurements:
            item = QtWidgets.QTreeWidgetItem([measurement.name])
            cuts, _ = measurement.get_cut_files()
            gutils.fill_tree(
                item, cuts, data_func=lambda fp: CutFile(cut_file_path=fp),
                text_func=lambda fp: fp.name)
            self.cutFilesTreeWidget.addTopLevelItem(item)
            item.setExpanded(True)
        # Resize columns to fit the content nicely
        for column in range(0, self.cutFilesTreeWidget.columnCount()):
            self.cutFilesTreeWidget.resizeColumnToContents(column)

        self.curveFittingWidget = CalibrationCurveFittingWidget(
            self, self.selected_cut_file, self.tof_calibration, self.detector,
            self.bin_width, 0, self.run)

        old_params = None
        # Get old parameters from the parent dialog
        if parent_settings_widget is not None:
            try:
                f1 = self.parent_settings_widget.tof_offset
                f2 = self.parent_settings_widget.tof_slope
                old_params = f1, f2
            except ValueError as e:
                print(f"Can't get old calibration parameters from the "
                      f"settings dialog: {e}.")

        self.linearFittingWidget = CalibrationLinearFittingWidget(
            self, self.tof_calibration, old_params)

        self.fittingResultsLayout.addWidget(self.curveFittingWidget)
        self.calibrationResultsLayout.addWidget(self.linearFittingWidget)

        # Set up connections
        self.cutFilesTreeWidget.itemSelectionChanged.connect(
            self.__update_curve_fit)
        self.pointsTreeWidget.itemClicked.connect(self.__set_state_for_point)
        self.acceptPointButton.clicked.connect(self.__accept_point)
        self.binWidthSpinBox.valueChanged.connect(self.__update_curve_fit)
        self.binWidthSpinBox.setKeyboardTracking(False)
        self.acceptCalibrationButton.clicked.connect(self.accept_calibration)
        self.cancelButton.clicked.connect(self.close)
        self.removePointButton.clicked.connect(self.remove_selected_points)
        self.tofChannelLineEdit.editingFinished.connect(
            lambda: self.set_calibration_point(
                float(self.tofChannelLineEdit.text())))

        # Set the validator for lineEdit so user can't give invalid values
        double_validator = QtGui.QDoubleValidator()
        self.tofChannelLineEdit.setValidator(double_validator)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.label_remove_timeout)

        try:
            self.__load_object(self.POINTS_OBJECT_FILENAME)
            for p in self.tof_calibration.tof_points:
                self.__accept_points(p)
        except OSError:
            pass

        self.exec_()

    def showEvent(self, _):
        """Called after dialog is shown. Size is adjusted so that all elements
        fit nicely on screen.
        """
        self.adjustSize()

    def remove_selected_points(self):
        """Remove selected items from point tree widget
        """
        removed_something = False
        root = self.pointsTreeWidget.invisibleRootItem()
        for item in self.pointsTreeWidget.selectedItems():
            if item and hasattr(item, "point"):
                removed_something = True
                self.tof_calibration.remove_point(item.point)
            (item.parent() or root).removeChild(item)
        if removed_something:
            self.__change_selected_points()
            self.__save_object(self.POINTS_OBJECT_FILENAME)

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
        if self.parent_settings_widget is not None:
            self.parent_settings_widget.tof_slope = float(
                self.slopeLineEdit.text())
            self.parent_settings_widget.tof_offset = float(
                self.offsetLineEdit.text())
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
                self.acceptCalibrationLabel.setText(calib_ok)
            else:
                self.acceptCalibrationLabel.setText(calib_no)
        else:
            self.acceptCalibrationLabel.setText(calib_inv)

    def __update_curve_fit(self):
        """Redraws everything in the curve fitting graph. Updates the bin width
        too.
        """
        self.__change_accept_point_label("")
        if self.selected_cut_file is not None:
            self.curveFittingWidget.matplotlib.change_bin_width(self.bin_width)
            try:
                self.curveFittingWidget.matplotlib.change_cut(
                    self.selected_cut_file)
            except ValueError as e:
                QtWidgets.QMessageBox.critical(self, "Warning", str(e))
                # TODO: Clear plot

    def __set_state_for_point(self, tree_item):
        """Sets if the tof calibration point is drawn to the linear fit graph
        
        Args:
            tree_item: QtWidgets.QTreeWidgetItem
        """
        if tree_item and hasattr(tree_item, "point"):
            tree_item.point.point_used = tree_item.checkState(0)
            self.__change_selected_points()
            self.__enable_accept_calibration_button()

    def __accept_points(self, point):
        """ Called when 'accept point' button is clicked.

        Adds the calibration point to the point set for linear fitting and
        updates the treewidget of points.
        """
        self.__add_point_to_tree(point)
        self.__change_selected_points()
        self.__enable_accept_calibration_button()
        self.__change_accept_point_label("Point accepted.")

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
            self.__save_object(self.POINTS_OBJECT_FILENAME)
        else:
            self.__change_accept_point_label("Point already exists.")

    def __load_object(self, filename):
        file_to_open = self.detector.path.parent / filename
        with open(file_to_open, 'rb') as output:
            self.tof_calibration.tof_points = pickle.load(output)

    def __save_object(self, filename):
        file_to_open = self.detector.path.parent / filename
        with open(file_to_open, 'wb') as output:
            pickle.dump(self.tof_calibration.tof_points, output,
                        pickle.HIGHEST_PROTOCOL)

    def __change_accept_point_label(self, text):
        """Sets text for the 'acceptPointLabel' label 
        and starts timer.
        
        Args:
            text: String to be set to the label.
        """
        self.acceptPointLabel.setText(text)
        self.timer.start(1500)

    def label_remove_timeout(self):
        """Timeout event method to remove label text.
        """
        self.acceptPointLabel.setText("")
        self.timer.stop()

    def __enable_accept_calibration_button(self):
        """Let press accept calibration only if there are parameters available.
        """
        if self.tof_calibration.slope or self.tof_calibration.offset:
            self.acceptCalibrationButton.setEnabled(True)
        else:
            self.acceptCalibrationButton.setEnabled(False)

    def __add_point_to_tree(self, tof_calibration_point):
        """Adds a ToF Calibration point to the pointsTreeWidget and sets the 
        QTreeWidgetItem's attribute 'point' as the given TOFCalibrationPoint. 
        """
        item = QtWidgets.QTreeWidgetItem([tof_calibration_point.get_name()])
        item.point = tof_calibration_point
        item.setCheckState(0, QtCore.Qt.Checked)
        self.pointsTreeWidget.addTopLevelItem(item)

    def __change_selected_points(self):
        """Redraws the linear fitting graph.
        """
        self.linearFittingWidget.matplotlib.on_draw()  # Redraw


class CalibrationCurveFittingWidget(QtWidgets.QWidget):
    """Widget class for holding MatplotlibCalibrationCurveFittingWidget.
    """

    def __init__(self, dialog, cut, tof_calibration, detector: Detector,
                 bin_width: float, column: int, run: Run):
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
        uic.loadUi(gutils.get_ui_dir() / "ui_tof_curve_fitting_widget.ui", self)
        # NOTE: One of these should always be there. Could probably use "else"
        if hasattr(dialog.parent_settings_widget, "request"):
            self.img_dir = dialog.parent_settings_widget.request.directory
        elif hasattr(dialog.parent_settings_widget, "measurement") and \
                dialog.parent_settings_widget.measurement is not None:
            self.img_dir = dialog.parent_settings_widget.measurement.directory
        self.matplotlib = MatplotlibCalibrationCurveFittingWidget(
            self, detector, tof_calibration, cut, run, bin_width, column,
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
        uic.loadUi(
            gutils.get_ui_dir() / "ui_tof_linear_fitting_widget.ui", self)
        # NOTE: One of these should always be there. Could probably use "else"
        if hasattr(dialog.parent_settings_widget, "request"):
            self.img_dir = dialog.parent_settings_widget.request.directory
        elif hasattr(dialog.parent_settings_widget, "measurement") and \
                dialog.parent_settings_widget.measurement is not None:
            self.img_dir = dialog.parent_settings_widget.measurement.directory
        self.matplotlib = MatplotlibCalibrationLinearFittingWidget(
            self, tof_calibration, dialog=dialog, old_params=old_params)
