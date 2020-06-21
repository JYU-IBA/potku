# coding=utf-8
"""
Created on 21.06.2020

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2020 Juhani Sundell

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
import tests.gui
import tests.mock_objects as mo

from unittest.mock import Mock
from unittest.mock import patch

from dialogs.measurement.element_losses import ElementLossesDialog
from dialogs.measurement.depth_profile import DepthProfileDialog
from dialogs.energy_spectrum import EnergySpectrumParamsDialog
from dialogs.measurement.calibration import CalibrationDialog
from dialogs.simulation.optimization import OptimizationDialog


class TestDialogInitialization(unittest.TestCase):
    @patch("PyQt5.QtWidgets.QDialog.exec_")
    def test_initialization(self, mock_exec):
        """A simple test to see if various dialogs get initialized properly.
        """
        e = ElementLossesDialog(Mock(), mo.get_measurement())
        e.close()

        d = DepthProfileDialog(
            Mock(), mo.get_measurement(), mo.get_global_settings())
        d.close()

        c = CalibrationDialog(
            [mo.get_measurement()], mo.get_detector(), mo.get_run())
        c.close()

        o = OptimizationDialog(mo.get_simulation(), Mock())
        self.assertFalse(o.pushButton_OK.isEnabled())
        o.close()

        assert mock_exec.call_count == 4

    @patch("PyQt5.QtWidgets.QDialog.exec_")
    def test_espe_params(self, mock_exec):
        esp = EnergySpectrumParamsDialog(
            Mock(), "measurement", measurement=mo.get_measurement())
        esp.close()

        self.assertRaises(
            ValueError, lambda: EnergySpectrumParamsDialog(Mock(), "simu"))

        sim = mo.get_simulation()
        elem_sim = sim.add_element_simulation(
            mo.get_recoil_element(), save_on_creation=False)
        esp = EnergySpectrumParamsDialog(
            Mock(), "simulation", simulation=sim, element_simulation=elem_sim)
        esp.close()

        assert mock_exec.call_count == 2


if __name__ == '__main__':
    unittest.main()
