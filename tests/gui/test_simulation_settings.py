# coding=utf-8
"""
Created on 17.03.2020

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2020 TODO

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program (file named 'LICENCE').
"""
__author__ = "Juhani Sundell"
__version__ = ""  # TODO

import unittest
import sys
import tempfile

import tests.mock_objects as mo
import tests.utils as utils

from unittest.mock import patch
from widgets.simulation.settings import SimulationSettingsWidget

from PyQt5.QtWidgets import QApplication

app = QApplication(sys.argv)


class TestSimulationSettingsWidget(unittest.TestCase):
    def setUp(self):
        elem_sim = mo.get_element_simulation()
        elem_sim.name = "foo"
        elem_sim.description = "bar"
        # TODO simmode and simtype
        elem_sim.number_of_ions = 1
        elem_sim.number_of_preions = 2
        elem_sim.number_of_scaling_ions = 3
        elem_sim.number_of_recoils = 4
        elem_sim.minimum_energy = 5.5
        elem_sim.minimum_main_scattering_angle = 6.5
        elem_sim.minimum_scattering_angle = 7.5
        elem_sim.directory = tempfile.gettempdir()

        self.elem_sim = elem_sim

    @utils.change_wd_to_root
    def test_setting_parameters(self):
        sim_widget = SimulationSettingsWidget(self.elem_sim)
        self.assertEqual("foo", sim_widget.nameLineEdit.text())
        self.assertEqual("bar",
                         sim_widget.descriptionPlainTextEdit.toPlainText())
        self.assertEqual(1, sim_widget.numberOfIonsSpinBox.value())
        self.assertEqual(2, sim_widget.numberOfPreIonsSpinBox.value())
        self.assertEqual(3, sim_widget.numberOfScalingIonsSpinBox.value())
        self.assertEqual(4, sim_widget.numberOfRecoilsSpinBox.value())
        self.assertEqual(5.5, sim_widget.minimumEnergyDoubleSpinBox.value())
        self.assertEqual(
            6.5, sim_widget.minimumMainScatterAngleDoubleSpinBox.value())
        self.assertEqual(
            7.5, sim_widget.minimumScatterAngleDoubleSpinBox.value())

    @patch("os.remove")
    @patch("modules.element_simulation.ElementSimulation.to_file")
    @utils.change_wd_to_root
    def test_update_elementsimulation(self, mock_remove, mock_to_file):
        sim_widget = SimulationSettingsWidget(self.elem_sim)
        sim_widget.name = "foofoo"
        sim_widget.description = "barbar"
        sim_widget.number_of_ions = 11
        sim_widget.minimum_scattering_angle = 12.5

        # ElementSimulation is only updated after update_settings is called
        self.assertEqual("foo", self.elem_sim.name)

        sim_widget.update_settings()
        self.assertEqual("foofoo", self.elem_sim.name)
        self.assertEqual("barbar", self.elem_sim.description)
        self.assertEqual(11, self.elem_sim.number_of_ions)
        self.assertEqual(12.5, self.elem_sim.minimum_scattering_angle)




if __name__ == '__main__':
    unittest.main()