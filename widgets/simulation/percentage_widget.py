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

import modules.math_functions as mf

from PyQt5 import QtWidgets
from PyQt5 import uic

from widgets.simulation.circle import Circle


class PercentageWidget(QtWidgets.QWidget):
    """
    Class for a widget that calculates the percentages for given recoils and
    intervals.
    """

    def __init__(self, recoil_elements, same_interval, use_same_interval,
                 use_individual_intervals, icon_manager):
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

        self.ui = uic.loadUi(os.path.join("ui_files",
                                          "ui_percentage_widget.ui"), self)

        self.setWindowTitle("Percentages")
        self.ui.comboBox.currentIndexChanged.connect(
            lambda: self.__show_percents_and_areas())
        self.icon_manager.set_icon(self.ui.absRelButton,
                                   "depth_profile_rel.svg")
        self.__relative_values = True
        self.ui.absRelButton.setToolTip(
            "Toggle between relative and absolute values")
        self.ui.absRelButton.clicked.connect(self.__show_abs_or_rel_values)

        self.__common_areas, self.__common_percentages = \
            self.__calculate_percents(start=self.common_interval[0],
                                      end=self.common_interval[1])

        self.__individual_areas, self.__individual_percentages = \
            self.__calculate_percents()

        self.__show_percents_and_areas()

    def __calculate_percents(self, start=None, end=None, rounding=2):
        """
        Calculate percents for recoil elements.
        """
        areas = {}
        percentages = {}
        for recoil in self.recoil_elements:
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
        for i in range(self.ui.gridLayout.rowCount()):
            layout = self.ui.gridLayout.itemAtPosition(i, 3)
            if layout:
                layout.widget().deleteLater()

        new_row = 0
        if self.__relative_values:
            self.icon_manager.set_icon(self.ui.absRelButton,
                                       "depth_profile_abs.svg")
            if self.ui.comboBox.currentText().startswith("Same"):
                areas = self.__common_areas
            else:
                areas = self.__individual_areas
            for recoil in self.recoil_elements:
                area = round(areas[recoil] * \
                       recoil.reference_density, 4)
                if 'e' in str(recoil.multiplier):
                    power = int(str(recoil.multiplier)[2:])
                    new_power = power - 7
                    label = QtWidgets.QLabel(str(area) + 'e' + str(new_power))
                else:
                    label = QtWidgets.QLabel(str(round(area * 10**-7, 4)))
                self.ui.gridLayout.addWidget(label, new_row, 3)
                new_row += 1
            self.__relative_values = False
        else:
            self.icon_manager.set_icon(self.ui.absRelButton,
                                       "depth_profile_rel.svg")
            if self.ui.comboBox.currentText().startswith("Same"):
                areas = self.__common_areas
            else:
                areas = self.__individual_areas
            for recoil in self.recoil_elements:
                area = areas[recoil]
                label = QtWidgets.QLabel(str(round(area, 4)))
                self.ui.gridLayout.addWidget(label, new_row, 3)
                new_row += 1
            self.__relative_values = True

    def __show_percents_and_areas(self):
        """
        Show the percentages of the recoil elements.
        """
        # Show percentages in widget with element information and color (also
        #  interval which was used?)
        for i in range(self.ui.gridLayout.rowCount()):
            for j in range(self.ui.gridLayout.columnCount()):
                layout = self.ui.gridLayout.itemAtPosition(i, j)
                if layout:
                    layout.widget().deleteLater()

        new_row = 0
        if self.ui.comboBox.currentText().startswith("Same"):
            if not self.__common_percentages:
                self.ui.absRelButton.setEnabled(False)
            else:
                self.ui.absRelButton.setEnabled(True)
            for recoil, percentage in self.__common_percentages.items():
                dimension = (1, 4, 4, 4)

                if platform.system() == "Linux":
                    dimension = None

                circle = Circle(recoil.color, dimension)
                if recoil.element.isotope:
                    text = "Element: " + "<sup>" + str(recoil.element.isotope)\
                           + "</sup>" + recoil.element.symbol + " "
                else:
                    text = "Element: " + recoil.element.symbol + " "
                percentage = str(percentage) + "%"
                if self.__relative_values:
                    area = self.__common_areas[recoil]
                    label = QtWidgets.QLabel(str(round(area, 4)))
                else:
                    area = round(self.__common_areas[recoil] * \
                           recoil.reference_density, 4)
                    label = QtWidgets.QLabel(str(area) + str(
                        recoil.multiplier)[1:])

                self.ui.gridLayout.addWidget(QtWidgets.QLabel(text),
                                             new_row, 0)
                self.ui.gridLayout.addWidget(circle, new_row, 1)
                self.ui.gridLayout.addWidget(QtWidgets.QLabel(percentage),
                                             new_row, 2)
                self.ui.gridLayout.addWidget(label, new_row, 3)
                new_row += 1
        else:
            if not self.__individual_percentages:
                self.ui.absRelButton.setEnabled(False)
            else:
                self.ui.absRelButton.setEnabled(True)
            for recoil, percentage in self.__individual_percentages.items():
                dimension = (1, 4, 4, 4)

                if platform.system() == "Linux":
                    dimension = None

                circle = Circle(recoil.color, dimension)
                if recoil.element.isotope:
                    text = "Element: " + "<sup>" + str(recoil.element.isotope)\
                           + "</sup>" + recoil.element.symbol + " "
                else:
                    text = "Element: " + recoil.element.symbol + " "
                percentage = str(percentage) + "%"
                if self.__relative_values:
                    area = self.__individual_areas[recoil]
                    label = QtWidgets.QLabel(str(round(area, 4)))
                else:
                    area = round(self.__individual_areas[recoil] * \
                           recoil.reference_density, 4)
                    label = QtWidgets.QLabel(str(area) + str(
                        recoil.multiplier)[1:])

                self.ui.gridLayout.addWidget(QtWidgets.QLabel(text), new_row, 0)
                self.ui.gridLayout.addWidget(circle, new_row, 1)
                self.ui.gridLayout.addWidget(QtWidgets.QLabel(percentage),
                                             new_row, 2)
                self.ui.gridLayout.addWidget(label, new_row, 3)
                new_row += 1
