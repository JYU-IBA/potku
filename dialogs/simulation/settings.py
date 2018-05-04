# coding=utf-8
"""
Created on 4.5.2018
Updated on ....
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
from dialogs.measurement.calibration import CalibrationDialog
from widgets.foil import FoilWidget
from modules.foil import CircularFoil


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
        self.ui = uic.loadUi(os.path.join("ui_files", "ui_settings.ui"), self)
        self.ui.setWindowTitle("Simulation Settings")
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        screen_geometry = QtWidgets.QDesktopWidget.availableGeometry(
            QtWidgets.QApplication.desktop())
        self.resize(self.geometry().width(), screen_geometry.size().height()
                    * 0.8)

        double_validator = InputValidator()
        positive_double_validator = InputValidator(bottom=0)

        # Add measurement settings view to the settings view
        self.measurement_settings_widget = MeasurementSettingsWidget()
        self.ui.tabs.addTab(self.measurement_settings_widget, "Measurement")
        self.measurement_settings_widget.ui.beamIonButton.setText("Select")
        self.measurement_settings_widget.ui.isotopeComboBox.setEnabled(False)

        self.measurement_settings_widget.ui.energyLineEdit.setValidator(
            positive_double_validator)
        double_angle_validator = InputValidator(0, 90, 10)
        self.measurement_settings_widget.ui.detectorThetaLineEdit.setValidator(
            double_angle_validator)
        self.measurement_settings_widget.ui.targetThetaLineEdit.setValidator(
            double_angle_validator)
        self.measurement_settings_widget.ui.picture.setScaledContents(True)
        pixmap = QtGui.QPixmap(os.path.join("images", "hardwaresetup.png"))
        self.measurement_settings_widget.ui.picture.setPixmap(pixmap)

        self.measurement_settings_widget.ui.beamIonButton.clicked.connect(
            lambda: self.__change_element(
                self.measurement_settings_widget.ui.beamIonButton,
                self.measurement_settings_widget.ui.isotopeComboBox))

        # Add detector settings view to the settings view
        self.detector_settings_widget = DetectorSettingsWidget()
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
        self.detector_settings_widget.ui.efficiencyListWidget.addItems(
            self.simulation.detector.get_efficiency_files())
        self.detector_settings_widget.ui.addEfficiencyButton.clicked.connect(
            lambda: self.__add_efficiency())
        self.detector_settings_widget.ui.removeEfficiencyButton.clicked.connect(
            lambda: self.__remove_efficiency())

        # Calibration settings
        self.detector_settings_widget.ui.executeCalibrationButton.clicked. \
            connect(self.__open_calibration_dialog)
        self.detector_settings_widget.ui.slopeLineEdit.setValidator(
            double_validator)
        self.detector_settings_widget.ui.offsetLineEdit.setValidator(
            double_validator)

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
            lambda: self._open_composition_dialog())
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

    def __enabled_element_information(self):
        """
        Change the UI accordingly when an element is selected.
        """
        self.measurement_settings_widget.ui.isotopeComboBox.setEnabled(True)
        self.measurement_settings_widget.ui.isotopeLabel.setEnabled(True)
        self.ui.OKButton.setEnabled(True)

    def __open_calibration_dialog(self):
        """
        Open a CalibrationDialog.
        """
        measurements = [self.request.measurements.get_key_value(key)
                        for key in
                        self.request.samples.measurements.measurements.keys()]
        CalibrationDialog(measurements, self.settings, self)

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
