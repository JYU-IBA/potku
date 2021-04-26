# coding=utf-8
"""
Created on 21.3.2013
Updated on 30.5.2018

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2013-2018 Jarkko Aalto, Severi Jääskeläinen, Samuel Kaiponen,
Timo Konu, Samuli Kärkkäinen, Samuli Rahkonen, Miika Raunio, Heta Rekilä and
Sinikka Siironen, 2020 Juhani Sundell, Tuomas Pitkänen

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
__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen" \
             " \n Samuli Rahkonen \n Miika Raunio \n Severi Jääskelänen \n " \
             "Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen" \
             "Juhani Sundell \n Tuomas Pitkänen"
__version__ = "2.0"

from typing import Tuple, Optional

from PyQt5 import uic
from PyQt5 import QtWidgets

from modules.enums import ToFEColorScheme, AxisRangeMode
import widgets.binding as bnd
import widgets.gui_utils as gutils


class TofeGraphSettingsWidget(QtWidgets.QDialog):
    """Graph settings dialog for the ToF-E histogram graph.
    """
    OKButton: QtWidgets.QPushButton
    cancelButton: QtWidgets.QPushButton
    colorbox: QtWidgets.QComboBox
    btn_group_range_mode: QtWidgets.QButtonGroup
    spin_range_x_min: QtWidgets.QSpinBox
    spin_range_x_max: QtWidgets.QSpinBox
    spin_range_y_min: QtWidgets.QSpinBox
    spin_range_y_max: QtWidgets.QSpinBox

    color_scheme: ToFEColorScheme = bnd.bind("colorbox")
    bin_x: int = bnd.bind("spin_bin_x")
    bin_y: int = bnd.bind("spin_bin_y")
    invert_x: bool = bnd.bind("chk_invert_x")
    invert_y: bool = bnd.bind("chk_invert_y")
    show_axis_ticks: bool = bnd.bind("chk_axes_ticks")
    transpose_axes: bool = bnd.bind("transposeAxesCheckBox")
    x_range: Tuple[int, int] = bnd.multi_bind(
        ["spin_range_x_min", "spin_range_x_max"])
    y_range: Tuple[int, int] = bnd.multi_bind(
        ["spin_range_y_min", "spin_range_y_max"])
    axis_range_mode: int = bnd.bind("btn_group_range_mode")

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        """Inits ToF-E graph histogram graph settings dialog.
        
        Args:
            parent: QWidget passed down to super().__init__.
        """
        super().__init__(parent)
        uic.loadUi(gutils.get_ui_dir() / "ui_tofe_graph_settings.ui", self)

        gutils.fill_combobox(self.colorbox, ToFEColorScheme)
        gutils.set_min_max_handlers(
            self.spin_range_x_min, self.spin_range_x_max
        )
        gutils.set_min_max_handlers(
            self.spin_range_y_min, self.spin_range_y_max
        )
        gutils.set_btn_group_data(self.btn_group_range_mode, AxisRangeMode)
        self.btn_group_range_mode.buttonClicked.connect(
            self._enable_manual_axes_ranges)

        self.OKButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)

    def _enable_manual_axes_ranges(self):
        """Enables axes range spin boxes if manual mode is on.
        """
        is_disabled = self.axis_range_mode == AxisRangeMode.AUTOMATIC
        self.spin_range_x_min.setDisabled(is_disabled)
        self.spin_range_x_max.setDisabled(is_disabled)
        self.spin_range_y_min.setDisabled(is_disabled)
        self.spin_range_y_max.setDisabled(is_disabled)
