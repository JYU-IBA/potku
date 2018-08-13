# coding=utf-8
"""
Created on 10.8.2018
Updated on 13.8.2018

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

from PyQt5 import QtWidgets
from PyQt5 import uic


class PercentageWidget(QtWidgets.QWidget):
    """
    Class for a widget that calculates the percentages for given recoils and
    intervals.
    """

    def __init__(self, recoil_elements, same_interval, use_same_interval,
                 use_individual_intervals):
        """
        Initialize the widget.

        Args:
            recoil_elements: List of recoil elements.
            same_interval: Interval that used for all the recoils.
            use_same_interval: Whether to use the same interval for all
            recoils or not.
            use_individual_intervals: Whether to use individual intervals or
            not.
        """
        super().__init__()
        self.recoil_elements = recoil_elements
        self.common_interval = same_interval
        self.use_same_interval = use_same_interval
        self.use_individual_intervals = use_individual_intervals
        self.ui = uic.loadUi(os.path.join("ui_files",
                                          "ui_percentage_widget.ui"), self)

        self.setWindowTitle("Percentages")
        self.ui.comboBox.currentIndexChanged.connect(
            lambda: self.__show_percents())

        self.__common_percentages = {}
        self.__common_areas = {}

        self.__individual_percentages = {}
        self.__individual_areas = {}

        self.__calculate_percents()
        self.__show_percents()

    def __calculate_percents(self):
        """
        Calculate percents for recoil elements.
        """
        # Calculate the areas of the recoils
        # Calculate percentages for same interval (if is used)
        # Calculate percentage for individual intervals (if all have none,
        # don't count, if some don't have, use all area)
        if self.use_same_interval:
            start = self.common_interval[0]
            end = self.common_interval[1]
            for recoil in self.recoil_elements:
                area = recoil.calculate_area_for_interval(start, end)
                self.__common_areas[recoil] = area

            total_area = 0
            for area in self.__common_areas.values():
                total_area += area

            for recoil, area in self.__common_areas.items():
                self.__common_percentages[recoil] = round(
                    ((area / total_area) * 100), 2)

        if self.use_individual_intervals:
            for recoil in self.recoil_elements:
                area = recoil.calculate_area_for_interval()
                self.__individual_areas[recoil] = area

            total_area = 0
            for area in self.__individual_areas.values():
                total_area += area

            for recoil, area in self.__individual_areas.items():
                self.__individual_percentages[recoil] = round(
                    ((area / total_area) * 100), 2)

    def __show_percents(self):
        """
        Show the percentages of the recoil elements.
        """
        # Show percentages in widget with element information and color (also
        #  interval which was used?)
        for i in range(self.ui.percentageLayout.count()):
            self.ui.percentageLayout.itemAt(i).widget().close()

        if self.ui.comboBox.currentText().startswith("Same"):
            for recoil, percentage in self.__common_percentages.items():
                text = "Element: " + recoil.prefix + " " + recoil.name + \
                    "  " + str(percentage) + "%"
                self.ui.percentageLayout.addWidget(QtWidgets.QLabel(text))
        else:
            for recoil, percentage in self.__individual_percentages.items():
                text = "Element: " + recoil.prefix + " " + recoil.name + \
                    "  " + str(percentage) + "%"
                self.ui.percentageLayout.addWidget(QtWidgets.QLabel(text))
