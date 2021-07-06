# coding=utf-8
"""
Created on 4.5.2018
Updated on 21.8.2018

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

__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä " \
             "\n Sinikka Siironen \n Juhani Sundell \n Tuomas Pitkänen"
__version__ = "2.0"

import time

from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5 import uic

import dialogs.dialog_functions as df
import modules.general_functions as gf
import widgets.binding as bnd
import widgets.gui_utils as gutils

from modules.measurement import Measurement
from widgets.detector_settings import DetectorSettingsWidget
from widgets.measurement.settings import MeasurementSettingsWidget
from widgets.profile_settings import ProfileSettingsWidget


class MeasurementSettingsDialog(QtWidgets.QDialog):
    """
    Dialog class for handling the measurement parameter input.
    """
    use_request_settings = bnd.bind("defaultSettingsCheckBox")

    def __init__(self, tab, measurement: Measurement, icon_manager):
        """
        Initializes the dialog.

        Args:
            measurement: A Measurement object whose parameters are handled.
            icon_manager: An icon manager.
        """
        super().__init__()
        uic.loadUi(gutils.get_ui_dir() / "ui_specific_settings.ui", self)
        self.warning_text = bnd.bind('warning_text')

        self.tab = tab
        self.measurement = measurement
        self.icon_manager = icon_manager
        self.setWindowTitle("Measurement Settings")
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        screen_geometry = QtWidgets.QDesktopWidget.availableGeometry(
            QtWidgets.QApplication.desktop())
        self.resize(int(self.geometry().width() * 1.2),
                    int(screen_geometry.size().height() * 0.8))
        self.defaultSettingsCheckBox.stateChanged.connect(
            self._change_used_settings)
        self.OKButton.clicked.connect(self._save_settings_and_close)
        self.applyButton.clicked.connect(self._update_parameters)
        self.cancelButton.clicked.connect(self.close)

        preset_folder = gutils.get_preset_dir(
            self.measurement.request.global_settings)
        # Add measurement settings view to the settings view
        self.measurement_settings_widget = MeasurementSettingsWidget(
            self.measurement, preset_folder=preset_folder)
        self.tabs.addTab(self.measurement_settings_widget, "Measurement")

        self.measurement_settings_widget.beam_selection_ok.connect(
            self.OKButton.setEnabled
        )

        # Add detector settings view to the settings view
        self.detector_settings_widget = DetectorSettingsWidget(
            self.measurement.detector, self.measurement.request,
            self.icon_manager, self.measurement_settings_widget.tmp_run)

        self.tabs.addTab(self.detector_settings_widget, "Detector")

        self.use_request_settings = self.measurement.use_request_settings

        # TODO these should be set in the widget, not here
        self.measurement_settings_widget.nameLineEdit.setText(
            self.measurement.measurement_setting_file_name)
        self.measurement_settings_widget.descriptionPlainTextEdit.setPlainText(
            self.measurement.measurement_setting_file_description)
        self.measurement_settings_widget.dateLabel.setText(time.strftime(
            "%c %z %Z", time.localtime(self.measurement.modification_time)))

        # Add profile settings view to the settings view
        self.profile_settings_widget = ProfileSettingsWidget(
            self.measurement, preset_folder=preset_folder)
        self.tabs.addTab(self.profile_settings_widget, "Profile")

        self.tabs.currentChanged.connect(lambda: df.check_for_red(self))

        self.exec()

    def _change_used_settings(self):
        check_box = self.sender()
        if check_box.isChecked():
            self.tabs.setEnabled(False)
        else:
            self.tabs.setEnabled(True)

    def _remove_extra_files(self):
        gf.remove_matching_files(
            self.measurement.directory,
            exts={".measurement", ".profile", ".target"})
        gf.remove_matching_files(
            self.measurement.directory / "Detector",
            exts={".detector"})

    def _update_parameters(self):
        if self.measurement_settings_widget.isotopeComboBox.currentIndex() \
                == -1:
            QtWidgets.QMessageBox.critical(
                self, "Warning",
                "No isotope selected.\n\nPlease select an isotope for the beam "
                "element.", QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return False

        if not self.measurement.measurement_setting_file_name:
            self.measurement.measurement_setting_file_name = \
                self.measurement.name

        # Copy request settings without checking their validity. They
        # have been checked once in request settings anyway.
        if self.use_request_settings:
            self.measurement.use_request_settings = True

            # Remove measurement-specific efficiency files
            if self.measurement.detector is not \
                    self.measurement.request.default_detector:
                self.measurement.detector.remove_efficiency_files()

            self.measurement.clone_request_settings()

            self._remove_extra_files()
            self.measurement.to_file()
            return True

        # Check the target and detector angles
        if not self.measurement_settings_widget.check_angles():
            return False

        if not self.tabs.currentWidget().fields_are_valid:
            QtWidgets.QMessageBox.critical(
                self, "Warning",
                "Some of the setting values have not been set.\n"
                "Please input values in fields indicated in red.",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            return False

        # Use Measurement specific settings
        try:
            self.measurement.use_request_settings = False

            # Set Detector object to settings widget
            self.detector_settings_widget.obj = self.measurement.detector

            # Update settings
            self.measurement_settings_widget.update_settings()
            self.detector_settings_widget.update_settings()
            self.profile_settings_widget.update_settings()

            self._remove_extra_files()
            self.measurement.to_file()
            return True

        except TypeError:
            QtWidgets.QMessageBox.question(
                self, "Warning",
                "Some of the setting values have not been set.\n"
                "Please input setting values to save them.",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)

        return False

    def _save_settings_and_close(self):
        """ Save settings and close dialog if __update_parameters returns True.
        """
        if self._update_parameters():
            self.tab.check_default_settings_clicked()
            self.close()
