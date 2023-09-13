# coding=utf-8
"""
Created on 1.3.2018
Updated on 27.5.2019

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

import os
from collections import Counter
from pathlib import Path
from typing import Optional, Union

from PyQt5 import QtWidgets
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal

import dialogs.dialog_functions as df
import widgets.gui_utils as gutils

from dialogs.energy_spectrum import EnergySpectrumWidget
from dialogs.simulation.optimization import OptimizationDialog
from dialogs.simulation.settings import SimulationSettingsDialog

from modules.concurrency import CancellationToken
from modules.element_simulation import ElementSimulation
from modules.enums import OptimizationType
from modules.general_functions import check_if_sum_in_directory_name
from modules.global_settings import GlobalSettings
from modules.observing import ProgressReporter
from modules.request import Request
from modules.simulation import Simulation

from widgets.base_tab import BaseTab
from widgets.icon_manager import IconManager
from widgets.simulation.optimized_fluence import OptimizedFluenceWidget
from widgets.simulation.optimized_recoils import OptimizedRecoilsWidget
from widgets.simulation.target import TargetWidget


class SimulationTabWidget(BaseTab):
    """Tab widget where simulation stuff is added.
    """

    def __init__(
            self,
            request: Request,
            tab_id: int,
            simulation: Simulation,
            icon_manager: IconManager,
            statusbar: Optional[QtWidgets.QStatusBar] = None):
        """ Init simulation tab class.
        
        Args:
            request: Request that has the simulation object.
            tab_id: An integer representing ID of the tab widget.
            simulation: A simulation class object.
            icon_manager: An icon manager class object.
            statusbar: A QtGui.QMainWindow's QStatusBar.
        """
        super().__init__(simulation, tab_id, icon_manager, statusbar)
        uic.loadUi(gutils.get_ui_dir() / "ui_simulation_tab.ui", self)

        self.request = request

        self.simulation_target = None
        self.energy_spectrum_widgets = []
        self.optimization_result_widget = None

        df.set_up_side_panel(self, "simu_panel_shown", "right")

        self.openSettingsButton.clicked.connect(self.__open_settings)
        self.optimizeButton.clicked.connect(self.__open_optimization_dialog)
        BaseTab.check_default_settings(self)

    def get_saveable_widgets(self):
        """Returns a list of Widgets whose geometries can be saved.
        """
        return {}

    def get_default_widget(self) -> None:
        # TODO
        return None

    def add_simulation_target_and_recoil(
            self,
            settings: GlobalSettings,
            progress: Optional[ProgressReporter] = None,
            **kwargs) -> None:
        """Add target widget for modifying the target and recoils into tab.

        Args:
            settings: a GlobalSettings object
            progress: ProgressReporter object
            kwargs: keyword arguments passed down to TargetWidget
        """
        self.simulation_target = TargetWidget(
            self, self.obj, self.obj.target, self.icon_manager, settings,
            progress=progress, statusbar=self.statusbar, **kwargs)
        self.add_widget(self.simulation_target, has_close_button=False)

    def add_optimization_results_widget(
            self,
            elem_sim: ElementSimulation,
            cut_file_name: str,
            mode_recoil: OptimizationType,
            ct: Optional[CancellationToken] = None) -> \
            Union[OptimizedRecoilsWidget, OptimizedFluenceWidget]:
        """
        Add a widget that holds progress and results of optimization.

        Args:
            elem_sim: Element simulation that is being optimized.
            cut_file_name: Measured element used in optimization.
            mode_recoil: Whether recoil result widget is shown or fluence
                result widget.
            ct: token used to indicate the stopping of
                optimization
        """
        if mode_recoil == OptimizationType.RECOIL:
            self.optimization_result_widget = OptimizedRecoilsWidget(
                elem_sim, cut_file_name, self.obj.target, ct=ct)
            self.optimization_result_widget.results_accepted.connect(
                self.simulation_target.results_accepted.emit)
        else:
            self.optimization_result_widget = OptimizedFluenceWidget(
                elem_sim, ct=ct)
        elem_sim.optimization_widget = self.optimization_result_widget
        icon = self.icon_manager.get_icon("potku_icon.ico")
        self.add_widget(self.optimization_result_widget, icon=icon)
        return self.optimization_result_widget

    def check_previous_state_files(
            self, progress: Optional[ProgressReporter] = None) -> None:
        """Check if saved state for Energy Spectra exist.
        If yes, make widgets.

        Args:
            progress: a ProgressReporter object
        """
        self.make_energy_spectra(
            spectra_changed=self.simulation_target.spectra_changed)
        # Show optimized results if there are any
        used_measured_element = ""
        for element_simulation in self.obj.element_simulations:
            if element_simulation.optimization_recoils:
                # Find file that contains measurement element name used in
                # optimization
                for file in os.listdir(element_simulation.directory):
                    if file.startswith(element_simulation.name_prefix) and \
                            file.endswith(".measured"):
                        with open(Path(element_simulation.directory, file)) \
                                as m_f:
                            used_measured_element = m_f.readline()
                        break
                self.optimization_result_widget = OptimizedRecoilsWidget(
                    element_simulation, used_measured_element, self.obj.target)
                self.optimization_result_widget.results_accepted.connect(
                    self.simulation_target.results_accepted.emit
                )
                element_simulation.optimization_widget = \
                    self.optimization_result_widget
                icon = self.icon_manager.get_icon("potku_icon.ico")
                self.add_widget(self.optimization_result_widget, icon=icon)
                break
            elif element_simulation.optimized_fluence:
                self.optimization_result_widget = OptimizedFluenceWidget(
                    element_simulation)
                element_simulation.optimization_widget = \
                    self.optimization_result_widget
                icon = self.icon_manager.get_icon("potku_icon.ico")
                self.add_widget(self.optimization_result_widget, icon=icon)
                break
        if progress is not None:
            progress.report(100)

    def make_energy_spectra(
            self, spectra_changed: Optional[pyqtSignal] = None) -> None:
        """
        Make corresponding energy spectra for each save file in simulation
        directory.
        """
        save_energy_spectrum = False
        for file in os.listdir(self.obj.directory):
            if file.endswith(".save"):
                # TODO this can be a problem if the request folder has been
                #   copied elsewhere, as the '.save' file has the old file
                #   paths saved
                file_path = Path(self.obj.directory, file)
                save_file_int = int(file.rsplit('_', 1)[1].split(".save")[0])
                with open(file_path, 'r') as save_file:
                    lines = save_file.readlines()
                if not lines:
                    return
                used_files = [Path(f) for f in lines[0].strip().split("\t") if f != '']
                used_files_confirmed = []
                for u_f in used_files:
                    if u_f.exists():
                        used_files_confirmed.append(u_f)
                if Counter(used_files) != Counter(used_files_confirmed):
                    save_energy_spectrum = True
                bin_width = float(lines[1].strip())
                icon = self.icon_manager.get_icon("energy_spectrum_icon_16.png")
                is_measured_sum_spectrum_selected, \
                is_simulated_sum_spectrum_selected = \
                    check_if_sum_in_directory_name(file_path.parent)
                energy_spectrum_widget = EnergySpectrumWidget(
                    self, "simulation",
                    use_cuts=used_files_confirmed,
                    bin_width=bin_width,
                    save_file_int=save_file_int,
                    spectra_changed=spectra_changed,
                    measured_sum_spectrum_is_selected=is_measured_sum_spectrum_selected,
                    simulated_sum_spectrum_is_selected=is_simulated_sum_spectrum_selected,
                )
                self.energy_spectrum_widgets.append(energy_spectrum_widget)
                self.add_widget(energy_spectrum_widget, icon=icon)

                if save_energy_spectrum:
                    energy_spectrum_widget.save_to_file(
                        measurement=False, update=True)

    def __open_settings(self) -> None:
        """Opens simulation settings dialog.
        """
        SimulationSettingsDialog(self, self.obj, self.icon_manager)

    def __open_optimization_dialog(self) -> None:
        OptimizationDialog(self.obj, self)

    def load_data(
            self,
            progress: Optional[ProgressReporter] = None,
            **kwargs) -> None:
        """Loads the data belonging to the Simulation into view.
        """
        if not self.data_loaded:
            self.data_loaded = True

            if progress is not None:
                sub_progress = progress.get_sub_reporter(lambda x: 0.70 * x)
            else:
                sub_progress = None

            self.add_simulation_target_and_recoil(
                progress=sub_progress, **kwargs)

            if progress is not None:
                sub_progress = progress.get_sub_reporter(
                    lambda x: 70 + 0.25 * x)

            self.check_previous_state_files(progress=sub_progress)

        if progress is not None:
            progress.report(100)

    def remove_energy_spectrum_widgets(self) -> None:
        """Removes all EnergySpectrumWidgets from this tab.
        """
        widgets = list(self.energy_spectrum_widgets)
        for widget in widgets:
            self.remove_energy_spectrum_widget(widget)

    def remove_energy_spectrum_widget(
            self, widget: EnergySpectrumWidget) -> None:
        """Removes given EnergySpectrumWidget from this tab.
        """
        self.del_widget(widget)
        self.energy_spectrum_widgets.remove(widget)
        save_file_path = Path(self.obj.directory, widget.save_file)
        try:
            save_file_path.unlink()
        except OSError:
            pass

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

