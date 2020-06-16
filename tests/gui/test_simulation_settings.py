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
__version__ = "2.0"

import unittest
import sys
import tempfile

import tests.mock_objects as mo
import tests.utils as utils

from modules.enums import SimulationType
from modules.enums import SimulationMode
from unittest.mock import patch
from widgets.simulation.settings import SimulationSettingsWidget

from PyQt5.QtWidgets import QApplication

app = QApplication(sys.argv)


class TestSimulationSettingsWidget(unittest.TestCase):
    def setUp(self):
        elem_sim = mo.get_element_simulation()
        elem_sim.name = "foo"
        elem_sim.description = "bar"
        elem_sim.simulation_mode = SimulationMode.NARROW
        elem_sim.simulation_type = SimulationType.ERD
        elem_sim.seed_number = 42
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
        """Test that correct values are shown in the widget.
        """
        sim_widget = utils.run_without_warnings(
            lambda: SimulationSettingsWidget(self.elem_sim))
        self.assertEqual("foo", sim_widget.nameLineEdit.text())
        self.assertEqual("bar",
                         sim_widget.descriptionPlainTextEdit.toPlainText())
        self.assertEqual("REC",
                         sim_widget.typeOfSimulationComboBox.currentText())
        self.assertEqual("Narrow", sim_widget.modeComboBox.currentText())
        self.assertTrue(42, sim_widget.seedSpinBox.value())
        self.assertEqual(1, sim_widget.numberOfIonsSpinBox.value())
        self.assertEqual(2, sim_widget.numberOfPreIonsSpinBox.value())
        self.assertEqual(3, sim_widget.numberOfScalingIonsSpinBox.value())
        self.assertEqual(4, sim_widget.numberOfRecoilsSpinBox.value())
        self.assertEqual(5.5, sim_widget.minimumEnergyDoubleSpinBox.value())
        self.assertEqual(
            6.5, sim_widget.minimumMainScatterAngleDoubleSpinBox.value())
        self.assertEqual(
            7.5, sim_widget.minimumScatterAngleDoubleSpinBox.value())

        sim_widget.simulation_type = SimulationType.RBS
        self.assertEqual("SCT",
                         sim_widget.typeOfSimulationComboBox.currentText())

    @patch("os.remove")
    @patch("modules.recoil_element.RecoilElement.to_file")
    @utils.change_wd_to_root
    def test_update_elementsimulation(self, mock_remove, mock_rec_to_file):
        """Tests if updating properties also updates ElementSimulation
        object.

        Patching is used to avoid unneccessary file removal and writing.
        """
        sim_widget = SimulationSettingsWidget(self.elem_sim)
        sim_widget.name = "foofoo"
        sim_widget.description = "barbar"
        sim_widget.simulation_type = SimulationType.RBS
        sim_widget.simulation_mode = SimulationMode.WIDE
        sim_widget.number_of_ions = 11
        sim_widget.minimum_scattering_angle = 12.5
        sim_widget.seed_number = 45

        # ElementSimulation is only updated after update_settings is called
        self.assertEqual("foo", self.elem_sim.name)
        self.assertEqual(SimulationType.ERD, self.elem_sim.simulation_type)
        self.assertEqual(SimulationMode.NARROW, self.elem_sim.simulation_mode)

        sim_widget.update_settings()
        self.assertEqual("foofoo", self.elem_sim.name)
        self.assertEqual("barbar", self.elem_sim.description)
        self.assertEqual(SimulationType.RBS, self.elem_sim.simulation_type)
        self.assertEqual(SimulationMode.WIDE, self.elem_sim.simulation_mode)
        self.assertEqual(11, self.elem_sim.number_of_ions)
        self.assertEqual(12.5, self.elem_sim.minimum_scattering_angle)
        self.assertEqual(45, self.elem_sim.seed_number)

        # Assert that the patched methods got called at least once
        mock_remove.assert_called()
        mock_rec_to_file.assert_called()

    @utils.change_wd_to_root
    def test_value_changed(self):
        sim_widget = utils.run_without_warnings(
            lambda: SimulationSettingsWidget(self.elem_sim))
        self.assertFalse(sim_widget.are_values_changed())

        # Seed is not taken into account
        sim_widget.seed = 45
        self.assertFalse(sim_widget.are_values_changed())

        sim_widget.name = "bar"
        self.assertTrue(sim_widget.are_values_changed())

        # Changing the name back also resets value_changed
        sim_widget.name = "foo"
        self.assertFalse(sim_widget.are_values_changed())


if __name__ == '__main__':
    unittest.main()
