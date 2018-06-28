# coding=utf-8
"""
Created on 1.3.2018
Updated on 28.6.2018

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

    def __init__(self, element_simulation):
        """
        Initializes a SimulationControlsWidget.

        Args:
             element_simulation: An ElementSimulation class object.
        """
        super().__init__()

        self.element_simulation = element_simulation
        self.element_simulation.controls = self

        main_layout = QtWidgets.QHBoxLayout()
        element = self.element_simulation.recoil_elements[
            0].element
        controls_group_box = QtWidgets.QGroupBox(str(element.isotope)
                                                 + element.symbol)
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

        state_and_controls_layout = QtWidgets.QVBoxLayout()
        state_and_controls_layout.setContentsMargins(6, 6, 6, 6)
        state_and_controls_layout.addWidget(processes_widget)
        state_and_controls_layout.addWidget(state_widget)
        state_and_controls_layout.addWidget(controls_widget)

        controls_group_box.setLayout(state_and_controls_layout)

        main_layout.addWidget(controls_group_box)

        self.setLayout(main_layout)

    def __start_simulation(self):
        """ Calls ElementSimulation's start method.
        """
        number_of_processes = self.processes_spinbox.value()
        self.element_simulation.start(number_of_processes)
        self.state_label.setText("Running")
        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)

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
