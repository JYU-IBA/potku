# coding=utf-8
"""
Created on 12.4.2018
Updated on 16.8.2018

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
             "\n Sinikka Siironen"
__version__ = "2.0"

import copy
import math
import os
import time

from dialogs.measurement.calibration import CalibrationDialog
from dialogs.simulation.foil import FoilDialog

from modules.foil import CircularFoil
from modules.general_functions import check_text
from modules.general_functions import open_file_dialog
from modules.general_functions import set_input_field_red
from modules.general_functions import validate_text_input

from PyQt5 import QtWidgets
from PyQt5 import uic
from PyQt5.QtCore import QLocale
from PyQt5.QtCore import Qt

from widgets.foil import FoilWidget
from widgets.scientific_spinbox import ScientificSpinBox


class DetectorSettingsWidget(QtWidgets.QWidget):
    """Class for creating a detector settings tab.
    """
    def __init__(self, obj, request, icon_manager, run=None):
        """
        Initializes a DetectorSettingsWidget object.

        Args:
              obj: a Detector object.
              request: Which request it belongs to.
              icon_manager: IconManager object.
              run: Run object. None if detector is default detector.
        """
        super().__init__()
        self.ui = uic.loadUi(os.path.join("ui_files",
                                          "ui_request_detector_settings.ui"),
                             self)

        self.obj = obj
        self.request = request
        self.icon_manager = icon_manager
        self.run = run

        # Temporary foils list which holds all the information given in the
        # foil dialog
        # If user presses ok or apply, these values will be saved into
        # request's default detector
        self.tmp_foil_info = []

        # List of foil indexes that are timing foils
        self.tof_foils = []

        # Add foil widgets and foil objects
        self.detector_structure_widgets = []
        self.foils_layout = self._add_default_foils()
        self.ui.detectorScrollAreaContents.layout() \
            .addLayout(self.foils_layout)
        self.ui.newFoilButton.clicked.connect(
            lambda: self._add_new_foil(self.foils_layout))

        # Efficiency files
        efficiency_files = self.obj.get_efficiency_files()
        self.ui.efficiencyListWidget.addItems(efficiency_files)
        self.obj.efficiencies = []
        for f in efficiency_files:
            self.obj.efficiencies.append(os.path.join(
                self.obj.efficiency_directory, f))
        self.ui.addEfficiencyButton.clicked.connect(
            lambda: self.__add_efficiency())
        self.ui.removeEfficiencyButton.clicked.connect(
            lambda: self.__remove_efficiency())

        # Calibration settings
        self.ui.loadCalibrationParametersButton. \
            clicked.connect(lambda: self.__load_file("CALIBRATION_SETTINGS"))
        self.ui.saveCalibrationParametersButton. \
            clicked.connect(lambda: self.__save_file("CALIBRATION_SETTINGS"))
        self.ui.executeCalibrationButton.clicked. \
            connect(self.__open_calibration_dialog)
        self.ui.executeCalibrationButton.setEnabled(
            not self.request.samples.measurements.is_empty())

        set_input_field_red(self.ui.nameLineEdit)
        self.fields_are_valid = False
        self.ui.nameLineEdit.textChanged.connect(lambda: self.__check_text(
            self.ui.nameLineEdit, self))

        self.ui.nameLineEdit.textEdited.connect(lambda: self.__validate())

        locale = QLocale.c()
        self.timeResSpinBox.setLocale(locale)
        self.virtualSizeXSpinBox.setLocale(locale)
        self.virtualSizeYSpinBox.setLocale(locale)

        # Create scientific spinboxes for tof slope and tof offset
        self.ui.formLayout_2.removeRow(self.ui.slopeLineEdit)
        self.ui.formLayout_2.removeRow(self.ui.offsetLineEdit)

        # Parse the value and multiplier
        slope_value_and_mult = str(self.obj.tof_slope)
        try:
            e_index = slope_value_and_mult.index('e')
            number_part = slope_value_and_mult[:e_index]
            multiply_part = "1" + slope_value_and_mult[e_index:]
        except ValueError:
            number_part = slope_value_and_mult
            multiply_part = 1
        self.scientific_tof_slope = ScientificSpinBox(number_part,
                                                      multiply_part,
                                                      -math.inf, math.inf)
        # Parse the value and multiplier
        offset_value_and_mult = str(self.obj.tof_offset)
        try:
            e_index = offset_value_and_mult.index('e')
            number_part = offset_value_and_mult[:e_index]
            multiply_part = "1" + offset_value_and_mult[e_index:]
        except ValueError:
            number_part = offset_value_and_mult
            multiply_part = 1
        self.scientific_tof_offset = ScientificSpinBox(number_part,
                                                       multiply_part,
                                                       -math.inf, math.inf)
        self.ui.formLayout_2.insertRow(0, "ToF slope [s/channel]:",
                                       self.scientific_tof_slope)
        self.ui.formLayout_2.insertRow(1, "ToF offset[s]:",
                                       self.scientific_tof_offset)

        self.show_settings()

    def show_settings(self):
        """
        Show Detector settings.
        """
        # Detector settings
        self.nameLineEdit.setText(self.obj.name)
        self.dateLabel.setText(time.strftime("%c %z %Z", time.localtime(
            self.obj.modification_time)))
        self.descriptionLineEdit.setPlainText(self.obj.description)
        self.typeComboBox.setCurrentIndex(self.typeComboBox.findText(
            self.obj.type, Qt.MatchFixedString))
        self.angleSlopeLineEdit.setText(
            str(self.obj.angle_slope))
        self.angleOffsetLineEdit.setText(
            str(self.obj.angle_offset))

        self.timeResSpinBox.setValue(self.obj.timeres)
        self.virtualSizeXSpinBox.setValue(self.obj.virtual_size[0])
        self.virtualSizeYSpinBox.setValue(self.obj.virtual_size[1])

        # Detector foils
        self.calculate_distance()
        self.tmp_foil_info = copy.deepcopy(self.obj.foils)

        # Tof foils
        self.tof_foils = copy.deepcopy(self.obj.tof_foils)

    def update_settings(self):
        """
        Update detector settings.
        """
        self.obj.name = self.nameLineEdit.text()
        self.obj.description = self.descriptionLineEdit.toPlainText()
        self.obj.type = self.typeComboBox.currentText()
        self.obj.angle_offset = self.angleOffsetLineEdit.text()
        self.obj.angle_slope = self.angleSlopeLineEdit.text()
        self.obj.tof_slope = self.scientific_tof_slope.value_str
        self.obj.tof_offset = self.scientific_tof_offset.value_str

        self.obj.virtual_size = self.virtualSizeXSpinBox.value(), \
                                self.virtualSizeYSpinBox.value()
        self.obj.timeres = self.timeResSpinBox.value()
        # Detector foils
        self.calculate_distance()
        self.obj.foils = self.tmp_foil_info
        # Tof foils
        self.obj.tof_foils = self.tof_foils

    def values_changed(self):
        """
        Check if detector settings values have been changed.

        Return:
            True or False.
        """
        if self.obj.name != self.nameLineEdit.text():
            return True
        if self.obj.description != self.descriptionLineEdit.toPlainText():
            return True
        if self.obj.type != self.typeComboBox.currentText():
            return True
        if self.obj.angle_offset != self.angleOffsetLineEdit.text():
            return True
        if self.obj.angle_slope != self.angleSlopeLineEdit.text():
            return True
        if self.obj.tof_offset != self.scientific_tof_offset.value_str:
            return True
        if self.obj.tof_slope != self.scientific_tof_slope.value_str:
            return True
        if self.obj.virtual_size != (self.virtualSizeXSpinBox.value(),
                                self.virtualSizeYSpinBox.value()):
            return True
        if self.obj.timeres != self.timeResSpinBox.value():
            return True
        # Detector foils
        self.calculate_distance()
        if self.foils_changed():
            return True
        # Tof foils
        if self.obj.tof_foils != self.tof_foils:
            return True
        # Efficiencies
        existing_efficiency_files = [os.path.join(
            self.obj.efficiency_directory, x) for x in
            self.obj.get_efficiency_files()]
        modified_efficiencies = copy.deepcopy(existing_efficiency_files)
        for file in self.obj.efficiencies:
            file_name = os.path.split(file)[1]
            new_path = os.path.join(self.obj.efficiency_directory, file_name)
            if new_path not in modified_efficiencies:
                modified_efficiencies.append(new_path)

        for file in self.obj.efficiencies_to_remove:
            modified_efficiencies.remove(file)

        if existing_efficiency_files != modified_efficiencies:
            return True

        return False

    def foils_changed(self):
        """
        Check if detector foils have been changed.

        Return:
            True or False.
        """
        if len(self.obj.foils) != len(self.tmp_foil_info):
            return True
        for i in range(len(self.obj.foils)):
            foil = self.obj.foils[i]
            tmp_foil = self.tmp_foil_info[i]
            if type(foil) != type(tmp_foil):
                return True
            if foil.name != tmp_foil.name:
                return True
            if foil.distance != tmp_foil.distance:
                return True
            if foil.transmission != tmp_foil.transmission:
                return True
            # Check layers
            if self.layers_changed(foil, tmp_foil):
                return True
            if type(foil) is CircularFoil:
                if foil.diameter != tmp_foil.diameter:
                    return True
            else:
                if foil.size != tmp_foil.size:
                    return True
        return False

    def layers_changed(self, foil1, foil2):
        """
        Check if foil1 has different layers than foil2.

        Args:
            foil1: Foil object.
            foil2: Foil object.

        Return:
            True or False.
        """
        if len(foil1.layers) != len(foil2.layers):
            return True
        for i in range(len(foil1.layers)):
            layer1 = foil1.layers[i]
            layer2 = foil2.layers[i]
            if layer1.name != layer2.name:
                return True
            if layer1.thickness != layer2.thickness:
                return True
            if layer1.density != layer2.density:
                return True
            if layer1.start_depth != layer2.start_depth:
                return True
            # Check layer elements
            if self.layer_elements_changed(layer1, layer2):
                return True
        return False

    def layer_elements_changed(self, layer1, layer2):
        """
        Check if layer1 elements are different than layer2 elements.

        Args:
            layer1: Layer object.
            layer2: Layer object.

        Return:
            True or False.
        """
        if len(layer1.elements) != len(layer2.elements):
            return True
        for i in range(len(layer1.elements)):
            elem1 = layer1.elements[i]
            elem2 = layer2.elements[i]
            if elem1 != elem2:
                return True
        return False

    def _add_new_foil(self, layout, new_foil=None):
        """
        Add a new foil into detector.
         Args:
              layout: Layout into which the foil widget is added.
              new_foil: New Foil object to be added.
        """
        if new_foil is None:
            new_foil = CircularFoil()
        foil_widget = FoilWidget(self)
        self.tmp_foil_info.append(new_foil)
        foil_widget.ui.foilButton.setText(new_foil.name)
        foil_widget.ui.distanceDoubleSpinBox.setValue(0.0)
        distance = new_foil.distance
        foil_widget.ui.distanceLabel.setText(str(distance))
        foil_widget.ui.foilButton.clicked.connect(
            lambda: self._open_foil_dialog())
        foil_widget.ui.timingFoilCheckBox.stateChanged.connect(
            lambda: self._check_and_add())
        self.detector_structure_widgets.append(foil_widget)
        layout.addWidget(foil_widget)

        if len(self.tof_foils) >= 2:
            foil_widget.ui.timingFoilCheckBox.setEnabled(False)
        return foil_widget

    def _add_default_foils(self):
        """
        Add default foils as widgets.

        Return:
            Layout that holds the default foil widgets.
        """
        layout = QtWidgets.QHBoxLayout()

        foils = self.obj.foils
        for i in range(len(foils)):
            foil_widget = self._add_new_foil(layout, foils[i])
            for index in self.obj.tof_foils:
                if index == i:
                    foil_widget.ui.timingFoilCheckBox.setChecked(True)
            if i != 0:
                distance = foils[i].distance - foils[i - 1].distance
                foil_widget.ui.distanceDoubleSpinBox.setValue(distance)
            else:
                foil_widget.ui.distanceDoubleSpinBox.setValue(
                    foils[i].distance)
        return layout

    def _check_and_add(self):
        """
        Check if foil widget needs to be added into tof_foils list or
        removed from it.
        """
        check_box = self.sender()
        for i in range(len(self.detector_structure_widgets)):
            if self.detector_structure_widgets[i]. \
                    ui.timingFoilCheckBox is self.sender():
                if check_box.isChecked():
                    if self.tof_foils:
                        if self.tof_foils[0] > i:
                            self.tof_foils.insert(0, i)
                        else:
                            self.tof_foils.append(i)
                        if len(self.tof_foils) >= 2:
                            self._disable_checkboxes()
                    else:
                        self.tof_foils.append(i)
                else:
                    self.tof_foils.remove(i)
                    if 0 < len(self.tof_foils) < 2:
                        self._enable_checkboxes()
                break

    def _disable_checkboxes(self):
        """
        Disbale selection of foil widgets as tof foil if they are not in the
        tof_foils list.
        """
        for i in range(len(self.detector_structure_widgets)):
            if i not in self.tof_foils:
                widget = self.detector_structure_widgets[i]
                widget.ui.timingFoilCheckBox.setEnabled(False)

    def _enable_checkboxes(self):
        """
        Allow all foil widgets to be selected as tof foil.
        """
        for i in range(len(self.detector_structure_widgets)):
            widget = self.detector_structure_widgets[i]
            widget.ui.timingFoilCheckBox.setEnabled(True)

    def _open_foil_dialog(self):
        """
        Open the FoilDialog which is used to modify the Foil object.
        """
        foil_name = self.sender().text()
        foil_object_index = -1
        for i in range(len(self.tmp_foil_info)):
            if foil_name == self.tmp_foil_info[i].name:
                foil_object_index = i
                break
        FoilDialog(self.tmp_foil_info, foil_object_index, self.icon_manager)
        self.sender().setText(self.tmp_foil_info[foil_object_index].name)

    def __add_efficiency(self):
        """Adds efficiency file in detector's efficiency list for moving into
        efficiency folder later and updates settings view.
        """
        new_efficiency_file = open_file_dialog(self,
                                               self.request.default_folder,
                                               "Select efficiency file",
                                               "Efficiency File (*.eff)")
        if not new_efficiency_file:
            return
        # self.obj.add_efficiency_file(new_efficiency_file)
        self.obj.save_efficiency_file_path(new_efficiency_file)
        self.ui.efficiencyListWidget.clear()
        self.ui.efficiencyListWidget.addItems(
            self.obj.get_efficiency_files_from_list())

    def __remove_efficiency(self):
        """Removes efficiency file from detector's efficiency directory and
        updates settings view.
        """
        if self.ui.efficiencyListWidget.currentItem():
            reply = QtWidgets.QMessageBox.question(self, "Confirmation",
                                                   "Are you sure you want to "
                                                   "delete selected efficiency"
                                                   "?",
                                                   QtWidgets.QMessageBox.Yes |
                                                   QtWidgets.QMessageBox.No |
                                                   QtWidgets.QMessageBox.Cancel,
                                                   QtWidgets.QMessageBox.Cancel)
            if reply == QtWidgets.QMessageBox.No or reply == \
                    QtWidgets.QMessageBox.Cancel:
                return  # If clicked Yes, then continue normally

            selected_efficiency_file = self.ui. \
                efficiencyListWidget.currentItem().text()
            # self.obj.remove_efficiency_file(
            #     selected_efficiency_file)
            self.obj.remove_efficiency_file_path(selected_efficiency_file)
            self.ui.efficiencyListWidget.clear()
            self.ui.efficiencyListWidget.addItems(
                self.obj.get_efficiency_files_from_list())

    def __open_calibration_dialog(self):
        """
        Open the CalibrationDialog.
        """
        measurements = [self.request.samples.measurements.get_key_value(key)
                        for key in
                        self.request.samples.measurements.measurements.keys()]
        CalibrationDialog(measurements, self.obj, self.run, self)

    def calculate_distance(self):
        """
        Calculate the distances of the foils from the target.
        """
        distance = 0
        for i in range(len(self.detector_structure_widgets)):
            widget = self.detector_structure_widgets[i]
            dist_to_add = widget.ui.distanceDoubleSpinBox.value()
            distance = distance + dist_to_add
            widget.ui.distanceLabel.setText(str(distance))
            self.tmp_foil_info[i].distance = distance

    def delete_foil(self, foil_widget):
        """
        Delete a foil from widgets and Foil objects.

        Args:
            foil_widget: Widget to be deleted. Its index is used to delete
            Foil objects as well.
        """
        index_of_item_to_be_deleted = self.detector_structure_widgets.index(
            foil_widget)
        del (self.detector_structure_widgets[index_of_item_to_be_deleted])
        foil_to_be_deleted = self.tmp_foil_info[index_of_item_to_be_deleted]
        # Check if foil to be deleted is in tof_foils and remove it fro the
        # tof_foils list if it is.
        if index_of_item_to_be_deleted in self.tof_foils:
            self.tof_foils.remove(index_of_item_to_be_deleted)
            if 0 < len(self.tof_foils) < 2:
                self._enable_checkboxes()
        self.tmp_foil_info.remove(foil_to_be_deleted)
        for i in range(len(self.tof_foils)):
            if self.tof_foils[i] > index_of_item_to_be_deleted:
                self.tof_foils[i] = self.tof_foils[i] - 1

        self.foils_layout.removeWidget(foil_widget)
        foil_widget.deleteLater()

    @staticmethod
    def __check_text(input_field, settings):
        """Checks if there is text in given input field.

        Args:
            input_field: Input field the contents of which are checked.
            settings: Settings widget.
        """
        settings.fields_are_valid = check_text(input_field)

    def __validate(self):
        """
        Validate the sample name.
        """
        text = self.ui.nameLineEdit.text()
        regex = "^[A-Za-z0-9-ÖöÄäÅå]*"
        valid_text = validate_text_input(text, regex)

        self.ui.nameLineEdit.setText(valid_text)

