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
__author__ = "Heta Rekilä \n Juhani Sundell"
__version__ = "2.0"

import platform

import widgets.binding as bnd
import modules.math_functions as mf
import widgets.gui_utils as gutils

from modules.recoil_element import RecoilElement

from typing import List

from PyQt5 import QtWidgets
from PyQt5 import uic
from PyQt5.QtCore import Qt

from widgets.simulation.circle import Circle
from widgets.gui_utils import QtABCMeta


class PercentageWidget(QtWidgets.QWidget):
    """
    Class for a widget that calculates the percentages for given recoils and
    intervals.
    """
    # Interval is either same interval for all elements or individual interval
    # for each element.
    interval_type = bnd.bind("comboBox")

    def __init__(self, recoil_elements: List[RecoilElement], common_interval,
                 icon_manager, distribution_changed=None,
                 interval_changed=None):
        """
        Initialize the widget.

        Args:
            recoil_elements: List of recoil elements.
            common_interval: Interval that used for all the recoils.
            icon_manager: Icon manager.
        """
        super().__init__()
        uic.loadUi(gutils.get_ui_dir() / "ui_percentage_widget.ui", self)

        # Stores the PercentageRow objects for each recoil
        self._percentage_rows = {
            recoil: None
            for recoil in recoil_elements
        }
        if not common_interval:
            try:
                self.common_interval = list(
                    recoil_elements[0].get_individual_interval())
            except IndexError:
                self.common_interval = [0, 0]
        else:
            self.common_interval = common_interval

        self.icon_manager = icon_manager
        self.setWindowTitle("Percentages")

        self.comboBox.currentIndexChanged.connect(
            self.__show_percents_and_areas)

        self.icon_manager.set_icon(self.absRelButton,
                                   "depth_profile_rel.svg")
        self.__relative_values = True
        self.absRelButton.setToolTip("Toggle between relative and absolute "
                                     "values.")
        self.absRelButton.clicked.connect(self.__show_abs_or_rel_values)

        self.__dist_changed_sig = distribution_changed
        self.__interval_changed_sig = interval_changed
        if distribution_changed is not None:
            distribution_changed.connect(self._dist_changed)

        if interval_changed is not None:
            interval_changed.connect(self._limits_changed)

        self.__show_percents_and_areas()

    def closeEvent(self, event):
        """Overrides QWidget's closeEvent. Disconnects slots from signals.
        """
        try:
            self.__dist_changed_sig.disconnect(self._dist_changed)
        except (TypeError, AttributeError):
            # Signal was either already disconnected or None
            pass
        try:
            self.__interval_changed_sig.disconnect(self._limits_changed)
        except (TypeError, AttributeError):
            # Signal was either already disconnected or None
            pass
        event.accept()

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
        for recoil in self._percentage_rows:
            try:
                if not self._percentage_rows[recoil].selected:
                    area = 0
                else:
                    if start is None:
                        start_ = recoil.area_limits[0].get_xdata()[0]
                    else:
                        start_ = start

                    if end is None:
                        end_ = recoil.area_limits[-1].get_xdata()[0]
                    else:
                        end_ = end
                    area = recoil.calculate_area_for_interval(start_, end_)
            except (KeyError, AttributeError, IndexError):
                area = recoil.calculate_area_for_interval(start, end)

            if not self.__relative_values:
                # TODO label text needs to reformatted when using absolute
                #  values. See previous version of Potku for reference.
                area *= recoil.reference_density

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
        if self.__relative_values:
            self.icon_manager.set_icon(self.absRelButton,
                                       "depth_profile_abs.svg")
        else:
            self.icon_manager.set_icon(self.absRelButton,
                                       "depth_profile_rel.svg")

        self.__relative_values = not self.__relative_values
        self.__show_percents_and_areas()

    def __show_percents_and_areas(self):
        """
        Show the percentages of the recoil elements.
        """
        if self.interval_type == "Common interval":
            areas, percentages = self._calculate_areas_and_percentages(
                start=self.common_interval[0],
                end=self.common_interval[1]
            )
        else:
            areas, percentages = self._calculate_areas_and_percentages()

        for row_idx, recoil in enumerate(sorted(percentages)):
            try:
                self._percentage_rows[recoil].percentage = \
                    percentages[recoil]
                self._percentage_rows[recoil].area = \
                    areas[recoil]
            except (KeyError, AttributeError):
                row = PercentageRow(recoil.get_full_name(),
                                    recoil.color,
                                    percentage=percentages[recoil],
                                    area=areas[recoil])
                self._percentage_rows[recoil] = row
                row.selectedCheckbox.stateChanged.connect(
                    self.__show_percents_and_areas)
                self.gridLayout.addWidget(row, row_idx, 0)

    def _dist_changed(self, recoil, _):
        """Callback that is executed when RecoilElement distribution is changed.
        Checks that the recoil is being displayed in the Widget and then calls
        _show_percents_and_areas.

        Args:
            recoil: RecoilElement which distribution has changed.
            _: unused ElementSimulation object.
        """
        if recoil in self._percentage_rows:
            self.__show_percents_and_areas()

    def _limits_changed(self, low_x, high_x):
        """Updates the common_interval with given x values and calls
        __show_percents_and_areas.
        """
        self.common_interval[0] = low_x
        self.common_interval[1] = high_x
        self.__show_percents_and_areas()


# Helper functions that turn areas and percentages into label texts
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
    """PercentageRow is used to display percentage and area for each
    RecoilElement in the PercentageWidget.
    """
    percentage = bnd.bind("percentageLabel", fget=label_to_percentage,
                          fset=percentage_to_label)
    area = bnd.bind("areaLabel", fget=label_to_area, fset=area_to_label)
    selected = bnd.bind("selectedCheckbox")

    def __init__(self, label_text, color="red", **kwargs):
        """Initializes a PercentageRow.

        Args:
            label_text: text to be shown in the main label
            color: color of the Circle that is shown next to label
            kwargs: percentage and area.
        """
        super().__init__()
        layout = QtWidgets.QHBoxLayout()
        layout.setAlignment(Qt.AlignBottom)

        text_label = QtWidgets.QLabel(label_text)
        text_label.setMaximumWidth(100)
        text_label.setMinimumWidth(100)

        if platform.system() == "Linux":
            circle = Circle(color, None)
        else:
            circle = Circle(color, (1, 4, 4, 4))

        circle.setMinimumWidth(25)
        circle.setMaximumWidth(25)

        self.percentageLabel = QtWidgets.QLabel()
        self.percentageLabel.setMinimumWidth(80)
        self.percentageLabel.setMaximumWidth(80)

        self.areaLabel = QtWidgets.QLabel()
        self.areaLabel.setMinimumWidth(40)
        self.areaLabel.setMaximumWidth(40)

        self.selectedCheckbox = QtWidgets.QCheckBox()
        self.selectedCheckbox.setToolTip(f"Deselect to ignore the element "
                                         "from percentage and area "
                                         "calculations.")
        self.selectedCheckbox.setChecked(True)

        layout.addWidget(text_label)
        layout.addWidget(circle)
        layout.addWidget(self.percentageLabel)
        layout.addWidget(self.areaLabel)
        layout.addWidget(self.selectedCheckbox)

        self.set_properties(**kwargs)

        self.setLayout(layout)
