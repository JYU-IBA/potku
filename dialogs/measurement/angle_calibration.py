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
             "Juhani Sundell \n Timo Leppälä"
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
from widgets.matplotlib.calibration.angle_selector \
    import MatplotlibAngleSelectorWidget



class AngleCalibrationDialog(QtWidgets.QDialog):
    """A dialog for Angle calibration
    """
    bin_width = bnd.bind("binWidthSpinBox")
    selected_asc_file = bnd.bind(
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
        uic.loadUi(gutils.get_ui_dir() / "ui_angle_calibration_dialog.ui", self)

        self.measurements = measurements
        self.run = run
        self.detector = detector

        self.parent_settings_widget = parent_settings_widget

        # Go through all the measurements and their cut files and list them.
        for measurement in self.measurements:
            item = QtWidgets.QTreeWidgetItem([measurement.name])
            if measurement.measurement_file != None:
                with open(measurement.measurement_file, 'r') as f:
                    if len(f.readline().split()) > 2:
                        item2 = QtWidgets.QTreeWidgetItem([str(measurement.measurement_file.stem)+".asc"])
                        item2.setData(0, QtCore.Qt.UserRole, measurement.measurement_file)
                        item.addChild(item2)
                    self.cutFilesTreeWidget.addTopLevelItem(item)
        # Resize columns to fit the content nicely
        for column in range(0, self.cutFilesTreeWidget.columnCount()):
            self.cutFilesTreeWidget.resizeColumnToContents(column)

        self.AngleSelectorWidget = AngleSelectorWidget(
            self, self.selected_asc_file, self.detector,
            self.bin_width, 0, self.run)

        # old_params = None
        # # Get old parameters from the parent dialog
        # if parent_settings_widget is not None:
        #     try:
        #         f1 = self.parent_settings_widget.angle_offset
        #         f2 = self.parent_settings_widget.angle_slope
        #         old_params = f1, f2
        #     except ValueError as e:
        #         print(f"Can't get old calibration parameters from the "
        #               f"settings dialog: {e}.")

        self.angleSelectorLayout.addWidget(self.AngleSelectorWidget)

        # Set up connections
        self.cutFilesTreeWidget.itemSelectionChanged.connect(
            self.__update_graph)
        self.binWidthSpinBox.valueChanged.connect(self.__update_graph)
        self.binWidthSpinBox.setKeyboardTracking(False)
        self.acceptCalibrationButton.clicked.connect(self.accept_calibration)
        self.autoCalibrationButton.clicked.connect(self.auto_calibrate)
        self.cancelButton.clicked.connect(self.close)

        self.angleSlopeLineEdit.setText(str(0))
        self.angleSlopeLineEdit.setReadOnly(True)
        self.angleOffsetLineEdit.setText(str(0))
        self.angleSlopeLineEdit.setReadOnly(True)
        self.foilDistanceSpinBox.setValue(self.detector.foils[-1].distance)
        self.foilDistanceSpinBox.valueChanged.connect(self.__value_changed)
        self.foilWidthSpinBox.setValue(self.detector.foils[-1].size[0])
        self.foilWidthSpinBox.valueChanged.connect(self.__value_changed)

        self.adjustSize()

        self.exec_()

    def showEvent(self, _):
        """Called after dialog is shown. Size is adjusted so that all elements
        fit nicely on screen.
        """
        self.adjustSize()

    def accept_calibration(self):
        """Accept calibration (parameters).
        """
        self.set_calibration_parameters_to_parent()
        self.close()



    def __update_graph(self):
        """Redraws everything in the curve fitting graph. Updates the bin width
        too.
        """
        if self.selected_asc_file is not None:
            self.AngleSelectorWidget.matplotlib.change_bin_width(self.bin_width)
            try:
                self.AngleSelectorWidget.matplotlib.change_asc(
                    self.selected_asc_file)
            except ValueError as e:
                QtWidgets.QMessageBox.critical(self, "Warning", str(e))
                # TODO: Clear plot

    def __value_changed(self):
        self.AngleSelectorWidget.matplotlib.calculate_fit()

    def __set_state_for_point(self, tree_item):
        """Sets if the tof calibration point is drawn to the linear fit graph
        
        Args:
            tree_item: QtWidgets.QTreeWidgetItem
        """
        if tree_item and hasattr(tree_item, "point"):
            tree_item.point.point_used = tree_item.checkState(0)
            self.__change_selected_points()
            self.__enable_accept_calibration_button()

    def set_calibration_parameters_to_parent(self):
        """Set calibration parameters to parent dialog's calibration parameters
        fields.
        """
        if self.parent_settings_widget is not None:
            self.parent_settings_widget.set_calibrated_angles(float(self.angleSlopeLineEdit.text()),
                                                              float(self.angleOffsetLineEdit.text()))
            return True
        return False

    def auto_calibrate(self):
        if self.selected_asc_file != None:
            self.AngleSelectorWidget.matplotlib.set_auto_calibration()


class AngleSelectorWidget(QtWidgets.QWidget):
    """Widget class for holding MatplotlibAngleSelectorWidget.
    """

    def __init__(self, dialog, asc, detector: Detector,
                 bin_width: float, column: int, run: Run):
        """Initializes widget.

        Args:
            dialog: Parent dialog.
            cut: CutFile class object.
            detector: Detector object
            bin_width: Float representing histogram's bin width.
            column: Integer representing which column number is used.
            run: Run object.
        """
        super().__init__()
        uic.loadUi(gutils.get_ui_dir() / "ui_angle_selector_widget.ui", self)
        # NOTE: One of these should always be there. Could probably use "else"
        if hasattr(dialog.parent_settings_widget, "request"):
            self.img_dir = dialog.parent_settings_widget.request.directory
        elif hasattr(dialog.parent_settings_widget, "measurement") and \
                dialog.parent_settings_widget.measurement is not None:
            self.img_dir = dialog.parent_settings_widget.measurement.directory
        self.matplotlib = MatplotlibAngleSelectorWidget(
            self, detector, asc, run, bin_width, column,
            dialog)
