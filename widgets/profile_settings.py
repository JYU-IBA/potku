# coding=utf-8
"""
Created on 10.4.2018
Updated on 1.8.2018

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2018 Severi Jääskeläinen, Samuel Kaiponen, Heta Rekilä and
Sinikka Siironen

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
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä " \
             "\n Sinikka Siironen \n Juhani Sundell"

import widgets.input_validation as iv
import widgets.binding as bnd
import widgets.gui_utils as gutils
from modules.measurement import Measurement

from pathlib import Path

from PyQt5 import QtWidgets
from PyQt5 import uic
from PyQt5.QtCore import QLocale


class ProfileSettingsWidget(QtWidgets.QWidget, bnd.PropertyTrackingWidget,
                            metaclass=gutils.QtABCMeta):
    """Class for creating a profile settings tab.
    """
    # TODO track_change may not be necessary here, as none of these values
    #   are used for simulations
    profile_name = bnd.bind("nameLineEdit", track_change=True)
    profile_description = bnd.bind(
        "descriptionPlainTextEdit", track_change=True)
    profile_modification_time = bnd.bind(
        "dateLabel", fget=bnd.unix_time_from_label,
        fset=bnd.unix_time_to_label)

    reference_density = bnd.bind(
        "referenceDensityDoubleSpinBox", track_change=True)
    number_of_depth_steps = bnd.bind(
        "numberOfDepthStepsSpinBox", track_change=True)
    depth_step_for_stopping = bnd.bind(
        "depthStepForStoppingSpinBox", track_change=True)
    depth_step_for_output = bnd.bind(
        "depthStepForOutputSpinBox", track_change=True)
    depth_for_concentration_from = bnd.bind(
        "depthForConcentrationFromDoubleSpinBox", track_change=True)
    depth_for_concentration_to = bnd.bind(
        "depthForConcentrationToDoubleSpinBox", track_change=True)
    channel_width = bnd.bind(
        "channelWidthDoubleSpinBox", track_change=True)
    number_of_splits = bnd.bind("numberOfSplitsSpinBox", track_change=True)
    normalization = bnd.bind(
        "normalizationComboBox", track_change=True)

    def __init__(self, measurement: Measurement):
        """
        Initializes the widget.

        Args:
            measurement: Measurement object.
        """
        super().__init__()
        uic.loadUi(Path("ui_files", "ui_profile_settings_tab.ui"), self)
        self.measurement = measurement
        self._original_properties = {}

        self.fields_are_valid = False
        iv.set_input_field_red(self.nameLineEdit)
        self.nameLineEdit.textChanged.connect(
            lambda: iv.check_text(self.nameLineEdit, qwidget=self))
        self.nameLineEdit.textEdited.connect(
            lambda: iv.sanitize_file_name(self.nameLineEdit))

        locale = QLocale.c()
        self.referenceDensityDoubleSpinBox.setLocale(locale)
        self.depthForConcentrationFromDoubleSpinBox.setLocale(locale)
        self.depthForConcentrationToDoubleSpinBox.setLocale(locale)
        self.channelWidthDoubleSpinBox.setLocale(locale)

        gutils.fill_combobox(self.normalizationComboBox, ["First"])
        self.set_properties(**self.measurement.get_settings())

        gutils.set_min_max_handlers(
            self.depthForConcentrationFromDoubleSpinBox,
            self.depthForConcentrationToDoubleSpinBox,
            min_diff=0.01
        )

    def get_original_property_values(self):
        """Returns the original values of this Widget's properties.
        """
        return self._original_properties

    def update_settings(self):
        """Update profile settings.
        """
        self.measurement.set_settings(**self.get_properties())
