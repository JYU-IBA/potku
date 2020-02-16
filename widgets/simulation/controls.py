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

from modules.element_simulation import SimulationState
from modules.general_functions import delete_simulation_results
from modules.observing import Observer
from modules.concurrency import CancellationToken

from PyQt5 import QtWidgets
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSignal


class SimulationControlsWidget(Observer, QtWidgets.QWidget):
    """Class for creating simulation controls widget for the element simulation.
    """
    # PyQt signal that is used to invoke the GUI thread to
    # update simulation status
    state_changed = pyqtSignal(dict)

    def __init__(self, element_simulation, recoil_dist_widget):
        """
        Initializes a SimulationControlsWidget.

        Args:
             element_simulation: An ElementSimulation class object.
             recoil_dist_widget: RecoilAtomDistributionWidget.
        """
        super().__init__()

        self.element_simulation = element_simulation

        # TODO show starting seed in the UI?
        # TODO set minimum count for ions
        # TODO bind object values to PyQT elements
        # TODO decouple controls from element_simulation
        self.element_simulation.controls = self
        self.element_simulation.subscribe(self)
        self.recoil_dist_widget = recoil_dist_widget

        main_layout = QtWidgets.QHBoxLayout()
        recoil_element = self.element_simulation.recoil_elements[0]
        self.controls_group_box = QtWidgets.QGroupBox(
            recoil_element.prefix + "-" + recoil_element.name)
        self.controls_group_box.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                              QtWidgets.QSizePolicy.Preferred)

        state_layout = QtWidgets.QHBoxLayout()
        state_layout.setContentsMargins(0, 6, 0, 0)

        state_layout.addWidget(QtWidgets.QLabel("State: "))
        self.state_label = QtWidgets.QLabel("Not started")
        state_layout.addWidget(self.state_label)
        state_widget = QtWidgets.QWidget()
        state_widget.setLayout(state_layout)

        # Button that starts the simulation
        controls_layout = QtWidgets.QHBoxLayout()
        controls_layout.setContentsMargins(0, 6, 0, 0)
        self.run_button = QtWidgets.QPushButton()
        self.run_button.setIcon(QIcon("ui_icons/reinhardt/player_play.svg"))
        self.run_button.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                                      QtWidgets.QSizePolicy.Fixed)
        self.run_button.setToolTip("Start simulation")
        self.run_button.clicked.connect(self.__start_simulation)

        # Button that stops the simulation
        self.stop_button = QtWidgets.QPushButton()
        self.stop_button.setIcon(QIcon("ui_icons/reinhardt/player_stop.svg"))
        self.stop_button.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                                       QtWidgets.QSizePolicy.Fixed)
        self.stop_button.setToolTip("Stop simulation")
        self.stop_button.clicked.connect(self.stop_simulation)
        self.stop_button.setEnabled(False)

        controls_layout.addWidget(self.run_button)
        controls_layout.addWidget(self.stop_button)
        controls_widget = QtWidgets.QWidget()
        controls_widget.setLayout(controls_layout)

        # Spinbox to choose how many simulations processes are started
        # concurrently
        processes_layout = QtWidgets.QFormLayout()
        processes_layout.setContentsMargins(0, 6, 0, 0)
        processes_label = QtWidgets.QLabel("Processes: ")
        self.processes_spinbox = QtWidgets.QSpinBox()
        self.processes_spinbox.setValue(1)
        self.processes_spinbox.setMinimum(1)
        self.processes_spinbox.setToolTip(
            "Number of processes used in simulation")
        self.processes_spinbox.setFixedWidth(50)
        self.processes_spinbox.valueChanged.connect(self.show_ions_per_process)
        processes_layout.addRow(processes_label, self.processes_spinbox)
        processes_widget = QtWidgets.QWidget()
        processes_widget.setLayout(processes_layout)
        self.show_ions_per_process(self.processes_spinbox.value())

        # Show finished processes
        self.finished_processes_widget = QtWidgets.QWidget()
        r_p_layout = QtWidgets.QFormLayout()
        r_p_layout.setContentsMargins(0, 6, 0, 0)
        l_1 = QtWidgets.QLabel("Finished processes: ")
        self.finished_processes_label = QtWidgets.QLabel("0/1")

        # Observed atom count
        l_2 = QtWidgets.QLabel("Observed atoms: ")
        self.observed_atom_count_label = QtWidgets.QLabel("0")
        r_p_layout.addRow(l_1, self.finished_processes_label)
        r_p_layout.addRow(l_2, self.observed_atom_count_label)
        self.finished_processes_widget.setLayout(r_p_layout)

        state_and_controls_layout = QtWidgets.QVBoxLayout()
        state_and_controls_layout.setContentsMargins(6, 6, 6, 6)
        state_and_controls_layout.addWidget(processes_widget)
        state_and_controls_layout.addWidget(self.finished_processes_widget)
        state_and_controls_layout.addWidget(state_widget)
        state_and_controls_layout.addWidget(controls_widget)

        self.controls_group_box.setLayout(state_and_controls_layout)

        main_layout.addWidget(self.controls_group_box)

        self.setLayout(main_layout)

        self.state_changed.connect(
            lambda s: self.state_change_handler(s))

        # Update element sims status in the GUI
        # TODO state label shows 'Done' if there is an empty ERD file/s with
        #      name corresponding to the element simulation. This is slightly
        #      confusing to the user even if it is not an error per se
        status = self.element_simulation.get_current_status()
        self.show_status(status)

        # Set the process label to a default value as it  makes no sense to
        # show finished processes as '1/1' when the control is first loaded
        self.finished_processes_label.setText(
            f"0/{self.processes_spinbox.value()}")

    def reset_controls(self):
        """
        Reset controls to default.
        """
        # TODO when controls are reset, element_simulation's collection of
        #      ERD file paths is not cleared which means that the status will
        #      show 'DONE' even if the actual files have been removed. This
        #      would be trivial to fix by hard coding the status in here, but
        #      we might want to look for a nicer solution first.
        self.state_changed.emit(
            self.element_simulation.get_current_status())

    def __start_simulation(self):
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
                                                   QtWidgets.QMessageBox.Yes |
                                                   QtWidgets.QMessageBox.No |
                                                   QtWidgets.QMessageBox.Cancel,
                                                   QtWidgets.QMessageBox.Cancel)
            if reply == QtWidgets.QMessageBox.Cancel:
                return  # If clicked Cancel don't start simulation
            elif reply == QtWidgets.QMessageBox.No:
                # Delete old simulation results
                for recoil in self.element_simulation.recoil_elements:
                    delete_simulation_results(self.element_simulation, recoil)

                # This is the seed value set in the request settings
                start_value = self.element_simulation.seed_number
                use_old_erd_files = False
            else:
                # These are the old files. Seed is set to 'last seed' + 1
                start_value = self.element_simulation.get_max_seed() + 1
                use_old_erd_files = True
        elif status["state"] == SimulationState.NOTRUN:
            start_value = self.element_simulation.seed_number
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
            self.recoil_dist_widget.edit_lock_push_button.setText(
                "Unlock full edit")
            self.recoil_dist_widget.update_plot()
        self.element_simulation.y_min = 0.0001

        # TODO indicate to user that ion counts are shared between processes

        number_of_processes = self.processes_spinbox.value()

        starter_thread = threading.Thread(
            target=lambda: self.element_simulation.start(
                number_of_processes, start_value,
                use_old_erd_files=use_old_erd_files,
                shared_ions=True,
                cancellation_token=CancellationToken()))
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
        self.observed_atom_count_label.setText(str(atom_count))

    def show_finished_processes(self, running_processes, starting=False):
        """Update the number of finished processes.

        Args:
            running_processes: Number of running processes.
            starting: boolean that determines if the processes are just
                      starting
        """
        all_proc = self.processes_spinbox.value()
        if starting:
            # This is a small fix to show correct number of finished
            # processes at the start when process count is still 0
            finished = 0
        else:
            # Otherwise we can just use the actual number of processes
            # to determine the number of finished processes
            finished = all_proc - running_processes

        self.finished_processes_label.setText(f"{finished}/{all_proc}")

    def show_state(self, state):
        """Update simulation state in the GUI

        Args:
            state: SimulationState enum
        """
        self.state_label.setText(str(state))

    def show_ions_per_process(self, process_count):
        # TODO this method is supposed to show how the ion counts are divided
        #      per process. ATM cannot update ion counts immeadiately after
        #      settings change, so this function is only printing the values
        #      to console
        # TODO either bind the value of ions to some variable or only show
        #      this when the simulation starts
        elem_sim = self.element_simulation.get_element_simulation()
        try:
            preions = elem_sim.number_of_preions // process_count
            ions = elem_sim.number_of_ions // process_count
            print("Number of ions per process (pre/full):",
                  preions, ions)
        except ZeroDivisionError:
            # User set the value of the spinbox to 0, lets
            # not divide with it
            pass

    def stop_simulation(self):
        """ Calls ElementSimulation's stop method.
        """
        try:
            self.element_simulation.stop()
        except FileNotFoundError:
            # Either .erd or .recoil files were not found for generating
            # energy spectrum.
            error_box = QtWidgets.QMessageBox()
            error_box.setIcon(QtWidgets.QMessageBox.Warning)
            error_box.addButton(QtWidgets.QMessageBox.Ok)
            error_box.setText("Energy spectrum data could not be generated.")
            error_box.setWindowTitle("Error")
            error_box.exec()

    def on_next(self, status):
        """Callback function that receives status from an
        ElementSimulation

        Args:
            status: status update sent by ElementSimulation
        """
        # Uncomment next line to see status updates in the console
        # print(status)
        self.state_changed.emit(status)

    def on_error(self, err):
        """Function that the ElementSimulation object invokes when it
        encounters an error.

        Currently ElementSimulation object does not invoke this function
        so NotImplementedError is raised.
        """
        raise NotImplementedError

    def on_complete(self, status):
        """This method is called when the ElementSimulation has run all of
        its simulation processes.

        GUI is updated to show the status and button states are switched
        accordingly.
        """
        self.state_changed.emit(status)

    def state_change_handler(self, status):
        """Handles status changes emitted by signals.

        Args:
            status: dictionary containing status information
                    about ElementSimulation object
        """
        self.show_status(status)

        # TODO button states are not updating immediately
        #      after starting multiple processes
        if status["state"] == SimulationState.STARTING:
            self.run_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.processes_spinbox.setEnabled(False)

        elif status["state"] == SimulationState.DONE:
            self.run_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.processes_spinbox.setEnabled(True)
