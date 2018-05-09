# coding=utf-8
"""
Created on 4.5.2018
Updated on 8.5.2018
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
from widgets.foil import FoilWidget
from modules.foil import CircularFoil
from dialogs.simulation.foil import FoilDialog


class SimulationSettingsDialog(QtWidgets.QDialog):
    """
    Dialog class for handling the simulation parameter input.
    """
    def __init__(self, simulation, icon_manager):
        """
        Initializes the dialog.

        Args:
            simulation: A Simulation object whose parameters are handled.
            icon_manager: An icon manager.
        """
        super().__init__()
        self.simulation = simulation
        self.icon_manager = icon_manager
        self.ui = uic.loadUi(os.path.join("ui_files",
                                          "ui_simulation_settings.ui"), self)
        self.ui.setWindowTitle("Simulation Settings")
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        screen_geometry = QtWidgets.QDesktopWidget.availableGeometry(
            QtWidgets.QApplication.desktop())
        self.resize(self.geometry().width(), screen_geometry.size().height()
                    * 0.8)
        self.ui.simulationSettingsCheckBox.stateChanged.connect(
            lambda: self.__change_used_settings())
        self.ui.OKButton.clicked.connect(lambda:
                                         self.__save_settings_and_close())
        self.ui.applyButton.clicked.connect(lambda: self.__save_settings())
        self.ui.cancelButton.clicked.connect(self.close)

        double_validator = InputValidator()
        positive_double_validator = InputValidator(bottom=0)

        # Add measurement settings view to the settings view
        self.measurement_settings_widget = MeasurementSettingsWidget()
        self.ui.tabs.addTab(self.measurement_settings_widget, "Measurement")
        self.measurement_settings_widget.ui.beamIonButton.setText("Select")
        self.measurement_settings_widget.ui.isotopeComboBox.setEnabled(False)

        # self.measurement_settings_widget.ui.energyLineEdit.setValidator(
        #     positive_double_validator)
        double_angle_validator = InputValidator(0, 90, 10)
        # self.measurement_settings_widget.ui.detectorThetaLineEdit.setValidator(
        #     double_angle_validator)
        # self.measurement_settings_widget.ui.targetThetaLineEdit.setValidator(
        #     double_angle_validator)
        self.measurement_settings_widget.ui.picture.setScaledContents(True)
        pixmap = QtGui.QPixmap(os.path.join("images", "hardwaresetup.png"))
        self.measurement_settings_widget.ui.picture.setPixmap(pixmap)

        self.measurement_settings_widget.ui.beamIonButton.clicked.connect(
            lambda: self.__change_element(
                self.measurement_settings_widget.ui.beamIonButton,
                self.measurement_settings_widget.ui.isotopeComboBox))

        # Add detector settings view to the settings view
        self.detector_settings_widget = DetectorSettingsWidget()
        # 2 is calibration tab that is not needed
        calib_tab_widget = self.detector_settings_widget.ui.tabs.widget(2)
        self.detector_settings_widget.ui.tabs.removeTab(2)
        calib_tab_widget.deleteLater()

        self.ui.tabs.addTab(self.detector_settings_widget, "Detector")

        # Temporary foils list which holds all the information given in the
        # foil dialog
        # If user presses ok or apply, these values will be saved into
        # request's default detector
        self.tmp_foil_info = []

        # List of foil indexes that are timing foils
        self.tof_foils = []

        # Add foil widgets and foil objects
        self.detector_structure_widgets = []

        self.foils_layout = self.__read_foils()
        self.detector_settings_widget.ui.detectorScrollAreaContents.layout() \
            .addLayout(self.foils_layout)
        self.detector_settings_widget.ui.newFoilButton.clicked.connect(
            lambda: self._add_new_foil(self.foils_layout))

        # Efficiency files
        if self.simulation.detector:
            self.detector_settings_widget.ui.efficiencyListWidget.addItems(
                self.simulation.detector.get_efficiency_files())
        else:
            self.detector_settings_widget.ui.efficiencyListWidget.addItems(
                self.simulation.request.default_detector.get_efficiency_files())
        self.detector_settings_widget.ui.addEfficiencyButton.clicked.connect(
            lambda: self.__add_efficiency())
        self.detector_settings_widget.ui.removeEfficiencyButton.clicked.connect(
            lambda: self.__remove_efficiency())

        self.exec()

    def _add_new_foil(self, layout):
        """
        Add a new foil to given layer. Default CircularFoil.

        Args:
             layout: Layout in which the new foil is added.
        """
        foil_widget = FoilWidget(self)
        new_foil = CircularFoil("Foil", layers=[])
        self.tmp_foil_info.append(new_foil)
        foil_widget.ui.foilButton.clicked.connect(
            lambda: self._open_foil_dialog())
        foil_widget.ui.timingFoilCheckBox.stateChanged.connect(
            lambda: self._check_and_add())
        foil_widget.ui.distanceEdit.setText(str(new_foil.distance))
        self.detector_structure_widgets.append(foil_widget)
        layout.addWidget(foil_widget)

        if len(self.tof_foils) >= 2:
            foil_widget.ui.timingFoilCheckBox.setEnabled(False)
        return foil_widget

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

    def _check_and_add(self):
        """
        Check if foil needs to be added or deleted from tof foils and update
        the list and enabled cehckboxes accordingly.
        """
        check_box = self.sender()
        for i in range(len(self.detector_structure_widgets)):
            if self.detector_structure_widgets[i].\
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
        Disable all but tof foil checkboxes.
        """
        for i in range(len(self.detector_structure_widgets)):
            if i not in self.tof_foils:
                widget = self.detector_structure_widgets[i]
                widget.ui.timingFoilCheckBox.setEnabled(False)

    def _enable_checkboxes(self):
        """
        Enable all checkboxes.
        """
        for i in range(len(self.detector_structure_widgets)):
            widget = self.detector_structure_widgets[i]
            widget.ui.timingFoilCheckBox.setEnabled(True)

    def __enabled_element_information(self):
        """
        Change the UI accordingly when an element is selected.
        """
        self.measurement_settings_widget.ui.isotopeComboBox.setEnabled(True)
        self.measurement_settings_widget.ui.isotopeLabel.setEnabled(True)
        self.ui.OKButton.setEnabled(True)

    def _open_foil_dialog(self):
        """
        Open FoilDialog, with which the foil info can be updated.
        """
        foil_name = self.sender().text()
        foil_object_index = -1
        for i in range(len(self.tmp_foil_info)):
            if foil_name == self.tmp_foil_info[i].name:
                foil_object_index = i
                break
        FoilDialog(self.tmp_foil_info, foil_object_index, self.icon_manager)
        self.sender().setText(self.tmp_foil_info[foil_object_index].name)

    def __read_foils(self):
        """
        Read foils and add into layout.

        Return:
            Layout that has the foils.
        """
        # TODO: This should read foil info from file or objects.
        layout = QtWidgets.QHBoxLayout()
        target = QtWidgets.QLabel("Target")
        layout.addWidget(target)
        return layout

    def __save_settings(self):
        check_box = self.ui.simulationSettingsCheckBox
        if check_box.isChecked():
            self.simulation.run = self.simulation.request.default_run
            self.simulation.detector = None
            # TODO: delete possible simulation specific files.
        else:
            # TODO: update settings for run, target angle, and detector
            try:
                self.measurement_settings_widget.update_settings()
                self.request.default_measurement.to_file(os.path.join(
                    self.request.default_measurement.directory,
                    "Default.measurement"), os.path.join(
                    self.request.default_measurement.directory,
                    "Default.profile"))
            except TypeError:
                QtWidgets.QMessageBox.question(self, "Warning",
                                               "Some of the setting values "
                                               "have not been set.\n" +
                                               "Please input setting values to "
                                               "save them.",
                                               QtWidgets.QMessageBox.Ok,
                                               QtWidgets.QMessageBox.Ok)

    def __save_settings_and_close(self):
        self.__save_settings()
        self.close()
