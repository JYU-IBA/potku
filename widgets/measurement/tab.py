# coding=utf-8
"""
Created on 21.3.2013
Updated on 18.12.2018

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2013-2018 Jarkko Aalto, Severi Jääskeläinen, Samuel Kaiponen,
Timo Konu, Samuli Kärkkäinen, Samuli Rahkonen, Miika Raunio, Heta Rekilä and
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
__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen " \
             "\n Samuli Rahkonen \n Miika Raunio \n Severi Jääskeläinen \n " \
             "Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"
__version__ = "2.0"

import os
from pathlib import Path
from typing import Optional

from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5 import uic

import dialogs.dialog_functions as df
import widgets.gui_utils as gutils

from dialogs.energy_spectrum import EnergySpectrumParamsDialog
from dialogs.energy_spectrum import EnergySpectrumWidget
from dialogs.measurement.depth_profile import DepthProfileDialog
from dialogs.measurement.depth_profile import DepthProfileWidget
from dialogs.measurement.element_losses import ElementLossesDialog
from dialogs.measurement.element_losses import ElementLossesWidget
from dialogs.measurement.settings import MeasurementSettingsDialog

from modules.element import Element
from modules.enums import DepthProfileUnit
from modules.general_functions import check_if_sum_in_directory_name
from modules.measurement import Measurement

from widgets.base_tab import BaseTab
from widgets.gui_utils import StatusBarHandler
from widgets.icon_manager import IconManager
from widgets.measurement.tofe_histogram import TofeHistogramWidget


class MeasurementTabWidget(BaseTab):
    """Tab widget where measurement stuff is added.
    """

    issueMaster = QtCore.pyqtSignal()

    def __init__(
            self,
            tab_id: int,
            measurement: Measurement,
            icon_manager: IconManager,
            statusbar: Optional[QtWidgets.QStatusBar] = None):
        """Init measurement tab class.
        Args:
            tab_id: An integer representing ID of the tabwidget.
            measurement: A measurement class object.
            icon_manager: An iconmanager class object.
            statusbar: A QtGui.QMainWindow's QStatusBar.
        """
        super().__init__(measurement, tab_id, icon_manager, statusbar)
        uic.loadUi(gutils.get_ui_dir() / "ui_measurement_tab.ui", self)

        # Various widgets that are shown in the tab. These will be populated
        # using the load_data method
        self.histogram = None
        self.elemental_losses_widget = None
        self.energy_spectrum_widget = None
        self.depth_profile_widget = None

        self.saveCutsButton.clicked.connect(self.measurement_save_cuts)
        self.analyzeElementLossesButton.clicked.connect(
            self.open_element_losses)
        self.energySpectrumButton.clicked.connect(self.open_energy_spectrum)
        self.createDepthProfileButton.clicked.connect(self.open_depth_profile)
        self.command_master.clicked.connect(self.__master_issue_commands)
        self.openSettingsButton.clicked.connect(self.__open_settings)

        df.set_up_side_panel(self, "mesu_panel_shown", "right")

        # Enable master button
        self.toggle_master_button()
        self.set_icons()
        BaseTab.check_default_settings(self)

    def get_default_widget(self):
        """Histogram will be the widget that gets activated when the tab
        is created.
        """
        return self.histogram

    def get_saveable_widgets(self):
        """Returns dictionary of widgets whose geometries will be stored.
        """
        return {
            "hist": self.histogram,
            "elem_loss": self.elemental_losses_widget,
            "espe": self.energy_spectrum_widget,
            "depth": self.depth_profile_widget,
            "log": self.log
        }

    def add_histogram(self, progress=None):
        """Adds ToF-E histogram into tab if it doesn't have one already.

        Args:
            progress: ProgressReporter object
        """
        self.histogram = TofeHistogramWidget(
            self.obj, self.icon_manager, self, statusbar=self.statusbar)

        if progress is not None:
            progress.report(40)
            sub_progress = progress.get_sub_reporter(lambda x: 40 + x * 0.2)
        else:
            sub_progress = None

        self.obj.set_axes(self.histogram.matplotlib.axes, progress=sub_progress)

        self.makeSelectionsButton.clicked.connect(
            lambda: self.histogram.matplotlib.elementSelectionButton.setChecked(
                True))
        self.histogram.matplotlib.selectionsChanged.connect(
            self.__set_cut_button_enabled)

        if progress is not None:
            progress.report(60)

        # Draw after giving axes -> selections set properly
        self.histogram.matplotlib.on_draw()

        #self.histogram.matplotlib.elementSelectionSelectButton.setEnabled(
        #   not self.obj.selector.is_empty()) # -TL
        self.add_widget(self.histogram, has_close_button=False)
        self.histogram.set_cut_button_enabled()

        # Check if there are selections in the measurement and enable save cut 
        # button. 
        self.__set_cut_button_enabled(self.obj.selector.selections)

        if progress is not None:
            progress.report(100)

    def check_previous_state_files(self, progress=None):
        """Check if saved state for Elemental Losses, Energy Spectrum or Depth
        Profile exists. If yes, load them also.

        Args:
            progress: a ProgressReporter object
        """
        self.make_elemental_losses(self.obj.get_composition_changes_dir())

        if progress is not None:
            progress.report(33)

        self.make_energy_spectrum(self.obj.get_energy_spectra_dir())

        if progress is not None:
            progress.report(50)
            sub_progress = progress.get_sub_reporter(lambda x: 50 + 0.4 * x)
        else:
            sub_progress = None

        directory_d = self.obj.get_depth_profile_dir()
        self.make_depth_profile(directory_d, progress=sub_progress)

        if progress is not None:
            progress.report(100)

    def make_depth_profile(self, save_directory: Path, progress=None):
        """Make depth profile from loaded lines from saved file.

        Args:
            directory: A path to depth files directory.
            progress: a ProgressReporter object
        """
        file = Path(save_directory, DepthProfileWidget.save_file)
        lines = MeasurementTabWidget._load_file(file)
        if not lines:
            return
        m_name = self.obj.name
        try:
            output_dir = self.obj.directory / lines[0].strip()
            use_cuts = self.__cutfiles_from_other_measurement(save_directory.parent, lines[2].strip().split("\t"))
            elements = [Element.from_string(e) for e in lines[1].strip().split("\t")]
            try:
                x_unit = DepthProfileUnit.from_string(lines[3].strip())
            except ValueError:
                x_unit = DepthProfileUnit.ATOMS_PER_SQUARE_CM
            line_zero = False
            line_scale = False
            systerr = 0.0
            used_eff = True
            eff_files_str = None
            if len(lines) == 7:  # "Backwards compatibility"
                line_zero = lines[4].strip() == "True"
                line_scale = lines[5].strip() == "True"
                systerr = float(lines[6].strip())
            DepthProfileDialog.x_unit = x_unit
            DepthProfileDialog.checked_cuts[m_name] = set(use_cuts)
            DepthProfileDialog.line_zero = line_zero
            DepthProfileDialog.line_scale = line_scale
            DepthProfileDialog.systerr = systerr
            DepthProfileDialog.used_eff = used_eff
            DepthProfileDialog.eff_files_str = eff_files_str

            self.depth_profile_widget = DepthProfileWidget(self, output_dir, use_cuts, elements, x_unit, line_zero, used_eff,
                                                           line_scale, systerr, eff_files_str, progress=progress)
            icon = self.icon_manager.get_icon("depth_profile_icon_2_16.png")
            self.add_widget(self.depth_profile_widget, icon=icon)
        except Exception as e:
            # We do not need duplicate error logs, log in widget instead
            print(e)

    def make_elemental_losses(self, directory, progress=None):
        """Make elemental losses from loaded lines from saved file.

        Args:
            directory: A string representing directory.
            name: A string representing measurement's name.
            serial_number: Measurement's serial number.
            old_sample_name: Sample folder of the measurement.
            progress: a ProgressReporter object
        """
        file = Path(directory, ElementLossesWidget.save_file)
        lines = MeasurementTabWidget._load_file(file)
        if not lines:
            return
        m_name = self.obj.name
        try:
            reference_cut = self.__cutfiles_from_other_measurement(directory.parent, [lines[0].strip()])[0]
            checked_cuts = self.__cutfiles_from_other_measurement(directory.parent, lines[1].strip().split("\t"))
            split_count = int(lines[2])
            y_scale = int(lines[3])
            ElementLossesDialog.reference_cut[m_name] = reference_cut
            ElementLossesDialog.checked_cuts[m_name] = set(checked_cuts)
            ElementLossesDialog.split_count = split_count
            ElementLossesDialog.y_scale = y_scale
            self.elemental_losses_widget = ElementLossesWidget(
                self, self.obj, reference_cut, checked_cuts, split_count,
                y_scale, statusbar=self.statusbar, progress=progress)
            icon = self.icon_manager.get_icon("elemental_losses_icon_16.png")
            self.add_widget(self.elemental_losses_widget, icon=icon)
        except Exception as e:
            # We do not need duplicate error logs, log in widget instead
            print(e)

    def make_energy_spectrum(self, directory: Path):
        """Make energy spectrum from loaded lines from saved file.

        Args:
            directory: The directory where widget_energy_spectrum.save can be found, containing all settings .
        """
        file = Path(directory, EnergySpectrumWidget.save_file)
        lines = MeasurementTabWidget._load_file(file)
        if not lines:
            return
        m_name = self.obj.name
        try:
            use_cuts = self.__cutfiles_from_other_measurement(directory.parent, lines[0].strip().split("\t"))
            width = float(lines[1].strip())
            EnergySpectrumParamsDialog.bin_width = width
            EnergySpectrumParamsDialog.checked_cuts[m_name] = set(use_cuts)
            is_measured_sum_spectrum_selected, _ = \
                check_if_sum_in_directory_name(directory)
            self.energy_spectrum_widget = EnergySpectrumWidget(
                self, use_cuts=use_cuts, spectrum_type=EnergySpectrumWidget.MEASUREMENT,
                measured_sum_spectrum_is_selected=is_measured_sum_spectrum_selected,
                bin_width=width)
            icon = self.icon_manager.get_icon("energy_spectrum_icon_16.png")
            self.add_widget(self.energy_spectrum_widget, icon=icon)
        except Exception as e:
            print(e)

    def measurement_save_cuts(self):
        """Save measurement selections to cut files.
        """
        sbh = StatusBarHandler(self.statusbar)
        self.obj.save_cuts(progress=sbh.reporter)
        # Do for all slaves if master.
        self.obj.request.save_cuts(self.obj)

    def __open_settings(self):
        """Opens measurement settings dialog.
        """
        MeasurementSettingsDialog(self, self.obj, self.icon_manager)

    def open_depth_profile(self):
        """Opens depth profile dialog.
        """
        previous = self.depth_profile_widget
        DepthProfileDialog(self, self.obj, self.obj.request.global_settings,
                           statusbar=self.statusbar)
        if self.depth_profile_widget != previous and \
                type(self.depth_profile_widget) is not None:
            # TODO type(x) is not None???
            self.depth_profile_widget.save_to_file()

    def open_energy_spectrum(self):
        """Opens energy spectrum dialog.
        """
        previous = self.energy_spectrum_widget
        EnergySpectrumParamsDialog(
            self, spectrum_type=EnergySpectrumWidget.MEASUREMENT,
            measurement=self.obj, statusbar=self.statusbar)
        if self.energy_spectrum_widget != previous and \
                type(self.energy_spectrum_widget) is not None:
            # TODO type(x) is not None???
            self.energy_spectrum_widget.save_to_file()

    def open_element_losses(self):
        """Opens element losses dialog.
        """
        previous = self.elemental_losses_widget
        ElementLossesDialog(self, self.obj, statusbar=self.statusbar)
        if self.elemental_losses_widget != previous and \
                self.elemental_losses_widget is not None:
            self.elemental_losses_widget.save_to_file()

    def toggle_master_button(self):
        """Toggle enabled state of the master measurement button in the
        measurementtabwidget.
        """
        measurement_name = self.obj.name
        master = self.obj.request.has_master()
        if master != "":
            master_name = master.name
        else:
            master_name = None
        self.command_master.setEnabled(measurement_name == master_name)

    def __cutfiles_with_correct_measurement_name(self, cuts: list[Path]) -> list[Path]:
        """Changes measurement name from a list of cutfiles. Bad solution that replaces an even worse solution.
        e.g. path/to/foo.1H.ERD.0.cut will be turned into path/to/self_obj_name.1H.ERD.0.cut
        """
        return [cut.parent / cut.name.replace(cut.name.split(".", 1)[0], self.obj.name) for cut in cuts]
    def __cutfiles_from_other_measurement(self, other_directory: Path, cutfiles_str: list[str]) -> list[Path]:
        """Other measurement can also be the same measurement. Changes absolute and relative paths to be absolute
        (and for this measurement). Changes the name of the measurement too
        (see __cutfiles_with_correct_measurement_name())"""
        cuts = [Path(cut_str).relative_to(other_directory) if Path(cut_str).is_absolute()
                    else Path(cut_str) for cut_str in cutfiles_str if cut_str != '']  # Turn absolute paths
        # relative to (target) measurement directory
        cuts = [Path(self.obj.directory) / cut
                    for cut in self.__cutfiles_with_correct_measurement_name(cuts)]
        return cuts


    def __validate_file_path(self, file_path: Path):
        """Helper function that checks if the given file_path points to file.
        If it does, returns the file path as it was given, otherwise treats
        the file_path as a relative path and returns an absolute path within
        object's directory.
        """
        if file_path.is_file():
            return file_path
        return Path(self.obj.directory, file_path)

    @staticmethod
    def _load_file(file: Path):
        """Load file

        Args:
            file: A string representing full filepath to the file.
        """
        lines = []
        try:
            with file.open("r") as fp:
                for line in fp:
                    lines.append(line)
        except (OSError, UnicodeDecodeError) as e:
            # TODO when opening a widget_safe_file that was saved on another
            #      platform, UnicodeDecodeError is raised. Log this.
            print(e)
        return lines

    def __master_issue_commands(self):
        """Signal that master measurement's command has been issued
        to all slave measurements in the request.
        """
        meas_name = self.obj.name
        master = self.obj.request.has_master()
        if master != "":
            master_name = master.name
        else:
            master_name = None
        if meas_name == master_name:
            self.issueMaster.emit()

    def __set_cut_button_enabled(self, selections):
        """Enables save cuts button if the given selections list's lenght is
        not 0.
        Otherwise disable.

        Args:
            selections: list of Selection objects
        """
        self.saveCutsButton.setEnabled(len(selections))

    def set_icons(self):
        """Adds icons to UI elements.
        """
        self.icon_manager.set_icon(self.makeSelectionsButton,
                                   "amarok_edit.svg", size=(30, 30))
        self.icon_manager.set_icon(self.saveCutsButton,
                                   "save_all.svg", size=(30, 30))
        self.icon_manager.set_icon(self.analyzeElementLossesButton,
                                   "elemental_losses_icon.svg", size=(30, 30))
        self.icon_manager.set_icon(self.energySpectrumButton,
                                   "energy_spectrum_icon.svg", size=(30, 30))
        self.icon_manager.set_icon(self.createDepthProfileButton,
                                   "depth_profile.svg", size=(30, 30))
        self.icon_manager.set_icon(self.command_master,
                                   "editcut.svg", size=(30, 30))

    def load_data(self, progress=None):
        """Loads the data belonging to the Measurement into view.
        """
        # Check that the data is read.
        if not self.data_loaded:
            self.data_loaded = True
            self.obj.load_data()

            if progress is not None:
                progress.report(25)
                sub_progress = progress.get_sub_reporter(
                    lambda x: 25 + 0.5 * x
                )
            else:
                sub_progress = None

            self.add_histogram(progress=sub_progress)

            if progress is not None:
                progress.report(75)
                sub_progress = progress.get_sub_reporter(
                    lambda x: 75 + 0.2 * x
                )

            # Load previous states.
            self.check_previous_state_files(sub_progress)

            self.restore_geometries()

        if progress is not None:
            progress.report(100)

    def check_default_settings_clicked(self) -> None:
        """Gives an warning if the default settings are checked in the
        settings tab.
        """
        if not self.obj.use_request_settings:
            self.warning_text.setText("Not using request setting values ("
                                      "default)")
            self.warning_text.setStyleSheet("background-color: yellow")
        else:
            self.warning_text.setText("")
            self.warning_text.setStyleSheet("")