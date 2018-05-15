# coding=utf-8
"""
Created on 4.5.2018
Updated on 11.5.2018
"""
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä " \
             "\n Sinikka Siironen"
__version__ = "2.0"

from PyQt5 import uic
from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore
import os
import modules.masses as masses
from widgets.measurement.settings import MeasurementSettingsWidget
from modules.input_validator import InputValidator
from dialogs.element_selection import ElementSelectionDialog
from widgets.detector_settings import DetectorSettingsWidget
from widgets.profile_settings import ProfileSettingsWidget
from modules.run import Run
from modules.detector import Detector
import json
import datetime
import time
import shutil


class MeasurementSettingsDialog(QtWidgets.QDialog):
    """
    Dialog class for handling the measurement parameter input.
    """
    def __init__(self, measurement, icon_manager):
        """
        Initializes the dialog.

        Args:
            measurement: A Measurement object whose parameters are handled.
            icon_manager: An icon manager.
        """
        super().__init__()
        self.measurement = measurement
        self.icon_manager = icon_manager
        self.ui = uic.loadUi(os.path.join("ui_files",
                                          "ui_specific_settings.ui"), self)
        self.ui.setWindowTitle("Measurement Settings")
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        screen_geometry = QtWidgets.QDesktopWidget.availableGeometry(
            QtWidgets.QApplication.desktop())
        self.resize(self.geometry().width(), screen_geometry.size().height()
                    * 0.8)
        self.ui.defaultSettingsCheckBox.stateChanged.connect(
            lambda: self.__change_used_settings())
        self.ui.OKButton.clicked.connect(lambda:
                                         self.__save_settings_and_close())
        self.ui.applyButton.clicked.connect(lambda: self.__update_parameters())
        self.ui.cancelButton.clicked.connect(self.close)

        # Add measurement settings view to the settings view
        self.measurement_settings_widget = MeasurementSettingsWidget(
            self.measurement)
        self.ui.tabs.addTab(self.measurement_settings_widget, "Measurement")

        self.measurement_settings_widget.ui.picture.setScaledContents(True)
        pixmap = QtGui.QPixmap(os.path.join("images", "hardwaresetup.png"))
        self.measurement_settings_widget.ui.picture.setPixmap(pixmap)

        self.measurement_settings_widget.ui.beamIonButton.clicked.connect(
            lambda: self.__change_element(
                self.measurement_settings_widget.ui.beamIonButton,
                self.measurement_settings_widget.ui.isotopeComboBox))

        # Add detector settings view to the settings view
        if self.measurement.detector:
            detector_object = self.measurement.detector
        else:
            detector_object = self.measurement.request.default_detector
        self.detector_settings_widget = DetectorSettingsWidget(
            detector_object, self.measurement.request, self.icon_manager)
        # 2 is calibration tab that is not needed
        calib_tab_widget = self.detector_settings_widget.ui.tabs.widget(2)
        self.detector_settings_widget.ui.tabs.removeTab(2)
        calib_tab_widget.deleteLater()

        self.ui.tabs.addTab(self.detector_settings_widget, "Detector")

        if self.measurement.detector is not None:
            self.ui.defaultSettingsCheckBox.setCheckState(0)
            self.measurement_settings_widget.ui.nameLineEdit.setText(
                self.measurement.measurement_setting_file_name)
            self.measurement_settings_widget.ui.descriptionPlainTextEdit\
                .setPlainText(
                    self.measurement.measurement_setting_file_description)
            self.measurement_settings_widget.ui.dateLabel.setText(str(
                datetime.datetime.fromtimestamp(
                    self.measurement.modification_time)))

        # Add profile settings view to the settings view
        self.profile_settings_widget = ProfileSettingsWidget(
            self.measurement)
        self.ui.tabs.addTab(self.profile_settings_widget, "Profile")

        self.exec()

    def __change_element(self, button, combo_box):
        """ Opens element selection dialog and loads selected element's isotopes
        to a combobox.

        Args:
            button: button whose text is changed accordingly to the made
            selection.
        """
        dialog = ElementSelectionDialog()
        if dialog.element:
            button.setText(dialog.element)
            # Enabled settings once element is selected
            self.__enabled_element_information()
            masses.load_isotopes(dialog.element, combo_box)

    def __change_used_settings(self):
        check_box = self.sender()
        if check_box.isChecked():
            self.ui.tabs.setEnabled(False)
        else:
            self.ui.tabs.setEnabled(True)

    def __enabled_element_information(self):
        """
        Change the UI accordingly when an element is selected.
        """
        self.measurement_settings_widget.ui.isotopeComboBox.setEnabled(True)
        self.measurement_settings_widget.ui.isotopeLabel.setEnabled(True)
        self.ui.OKButton.setEnabled(True)

    def __update_parameters(self):
        """
         Update Measurement's Run, Detector and Target objects. If measurement
         specific parameters are in use, save them into a file.
        """
        check_box = self.ui.defaultSettingsCheckBox
        if check_box.isChecked():
            self.measurement.run = None
            self.measurement.detector = None
            self.measurement.measurement_setting_file_name = None
            self.measurement.measurement_setting_file_description = None
            self.measurement.target.target_theta = \
                self.measurement.request.default_target.target_theta
            # TODO: delete possible measurement specific files.
            det_folder_path =os.path.join(self.measurement.directory,
                                           "Detector")
            if os.path.exists(det_folder_path):
                shutil.rmtree(det_folder_path)
            filenames_to_remove = []
            for file in os.listdir(self.measurement.directory):
                if file.endswith(".measurement") or file.endswith(".profile"):
                    filenames_to_remove.append(file)
            for file in filenames_to_remove:
                os.remove(os.path.join(self.measurement.directory,
                                       file))
        else:
            try:
                if self.measurement.measurement_setting_file_name is None:
                    file_name = "temp"
                else:
                    file_name = self.measurement.measurement_setting_file_name
                measurement_settings_file_path = os.path.join(
                    self.measurement.directory, file_name + ".measurement")
                profile_file_path = os.path.join(self.measurement.directory,
                                                self.measurement.profile_name +
                                                ".profile")
                det_folder_path = os.path.join(self.measurement.directory,
                                               "Detector")
                if self.measurement.run is None:
                    self.measurement.run = Run()
                if self.measurement.detector is None:
                    detector_file_path = os.path.join(det_folder_path,
                                                      "Default.detector")
                    if not os.path.exists(det_folder_path):
                        os.makedirs(det_folder_path)
                    self.measurement.detector = Detector(
                        detector_file_path, measurement_settings_file_path)
                    self.measurement.detector.create_folder_structure(
                        det_folder_path)
                else:
                    detector_file_path = self.measurement.detector.path
                self.detector_settings_widget.obj = self.measurement.detector

                self.measurement_settings_widget.update_settings()
                self.detector_settings_widget.update_settings()
                self.profile_settings_widget.update_settings()
                self.measurement.detector.path = \
                    os.path.join(det_folder_path,
                                 self.measurement.detector.name + ".detector")

                # Save general measurement settings parameters.
                new_measurement_settings_file_path = os.path.join(
                    self.measurement.directory,
                    self.measurement.measurement_setting_file_name +
                    ".measurement")
                gen_obj = {
                        "name": self.measurement.measurement_setting_file_name,
                        "description": self.measurement.
                        measurement_setting_file_description,
                        "modification_time": str(
                            datetime.datetime.fromtimestamp(time.time(

                            ))),
                        "modification_time_unix": time.time()
                }
                if os.path.exists(new_measurement_settings_file_path):
                    obj = json.load(open(new_measurement_settings_file_path))
                    obj["general"] = gen_obj
                else:
                    obj = {
                        "general": gen_obj
                    }

                # Delete possible extra .measurement files
                filename_to_remove = ""
                for file in os.listdir(self.measurement.directory):
                    if file.endswith(".measurement"):
                        filename_to_remove = file
                        break
                if filename_to_remove:
                    os.remove(os.path.join(self.measurement.directory,
                                           filename_to_remove))

                with open(new_measurement_settings_file_path, "w") as file:
                    json.dump(obj, file, indent=4)

                self.measurement.run.to_file(new_measurement_settings_file_path)
                self.measurement.detector.\
                    to_file(self.measurement.detector.path,
                            new_measurement_settings_file_path)
                self.measurement.profile_to_file(profile_file_path)
            except TypeError:
                QtWidgets.QMessageBox.question(self, "Warning",
                                               "Some of the setting values "
                                               "have not been set.\n" +
                                               "Please input setting values to "
                                               "save them.",
                                               QtWidgets.QMessageBox.Ok,
                                               QtWidgets.QMessageBox.Ok)

    def __save_settings_and_close(self):
        self.__update_parameters()
        self.close()
