# coding=utf-8
"""
Created on 12.4.2018
Updated on 17.12.2018

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
__version__ = "2.0"

import copy
import math
import platform

import widgets.input_validation as iv
import widgets.binding as bnd
import dialogs.file_dialogs as fdialogs
import widgets.gui_utils as gutils

from pathlib import Path

from dialogs.measurement.calibration import CalibrationDialog
from dialogs.simulation.foil import FoilDialog

from modules.detector import Detector
from modules.foil import CircularFoil
from modules.request import Request
from modules.enums import DetectorType

from PyQt5 import QtWidgets
from PyQt5 import uic
from PyQt5.QtCore import QLocale
from PyQt5 import QtCore

from widgets.foil import FoilWidget
from widgets.scientific_spinbox import ScientificSpinBox


class DetectorSettingsWidget(QtWidgets.QWidget, bnd.PropertyTrackingWidget,
                             metaclass=gutils.QtABCMeta):
    """Class for creating a detector settings tab.
    """
    # Key that is used to store the folder of the most recently added eff file
    EFF_FILE_FOLDER_KEY = "efficiency_folder"

    efficiency_files = bnd.bind("efficiencyListWidget")

    name = bnd.bind("nameLineEdit")
    modification_time = bnd.bind(
        "dateLabel", fget=bnd.unix_time_from_label, fset=bnd.unix_time_to_label)
    description = bnd.bind("descriptionLineEdit")
    detector_type = bnd.bind("typeComboBox", track_change=True)
    angle_slope = bnd.bind("angleSlopeLineEdit", track_change=True)
    angle_offset = bnd.bind("angleOffsetLineEdit", track_change=True)
    tof_slope = bnd.bind("scientific_tof_slope", track_change=True)
    tof_offset = bnd.bind("scientific_tof_offset", track_change=True)
    timeres = bnd.bind("timeResSpinBox", track_change=True)
    virtual_size = bnd.multi_bind(
        ("virtualSizeXSpinBox", "virtualSizeYSpinBox"), track_change=True
    )

    def __init__(self, obj: Detector, request: Request, icon_manager, run=None):
        """Initializes a DetectorSettingsWidget object.

        Args:
              obj: a Detector object.
              request: Which request it belongs to.
              icon_manager: IconManager object.
              run: Run object. None if detector is default detector.
        """
        super().__init__()
        uic.loadUi(
            gutils.get_ui_dir() / "ui_request_detector_settings.ui", self)

        self.obj = obj
        self.request = request
        self.icon_manager = icon_manager
        self.run = run
        self.__original_properties = {}

        # Temporary foils list which holds all the information given in the
        # foil dialog
        # If user presses ok or apply, these values will be saved into
        # request's default detector
        self.tmp_foil_info = []

        # List of foil indexes that are timing foils
        self.tof_foils = []

        # Add foil widgets and foil objects
        self.detector_structure_widgets = []
        self.foils_layout = self._add_default_foils(self.obj)
        self.detectorScrollAreaContents.layout().addLayout(self.foils_layout)
        self.newFoilButton.clicked.connect(
            lambda: self._add_new_foil(self.foils_layout))

        self.addEfficiencyButton.clicked.connect(self.__add_efficiency)
        self.removeEfficiencyButton.clicked.connect(self.__remove_efficiency)

        self.efficiencyListWidget.itemSelectionChanged.connect(
            self._enable_remove_btn)
        self._enable_remove_btn()

        # Calibration settings
        self.executeCalibrationButton.clicked.connect(
            self.__open_calibration_dialog)
        self.executeCalibrationButton.setEnabled(
            not self.request.samples.measurements.is_empty())

        gutils.fill_combobox(self.typeComboBox, DetectorType)

        self.fields_are_valid = False
        iv.set_input_field_red(self.nameLineEdit)
        self.nameLineEdit.textChanged.connect(
            lambda: iv.check_text(self.nameLineEdit, qwidget=self))
        self.nameLineEdit.textEdited.connect(
            lambda: iv.sanitize_file_name(self.nameLineEdit))

        locale = QLocale.c()
        self.timeResSpinBox.setLocale(locale)
        self.virtualSizeXSpinBox.setLocale(locale)
        self.virtualSizeYSpinBox.setLocale(locale)

        # Create scientific spinboxes for tof slope and tof offset
        self.formLayout_2.removeRow(self.slopeLineEdit)
        self.formLayout_2.removeRow(self.offsetLineEdit)

        # Parse the value and multiplier
        self.scientific_tof_slope = ScientificSpinBox(
            minimum=-math.inf, maximum=math.inf
        )
        self.scientific_tof_offset = ScientificSpinBox(
            minimum=-math.inf, maximum=math.inf
        )

        self.formLayout_2.insertRow(
            0, "ToF slope [s/channel]:", self.scientific_tof_slope)
        self.formLayout_2.insertRow(
            1, "ToF offset[s]:", self.scientific_tof_offset)

        if platform.system() == "Darwin":
            self.scientific_tof_offset.scientificLineEdit.setFixedWidth(170)
            self.scientific_tof_slope.scientificLineEdit.setFixedWidth(170)

        # Save as and load
        self.saveButton.clicked.connect(self.__save_file)
        self.loadButton.clicked.connect(self.__load_file)

        self.show_settings()

    def get_original_property_values(self):
        """Returns the original values of the widget's properties.
        """
        return self.__original_properties

    def __load_file(self):
        """Load settings from file.
        """
        file = fdialogs.open_file_dialog(
            self, self.request.default_folder, "Select detector file",
            "Detector File (*.detector)")
        if not file:
            return

        temp_detector = Detector.from_file(file, file, self.request, False)
        self.obj.set_settings(**temp_detector.get_settings())

        self.tmp_foil_info = []
        self.tof_foils = []
        self.detector_structure_widgets = []
        # Remove old widgets
        for i in range(self.detectorScrollAreaContents.layout().count()):
            layout_item = self.detectorScrollAreaContents.layout().itemAt(i)
            if layout_item == self.foils_layout:
                self.detectorScrollAreaContents.layout().removeItem(
                    layout_item)
                for j in reversed(range(layout_item.count())):
                    layout_item.itemAt(j).widget().deleteLater()

        # Add foil widgets and foil objects
        self.foils_layout = self._add_default_foils(temp_detector)
        self.detectorScrollAreaContents.layout().addLayout(self.foils_layout)

        self.show_settings()

    def __save_file(self):
        """Opens file dialog and sets and saves the settings to a file.
        """
        file = fdialogs.save_file_dialog(
            self, self.request.default_folder, "Save detector file",
            "Detector File (*.detector)")
        if not file:
            return
        file = Path(file)
        if file.suffix != ".detector":
            file = Path(file.parent, f"{file.name}.detector")
        if not self.some_values_changed():
            self.obj.to_file(file, None)
        else:
            # Make temp detector, modify it according to widget values,
            # and write it to file.
            temp_detector = copy.deepcopy(self.obj)
            original_obj = self.obj
            self.obj = temp_detector
            self.update_settings()
            self.obj.to_file(file, None)
            self.obj = original_obj

    def show_settings(self):
        """Show Detector settings.
        """
        # Detector settings
        self.set_properties(**self.obj.get_settings())
        self.efficiency_files = self.obj.get_efficiency_files()

        # Detector foils
        self.tmp_foil_info = copy.deepcopy(self.obj.foils)
        self.calculate_distance()

        # Tof foils
        self.tof_foils = copy.deepcopy(self.obj.tof_foils)

    def update_settings(self):
        """Update detector settings.
        """
        self.obj.set_settings(**self.get_properties())
        # Detector foils
        self.calculate_distance()
        self.obj.foils = self.tmp_foil_info
        # Tof foils
        self.obj.tof_foils = self.tof_foils

    def some_values_changed(self):
        """Check if any detector settings values have been changed.

        Return:
            True or False.
        """
        if self.values_changed():
            return True
        if self.other_values_changed():
            return True
        return False

    def values_changed(self):
        """Check if detector settings values that require rerunning of the
        simulation have been changed.

        Return:
            True or False.
        """
        if self.are_values_changed():
            return True

        # TODO refactor foils
        # Detector foils
        self.calculate_distance()
        if self.foils_changed():
            return True
        # Tof foils
        if self.obj.tof_foils != self.tof_foils:
            return True

        return False

    def other_values_changed(self):
        """Check if detector settings values that don't require rerunning
        simulations have been changed.

        Return:
             True or False.
        """
        if self.obj.name != self.name:
            return True
        if self.obj.description != self.description:
            return True

        return False

    def foils_changed(self):
        """Check if detector foils have been changed.

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
        """Check if foil1 has different layers than foil2.

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

    @staticmethod
    def layer_elements_changed(layer1, layer2):
        """Check if layer1 elements are different than layer2 elements.

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
        """Add a new foil into detector.
        Args:
            layout: Layout into which the foil widget is added.
            new_foil: New Foil object to be added.
        """
        if self.tmp_foil_info:
            prev_distance = self.tmp_foil_info[-1].distance
        else:
            prev_distance = 0.0

        if new_foil is None:
            new_foil = CircularFoil(distance=prev_distance)

        foil_widget = FoilWidget(new_foil)
        foil_widget.distance_from_previous = new_foil.distance - prev_distance

        foil_widget.distanceDoubleSpinBox.valueChanged.connect(
            self.calculate_distance)
        foil_widget.foil_deletion.connect(self.delete_foil)
        foil_widget.foilButton.clicked.connect(self._open_foil_dialog)
        foil_widget.timingFoilCheckBox.stateChanged.connect(self._check_and_add)

        layout.addWidget(foil_widget)
        self.tmp_foil_info.append(new_foil)
        self.detector_structure_widgets.append(foil_widget)

        if len(self.tof_foils) >= 2:
            foil_widget.timingFoilCheckBox.setEnabled(False)
        return foil_widget

    def _add_default_foils(self, detector: Detector):
        """Add default foils as widgets.

        Return:
            Layout that holds the default foil widgets.
        """
        layout = QtWidgets.QHBoxLayout()

        foils = detector.foils
        for i in range(len(foils)):
            foil_widget = self._add_new_foil(layout, foils[i])
            for index in detector.tof_foils:
                if index == i:
                    foil_widget.timingFoilCheckBox.setChecked(True)
        return layout

    def _check_and_add(self):
        """Check if foil widget needs to be added into tof_foils list or
        removed from it.
        """
        check_box = self.sender()
        for i in range(len(self.detector_structure_widgets)):
            if self.detector_structure_widgets[i].timingFoilCheckBox is \
                    self.sender():
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
        """Disable selection of foil widgets as tof foil if they are not in the
        tof_foils list.
        """
        for i in range(len(self.detector_structure_widgets)):
            if i not in self.tof_foils:
                widget = self.detector_structure_widgets[i]
                widget.timingFoilCheckBox.setEnabled(False)

    def _enable_checkboxes(self):
        """Allow all foil widgets to be selected as tof foil.
        """
        for i in range(len(self.detector_structure_widgets)):
            widget = self.detector_structure_widgets[i]
            widget.timingFoilCheckBox.setEnabled(True)

    def _enable_remove_btn(self):
        """Sets the remove button either enabled or not depending whether an
        item is selected in the efficiency file list.
        """
        self.removeEfficiencyButton.setEnabled(
            bool(self.efficiencyListWidget.currentItem())
        )

    def _open_foil_dialog(self):
        """Open the FoilDialog which is used to modify the Foil object.
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
        """Opens a dialog that allows the user to add efficiency files to
        the Efficiency_files folder of the detector.
        """
        eff_folder = gutils.get_potku_setting(
            DetectorSettingsWidget.EFF_FILE_FOLDER_KEY,
            self.request.default_folder)

        new_eff_files = fdialogs.open_files_dialog(
            self, eff_folder, "Select efficiency files",
            "Efficiency File (*.eff)")
        if not new_eff_files:
            return

        used_eff_files = {
            Detector.get_used_efficiency_file_name(f)
            for f in self.efficiency_files
        }

        for eff_file in new_eff_files:
            new_eff_file = Path(eff_file)
            used_eff_file = Detector.get_used_efficiency_file_name(new_eff_file)

            if used_eff_file not in used_eff_files:
                try:
                    self.obj.add_efficiency_file(new_eff_file)
                    used_eff_files.add(used_eff_file)
                except OSError as e:
                    QtWidgets.QMessageBox.critical(
                        self, "Error",
                        f"Failed to add the efficiency file: {e}\n",
                        QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            else:
                QtWidgets.QMessageBox.critical(
                    self, "Error",
                    f"There already is an efficiency file for element "
                    f"{used_eff_file.stem}.\n",
                    QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)

        self.efficiency_files = self.obj.get_efficiency_files()
        # Store the folder where we previously fetched an eff-file
        gutils.set_potku_setting(
            DetectorSettingsWidget.EFF_FILE_FOLDER_KEY,
            str(new_eff_file.parent))

    def __remove_efficiency(self):
        """Removes efficiency files from detector's efficiency directory and
        updates settings view.
        """
        self.efficiencyListWidget: QtWidgets.QListWidget
        selected_items = self.efficiencyListWidget.selectedItems()
        if selected_items:
            reply = QtWidgets.QMessageBox.question(
                self, "Confirmation",
                "Are you sure you want to delete selected efficiencies?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No |
                QtWidgets.QMessageBox.Cancel, QtWidgets.QMessageBox.Cancel)
            if reply == QtWidgets.QMessageBox.No or reply == \
                    QtWidgets.QMessageBox.Cancel:
                return

            for item in selected_items:
                selected_eff_file = item.data(QtCore.Qt.UserRole)
                self.obj.remove_efficiency_file(selected_eff_file)

            self.efficiency_files = self.obj.get_efficiency_files()
            self._enable_remove_btn()

    def __open_calibration_dialog(self):
        """
        Open the CalibrationDialog.
        """
        measurements = [self.request.samples.measurements.get_key_value(key)
                        for key in
                        self.request.samples.measurements.measurements]
        CalibrationDialog(measurements, self.obj, self.run, self)

    def calculate_distance(self):
        """
        Calculate the distances of the foils from the target.
        """
        distance = 0
        for foil, widget in zip(self.tmp_foil_info,
                                self.detector_structure_widgets):
            distance += widget.distance_from_previous
            widget.cumulative_distance = distance
            foil.distance = distance

    def delete_foil(self, foil_widget):
        """Delete a foil from widgets and Foil objects.

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
        self.calculate_distance()
