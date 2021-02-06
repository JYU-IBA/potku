# coding=utf-8
"""
Created on 06.02.2021

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2021 Juhani Sundell

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

from modules.enums import CrossSection
from dialogs.measurement.depth_profile import DepthProfileDialog


class TestDialogInitialization(unittest.TestCase):
    """Tests initialization conditions that various Dialogs must have.
    """
    def setUp(self) -> None:
        self.measurement = mo.get_measurement()
        self.global_settings = mo.get_global_settings()
        self.parent_widget = Mock()

    @patch("PyQt5.QtWidgets.QDialog.exec_")
    def test_dialog_is_opened(self, mock_exec):
        dialog = DepthProfileDialog(
            self.parent_widget,
            self.measurement,
            self.global_settings)
        dialog.close()
        mock_exec.assert_called_once()

    @patch("PyQt5.QtWidgets.QDialog.exec_")
    def test_dialog_shows_correct_cross_section_model(self, _):
        cross_section = CrossSection.LECUYER
        self.global_settings.set_cross_sections(cross_section)
        dialog = DepthProfileDialog(
            self.parent_widget,
            self.measurement,
            self.global_settings)

        self.assertEqual(
            dialog.label_cross.text(),
            str(cross_section))
        dialog.close()

    @patch("PyQt5.QtWidgets.QDialog.exec_")
    def test_dialog_shows_correct_measurement_settings(self, _):
        dialog = DepthProfileDialog(
            self.parent_widget,
            self.measurement,
            self.global_settings)

        self.assertEqual(
            dialog.label_calibslope.text(),
            str(self.measurement.detector.tof_slope))
        self.assertEqual(
            dialog.label_caliboffset.text(),
            str(self.measurement.detector.tof_offset))
        self.assertEqual(
            dialog.label_depthstop.text(),
            str(self.measurement.profile.depth_step_for_stopping))
        self.assertEqual(
            dialog.label_depthnumber.text(),
            str(self.measurement.profile.number_of_depth_steps))
        self.assertEqual(
            dialog.label_depthbin.text(),
            str(self.measurement.profile.depth_step_for_output))
        self.assertEqual(
            dialog.label_depthscale.text(),
            f"{self.measurement.profile.depth_for_concentration_from} - "
            f"{self.measurement.profile.depth_for_concentration_to}")

        dialog.close()

    @patch("PyQt5.QtWidgets.QDialog.exec_")
    def test_dialog_shows_efficiency_files_are_correctly_shown(self, _):
        dialog = DepthProfileDialog(
            self.parent_widget,
            self.measurement,
            self.global_settings)

        expected = "No efficiency files."

        self.assertEqual(
            dialog.label_efficiency_files.text(),
            expected
        )
        dialog.close()

    @patch("PyQt5.QtWidgets.QDialog.exec_")
    def test_dialog_shows_correct_other_settings(self, _):
        dialog = DepthProfileDialog(
            self.parent_widget,
            self.measurement,
            self.global_settings)

        self.assertEqual(
            dialog.check_0line.isChecked(),
            DepthProfileDialog.line_zero
        )
        self.assertEqual(
            dialog.check_scaleline.isChecked(),
            DepthProfileDialog.line_scale
        )
        self.assertEqual(
            dialog.spin_systerr.value(),
            DepthProfileDialog.systerr
        )
        dialog.close()


if __name__ == '__main__':
    unittest.main()
