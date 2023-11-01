# coding=utf-8
"""
Created on 1.3.2018
Updated on 28.1.2020

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2018 Severi Jääskeläinen, Samuel Kaiponen, Heta Rekilä and
Sinikka Siironen, 2020 Juhani Sundell

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

__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n " \
             "Sinikka Siironen \n Juhani Sundell"
__version__ = "2.0"

import widgets.binding as bnd
import widgets.gui_utils as gutils
import widgets.icon_manager as icons

from typing import Optional
from reactivex import operators as ops

from modules.element_simulation import SimulationState
from modules.element_simulation import ElementSimulation
from modules.mcerd import MCERD
from modules.global_settings import GlobalSettings
from modules.enums import IonDivision
from widgets.gui_utils import GUIObserver
from modules.enums import SimulationType

from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5 import uic
from PyQt5.QtCore import Qt


def _process_count_to_label(instance, attr, value):
    """Sets the value of finished process count in GUI.
    """
    getattr(instance, attr).setText(f"{value[0]}/{value[1]}")


def _process_count_from_label(instance, attr):
    """Gets the value of finished process count from GUI.
    """
    fin, all_proc = getattr(instance, attr).text().split("/")
    return int(fin), int(all_proc)


class SimulationControlsWidget(QtWidgets.QWidget, GUIObserver):
    """Class for creating simulation controls widget for the element simulation.
    """
    recoil_name = bnd.bind("controls_group_box")
    process_count = bnd.bind("processes_spinbox")
    finished_processes = bnd.bind(
        "finished_processes_label", fget=_process_count_from_label,
        fset=_process_count_to_label)
    observed_atoms = bnd.bind("observed_atom_count_label")
    simulation_state = bnd.bind("state_label")
    mcerd_error = bnd.bind("mcerd_error_lbl")
    ion_settings_error = bnd.bind("ion_settings_label")

    # TODO these styles could use some brush up...
    PRESIM_PROGRESS_STYLE = """
        QProgressBar::chunk:horizontal {
            background: #b8112a;
        }
    """
    SIM_PROGRESS_STYLE = """
        QProgressBar::chunk:horizontal {
            background: #0ec95c;
        }
    """

    def __init__(self, element_simulation: ElementSimulation,
                 recoil_dist_widget, recoil_name_changed=None,
                 settings_updated=None, ion_division=IonDivision.BOTH,
                 min_presim_ions=0, min_sim_ions=0):
        """
        Initializes a SimulationControlsWidget.

        Args:
             element_simulation: An ElementSimulation class object.
             recoil_dist_widget: RecoilAtomDistributionWidget.
             recoil_name_changed: signal that indicates that a recoil name
                has changed.
            ion_division: ion division mode
        """
        super().__init__()
        GUIObserver.__init__(self)
        uic.loadUi(gutils.get_ui_dir() / "ui_simulation_controls.ui", self)

        self.element_simulation = element_simulation
        self.element_simulation.subscribe(self)
        self.recoil_dist_widget = recoil_dist_widget
        self.progress_bars = {}

        main_recoil = self.element_simulation.get_main_recoil()
        if main_recoil.type == SimulationType.ERD:
            self.recoil_name = main_recoil.get_full_name()
        else:
            self.recoil_name = main_recoil.get_full_name() + "    Scatter"

        self.show_status(self.element_simulation.get_current_status())
        self.finished_processes = 0, self.process_count

        self.run_button.clicked.connect(self.start_simulation)
        self.run_button.setIcon(icons.get_reinhardt_icon("player_play.svg"))
        self.stop_button.clicked.connect(self.stop_simulation)
        self.stop_button.setIcon(icons.get_reinhardt_icon("player_stop.svg"))
        self.enable_buttons()

        self.mcerd_error_lbl.hide()
        self.ion_settings_label.hide()

        self.__unsub = None

        self._ion_division = ion_division
        self._min_presim_ions = min_presim_ions
        self._min_sim_ions = min_sim_ions
        self.show_ion_settings_label()

        self.processes_spinbox.valueChanged.connect(
            self.show_ion_settings_label)
        self._recoil_name_changed = recoil_name_changed
        if self._recoil_name_changed is not None:
            self._recoil_name_changed.connect(self._set_name)

        self._settings_updated = settings_updated
        if self._settings_updated is not None:
            self._settings_updated.connect(self.settings_update_handler)
            self._settings_updated[GlobalSettings].connect(
                self.settings_update_handler)

    def closeEvent(self, event):
        """Disconnects self from recoil_name_changed signal and closes the
        widget.
        """
        # FIXME not being called. This is a problem as there may be memory
        #  leaks.
        try:
            self._recoil_name_changed.disconnect(self._set_name)
        except (AttributeError, TypeError):
            pass
        try:
            self.settings_updated.disconnect(self.settings_update_handler)
        except (AttributeError, TypeError):
            pass
        super().closeEvent(event)

    def _set_name(self, _, recoil_elem):
        """Sets the name shown in group box title to the name of the
        given recoil element if the recoil element is the same as the
        main recoil.
        """
        if recoil_elem is self.element_simulation.get_main_recoil():
            if recoil_elem.type == SimulationType.ERD:
                self.recoil_name = recoil_elem.get_full_name()
            else:
                self.recoil_name = recoil_elem.get_full_name() + "    Scatter"

    def enable_buttons(self, starting=False):
        """Switches the states of run and stop button depending on the state
        of the ElementSimulation object.
        """
        if self.element_simulation.is_optimization_running():
            start_enabled, stop_enabled = False, False
        else:
            start_enabled = not (self.element_simulation.is_simulation_running()
                                 and starting)
            stop_enabled = not (
                start_enabled or
                self.element_simulation.is_optimization_running())
        self.run_button.setEnabled(start_enabled)
        self.stop_button.setEnabled(stop_enabled)
        self.processes_spinbox.setEnabled(start_enabled)

    def start_simulation(self):
        """Calls ElementSimulation's start method.
        """
        # Ask the user if they want to write old simulation results over (if
        # they exist), or continue
        status = self.element_simulation.get_current_status()

        if status[ElementSimulation.STATE] == SimulationState.DONE:
            reply = QtWidgets.QMessageBox.question(
                self, "Confirmation",
                "Do you want to continue this simulation?\n\n"
                "If you do, old simulation results will be preserved.\n"
                "Otherwise they will be deleted.",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No |
                QtWidgets.QMessageBox.Cancel, QtWidgets.QMessageBox.Cancel)
            if reply == QtWidgets.QMessageBox.Cancel:
                return  # If clicked Cancel don't start simulation
            elif reply == QtWidgets.QMessageBox.No:
                use_old_erd_files = False
            else:
                use_old_erd_files = True
        elif status[ElementSimulation.STATE] == SimulationState.NOTRUN:
            use_old_erd_files = False
        else:
            self.mcerd_error = "Simulation currently running. Cannot start a " \
                               "new one."
            self.mcerd_error_lbl.show()
            return

        self.mcerd_error_lbl.hide()

        # Lock full edit
        self.element_simulation.lock_edit()
        if self.recoil_dist_widget.current_element_simulation is \
           self.element_simulation:
            self.recoil_dist_widget.full_edit_on = False
            self.recoil_dist_widget.update_plot()

        self.finished_processes = 0, self.process_count
        self.remove_progress_bars()

        observable = self.element_simulation.start(
            self.process_count, use_old_erd_files=use_old_erd_files,
            ion_division=self._ion_division
        )
        if observable is not None:
            self.__unsub = observable.pipe(
                ops.scan(lambda acc, x: {
                    **x,
                    "started":  x[MCERD.IS_RUNNING] and not acc["started"]
                }, seed={"started": False})
            ).subscribe(self)
        else:
            self.mcerd_error = "Could not start simulation. Check that there " \
                               "is no other simulation running for this " \
                               "recoil element"
            self.mcerd_error_lbl.show()

    def show_status(self, status):
        """Updates the status of simulation in the GUI

        Args:
            status: status of the ElementSimulation object
        """
        self.observed_atoms = status[ElementSimulation.ATOMS]
        self.simulation_state = status[ElementSimulation.STATE]

    def settings_update_handler(
            self, settings: Optional[GlobalSettings] = None):
        """Updates SimulationControlsWidget when a setting has been updated.
        """
        if settings is not None:
            self._ion_division = settings.get_ion_division()
            self._min_presim_ions = settings.get_min_presim_ions()
            self._min_sim_ions = settings.get_min_simulation_ions()
        self.show_ion_settings_label()

    def show_ion_settings_label(self):
        """Shows a warning label if ion counts are below the user defined
        treshold.
        """
        settings, _, _ = self.element_simulation.get_mcerd_params()
        presim_ions, sim_ions = self._ion_division.get_ion_counts(
            settings["number_of_ions_in_presimu"], settings["number_of_ions"],
            self.process_count
        )
        txt = ""
        if self._min_presim_ions > presim_ions:
            txt += "Not enough pre-simulation ions. "
        if self._min_sim_ions > sim_ions:
            txt += "Not enough simulation ions."
        if txt:
            self.ion_settings_error = txt
            self.ion_settings_label.show()
        else:
            self.ion_settings_label.hide()

    def stop_simulation(self):
        """ Calls ElementSimulation's stop method.
        """
        self.element_simulation.stop()

    def on_next_handler(self, status):
        """Callback function that receives status from an
        ElementSimulation

        Args:
            status: status update sent by ElementSimulation or observable stream
        """
        if status[MCERD.MSG] == MCERD.PRESIM_FINISHED:
            style = SimulationControlsWidget.SIM_PROGRESS_STYLE
        else:
            style = None
        self.update_progress_bar(
            status[MCERD.SEED], status[MCERD.PERCENTAGE], stylesheet=style)

        self.finished_processes = (
            status[ElementSimulation.FINISHED], status[ElementSimulation.TOTAL])

        if status["started"]:
            self.enable_buttons(starting=True)

        self.show_status(status)

    def on_error_handler(self, err):
        """Called when observable (either ElementSimulation or the rx stream
        reports an error.
        """
        self.mcerd_error = err
        self.mcerd_error_lbl.show()

        self.enable_buttons()
        self.show_status(self.element_simulation.get_current_status())
        if self.__unsub is not None:
            self.__unsub.dispose()

    @QtCore.pyqtSlot()
    @QtCore.pyqtSlot(object)
    def on_completed_handler(self, status=None):
        """This method is called when the ElementSimulation has run all of
        its simulation processes.

        GUI is updated to show the status and button states are switched
        accordingly.
        """
        if status is None:
            self.show_status(self.element_simulation.get_current_status())
            if self.__unsub is not None:
                self.__unsub.dispose()
        else:
            self.show_status(status)
        for process_bar in self.progress_bars.values():
            # TODO this only affects the number, adjust the color too
            process_bar.setEnabled(False)
        self.enable_buttons()

    def remove_progress_bars(self):
        """Removes all progress bars and seed labels.
        """
        self.progress_bars = {}
        for i in reversed(range(self.process_layout.count())):
            self.process_layout.itemAt(i).widget().deleteLater()

    def update_progress_bar(self, seed: int, value: int, stylesheet=None):
        """Updates or adds a progress bar for a simulation process that uses
        the given seed.

        Args:
            seed: seed of the simulation process
            value: value to be shown in the progress bar.
            stylesheet: stylesheet given to to the progress bar.
        """
        if seed not in self.progress_bars:
            if stylesheet is None:
                stylesheet = SimulationControlsWidget.PRESIM_PROGRESS_STYLE
            progress_bar = QtWidgets.QProgressBar()
            progress_bar.setStyleSheet(stylesheet)

            # Align the percentage display to the right side of the
            # progress bar.
            progress_bar.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

            # Make sure it fills the horizontal space by setting size policy
            # to expanding.
            progress_bar.setSizePolicy(
                QtWidgets.QSizePolicy.Expanding,
                QtWidgets.QSizePolicy.Fixed)

            self.progress_bars[seed] = progress_bar
            self.process_layout.addRow(
                QtWidgets.QLabel(str(seed)), progress_bar)
        else:
            progress_bar = self.progress_bars[seed]
            if stylesheet is not None:
                progress_bar.setStyleSheet(stylesheet)
        progress_bar.setValue(value)
