# coding=utf-8
"""
Created on 30.4.2013
Updated on 28.6.2018

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2013-2018 Jarkko Aalto, Severi Jääskeläinen, Samuel Kaiponen,
Timo Konu, Samuli Kärkkäinen, Samuli Rahkonen, Miika Raunio, Heta Rekilä and
Sinikka Siironen, 2020 Juhani Sundell

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
__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen \n " \
             "Samuli Rahkonen \n Miika Raunio \n Severi Jääskeläinen \n " \
             "Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen \n " \
             "Juhani Sundell"
__version__ = "2.0"

import platform

import dialogs.dialog_functions as df
import widgets.binding as bnd
import widgets.gui_utils as gutils

from pathlib import Path

from widgets.base_tab import BaseTab
from widgets.scientific_spinbox import ScientificSpinBox
from modules.global_settings import GlobalSettings
from modules.enums import IonDivision
from modules.enums import CrossSection
from modules.enums import ToFEColorScheme

from PyQt5 import QtCore
from PyQt5 import uic
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from dialogs.measurement.import_measurement import CoincTiming


class GlobalSettingsDialog(QtWidgets.QDialog):
    """
    A GlobalSettingsDialog.
    """
    color_scheme = bnd.bind("combo_tofe_colors")
    tofe_invert_x = bnd.bind("check_tofe_invert_x")
    tofe_invert_y = bnd.bind("check_tofe_invert_y")
    tofe_transposed = bnd.bind("check_tofe_transpose")
    tofe_bin_x = bnd.multi_bind(
        ("spin_tofe_bin_x_min", "spin_tofe_bin_x_max")
    )
    tofe_bin_y = bnd.multi_bind(
        ("spin_tofe_bin_y_min", "spin_tofe_bin_y_max")
    )
    comp_x = bnd.bind("spin_tofe_compression_x")
    comp_y = bnd.bind("spin_tofe_compression_y")

    depth_iters = bnd.bind("spin_depth_iterations")

    presim_ions = bnd.bind("presim_spinbox")
    sim_ions = bnd.bind("sim_spinbox")
    ion_division = bnd.bind("ion_division_radios")
    min_concentration = bnd.bind("min_conc_spinbox")
    default_density = bnd.bind("scientific_spinbox")
    
    coinc_count = bnd.bind("line_coinc_count")
    
    cross_section = bnd.bind("cross_section_radios")
 
    save_window_geometries = bnd.bind("window_geom_chkbox")

    settings_updated = QtCore.pyqtSignal(GlobalSettings)

    def __init__(self, settings: GlobalSettings):
        """Constructor for the program
        """
        super().__init__()
        
        self.settings = settings
        
        uic.loadUi(gutils.get_ui_dir() / "ui_global_settings.ui", self)

        self.__added_timings = {}  # Placeholder for timings
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        gutils.set_min_max_handlers(
            self.spin_tofe_bin_x_min, self.spin_tofe_bin_x_max
        )
        gutils.set_min_max_handlers(
            self.spin_tofe_bin_y_min, self.spin_tofe_bin_y_max
        )
        gutils.set_btn_group_data(self.ion_division_radios, IonDivision)
        gutils.set_btn_group_data(self.cross_section_radios, CrossSection)
        gutils.fill_combobox(self.combo_tofe_colors, ToFEColorScheme)

        # Connect UI buttons
        self.OKButton.clicked.connect(self.__accept_changes)
        self.cancelButton.clicked.connect(self.close)
        buttons = self.findChild(QtWidgets.QButtonGroup, "elementButtons")
        buttons.buttonClicked.connect(self.__change_element_color)

        self.min_conc_spinbox.setLocale(QtCore.QLocale.c())

        if platform.system() == "Darwin":
            self.gridLayout.setVerticalSpacing(15)
            self.gridLayout.setHorizontalSpacing(15)

        self.__set_values()

    def closeEvent(self, event):
        """Disconnects settings updated signal before closing.
        """
        try:
            self.settings_updated.disconnect()
        except AttributeError:
            pass
        super().closeEvent(event)

    def __set_values(self):
        """Set settings values to dialog.
        """
        for button in self.groupBox_3.findChildren(QtWidgets.QPushButton):
            self.set_btn_color(
                button, self.settings.get_element_color(button.text()))

        label_adc = QtWidgets.QLabel("ADC")
        label_low = QtWidgets.QLabel("Low")
        label_high = QtWidgets.QLabel("High")
        self.grid_timing.addWidget(label_adc, 0, 0)
        self.grid_timing.addWidget(label_low, 1, 0)
        self.grid_timing.addWidget(label_high, 2, 0)
        for i in range(3):
            timing = self.settings.get_import_timing(i)
            label = QtWidgets.QLabel(f"{i}")
            spin_low = self.__create_spinbox(timing[0])
            spin_high = self.__create_spinbox(timing[1])
            self.__added_timings[i] = CoincTiming(i, spin_low, spin_high)
            self.grid_timing.addWidget(label, 0, i + 1)
            self.grid_timing.addWidget(spin_low, 1, i + 1)
            self.grid_timing.addWidget(spin_high, 2, i + 1)
        self.coinc_count = self.settings.get_import_coinc_count()
        # self.__set_cross_sections()
        self.cross_section = self.settings.get_cross_sections()

        # ToF-E graph settings
        self.tofe_invert_x = self.settings.get_tofe_invert_x()
        self.tofe_invert_y = self.settings.get_tofe_invert_y()
        self.tofe_transposed = self.settings.get_tofe_transposed()

        # TODO binding for bin mode
        tofe_bin_mode = self.settings.get_tofe_bin_range_mode()
        self.radio_tofe_bin_auto.setChecked(tofe_bin_mode == 0)
        self.radio_tofe_bin_manual.setChecked(tofe_bin_mode == 1)
        self.tofe_bin_x = self.settings.get_tofe_bin_range_x()
        self.tofe_bin_y = self.settings.get_tofe_bin_range_y()

        self.comp_x = self.settings.get_tofe_compression_x()
        self.comp_y = self.settings.get_tofe_compression_y()

        self.depth_iters = self.settings.get_num_iterations()

        self.presim_ions = self.settings.get_min_presim_ions()
        self.sim_ions = self.settings.get_min_simulation_ions()
        self.ion_division = self.settings.get_ion_division()
        self.min_conc_spinbox.setMinimum(GlobalSettings.MIN_CONC_LIMIT)
        self.min_concentration = self.settings.get_minimum_concentration()
        
        reference_density_value = self.settings.get_default_reference_density()
        self.scientific_spinbox = ScientificSpinBox(
            value=reference_density_value, minimum=0.01, maximum=9.99e26) 
        
        self.formLayout_3.insertRow(
            4,
            QtWidgets.QLabel(r"Reference density [at./cm<sup>3</sup>]:"),
            self.scientific_spinbox)        
        
        
        # Set used paths to LineEdits
        self.lineEdit_ini.setText(str(self.settings.get_config_file()))
        self.lineEdit_Request.setText(str(self.settings.get_request_directory_last_open()))
        eff_text = str(Path(str(self.settings.get_request_directory_last_open())) / 
        "Default" / "Detector" / "efficiency_files")
        self.lineEdit_Eff.setText(eff_text)
        
        self.lineEdit_ini.setReadOnly(True)
        self.lineEdit_Request.setReadOnly(True)
        self.lineEdit_Eff.setReadOnly(True)
        
        self.save_window_geometries = gutils.get_potku_setting(
            BaseTab.SAVE_WINDOW_GEOM_KEY, True
        )
        self.color_scheme = self.settings.get_tofe_color()

    @staticmethod
    def __create_spinbox(default):
        """
        Create a spinbox.
        """
        spinbox = QtWidgets.QSpinBox()
        spinbox.stepBy(1)
        spinbox.setMinimum(-1000)
        spinbox.setMaximum(1000)
        spinbox.setValue(int(default))
        return spinbox

    def __accept_changes(self):
        """Accept changed settings and save.
        """
        for button in self.groupBox_3.findChildren(QtWidgets.QPushButton):
            self.settings.set_element_color(button.text(), button.color)
        for key, coinc_timing in self.__added_timings.items():
            self.settings.set_import_timing(
                key, coinc_timing.low.value(), coinc_timing.high.value())
        self.settings.set_import_coinc_count(self.coinc_count)

        self.settings.set_cross_sections(self.cross_section)

        # ToF-E graph settings
        self.settings.set_tofe_invert_x(self.tofe_invert_x)
        self.settings.set_tofe_invert_y(self.tofe_invert_y)
        self.settings.set_tofe_transposed(self.tofe_transposed)
        self.settings.set_tofe_color(self.color_scheme)
        if self.radio_tofe_bin_auto.isChecked():
            self.settings.set_tofe_bin_range_mode(0)
        elif self.radio_tofe_bin_manual.isChecked():
            self.settings.set_tofe_bin_range_mode(1)

        self.settings.set_tofe_bin_range_x(*self.tofe_bin_x)
        self.settings.set_tofe_bin_range_y(*self.tofe_bin_y)
        self.settings.set_tofe_compression_x(self.comp_x)
        self.settings.set_tofe_compression_y(self.comp_y)
        self.settings.set_num_iterations(self.depth_iters)
        self.settings.set_min_presim_ions(self.presim_ions)
        self.settings.set_min_simulation_ions(self.sim_ions)
        self.settings.set_ion_division(self.ion_division)
        self.settings.set_minimum_concentration(self.min_concentration)
        self.settings.set_default_reference_density(self.default_density)

        gutils.set_potku_setting(
            BaseTab.SAVE_WINDOW_GEOM_KEY, self.save_window_geometries)

        # Save config and close
        self.settings.save_config()
        self.settings_updated.emit(self.settings)
        self.close()

        # TODO This is not used anywhere?
    def __change_request_directory(self):
        """Change default request directory.
        """
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select default request directory",
            directory=self.requestPathLineEdit.text())
        if folder:
            self.requestPathLineEdit.setText(folder)

    def __change_element_color(self, button):
        """Change color of element button.
        
        Args:
            button: QPushButton
        """
        dialog = QtWidgets.QColorDialog(self)
        self.color = dialog.getColor(
            QtGui.QColor(button.color), self,
            f"Select Color for Element: {button.text()}")
        if self.color.isValid():
            self.set_btn_color(button, self.color.name())

    @staticmethod
    def set_btn_color(button, color_name):
        """Change button text color.
        
        Args:
            button: QPushButton
            color_name: String representing color.
        """
        color = QtGui.QColor(color_name)
        style = df.get_btn_stylesheet(color)

        button.color = color.name()
        if not button.isEnabled():
            return  # Do not set color for disabled buttons.
        button.setStyleSheet(style)
