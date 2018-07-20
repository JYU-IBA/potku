# coding=utf-8
"""
Created on 12.7.2018
Updated on 20.7.2018

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2018 Heta Rekilä

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
__author__ = "Heta Rekilä"
__version__ = "2.0"

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt


class PointCoordinatesWidget(QtWidgets.QWidget):
    """
    Class for handling point coordinates spin boxes.
    """

    def __init__(self, parent):
        """
        Initializes the widget.

        Args:
            parent: RecoilAtomDistributionWidget.
        """
        super().__init__()

        self.parent = parent

        vertical_layout = QtWidgets.QVBoxLayout()
        vertical_layout.setContentsMargins(0, 0, 0, 0)
        horizontal_layout_x = QtWidgets.QHBoxLayout()
        horizontal_layout_x.setContentsMargins(0, 0, 0, 0)

        horizontal_layout_y = QtWidgets.QHBoxLayout()
        horizontal_layout_y.setContentsMargins(0, 0, 0, 0)

        # Point x coordinate spinbox
        self.x_coordinate_box = QtWidgets.QDoubleSpinBox(self)
        # Set decimal pointer to .
        self.x_coordinate_box.setLocale(self.parent.locale)
        self.x_coordinate_box.setToolTip("X coordinate of selected point")
        self.x_coordinate_box.setSingleStep(0.1)
        self.x_coordinate_box.setDecimals(2)
        self.x_coordinate_box.setMinimum(0)
        self.x_coordinate_box.setMaximum(1000000000000)
        self.x_coordinate_box.setMaximumWidth(62)
        self.x_coordinate_box.setKeyboardTracking(False)
        self.x_coordinate_box.valueChanged.connect(
            self.parent.set_selected_point_x)
        self.x_coordinate_box.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.actionXMultiply = QtWidgets.QAction(self)
        self.actionXMultiply.setText("Multiply with value in clipboard\n(" +
                                     self.parent.ratio_str + ")")
        self.actionXMultiply.triggered.connect(
            lambda: self.__multiply_coordinate(self.x_coordinate_box))
        self.x_coordinate_box.addAction(self.actionXMultiply)

        self.actionXUndo = QtWidgets.QAction(self)
        self.actionXUndo.setText("Undo multipy")
        self.actionXUndo.triggered.connect(
            lambda: self.undo(self.x_coordinate_box))
        self.actionXUndo.setEnabled(False)
        self.x_coordinate_box.addAction(self.actionXUndo)

        self.x_coordinate_box.setEnabled(False)

        # X label
        label_x = QtWidgets.QLabel("x:")

        # Point y coordinate spinbox
        self.y_coordinate_box = QtWidgets.QDoubleSpinBox(self)
        # Set decimal pointer to .
        self.y_coordinate_box.setLocale(self.parent.locale)
        self.y_coordinate_box.setToolTip("Y coordinate of selected point")
        self.y_coordinate_box.setSingleStep(0.1)
        self.y_coordinate_box.setDecimals(4)
        self.y_coordinate_box.setMaximum(1000000000000)
        self.y_coordinate_box.setMaximumWidth(62)
        self.y_coordinate_box.setMinimum(0.0)
        self.y_coordinate_box.setKeyboardTracking(False)
        self.y_coordinate_box.valueChanged.connect(
            self.parent.set_selected_point_y)
        self.y_coordinate_box.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.actionYMultiply = QtWidgets.QAction(self)
        self.actionYMultiply.setText("Multiply with value in clipboard\n(" +
                                     self.parent.ratio_str + ")")
        self.actionYMultiply.triggered.connect(
            lambda: self.__multiply_coordinate(self.y_coordinate_box))
        self.y_coordinate_box.addAction(self.actionYMultiply)

        self.actionYUndo = QtWidgets.QAction(self)
        self.actionYUndo.setText("Undo multiply")
        self.actionYUndo.triggered.connect(
            lambda: self.undo(self.y_coordinate_box))
        self.actionYUndo.setEnabled(False)
        self.y_coordinate_box.addAction(self.actionYUndo)

        self.y_coordinate_box.setEnabled(False)

        # Y label
        label_y = QtWidgets.QLabel("y:")

        horizontal_layout_x.addWidget(label_x)
        horizontal_layout_x.addWidget(self.x_coordinate_box)

        horizontal_layout_y.addWidget(label_y)
        horizontal_layout_y.addWidget(self.y_coordinate_box)

        vertical_layout.addLayout(horizontal_layout_x)
        vertical_layout.addLayout(horizontal_layout_y)

        self.setLayout(vertical_layout)

    def undo(self, spinbox):
        """
        Undo change to spinbox value.
        """
        if spinbox == self.x_coordinate_box:
            enable = False
            for point in self.parent.selected_points:
                if not point.previous_x:
                    continue
                old_value = point.previous_x.pop()
                self.parent.set_selected_point_x(old_value, point)
                if not point.previous_x:
                    self.actionXUndo.setEnabled(False)
                else:
                    enable = True
            if enable:
                self.actionXUndo.setEnabled(True)
        else:
            enable = False
            for point in self.parent.selected_points:
                if not point.previous_y:
                    continue
                old_value = point.previous_y.pop()
                self.parent.set_selected_point_y(old_value, point)
                if not point.previous_y:
                    self.actionYUndo.setEnabled(False)
                else:
                    enable = True
            if enable:
                self.actionYUndo.setEnabled(True)
        # spinbox.setValue(old_value)

    def __multiply_coordinate(self, spinbox):
        """
        Multiply the spinbox's value with the value in clipboard.

        Args:
            spinbox: Spinbox whose value is multiplied.
        """
        try:
            ratio = float(self.parent.ratio_str)
            if spinbox == self.x_coordinate_box:
                for point in reversed(self.parent.selected_points):
                    if point.get_y() == 0.0:
                        if not self.parent.full_edit_on or \
                                self.parent.current_element_simulation. \
                                        recoil_elements[0] != \
                                self.parent.current_recoil_element:
                            continue
                    point.previous_x.append(point.get_x())
                    coord = point.get_x()
                    new_coord = round(ratio * coord, 3)
                    if new_coord > self.parent.target_thickness:
                        new_coord = self.parent.target_thickness
                    self.parent.set_selected_point_x(new_coord, point)
                self.actionXUndo.setEnabled(True)
            else:
                for point in reversed(self.parent.selected_points):
                    if point.get_y() == 0.0:
                        if not self.parent.full_edit_on or \
                                self.parent.current_element_simulation. \
                                        recoil_elements[0] != \
                                self.parent.current_recoil_element:
                            continue
                    point.previous_y.append(point.get_y())
                    coord = point.get_y()
                    new_coord = round(ratio * coord, 3)
                    self.parent.set_selected_point_y(new_coord, point)
                self.actionYUndo.setEnabled(True)
            # spinbox.setValue(new_coord)
        except ValueError:
            QtWidgets.QMessageBox.critical(self.parent.parent, "Error",
                                           "Value '" + self.parent.ratio_str +
                                           "' is not suitable for "
                                           "multiplying.\n\nPlease copy a "
                                           "suitable value to clipboard.",
                                           QtWidgets.QMessageBox.Ok,
                                           QtWidgets.QMessageBox.Ok)
