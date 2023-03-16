"""
Created on 18.01.2022

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2019 Heta Rekilä, 2020 Juhani Sundell; 2022 Tuomas Pitkänen

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
__author__ = "Heta Rekilä \n Juhani Sundell \n Tuomas Pitkänen"
__version__ = "2.0"


import abc

import widgets.binding as bnd
import widgets.gui_utils as gutils

from modules.nsgaii import OptimizationType

from widgets.binding import PropertyBindingWidget
from widgets.gui_utils import QtABCMeta
from widgets.scientific_spinbox import ScientificSpinBox

from PyQt5 import QtWidgets
from PyQt5 import uic
from PyQt5.QtCore import QLocale
from PyQt5.QtCore import Qt


# TODO: Reduce copy-paste

_REC_TYPES = {
    "4-point box": ("box", 5),
    "6-point box": ("box", 7),
    "8-point two-peak": ("two-peak", 9),
    "10-point two-peak": ("two-peak", 11),
}
# Update _REC_TYPES to enable two-way binding based on solution sizes.
_REC_TYPES.update({
    (sol_size, key)
    for key, (rtype, sol_size) in _REC_TYPES.items()
})


def recoil_from_combobox(instance, combobox):
    """Converts the text value shown in combobox to a recoil type.
    """
    qbox = getattr(instance, combobox)
    return _REC_TYPES[qbox.currentText()][0]


def sol_size_from_combobox(instance, combobox):
    """Converts the text value shown in combobox to solution size.
    """
    qbox = getattr(instance, combobox)
    return _REC_TYPES[qbox.currentText()][1]


def sol_size_to_combobox(instance, combobox, value):
    """Sets the selected item in the given combobox based on the solution size.
    """
    qbox = getattr(instance, combobox)
    try:
        str_value = _REC_TYPES[value]
        qbox.setCurrentIndex(qbox.findText(str_value, Qt.MatchFixedString))
    except KeyError:
        pass


class LinearOptimizationParameterWidget(QtWidgets.QWidget,
                                        PropertyBindingWidget,
                                        abc.ABC,
                                        metaclass=QtABCMeta):
    """Abstract base class for linear recoil and fluence optimization parameter
    widgets.
    """
    # Common properties
    sample_count = bnd.bind("sampleCountSpinBox")
    sample_width = bnd.bind("sampleWidthDoubleSpinBox")
    sample_polynomial_degree = bnd.bind("samplePolynomialDegreeSpinBox")
    fitting_iteration_count = bnd.bind("fittingIterationCountSpinBox")
    is_skewed = bnd.bind("skewedCheckBox")
    stop_percent = bnd.bind("percentDoubleSpinBox")
    check_time = bnd.bind("timeSpinBox")
    check_max = bnd.bind("maxTimeEdit")
    check_min = bnd.bind("minTimeEdit")
    skip_simulation = bnd.bind("skip_sim_chk_box")

    @abc.abstractmethod
    def optimization_type(self) -> OptimizationType:
        pass

    def __init__(self, ui_file, **kwargs):
        """Initializes a optimization parameter widget.

        Args:
            ui_file: relative path to a ui_file
            kwargs: values to show in the widget
        """
        super().__init__()
        uic.loadUi(ui_file, self)

        locale = QLocale.c()
        self.sampleWidthDoubleSpinBox.setLocale(locale)
        self.samplePolynomialDegreeSpinBox.setLocale(locale)
        self.percentDoubleSpinBox.setLocale(locale)

        self.skip_sim_chk_box.stateChanged.connect(self.enable_sim_params)
        self.set_properties(**kwargs)
        self.enable_sim_params()

    def enable_sim_params(self, *_):
        """Either enables or disables simulation parameters depending on the
        value of skip_simulation parameter.

        Args:
            *_: not used
        """
        enable = not self.skip_simulation

        self.processesSpinBox.setEnabled(enable)
        self.percentDoubleSpinBox.setEnabled(enable)
        self.timeSpinBox.setEnabled(enable)
        self.minTimeEdit.setEnabled(enable)
        self.maxTimeEdit.setEnabled(enable)


class LinearOptimizationRecoilParameterWidget(LinearOptimizationParameterWidget):
    """
    Class that handles linear recoil optimization parameters' ui.
    """

    # Recoil specific properties
    upper_limits = bnd.multi_bind(
        ("upperXDoubleSpinBox", "upperYDoubleSpinBox")
    )
    lower_limits = bnd.multi_bind(
        ("lowerXDoubleSpinBox", "lowerYDoubleSpinBox")
    )

    # sol_size values are unique (5, 7, 9 or 11) so they can be used in
    # two-way binding
    sol_size = bnd.bind("recoilTypeComboBox", fget=sol_size_from_combobox,
                        fset=sol_size_to_combobox)
    recoil_type = bnd.bind("recoilTypeComboBox", fget=recoil_from_combobox,
                           twoway=False)

    @property
    def optimization_type(self) -> OptimizationType:
        return OptimizationType.RECOIL

    def __init__(self, **kwargs):
        """Initialize the widget.

        Args:
            kwargs: property values to be shown in the widget.
        """
        ui_file = gutils.get_ui_dir() / "ui_optimization_linear_recoil_params.ui"
        super().__init__(ui_file, **kwargs)
        locale = QLocale.c()
        self.upperXDoubleSpinBox.setLocale(locale)
        self.lowerXDoubleSpinBox.setLocale(locale)
        self.upperYDoubleSpinBox.setLocale(locale)
        self.lowerYDoubleSpinBox.setLocale(locale)


class LinearOptimizationFluenceParameterWidget(LinearOptimizationParameterWidget):
    """
    Class that handles linear fluence optimization parameters' ui.
    """

    # Fluence specific properties
    upper_limits = bnd.bind("fluenceDoubleSpinBox")

    @property
    def lower_limits(self):
        return 0.0

    @property
    def sol_size(self):
        return 1

    @property
    def optimization_type(self) -> OptimizationType:
        return OptimizationType.FLUENCE

    def __init__(self, **kwargs):
        """Initialize the widget.

        Args:
            kwargs: property values to be shown in the widget.
        """
        ui_file = gutils.get_ui_dir() / "ui_optimization_linear_fluence_params.ui"
        super().__init__(ui_file, **kwargs)
        self.fluenceDoubleSpinBox = ScientificSpinBox(10e12)
        self.fluence_form_layout.addRow(
            "Upper limit", self.fluenceDoubleSpinBox)
