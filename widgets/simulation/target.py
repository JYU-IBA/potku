# coding=utf-8
"""
Created on 28.3.2018
Updated on 27.11.2018

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
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä " \
             "\n Sinikka Siironen"
__version__ = "2.0"

import platform
import threading
import time

import widgets.gui_utils as gutils

from typing import Optional
from pathlib import Path

from modules.element_simulation import ElementSimulation
from modules.simulation import Simulation
from modules.global_settings import GlobalSettings
from modules.target import Target
from modules.observing import ProgressReporter

from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal

from widgets.icon_manager import IconManager
from widgets.base_tab import BaseTab
from widgets.gui_utils import StatusBarHandler
from widgets.matplotlib.simulation.composition import TargetCompositionWidget
from widgets.matplotlib.simulation.recoil_atom_distribution import \
    RecoilAtomDistributionWidget


class TargetWidget(QtWidgets.QWidget):
    """ Widget that can be used to define target composition and
        recoil atom distribution.
    """
    results_accepted = pyqtSignal(ElementSimulation)

    def __init__(self, tab: BaseTab, simulation: Simulation, target: Target,
                 icon_manager: IconManager, settings: GlobalSettings,
                 progress: Optional[ProgressReporter] = None,
                 statusbar: Optional[QtWidgets.QStatusBar] = None,
                 auto_save: bool = True, **kwargs):
        """Initializes thw widget that can be used to define target composition
        and
        recoil atom distribution.

        Args:
            tab: A TabWidget.
            simulation: A Simulation object.
            target: A Target object.
            icon_manager: An icon manager class object.
            progress: ProgressReporter object
            auto_save: whether automatic saving is enabled.
        """
        super().__init__()
        uic.loadUi(gutils.get_ui_dir() / "ui_target_widget.ui", self)

        if progress is not None:
            progress.report(0)

        self.tab = tab
        self.simulation = simulation
        self.target = target
        self.statusbar = statusbar

        self.recoil_distribution_widget = RecoilAtomDistributionWidget(
            self, self.simulation, self.target, tab, icon_manager, settings,
            statusbar=self.statusbar, **kwargs)

        if progress is not None:
            progress.report(50)

        self.target_widget = TargetCompositionWidget(
            self, self.target, icon_manager, self.simulation)

        self.results_accepted.connect(
            self.recoil_distribution_widget.update_element_simulation.emit)
        self.spectra_changed = self.recoil_distribution_widget. \
            recoil_dist_changed

        icon_manager.set_icon(self.editPushButton, "edit.svg")
        self.editPushButton.setIconSize(QtCore.QSize(14, 14))
        self.editPushButton.setToolTip(
            "Edit name, description and reference density "
            "of this recoil element")
        self.recoilListWidget.hide()
        self.editLockPushButton.hide()
        self.elementInfoWidget.hide()

        if platform.system() == "Darwin":
            self.percentButton.setText("Calculate\npercents")

        self.exportElementsButton.clicked.connect(
            lambda: self.recoil_distribution_widget.export_elements(**kwargs))

        self.targetRadioButton.clicked.connect(self.switch_to_target)
        self.recoilRadioButton.clicked.connect(self.switch_to_recoil)

        if not self.target.layers:
            self.recoilRadioButton.setEnabled(False)

        self.targetRadioButton.setChecked(True)
        self.stackedWidget.setCurrentIndex(1)

        self.saveButton.clicked.connect(self._save_target_and_recoils)

        self.del_points = None

        self.set_shortcuts()
        if progress is not None:
            progress.report(100)

        self.stop_saving = False
        self.thread = None

        if auto_save:
            self.add_automatic_saving()

    def add_automatic_saving(self):
        """Add this target widget to be saved (target and recoils) every 1
        minute in a thread.
        """
        self.thread = threading.Thread(target=self.timed_save)
        self.thread.daemon = True
        self.thread.start()

    def switch_to_target(self):
        """
        Switch to target view.
        """
        self.recoil_distribution_widget.original_x_limits = \
            self.recoil_distribution_widget.axes.get_xlim()
        self.stackedWidget.setCurrentIndex(1)
        self.recoilListWidget.hide()
        self.editLockPushButton.hide()
        self.exportElementsButton.show()
        self.elementInfoWidget.hide()
        self.instructionLabel.setText("")
        self.targetInfoWidget.show()

    def switch_to_recoil(self):
        """
        Switch to recoil atom distribution view.
        """
        self.stackedWidget.setCurrentIndex(0)
        self.recoil_distribution_widget.update_layer_borders()
        self.exportElementsButton.hide()
        self.recoilListWidget.show()
        self.editLockPushButton.show()
        self.targetInfoWidget.hide()
        self.recoil_distribution_widget.recoil_element_info_on_switch()

        text = "You can add a new point to the distribution on a line between "\
               "points using "
        if platform.system() == "Darwin":
            text += "⌘+click."
        else:
            text += "Ctrl+click."
        self.instructionLabel.setText(text)

    def timed_save(self):
        """
        Save target and recoils every 1 minute.
        """
        while True:
            # TODO it might be better to just save when something changes
            #  instead of automatically doing it every 60 seconds. This might
            #  cause a situation where files are being written or read at the
            #  same time by different threads.
            if self.stop_saving:
                break
            if self.target:
                self._save_target_and_recoils(True)
            time.sleep(60)

    def _save_target_and_recoils(self, thread=False):
        """
        Save target and element simulations.

        Args:
            thread: Whether saving happens in a thread or by pressing the
            button.
        """
        if not thread and self.statusbar is not None:
            sbh = StatusBarHandler(self.statusbar)
            reporter = sbh.reporter
        else:
            reporter = None

        if self.target.name:
            target_name = self.target.name
        else:
            target_name = "temp"

        target_path = Path(self.simulation.directory, f"{target_name}.target")
        self.target.to_file(target_path)

        if not thread and reporter is not None:
            reporter.report(50)
            sub_reporter = reporter.get_sub_reporter(lambda x: 50 + 0.5 * x)
        else:
            sub_reporter = None

        self.recoil_distribution_widget.save_mcsimu_rec_profile(
            self.simulation.directory, progress=sub_reporter)

        if reporter is not None:
            reporter.report(100)

    def set_shortcuts(self):
        """
        Set shortcuts for deleting points.
        """
        self.del_points = QtWidgets.QShortcut(self)
        self.del_points.setKey(QtCore.Qt.Key_Delete)
        self.del_points.activated.connect(
            lambda: self.recoil_distribution_widget.remove_points())
