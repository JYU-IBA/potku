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

import os
import abc

# TODO there is some circular dependency that prevents importing SimulationState
#      FIX THIS!
# from modules.element_simulation import SimulationState
from modules.general_functions import delete_simulation_results
from modules.observing import Observer

from PyQt5 import QtWidgets
from PyQt5.QtGui import QIcon


class QtObserverMeta(type(QtWidgets.QWidget), type(Observer)):
    """A common metaclass for Observers and QWidgets.

     QWidget has the metaclass 'sip.wrappertype' while Observer has
     'ABCMeta', which causes a conflict in multi-inheritance.

    QtObserverMeta provides a common metaclass for both types so a GUI element
    can inherit both QWidget and Observer classes.
    """
    # TODO create a GUI utils module and move this there
    pass


class SimulationControlsWidget(Observer, QtWidgets.QWidget,
                               metaclass=QtObserverMeta):
    """Class for creating simulation controls widget for the element simulation.
    """

    def __init__(self, element_simulation, recoil_dist_widget):
        """
        Initializes a SimulationControlsWidget.

        Args:
             element_simulation: An ElementSimulation class object.
             recoil_dist_widget: RecoilAtomDistributionWidget.
        """
        super().__init__()

        self.element_simulation = element_simulation

        # TODO decouple controls from element_simulation
        self.element_simulation.controls = self
        self.element_simulation.subscribe(self)
        self.recoil_dist_widget = recoil_dist_widget

        main_layout = QtWidgets.QHBoxLayout()
        recoil_element = self.element_simulation.recoil_elements[
            0]
        self.controls_group_box = QtWidgets.QGroupBox(
            recoil_element.prefix + "-" + recoil_element.name)
        self.controls_group_box.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                              QtWidgets.QSizePolicy.Preferred)

        state_layout = QtWidgets.QHBoxLayout()
        state_layout.setContentsMargins(0, 6, 0, 0)

        # TODO update these by querying from the elem sim
        state_layout.addWidget(QtWidgets.QLabel("State: "))
        self.state_label = QtWidgets.QLabel("Not started")
        state_layout.addWidget(self.state_label)
        state_widget = QtWidgets.QWidget()
        state_widget.setLayout(state_layout)

        # TODO get atom count from element simulation and display it
        # TODO update status label properly when simulation begins
        # TODO show starting seed in the UI?
        # TODO set minimum count for ions
        # TODO bind object values to PyQT elements
        status = self.element_simulation.get_current_status()
        print(status)

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

        self.finished_processes_widget.hide()

        self.controls_group_box.setLayout(state_and_controls_layout)

        main_layout.addWidget(self.controls_group_box)

        self.setLayout(main_layout)

    def reset_controls(self):
        """
        Reset controls to default.
        """
        self.finished_processes_widget.hide()
        self.observed_atom_count_label.setText("0")
        self.processes_spinbox.setEnabled(True)
        self.state_label.setText("Not started")

    def find_old_biggest_seed(self):
        """
        From possible old erd files, find biggest seed number.

        Return:
             Biggest seed for simulation.
        """
        # TODO make this a function of elem_sim
        # TODO this should be two functions (find_files &
        #      find_biggest_seed)
        old_files = []
        biggest_seed = 0

        start_part = self.element_simulation.recoil_elements[0].prefix + \
            "-" + self.element_simulation.recoil_elements[0].name + "."
        end = ".erd"

        for file in os.listdir(self.element_simulation.directory):
            if file.startswith(start_part) and file.endswith(end):
                seed = file.rsplit('.', 2)[1]
                old_files.append(os.path.join(
                    self.element_simulation.directory, file))
                try:
                    current_seed = int(seed)
                    if current_seed > biggest_seed:
                        biggest_seed = current_seed
                except ValueError:
                    continue
        if biggest_seed > 0:    # TODO seed cannot be 0?
            return biggest_seed, old_files
        return None, old_files

    def __start_simulation(self):
        """ Calls ElementSimulation's start method.
        """
        # Ask the user if they want to write old simulation results over (if
        # they exist), or continue
        start_value = None
        old_biggest_seed, erd_files = self.find_old_biggest_seed()
        use_erd_files = False
        if old_biggest_seed:    # TODO what if seed is 0? should check for None?
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
            if reply == QtWidgets.QMessageBox.No:
                # Delete old simulation results
                for recoil in self.element_simulation.recoil_elements:
                    delete_simulation_results(self.element_simulation, recoil)
            else:
                start_value = old_biggest_seed + 1
                use_erd_files = True

        number_of_processes = self.processes_spinbox.value()
        self.state_label.setText("Running")
        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.observed_atom_count_label.setText("0 (pre sim)")

        self.finished_processes_label.setText("0/" + str(number_of_processes))
        self.finished_processes_widget.show()
        self.processes_spinbox.setEnabled(False)

        # Lock full edit
        self.element_simulation.lock_edit()
        if self.recoil_dist_widget.current_element_simulation is \
           self.element_simulation:
            self.recoil_dist_widget.full_edit_on = False
            self.recoil_dist_widget.edit_lock_push_button.setText(
                "Unlock full edit")
            self.recoil_dist_widget.update_plot()
        self.element_simulation.y_min = 0.0001

        # TODO show wait cursor
        # TODO await start
        # TODO change cursor back to normal

        if use_erd_files:
            # TODO indicate to user that ion sharing is in use
            self.element_simulation.start(number_of_processes,
                                          start_value,
                                          erd_files,
                                          shared_ions=True)
        else:
            self.element_simulation.start(number_of_processes,
                                          start_value,
                                          shared_ions=True)

    def show_status(self, status):
        """Updates the status of simulation in the GUI

        Args:
            status: status of the ElementSimulation object
        """
        self.show_atom_count(status["atom_count"])
        self.show_finished_processes(status["running"])
        self.show_state(status["state"])

    def show_atom_count(self, atom_count):
        """Updates the atom count in the GUI

        Args:
            atom_count: number of atoms counted
        """
        try:
            self.observed_atom_count_label.setText(str(atom_count))
        except RuntimeError:
            pass

    def show_finished_processes(self, running_processes):
        """Update the number of finished processes.

        Args:
            running_processes: Number of running processes.
        """
        all_proc = self.processes_spinbox.value()
        finished = all_proc - running_processes

        self.finished_processes_label.setText("{0}/{1}".format(finished,
                                                               all_proc))

    def show_state(self, state):
        """Update simulation state in the GUI

        Args:
            state: SimulationState enum
        """
        self.state_label.setText(str(state).split(".")[-1])

        # TODO there is some circular dependecy which prevents this module from
        #      importing the SimulationState Enum from element_simulation.py
        #      This should be fixed.
        # In the meantime, use a hacky solution and convert the enum to string
        if str(state) == "SimulationState.Finished":
            self.run_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.processes_spinbox.setEnabled(True)

    def show_ions_per_process(self, process_count):
        # TODO this method is supposed to show how the ion counts are divided
        #      per process. ATM cannot update ion counts immeadiately after
        #      settings change, so this function is only printing the values
        #      to console
        # TODO either bind the value of ions to some variable or only show
        #      this when the simulation starts
        elem_sim = self.element_simulation.get_element_simulation()
        preions = elem_sim.number_of_preions // process_count
        ions = elem_sim.number_of_ions // process_count
        print("Number of ions per process (pre/full):",
              preions,
              ions)

    def stop_simulation(self):
        """ Calls ElementSimulation's stop method.
        """
        # TODO this is crashing currently
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
        self.show_stop()
        self.state_label.setText("Stopped")

    def receive(self, status):
        """Callback function that receives status from an
        ElementSimulation

        Args:
            status: status update sent by ElementSimulation
        """
        self.show_status(status)
