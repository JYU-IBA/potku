# coding=utf-8
'''
Created on 30.4.2013
Updated on 26.8.2013

Potku is a graphical user interface for analyzation and 
visualization of measurement data collected from a ToF-ERD 
telescope. For physics calculations Potku uses external 
analyzation components.  
Copyright (C) Jarkko Aalto, Timo Konu, Samuli Kärkkäinen, Samuli Rahkonen and 
Miika Raunio

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
'''
__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen \n Samuli Rahkonen \n Miika Raunio"
__versio__ = "1.0"

from os import path
from PyQt4 import QtCore, uic, QtGui

from Dialogs.ImportMeasurementDialog import CoincTiming
from Widgets.MatplotlibTofeHistogramWidget import MatplotlibHistogramWidget


class GlobalSettingsDialog(QtGui.QDialog):
    def __init__(self, masses, settings):
        '''Constructor for the program
        '''
        super().__init__()
        self.masses = masses
        self.settings = settings
        self.__added_timings = {}  # Placeholder for timings
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.ui = uic.loadUi(path.join("ui_files", "ui_global_settings.ui"), self)
        
        # Connect UI buttons
        self.ui.OKButton.clicked.connect(self.__accept_changes)
        self.ui.cancelButton.clicked.connect(self.close)
        self.ui.loadProjectPathButton.clicked.connect(
                                                  self.__change_project_directory)
        self.ui.loadEffPathButton.clicked.connect(
                                              self.__change_efficiency_directory)
        buttons = self.ui.findChild(QtGui.QButtonGroup, "elementButtons")
        buttons.buttonClicked.connect(self.__change_element_color)
        self.line_coinc_count.setValidator(QtGui.QIntValidator(0, 1000000))
        
        self.__set_values()
        self.exec_()
        
    
    def __set_values(self):
        '''Set settings values to dialog.
        '''
        self.ui.projectPathLineEdit.setText(self.settings.get_project_directory())
        self.ui.lineEdit_eff_directory.setText(
                                       self.settings.get_efficiency_directory())
        for button in self.ui.groupBox_3.findChildren(QtGui.QPushButton):
            self.__set_button_color(button,
                                    self.settings.get_element_color(button.text()))
            
        label_adc = QtGui.QLabel("ADC")
        label_low = QtGui.QLabel("Low")
        label_high = QtGui.QLabel("High")
        self.ui.grid_timing.addWidget(label_adc, 0, 0)
        self.ui.grid_timing.addWidget(label_low, 1, 0)
        self.ui.grid_timing.addWidget(label_high, 2, 0)
        for i in range(0, 3):
            timing = self.settings.get_import_timing(i)
            label = QtGui.QLabel("{0}".format(i))
            spin_low = self.__create_spinbox(timing[0])
            spin_high = self.__create_spinbox(timing[1])
            self.__added_timings[i] = CoincTiming(i, spin_low, spin_high)
            self.ui.grid_timing.addWidget(label, 0, i + 1)
            self.ui.grid_timing.addWidget(spin_low, 1, i + 1)
            self.ui.grid_timing.addWidget(spin_high, 2, i + 1)
        self.line_coinc_count.setText(str(self.settings.get_import_coinc_count()))
        self.__set_cross_sections()
        self.check_es_output.setChecked(self.settings.is_es_output_saved())
        
        # ToF-E graph settings
        self.ui.check_tofe_invert_x.setChecked(self.settings.get_tofe_invert_x())
        self.ui.check_tofe_invert_y.setChecked(self.settings.get_tofe_invert_y())
        self.ui.check_tofe_transpose.setChecked(self.settings.get_tofe_transposed())
        tofe_bin_mode = self.settings.get_tofe_bin_range_mode()
        self.ui.radio_tofe_bin_auto.setChecked(tofe_bin_mode == 0)
        self.ui.radio_tofe_bin_manual.setChecked(tofe_bin_mode == 1)
        x_range_min, x_range_max = self.settings.get_tofe_bin_range_x()
        y_range_min, y_range_max = self.settings.get_tofe_bin_range_y()
        self.ui.spin_tofe_bin_x_max.setValue(x_range_max)
        self.ui.spin_tofe_bin_x_min.setValue(x_range_min)
        self.ui.spin_tofe_bin_y_max.setValue(y_range_max)
        self.ui.spin_tofe_bin_y_min.setValue(y_range_min)
        self.ui.spin_tofe_compression_x.setValue(
                                           self.settings.get_tofe_compression_x())
        self.ui.spin_tofe_compression_y.setValue(
                                           self.settings.get_tofe_compression_y())
        self.ui.spin_depth_iterations.setValue(self.settings.get_num_iterations())
        dirtyinteger = 0
        colors = sorted(MatplotlibHistogramWidget.color_scheme.items())
        for key, unused_value in colors:
            self.ui.combo_tofe_colors.addItem(key)
            if key == self.settings.get_tofe_color():
                self.ui.combo_tofe_colors.setCurrentIndex(dirtyinteger)
            dirtyinteger += 1
    
    
    def __create_spinbox(self, default):
        spinbox = QtGui.QSpinBox()
        spinbox.stepBy(1)
        spinbox.setMinimum(-1000)
        spinbox.setMaximum(1000)
        spinbox.setValue(int(default))
        return spinbox
    
    
    def __accept_changes(self):
        '''Accept changed settings and save.
        '''
        self.settings.set_project_directory(self.ui.projectPathLineEdit.text())
        self.settings.set_efficiency_directory(
                                           self.ui.lineEdit_eff_directory.text())
        for button in self.ui.groupBox_3.findChildren(QtGui.QPushButton):
            self.settings.set_element_color(button.text(), button.color)
        for key in self.__added_timings.keys():
            coinc_timing = self.__added_timings[key]
            self.settings.set_import_timing(key,
                                            coinc_timing.low.value(),
                                            coinc_timing.high.value())
        self.settings.set_import_coinc_count(self.line_coinc_count.text())
        
        # Save cross sections
        if self.ui.radio_cross_1.isChecked():
            flag_cross = 1
        elif self.ui.radio_cross_2.isChecked():
            flag_cross = 2
        elif self.ui.radio_cross_3.isChecked():
            flag_cross = 3
        self.settings.set_cross_sections(flag_cross)
        self.settings.set_es_output_saved(self.check_es_output.isChecked())
        
        # ToF-E graph settings
        self.settings.set_tofe_invert_x(self.ui.check_tofe_invert_x.isChecked())
        self.settings.set_tofe_invert_y(self.ui.check_tofe_invert_y.isChecked())
        self.settings.set_tofe_transposed(self.ui.check_tofe_transpose.isChecked())
        self.settings.set_tofe_color(self.ui.combo_tofe_colors.currentText())
        if self.ui.radio_tofe_bin_auto.isChecked():    
            self.settings.set_tofe_bin_range_mode(0)
        elif self.ui.radio_tofe_bin_manual.isChecked():    
            self.settings.set_tofe_bin_range_mode(1)
        x_r_min = self.ui.spin_tofe_bin_x_min.value()
        x_r_max = self.ui.spin_tofe_bin_x_max.value()
        y_r_min = self.ui.spin_tofe_bin_y_min.value()
        y_r_max = self.ui.spin_tofe_bin_y_max.value()
        if x_r_min > x_r_max: x_r_min = 0
        if y_r_min > y_r_max: y_r_min = 0
        compression_x = self.ui.spin_tofe_compression_x.value()
        compression_y = self.ui.spin_tofe_compression_y.value()
        self.settings.set_tofe_bin_range_x(x_r_min, x_r_max)
        self.settings.set_tofe_bin_range_y(y_r_min, y_r_max)
        self.settings.set_tofe_compression_x(compression_x)
        self.settings.set_tofe_compression_y(compression_y)
        self.settings.set_num_iterations(self.ui.spin_depth_iterations.value())

        # Save config and close
        self.settings.save_config()
        self.close()
        
        
    def __change_project_directory(self):
        '''Change default project directory.
        '''
        folder = QtGui.QFileDialog.getExistingDirectory(self,
            "Select default project directory",
            directory=self.ui.projectPathLineEdit.text())
        if folder:
            self.ui.projectPathLineEdit.setText(folder)
            
    
    def __change_efficiency_directory(self):
        '''Change efficiency file directory.
        '''
        folder = QtGui.QFileDialog.getExistingDirectory(self,
            "Select efficiency file directory",
            directory=self.ui.lineEdit_eff_directory.text())
        if folder:
            self.ui.lineEdit_eff_directory.setText(folder)
        
        
    def __change_element_color(self, button):
        '''Change color of element button.
        
        Args:
            button: QPushButton
        '''
        dialog = QtGui.QColorDialog(self)
        self.color = dialog.getColor(QtGui.QColor(button.color),
                                     self,
                                     "Select Color for Element: {0}".format(
                                                                button.text()))
        if self.color.isValid():
            self.__set_button_color(button, self.color.name())
    
    
    def __set_button_color(self, button, color_name):
        '''Change button text color.
        
        Args:
            button: QPushButton
            color_name: String representing color.
        '''
        text_color = "black"
        color = QtGui.QColor(color_name)
        luminance = 0.2126 * color.red() + 0.7152 * color.green()
        luminance += 0.0722 * color.blue()
        if luminance < 50:
            text_color = "white"
        button.color = color.name()
        if not button.isEnabled():
            return  # Do not set color for disabled buttons.
        button.setStyleSheet("background-color: {0}; color: {1};".format(
                                                     color.name(), text_color))
    def __set_cross_sections(self):
        '''Set cross sections to UI.
        '''
        flag = self.settings.get_cross_sections()
        self.ui.radio_cross_1.setChecked(flag == 1)
        self.ui.radio_cross_2.setChecked(flag == 2)
        self.ui.radio_cross_3.setChecked(flag == 3)
        
