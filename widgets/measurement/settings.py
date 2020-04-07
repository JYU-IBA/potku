# coding=utf-8
"""
Created on 10.4.2018
Updated on 27.11.2018

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
import time
import os

import widgets.binding as bnd
import widgets.input_validation as iv
import modules.masses as masses

from pathlib import Path
from modules.element import Element
from widgets.gui_utils import QtABCMeta
from dialogs.element_selection import ElementSelectionDialog

from PyQt5 import QtWidgets
from PyQt5 import uic
from PyQt5 import QtGui
from PyQt5.QtCore import QLocale
from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QGuiApplication


# Getters and setter for binding an Element object to GUI
def element_from_gui(instance, attrs):
    """Returns Element object from GUI.
    """
    symbol_btn = getattr(instance, attrs[0])
    isotope_box = getattr(instance, attrs[1])
    symbol = symbol_btn.text()
    if symbol == "Select":
        return None
    if isotope_box.currentIndex() == -1:
        isotope = None
    else:
        isotope = isotope_box.itemData(isotope_box.currentIndex())[0]
    return Element(symbol, isotope)


def element_to_gui(instance, attrs, value: Element):
    """Shows Element object in GUI.
    """
    symbol_btn = getattr(instance, attrs[0])
    isotope_box = getattr(instance, attrs[1])
    if value is None:
        symbol_btn.setText("Select")
        isotope_box.setEnabled(False)
    else:
        symbol_btn.setText(value.symbol)
        masses.load_isotopes(value.symbol, isotope_box, value.isotope)


class MeasurementSettingsWidget(QtWidgets.QWidget,
                                bnd.PropertyTrackingWidget,
                                metaclass=QtABCMeta):
    """Class for creating a measurement settings tab.
    """
    # TODO fix floating point precision when checking changes in values

    # Signal that indicates whether the beam selection was ok or not (i.e. can
    # the selected element be used in measurements or simulations)
    beam_selection_ok = pyqtSignal(bool)

    measurement_setting_file_name = bnd.bind("nameLineEdit")
    measurement_setting_file_description = bnd.bind("descriptionPlainTextEdit")

    beam_ion = bnd.multi_bind(
        ["beamIonButton", "isotopeComboBox"], fget=element_from_gui,
        fset=element_to_gui, track_change=True
    )
    beam_energy = bnd.bind("energyDoubleSpinBox", track_change=True)
    beam_energy_distribution = bnd.bind("energyDistDoubleSpinBox",
                                        track_change=True)
    beam_charge = bnd.bind("beamChargeSpinBox")
    beam_spot_size = bnd.multi_bind(["spotSizeXdoubleSpinBox",
                                    "spotSizeYdoubleSpinBox"],
                                    track_change=True)
    beam_divergence = bnd.bind("divergenceDoubleSpinBox", track_change=True)
    beam_profile = bnd.bind("profileComboBox", track_change=True)

    run_fluence = bnd.bind("fluenceDoubleSpinBox")
    run_current = bnd.bind("currentDoubleSpinBox")
    run_time = bnd.bind("timeDoubleSpinBox")
    run_charge = bnd.bind("runChargeDoubleSpinBox")

    target_theta = bnd.bind("targetThetaDoubleSpinBox", track_change=True)
    detector_theta = bnd.bind("detectorThetaDoubleSpinBox", track_change=True)

    def __init__(self, obj):
        """
        Initializes the widget.

        Args:
            obj: object that uses these settings, either a Measurement or a
                Simulation.
        """
        super().__init__()
        uic.loadUi(Path("ui_files", "ui_measurement_settings_tab.ui"), self)
        # QPixmap does not accept Path object, so use os.path.join instead
        pixmap = QtGui.QPixmap(os.path.join(
            "images", "measurement_setup_angles.png"))
        self.picture.setScaledContents(True)
        self.picture.setPixmap(pixmap)

        self.obj = obj
        self.__original_property_values = {}

        iv.set_input_field_red(self.nameLineEdit)
        self.fields_are_valid = False
        self.nameLineEdit.textChanged.connect(lambda: self.check_text(
            self.nameLineEdit, self))

        locale = QLocale.c()

        self.energyDoubleSpinBox.setLocale(locale)
        self.energyDistDoubleSpinBox.setLocale(locale)
        self.spotSizeXdoubleSpinBox.setLocale(locale)
        self.spotSizeYdoubleSpinBox.setLocale(locale)
        self.divergenceDoubleSpinBox.setLocale(locale)
        self.fluenceDoubleSpinBox.setLocale(locale)
        self.currentDoubleSpinBox.setLocale(locale)
        self.timeDoubleSpinBox.setLocale(locale)
        self.runChargeDoubleSpinBox.setLocale(locale)

        self.targetThetaDoubleSpinBox.setLocale(locale)
        self.detectorThetaDoubleSpinBox.setLocale(locale)
        self.detectorFiiDoubleSpinBox.setLocale(locale)
        self.targetFiiDoubleSpinBox.setLocale(locale)

        # Fii angles are currently not used so disable their spin boxes
        # TODO find out how fii angles should be used in MCERD so these
        #   can be enabled
        self.detectorFiiDoubleSpinBox.setEnabled(False)
        self.targetFiiDoubleSpinBox.setEnabled(False)

        # Copy of measurement's/simulation's run or default run
        # TODO should default run also be copied?
        if not self.obj.run:
            self.tmp_run = self.obj.request.default_run
        else:
            self.tmp_run = copy.deepcopy(self.obj.run)

        self.isotopeInfoLabel.setVisible(False)

        self.show_settings()

        self.beamIonButton.clicked.connect(self.change_element)

        self.nameLineEdit.textEdited.connect(self.__validate)

        self.fluenceDoubleSpinBox.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.actionMultiply = QtWidgets.QAction(self.fluenceDoubleSpinBox)
        self.actionMultiply.triggered.connect(self.__multiply_fluence)
        self.fluenceDoubleSpinBox.addAction(self.actionMultiply)

        self.actionUndo = QtWidgets.QAction(self.fluenceDoubleSpinBox)
        self.actionUndo.setText("Undo multiply")
        self.actionUndo.triggered.connect(self.__undo_fluence)

        if self.tmp_run.previous_fluence:
            self.actionUndo.setEnabled(True)
        else:
            self.actionUndo.setEnabled(False)
        self.fluenceDoubleSpinBox.addAction(self.actionUndo)

        self.clipboard = QGuiApplication.clipboard()
        self._ratio = None
        self.clipboard.changed.connect(self.__update_multiply_action)
        self.__update_multiply_action()

        self.energyDoubleSpinBox.setToolTip("Energy set in MeV with .")

    def get_original_property_values(self):
        """Returns the values of the properties when they were first set.
        """
        return self.__original_property_values

    def show_settings(self):
        """
        Show measurement settings.
        """
        self.measurement_setting_file_name = \
            self.obj.measurement_setting_file_name
        self.measurement_setting_file_description = \
            self.obj.measurement_setting_file_description
        self.dateLabel.setText(time.strftime("%c %z %Z", time.localtime(
            self.obj.modification_time)))

        run_params = {
            f"run_{key}": value
            for key, value in self.tmp_run.get_setting_parameters().items()
        }
        bean_params = {
            f"beam_{key}": value
            for key, value in self.tmp_run.beam.get_setting_parameters().items()
        }
        self.set_properties(**run_params, **bean_params)

        if self.obj.detector is None:
            self.detector_theta = \
                self.obj.request.default_detector.detector_theta
            # TODO should there be a none check for target too?
            self.target_theta = self.obj.request.default_target.target_theta
        else:
            self.detector_theta = self.obj.detector.detector_theta
            self.target_theta = self.obj.target.target_theta

    def check_angles(self):
        """
        Check that detector angle is bigger than target angle.
        This is a must for measurement. Simulation can handle target angles
        greater than the detector angle.

        Return:
            Whether it is ok to use current angle settings.
        """
        if self.target_theta > self.detector_theta:
            reply = QtWidgets.QMessageBox.question(
                self, "Warning",
                "Measurement cannot use a target angle that is "
                "bigger than the detector angle (for simulation "
                "this is possible).\n\n"
                "Do you want to use these settings anyway?",
                QtWidgets.QMessageBox.Ok |
                QtWidgets.QMessageBox.Cancel,
                QtWidgets.QMessageBox.Cancel)
            if reply == QtWidgets.QMessageBox.Cancel:
                return False
        return True

    def get_run_and_beam_parameters(self):
        """Returns run and beam related properties as separate dictionaries with
        prefixes removed from each key.
        """
        run_params, beam_params = {}, {}
        for k, v in self.get_properties().items():
            if k.startswith("run_"):
                run_params[k[4:]] = v
            elif k.startswith("beam_"):
                beam_params[k[5:]] = v
        return run_params, beam_params

    def update_settings(self):
        """
        Update measurement settings.
        """
        isotope_index = self.isotopeComboBox.currentIndex()
        if isotope_index != -1:
            self.obj.measurement_setting_file_name = \
                self.measurement_setting_file_name
            self.obj.measurement_setting_file_description = \
                self.measurement_setting_file_description

            run_params, beam_params = self.get_run_and_beam_parameters()
            self.obj.run.set_setting_parameters(**run_params)
            self.obj.run.beam.set_setting_parameters(**beam_params)
            self.obj.run.previous_fluence = self.tmp_run.previous_fluence
            self.obj.detector.detector_theta = self.detector_theta
            self.obj.target.target_theta = self.target_theta
        else:
            QtWidgets.QMessageBox.critical(self, "Warning",
                                           "No isotope selected.\n\nPlease "
                                           "select an isotope for the beam "
                                           "element.",
                                           QtWidgets.QMessageBox.Ok,
                                           QtWidgets.QMessageBox.Ok)

    def other_values_changed(self):
        """
        Check whether measurement values that don't require running a
        simulation again have been changed.

        Return:
             True or False.
        """
        # TODO make it possible to group TrackingProperties (for example into
        #  'critical' and 'noncritical' properties)
        if self.obj.measurement_setting_file_name != \
                self.measurement_setting_file_name:
            return True
        if self.obj.measurement_setting_file_description != \
                self.measurement_setting_file_description:
            return True
        if self.obj.run.beam.charge != self.beam_charge:
            return True
        if self.obj.run.current != self.run_current:
            return True
        if self.obj.run.time != self.run_time:
            return True
        if self.obj.run.charge != self.run_charge:
            return True
        if self.obj.run.fluence != self.run_fluence:
            return True
        return False

    def save_to_tmp_run(self):
        """
        Save run and beam parameters to tmp_run object.
        """
        isotope_index = self.isotopeComboBox.currentIndex()
        # TODO: Show a message box, don't just quietly do nothing
        if isotope_index != -1:
            run_params, beam_params = self.get_run_and_beam_parameters()
            self.tmp_run.set_setting_parameters(**run_params)
            self.tmp_run.beam.set_setting_parameters(**beam_params)
        else:
            QtWidgets.QMessageBox.critical(self, "Warning",
                                           "No isotope selected.\n\nPlease "
                                           "select an isotope for the beam "
                                           "element.",
                                           QtWidgets.QMessageBox.Ok,
                                           QtWidgets.QMessageBox.Ok)

    @staticmethod
    def check_text(input_field, settings):
        """Checks if there is text in given input field.

        Args:
            input_field: Input field the contents of which are checked.
        """
        settings.fields_are_valid = iv.check_text(input_field)

    def __validate(self):
        """
        Validate the measurement settings file name.
        """
        text = self.measurement_setting_file_name
        regex = "^[A-Za-z0-9-ÖöÄäÅå]*"
        valid_text = iv.validate_text_input(text, regex)

        self.measurement_setting_file_name = valid_text

    def __multiply_fluence(self):
        """
        Multiply fluence with clipboard's value.
        """
        try:
            new_fluence = round(self._ratio * self.run_fluence, 2)
            self.tmp_run.previous_fluence.append(self.run_fluence)
            self.run_fluence = new_fluence
            self.actionUndo.setEnabled(True)
        except ValueError:
            pass

    def __undo_fluence(self):
        """
        Undo latest change to fluence.
        """
        try:
            old_value = self.tmp_run.previous_fluence.pop()
        except IndexError:
            # cannot undo as the previous fluence list was empty.
            self.actionUndo.setEnabled(False)
            return

        self.fluenceDoubleSpinBox.setValue(old_value)
        self.actionUndo.setEnabled(bool(self.tmp_run.previous_fluence))

    def __update_multiply_action(self):
        """
        Update the value with which the multiplication is done.
        """
        try:
            self._ratio = float(self.clipboard.text())
        except ValueError:
            if self._ratio is None:
                self._ratio = 1.0
        self.actionMultiply.setText(f"Multiply with value in clipboard\n"
                                    f"({self._ratio})")

    def change_element(self):
        """ Opens element selection dialog and loads selected element's isotopes
        to the combobox.
        """
        dialog = ElementSelectionDialog()
        if dialog.element:
            self.beamIonButton.setText(dialog.element)
            masses.load_isotopes(dialog.element, self.isotopeComboBox)

            # Check if no isotopes
            if self.isotopeComboBox.count() == 0:
                self.isotopeInfoLabel.setVisible(True)
                self.fields_are_valid = False
                iv.set_input_field_red(self.isotopeComboBox)
                self.beam_selection_ok.emit(False)
            else:
                self.isotopeInfoLabel.setVisible(False)
                self.check_text(self.nameLineEdit, self)
                self.isotopeComboBox.setStyleSheet(
                    "background-color: %s" % "None")
                self.beam_selection_ok.emit(True)
        else:
            self.beam_selection_ok.emit(False)
