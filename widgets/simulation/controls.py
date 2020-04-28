# coding=utf-8
"""
Created on 1.3.2018
Updated on 28.1.2020

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

__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n " \
             "Sinikka Siironen \n Juhani Sundell"
__version__ = "2.0"

import threading
try:
    import rx
    RX_ON = True
except ImportError:
    import warnings
    warnings.warn("RxPy not found. RxPy is required for simulation progress "
                  "updates.")
    RX_ON = False

import widgets.binding as bnd

from pathlib import Path

from modules.element_simulation import SimulationState
from modules.element_simulation import ElementSimulation
from modules.general_functions import delete_simulation_results
from modules.concurrency import CancellationToken
from widgets.gui_utils import GUIObserver

from PyQt5 import QtWidgets
from PyQt5.QtGui import QIcon
from PyQt5 import uic
from PyQt5.QtCore import Qt


def _str_from_group_box(instance, attr):
    return getattr(instance, attr).title()


def _str_to_group_box(instance, attr, txt):
    getattr(instance, attr).setTitle(txt)


class SimulationControlsWidget(QtWidgets.QWidget, GUIObserver):
    """Class for creating simulation controls widget for the element simulation.
    """
    recoil_name = bnd.bind("controls_group_box", fget=_str_from_group_box,
                           fset=_str_to_group_box)
    process_count = bnd.bind("processes_spinbox")
    finished_processes = bnd.bind("finished_processes_label")
    observed_atoms = bnd.bind("observed_atom_count_label")
    simulation_state = bnd.bind("state_label")

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
                 recoil_dist_widget):
        """
        Initializes a SimulationControlsWidget.

        Args:
             element_simulation: An ElementSimulation class object.
             recoil_dist_widget: RecoilAtomDistributionWidget.
        """
        super().__init__()
        GUIObserver.__init__(self)
        uic.loadUi(Path("ui_files", "ui_simulation_controls.ui"), self)

        # TODO show starting seed in the UI?
        # TODO set minimum count for ions (global setting that would be checked
        #   before running simulation, user should be warned if too low)
        # TODO decouple controls from element_simulation
        self.element_simulation = element_simulation
        self.element_simulation.controls = self
        self.element_simulation.subscribe(self)
        self.recoil_dist_widget = recoil_dist_widget
        self.progress_bars = {}

        self.recoil_name = self.element_simulation.get_full_name()
        self.show_status(self.element_simulation.get_current_status())

        self.run_button.clicked.connect(self.start_simulation)
        self.run_button.setIcon(QIcon("ui_icons/reinhardt/player_play.svg"))
        self.stop_button.clicked.connect(self.stop_simulation)
        self.stop_button.setIcon(QIcon("ui_icons/reinhardt/player_stop.svg"))
        self.enable_buttons()

    def enable_buttons(self):
        """Switches the states of run and stop button depending on the state
        of the ElementSimulation object.
        """
        # TODO make sure that this works when first started
        start_enabled = not self.element_simulation.is_simulation_running()
        stop_enabled = not (start_enabled or
                            self.element_simulation.is_optimization_running())
        self.run_button.setEnabled(start_enabled)
        self.stop_button.setEnabled(stop_enabled)
        self.processes_spinbox.setEnabled(start_enabled)

    def start_simulation(self):
        """ Calls ElementSimulation's start method.
        """
        # Ask the user if they want to write old simulation results over (if
        # they exist), or continue
        status = self.element_simulation.get_current_status()

        if status["state"] == SimulationState.DONE:
            reply = QtWidgets.QMessageBox.question(
                self, "Confirmation", "Do you want to continue this "
                                      "simulation?\n\nIf you do, old simulation"
                                      " results will be preserved.\nOtherwise "
                                      "they will be deleted.",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No |
                QtWidgets.QMessageBox.Cancel, QtWidgets.QMessageBox.Cancel)
            if reply == QtWidgets.QMessageBox.Cancel:
                return  # If clicked Cancel don't start simulation
            elif reply == QtWidgets.QMessageBox.No:
                # Delete old simulation results
                for recoil in self.element_simulation.recoil_elements:
                    delete_simulation_results(self.element_simulation, recoil)

                use_old_erd_files = False
            else:
                use_old_erd_files = True
        elif status["state"] == SimulationState.NOTRUN:
            use_old_erd_files = False
        else:
            # TODO we should handle these kinds of situation more gracefully
            #      but for now just raise an explicit error so that the
            #      programmer notices that something went wrong
            raise ValueError("Simulation state should either be {0} or {1} "
                             "before running a simulation. Current state was "
                             "{2}".format("DONE", "NOTRUN",
                                          str(status["state"])))

        # Lock full edit
        self.element_simulation.lock_edit()
        if self.recoil_dist_widget.current_element_simulation is \
           self.element_simulation:
            self.recoil_dist_widget.full_edit_on = False
            self.recoil_dist_widget.update_plot()

        # TODO indicate to user that ion counts are shared between processes

        number_of_processes = self.process_count

        starter_thread = threading.Thread(
            target=lambda: self.element_simulation.start(
                number_of_processes,
                use_old_erd_files=use_old_erd_files,
                shared_ions=True,
                cancellation_token=CancellationToken(),
                observer=self
            ))
        starter_thread.start()

    def show_status(self, status):
        """Updates the status of simulation in the GUI

        Args:
            status: status of the ElementSimulation object
        """
        self.show_atom_count(status["atom_count"])
        self.show_finished_processes(
            status["running"],
            starting=status["state"] == SimulationState.STARTING)
        self.show_state(status["state"])

    def show_atom_count(self, atom_count):
        """Updates the atom count in the GUI

        Args:
            atom_count: number of atoms counted
        """
        self.observed_atoms = atom_count

    def show_finished_processes(self, running_processes, starting=False):
        """Update the number of finished processes.

        Args:
            running_processes: Number of running processes.
            starting: boolean that determines if the processes are just
                      starting
        """
        all_proc = self.process_count
        if starting:
            # This is a small fix to show correct number of finished
            # processes at the start when process count is still 0
            finished = 0
        else:
            # Otherwise we can just use the actual number of processes
            # to determine the number of finished processes
            finished = all_proc - running_processes

        self.finished_processes = f"{finished}/{all_proc}"

    def show_state(self, state):
        """Update simulation state in the GUI

        Args:
            state: SimulationState enum
        """
        self.simulation_state = state

    def show_ions_per_process(self, process_count):
        # TODO this method is supposed to show how the ion counts are divided
        #      per process. ATM cannot update ion counts immeadiately after
        #      settings change, so this function is only printing the values
        #      to console
        # TODO either bind the value of ions to some variable or only show
        #      this when the simulation starts
        settings, _, _ = self.element_simulation.get_mcerd_params()
        try:
            preions = settings["number_of_ions_in_presimu"] // process_count
            ions = settings["number_of_ions"] // process_count
            print("Number of ions per process (pre/full):",
                  preions, ions)
        except ZeroDivisionError:
            # User set the value of the spinbox to 0, lets
            # not divide with it
            pass

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

        if "msg" in status:
            if status["msg"] == "Presimulation finished":
                self.update_progress_bars(
                    status["seed"], 0,
                    stylesheet=SimulationControlsWidget.SIM_PROGRESS_STYLE)
        elif "calculated" in status:
            self.update_progress_bars(
                status["seed"], status["calculated"] / status["total"] * 100)
        else:
            if status["state"] == SimulationState.STARTING:
                self.remove_progress_bars()
                self.enable_buttons()
            self.show_status(status)

    def on_error_handler(self, err):
        # For now just print any errors that the stream may thow at us
        print(err)

    def on_complete_handler(self, status):
        """This method is called when the ElementSimulation has run all of
        its simulation processes.

        GUI is updated to show the status and button states are switched
        accordingly.
        """
        self.show_status(status)
        self.enable_buttons()

    def on_completed(self, status):
        # rx requires the observer to have a method called on_completed
        # Currently this is not getting called
        # TODO rename the base method in modules.observing.Observer
        print(status)

    def remove_progress_bars(self):
        """Removes all progress bars and seed labels.
        """
        self.progress_bars = {}
        for i in reversed(range(self.process_layout.count())):
            self.process_layout.itemAt(i).widget().deleteLater()

    def update_progress_bars(self, seed, value, stylesheet=None):
        """Updates or adds a progress bar.
        """
        if seed not in self.progress_bars:
            if stylesheet is None:
                stylesheet = SimulationControlsWidget.PRESIM_PROGRESS_STYLE
            progress_bar = QtWidgets.QProgressBar()
            progress_bar.setStyleSheet(stylesheet)
            progress_bar.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.progress_bars[seed] = progress_bar
            self.process_layout.addRow(QtWidgets.QLabel(str(seed)),
                                       progress_bar)
        else:
            progress_bar = self.progress_bars[seed]
            if stylesheet is not None:
                progress_bar.setStyleSheet(stylesheet)
        progress_bar.setValue(value)
