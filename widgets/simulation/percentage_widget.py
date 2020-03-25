# coding=utf-8
"""
Created on 10.8.2018
Updated on 30.10.2018

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

import os
import platform

import widgets.binding as bnd
import modules.math_functions as mf

from PyQt5 import QtWidgets
from PyQt5 import uic

from widgets.simulation.circle import Circle
from widgets.gui_utils import QtABCMeta


class PercentageWidget(QtWidgets.QWidget):
    """
    Class for a widget that calculates the percentages for given recoils and
    intervals.
    """
    interval_type = bnd.bind("comboBox")

    def __init__(self, recoil_elements, same_interval, use_same_interval,
                 use_individual_intervals, icon_manager,
                 distribution_changed=None, interval_changed=None):
        """
        Initialize the widget.

        Args:
            recoil_elements: List of recoil elements.
            same_interval: Interval that used for all the recoils.
            use_same_interval: Whether to use the same interval for all
                recoils or not.
            use_individual_intervals: Whether to use individual intervals or
                not.
            icon_manager: Icon manager.
        """
        super().__init__()
        self.recoil_elements = recoil_elements
        self.common_interval = same_interval
        self.use_same_interval = use_same_interval
        self.use_individual_intervals = use_individual_intervals
        self.icon_manager = icon_manager

        uic.loadUi(os.path.join("ui_files",
                                "ui_percentage_widget.ui"), self)

        self.setWindowTitle("Percentages")
        self.comboBox.currentIndexChanged.connect(
            lambda: self.__show_percents_and_areas())
        self.icon_manager.set_icon(self.absRelButton,
                                   "depth_profile_rel.svg")
        self.__relative_values = True
        self.absRelButton.setToolTip(
            "Toggle between relative and absolute values")
        self.absRelButton.clicked.connect(self.__show_abs_or_rel_values)

        self._percentage_rows = {}

        self.__show_percents_and_areas()

        # TODO disconnect signals
        # TODO check that recoil is in this widget before recalculating
        if distribution_changed is not None:
            distribution_changed.connect(self._dist_changed)

        if interval_changed is not None:
            interval_changed.connect(self._limits_changed)

    def _calculate_areas_and_percentages(self, start=None, end=None,
                                         rounding=2):
        """Calculate areas and percents for recoil elements within the given
        interval.

        Args:
            start: first point of the interval.
            end: last point of the interval.
            rounding: rounding accuracy of percentage calculation
        Return:

        """
        areas = {}
        percentages = {}
        for recoil in self.recoil_elements:
            try:
                if self._percentage_rows[recoil].ignored:
                    area = 0
                else:
                    area = recoil.calculate_area_for_interval(start, end)
            except (KeyError, AttributeError):
                area = recoil.calculate_area_for_interval(start, end)
            areas[recoil] = area

        for recoil, percentage in zip(
                areas,
                mf.calculate_percentages(areas.values(),
                                         rounding=rounding)):
            percentages[recoil] = percentage

        return areas, percentages

    def __show_abs_or_rel_values(self):
        """
        Show recoil area in absolute or relative format.
        """
        for i in range(self.gridLayout.rowCount()):
            layout = self.gridLayout.itemAtPosition(i, 3)
            if layout:
                layout.widget().deleteLater()

        new_row = 0
        if self.__relative_values:
            self.icon_manager.set_icon(self.absRelButton,
                                       "depth_profile_abs.svg")
            if self.comboBox.currentText().startswith("Same"):
                areas = self.__common_areas
            else:
                areas = self.__individual_areas
            for recoil in self.recoil_elements:
                area = round(areas[recoil] *
                             recoil.reference_density, 4)
                if 'e' in str(recoil.multiplier):
                    power = int(str(recoil.multiplier)[2:])
                    new_power = power - 7
                    label = QtWidgets.QLabel(str(area) + 'e' + str(new_power))
                else:
                    label = QtWidgets.QLabel(str(round(area * 10**-7, 4)))
                self.gridLayout.addWidget(label, new_row, 3)
                new_row += 1
            self.__relative_values = False
        else:
            self.icon_manager.set_icon(self.absRelButton,
                                       "depth_profile_rel.svg")
            if self.comboBox.currentText().startswith("Same"):
                areas = self.__common_areas
            else:
                areas = self.__individual_areas
            for recoil in self.recoil_elements:
                area = areas[recoil]
                label = QtWidgets.QLabel(str(round(area, 4)))
                self.gridLayout.addWidget(label, new_row, 3)
                new_row += 1
            self.__relative_values = True

    def __show_percents_and_areas(self):
        """
        Show the percentages of the recoil elements.
        """
        if self.interval_type == "Same interval":
            areas, percentages = self._calculate_areas_and_percentages(
                start=self.common_interval[0],
                end=self.common_interval[1]
            )
        else:
            areas, percentages = self._calculate_areas_and_percentages()

        if not percentages:
            self.absRelButton.setEnabled(False)
        else:
            self.absRelButton.setEnabled(True)

        for row_idx, recoil in enumerate(sorted(percentages)):
            try:
                self._percentage_rows[recoil].percentage = \
                    percentages[recoil]
                self._percentage_rows[recoil].area = \
                    areas[recoil]
            except KeyError:
                row = PercentageRow(recoil.get_full_name(),
                                    recoil.color,
                                    percentage=percentages[recoil],
                                    area=areas[recoil])
                self._percentage_rows[recoil] = row
                row.ignoreChkbox.stateChanged.connect(
                    self.__show_percents_and_areas)
                self.gridLayout.addWidget(row, row_idx, 0)

    def _dist_changed(self, recoil, _):
        if recoil in self._percentage_rows:
            self.__show_percents_and_areas()

    def _limits_changed(self, low_x, high_x):
        self.common_interval[0] = low_x
        self.common_interval[1] = high_x
        self.__show_percents_and_areas()


def percentage_to_label(instance, attr, value):
    label = getattr(instance, attr)
    label.setText(f"{round(value, 2)}%")


def label_to_percentage(instance, attr):
    label = getattr(instance, attr)
    try:
        return float(label.text()[:-1])
    except ValueError:
        return 0.0


def area_to_label(instance, attr, value):
    label = getattr(instance, attr)
    label.setText(str(round(value, 4)))


def label_to_area(instance, attr):
    label = getattr(instance, attr)
    return float(label.text())


class PercentageRow(QtWidgets.QWidget, bnd.PropertyBindingWidget,
                    metaclass=QtABCMeta):
    percentage = bnd.bind("percentageLabel", fget=label_to_percentage,
                          fset=percentage_to_label)
    area = bnd.bind("areaLabel", fget=label_to_area, fset=area_to_label)
    ignored = bnd.bind("ignoreChkbox")

    def __init__(self, label_text, color="red", **kwargs):
        """Initializes a PercentageRow.

        Args:
            label_text: text to be shown in the main label
            color: color of the Circle that is shown next to label
            kwargs: percentage and area.
        """
        super().__init__()
        layout = QtWidgets.QHBoxLayout()

        text_label = QtWidgets.QLabel(label_text)
        text_label.setMaximumWidth(100)
        text_label.setMinimumWidth(100)

        if platform.system() == "Linux":
            circle = Circle(color, None)
        else:
            circle = Circle(color, (1, 4, 4, 4))

        self.percentageLabel = QtWidgets.QLabel()
        self.areaLabel = QtWidgets.QLabel()

        self.ignoreChkbox = QtWidgets.QCheckBox()

        layout.addWidget(text_label)
        layout.addWidget(circle)
        layout.addWidget(self.percentageLabel)
        layout.addWidget(self.areaLabel)
        layout.addWidget(self.ignoreChkbox)

        self.set_properties(**kwargs)

        self.setLayout(layout)
