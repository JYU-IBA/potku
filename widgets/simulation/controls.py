# coding=utf-8
"""
Created on 1.3.2018
Updated on 3.8.2018

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
             "Sinikka Siironen"
__version__ = "2.0"

from PyQt5 import QtWidgets
from PyQt5.QtGui import QIcon


class SimulationControlsWidget(QtWidgets.QWidget):
    """Class for creating simulation controls widget for the element simulation.

    Args:
        element_simulation: ElementSimulation object.
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
        self.element_simulation.controls = self
        self.recoil_dist_widget = recoil_dist_widget

        main_layout = QtWidgets.QHBoxLayout()
        recoil_element = self.element_simulation.recoil_elements[
            0]
        controls_group_box = QtWidgets.QGroupBox(recoil_element.prefix + "-"
                                                 + recoil_element.name)
        controls_group_box.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                         QtWidgets.QSizePolicy.Preferred)

        state_layout = QtWidgets.QHBoxLayout()
        state_layout.setContentsMargins(0, 6, 0, 0)
        state_layout.addWidget(QtWidgets.QLabel("State: "))
        self.state_label = QtWidgets.QLabel("Not started")
        state_layout.addWidget(self.state_label)
        state_widget = QtWidgets.QWidget()
        state_widget.setLayout(state_layout)

        controls_layout = QtWidgets.QHBoxLayout()
        controls_layout.setContentsMargins(0, 6, 0, 0)
        self.run_button = QtWidgets.QPushButton()
        self.run_button.setIcon(QIcon("ui_icons/reinhardt/player_play.svg"))
        self.run_button.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                                 QtWidgets.QSizePolicy.Fixed)
        self.run_button.setToolTip("Start simulation")
        self.run_button.clicked.connect(self.__start_simulation)

        self.stop_button = QtWidgets.QPushButton()
        self.stop_button.setIcon(QIcon("ui_icons/reinhardt/player_stop.svg"))
        self.stop_button.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                                  QtWidgets.QSizePolicy.Fixed)
        self.stop_button.setToolTip("Stop simulation")
        self.stop_button.clicked.connect(self.__stop_simulation)
        self.stop_button.setEnabled(False)

        controls_layout.addWidget(self.run_button)
        controls_layout.addWidget(self.stop_button)
        controls_widget = QtWidgets.QWidget()
        controls_widget.setLayout(controls_layout)

        processes_layout = QtWidgets.QFormLayout()
        processes_layout.setContentsMargins(0, 6, 0, 0)
        processes_label = QtWidgets.QLabel("Processes: ")
        self.processes_spinbox = QtWidgets.QSpinBox()
        self.processes_spinbox.setValue(1)
        self.processes_spinbox.setToolTip(
            "Number of processes used in simulation")
        self.processes_spinbox.setFixedWidth(50)
        processes_layout.addRow(processes_label, self.processes_spinbox)
        processes_widget = QtWidgets.QWidget()
        processes_widget.setLayout(processes_layout)

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

        controls_group_box.setLayout(state_and_controls_layout)

        main_layout.addWidget(controls_group_box)

        self.setLayout(main_layout)

    def reset_controls(self):
        """
        Reset controls to default.
        """
        self.finished_processes_widget.hide()
        self.observed_atom_count_label.setText("0")
        self.state_label.setText("Not started")

    def __start_simulation(self):
        """ Calls ElementSimulation's start method.
        """
        number_of_processes = self.processes_spinbox.value()
        self.state_label.setText("Running")
        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)

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

        self.element_simulation.start(number_of_processes)

    def show_number_of_observed_atoms(self, number):
        """
        Show the number of observed atoms in the coltrols.

        Args:
            number: Observed atom number.
        """
        try:
            self.observed_atom_count_label.setText(str(number))
        except RuntimeError:
            pass

    def update_finished_processes(self, running_processes):
        """
        Update the amount of finished processes.

        Args:
            running_processes: Number of running processes.
        """
        all_proc = self.processes_spinbox.value()
        finished = all_proc - running_processes

        self.finished_processes_label.setText(
            str(finished) + "/" + str(all_proc))

    def __stop_simulation(self):
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
        self.show_stop()
        self.state_label.setText("Stopped")

    def show_stop(self):
        """
        Set controls to show that simulation has ended.
        """
        self.state_label.setText("Finished")
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.processes_spinbox.setEnabled(True)
