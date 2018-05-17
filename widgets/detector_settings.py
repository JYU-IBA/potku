# coding=utf-8
"""
Created on 12.4.2018
Updated on 17.5.2018
"""
import time

from PyQt5.QtCore import Qt

__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä " \
             "\n Sinikka Siironen"
__version__ = "2.0"

import os
import datetime
from PyQt5 import uic, QtWidgets

from dialogs.measurement.calibration import CalibrationDialog
from dialogs.simulation.foil import FoilDialog
from modules.foil import CircularFoil
from widgets.foil import FoilWidget
from modules.general_functions import open_file_dialog


class DetectorSettingsWidget(QtWidgets.QWidget):
    """Class for creating a detector settings tab.
    """
    def __init__(self, obj, request, icon_manager):
        super().__init__()
        self.ui = uic.loadUi(os.path.join("ui_files",
                                          "ui_request_detector_settings.ui"),
                             self)

        self.obj = obj
        self.request = request
        self.icon_manager = icon_manager

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
        self.ui.efficiencyListWidget.addItems(
            self.obj.get_efficiency_files())
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
        self.slopeLineEdit.setText(
            str(self.obj.tof_slope))
        self.offsetLineEdit.setText(
            str(self.obj.tof_offset))

        # Detector foils
        self.calculate_distance()
        self.tmp_foil_info = self.obj.foils

        # Tof foils
        self.tof_foils = self.obj.tof_foils

    def update_settings(self):
        """
        Update detector settings.
        """
        self.obj.name = \
            self.nameLineEdit.text()
        self.obj.description = \
            self.descriptionLineEdit.toPlainText()
        self.obj.type = \
            self.typeComboBox.currentText()
        self.obj.angle_offset = self.angleOffsetLineEdit.text()
        self.obj.angle_slope = self.angleSlopeLineEdit.text()
        self.obj.tof_offset = self.offsetLineEdit.text()
        self.obj.tof_slope = self.slopeLineEdit.text()
        # Detector foils
        self.calculate_distance()
        self.obj.foils = self.tmp_foil_info
        # Tof foils
        self.obj.tof_foils = self.tof_foils

    def _add_new_foil(self, layout, new_foil=CircularFoil()):
        """
        Add a new foil into detector.
         Args:
              layout: Layout into which the foil widget is added.
              new_foil: New Foil object to be added.
        """
        foil_widget = FoilWidget(self)
        self.tmp_foil_info.append(new_foil)
        foil_widget.ui.foilButton.setText(new_foil.name)
        foil_widget.ui.distanceDoubleSpinBox.setValue(0.0)
        foil_widget.ui.distanceLabel.setText(str(new_foil.distance))
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
        Add dafault foils as widgets.

        Return:
            Layout that holds the default foil widgets.
        """
        layout = QtWidgets.QHBoxLayout()
        target = QtWidgets.QLabel("Target")
        layout.addWidget(target)

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
        """Adds efficiency file in detector's efficiency directory and
        updates settings view.
        """
        new_efficiency_file = open_file_dialog(self,
                                               self.request.default_folder,
                                               "Select efficiency file",
                                               "Efficiency File (*.eff)")
        if not new_efficiency_file:
            return
        self.obj.add_efficiency_file(new_efficiency_file)
        self.ui.efficiencyListWidget.clear()
        self.ui.efficiencyListWidget.addItems(
            self.obj.get_efficiency_files())

    def __remove_efficiency(self):
        """Removes efficiency file from detector's efficiency directory and
        updates settings view.
        """
        selected_efficiency_file = self.ui. \
            efficiencyListWidget.currentItem().text()
        self.obj.remove_efficiency_file(
            selected_efficiency_file)
        self.ui.efficiencyListWidget.clear()
        self.ui.efficiencyListWidget.addItems(
            self.obj.get_efficiency_files())

    def __open_calibration_dialog(self):
        """
        Open the CalibrationDialog.
        """
        measurements = [self.request.samples.measurements.get_key_value(key)
                        for key in
                        self.request.samples.measurements.measurements.keys()]
        CalibrationDialog(measurements, self.obj, self)

    def calculate_distance(self):
        """
        Calculate the distances of the foils from the target.
        """
        distance = 0
        for i in range(len(self.detector_structure_widgets)):
            widget = self.detector_structure_widgets[i]
            distance = distance + widget.ui.distanceDoubleSpinBox.value()
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
