# coding=utf-8
"""
Created on 20.5.2019
Updated on 22.5.2019

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2019 Heta Rekilä

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

import os
import abc
import itertools

import widgets.gui_utils as gutils

from PyQt5 import QtWidgets
from PyQt5 import uic
from PyQt5.QtCore import QLocale

_REC_TYPES = {
    "4-point box": ("box", 5),
    "6-point box": ("box", 7),
    "8-point two-peak": ("two-peak", 9),
    "10-point two-peak": ("two-peak", 11),
}


def time_conversion(qtime):
    """Converts QTime object to seconds.
    """
    return qtime.hour() * 60 * 60 + qtime.minute() * 60 + qtime.second()


def recoil_type_conversion(string):
    """Returns the recoil type for the given string.
    """
    return _REC_TYPES[string][0]


def sol_size_conversion(string):
    """Returns solution size for given string.
    """
    return _REC_TYPES[string][1]


class OptimizationParameterWidget(QtWidgets.QWidget,
                                  gutils.BindingPropertyWidget,
                                  abc.ABC,
                                  metaclass=gutils.QtABCMeta):
    """Abstract base class for recoil and fluence optimization parameter
    widgets.
    """
    # Common properties
    gen = gutils.bind("generationSpinBox", int)
    pop_size = gutils.bind("populationSpinBox", int)
    number_of_processes = gutils.bind("processesSpinBox", int)
    cross_p = gutils.bind("crossoverProbDoubleSpinBox", float)
    mut_p = gutils.bind("mutationProbDoubleSpinBox", float)
    stop_percent = gutils.bind("percentDoubleSpinBox", float)
    check_time = gutils.bind("timeSpinBox", float)
    check_max = gutils.bind("maxTimeEdit", time_conversion)
    check_min = gutils.bind("minTimeEdit", time_conversion)

    def __init__(self, ui_file, **kwargs):
        """Initializes a optimization parameter widget.

        Args:
            ui_file: relative path to a ui_file
            kwargs: values to show in the widget
        """
        super().__init__()
        uic.loadUi(ui_file, self)

        locale = QLocale.c()
        self.crossoverProbDoubleSpinBox.setLocale(locale)
        self.mutationProbDoubleSpinBox.setLocale(locale)
        self.percentDoubleSpinBox.setLocale(locale)

        self.set_properties(**kwargs)


class OptimizationRecoilParameterWidget(OptimizationParameterWidget):
    """
    Class that handles the recoil optimization parameters' ui.
    """

    # Recoil specific properties
    upper_limits = gutils.multi_bind(
        ("upperXDoubleSpinBox", "upperYDoubleSpinBox"),
        (float, float)
    )
    lower_limits = gutils.multi_bind(
        ("lowerXDoubleSpinBox", "lowerYDoubleSpinBox"),
        (float, float)
    )
    sol_size = gutils.bind("recoilTypeComboBox", sol_size_conversion,
                           twoway=False)
    recoil_type = gutils.bind("recoilTypeComboBox", recoil_type_conversion,
                              twoway=False)

    @property
    def optimize_recoil(self):
        return True

    def __init__(self, **kwargs):
        """Initialize the widget.

        Args:
            kwargs: property values to be shown in the widget.
        """
        ui_file = os.path.join("ui_files", "ui_optimization_recoil_params.ui")
        super().__init__(ui_file, **kwargs)

        locale = QLocale.c()
        self.upperXDoubleSpinBox.setLocale(locale)
        self.lowerXDoubleSpinBox.setLocale(locale)
        self.upperYDoubleSpinBox.setLocale(locale)
        self.lowerYDoubleSpinBox.setLocale(locale)


class OptimizationFluenceParameterWidget(OptimizationParameterWidget):
    """
    Class that handles the fluence optimization parameters' ui.
    """

    # Fluence specific properties
    upper_limits = gutils.bind("fluenceDoubleSpinBox", float)
    dis_c = gutils.bind("disCSpinBox", int)
    dis_m = gutils.bind("disMSpinBox", int)

    @property
    def lower_limits(self):
        return 0.0

    @property
    def sol_size(self):
        return 1

    @property
    def optimize_recoil(self):
        return False

    def __init__(self, **kwargs):
        """Initialize the widget.

        Args:
            kwargs: property values to be shown in the widget.
        """
        ui_file = os.path.join("ui_files", "ui_optimization_fluence_params.ui")
        super().__init__(ui_file, **kwargs)
