# coding=utf-8
"""
Created on 06.04.2020

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

import abc
import logging
from pathlib import Path
from typing import Union, Optional, Callable, Dict

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

import widgets.gui_utils as gutils

from modules.measurement import Measurement
from modules.simulation import Simulation
from modules.ui_log_handlers import CustomLogHandler

from widgets.gui_utils import QtABCMeta
from widgets.icon_manager import IconManager
from widgets.log import LogWidget


class BaseTab(QtWidgets.QWidget, abc.ABC, metaclass=QtABCMeta):
    """Base class for both Simulation and Measurement tabs.
    """
    SAVE_WINDOW_GEOM_KEY = "save_window_geometries"

    mdiArea: QtWidgets.QMdiArea

    def __init__(
            self,
            obj: Union[Measurement, Simulation],
            tab_id: int,
            icon_manager: IconManager,
            statusbar: Optional[QtWidgets.QStatusBar] = None):
        """Initializes BaseTab.

        Args:
            obj: either Measurement or Simulation
            tab_id: An integer representing ID of the tabwidget.
            icon_manager: An IconManager class object.
            statusbar: A QtGui.QMainWindow's QStatusBar.
        """
        super().__init__()
        self.obj = obj
        self.tab_id = tab_id
        self.icon_manager = icon_manager
        self.statusbar = statusbar
        self.log = None
        self.data_loaded = False

    def add_widget(
            self,
            widget: QtWidgets.QWidget,
            minimized: bool = False,
            has_close_button: bool = True,
            icon: Optional[QtGui.QIcon] = None):
        """Adds a new widget to current tab.

        Args:
            widget: QWidget to be added into measurement tab widget.
            minimized: Boolean representing if widget should be minimized.
            has_close_button: Whether widget has close button or not.
            icon: QtGui.QIcon for the subwindow.
        """
        if has_close_button:
            subwindow = self.mdiArea.addSubWindow(widget)
        else:
            subwindow = self.mdiArea.addSubWindow(
                widget, QtCore.Qt.CustomizeWindowHint |
                        QtCore.Qt.WindowTitleHint |
                        QtCore.Qt.WindowMinMaxButtonsHint)
        if icon is not None:
            subwindow.setWindowIcon(icon)
        subwindow.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        widget.subwindow = subwindow

        if minimized:
            widget.showMinimized()
        else:
            widget.show()

    def add_log(self) -> None:
        """Add the log to tab widget.

        Checks also if there's already some logging for this logging entity
        and appends the text field of the user interface with this log.
        """
        self.log = LogWidget()
        self.add_widget(self.log, minimized=True, has_close_button=False)
        self._add_ui_logger()

        self._read_log_file(self.obj.info_log_file, self.log.add_text)
        self._read_log_file(self.obj.error_log_file, self.log.add_error)

    def _add_ui_logger(self) -> None:
        """Adds handlers to logging entity so the entity can log the
        events to the user interface too.

        log_widget specifies which ui element will handle the logging. That
        should be the one which is added to this tab.
        """
        widgetlogger_default = CustomLogHandler(
            logging.INFO, self.obj.default_formatter, self.log)
        self.obj.logger.addHandler(widgetlogger_default)

    def del_widget(self, widget: QtWidgets.QWidget) -> None:
        """Delete a widget from current tab.

        Args:
            widget: QWidget to be removed.
        """
        try:
            self.mdiArea.removeSubWindow(widget.subwindow)
            widget.delete()
        except:
            # If window was manually closed, do nothing.
            pass

    @staticmethod
    def _read_log_file(
            file: Optional[Path],
            add_func: Callable[[str], None]) -> None:
        """Read the log file into the log window and add its lines to log
        widget.
        """
        if file is None:
            return
        try:
            with file.open("r") as f:
                for line in f:
                    add_func(line.strip())
        except OSError:
            pass

    @abc.abstractmethod
    def load_data(self) -> None:
        """Loads the data belonging to the object into view.
        """
        pass

    @abc.abstractmethod
    def get_saveable_widgets(self) -> Dict[str, Optional[QtWidgets.QWidget]]:
        """Returns a dictionary of where values are widgets and keys are
        strings that are used when widget geometries are saved.
        """
        pass

    @abc.abstractmethod
    def get_default_widget(self) -> Optional[QtWidgets.QWidget]:
        """Returns the default widget to activate when geometries are
        restored.
        """
        pass

    def save_geometries(self) -> None:
        """Saves the geometries of all saveable widgets that this tab
        has.
        """
        if not gutils.get_potku_setting(BaseTab.SAVE_WINDOW_GEOM_KEY, True):
            return
        for key, widget in self.get_saveable_widgets().items():
            if widget is not None:
                gutils.set_potku_setting(
                    key, widget.subwindow.saveGeometry())

    def restore_geometries(self) -> None:
        """Restores the geometries of all the widgets that have had their
        geometries saved. Activates the widget that is returned by
        get_default_widget.
        """
        if not gutils.get_potku_setting(BaseTab.SAVE_WINDOW_GEOM_KEY, True):
            return
        for key, widget in self.get_saveable_widgets().items():
            if widget is not None:
                geom = gutils.get_potku_setting(key, bytes("", "utf-8"))
                widget.subwindow.restoreGeometry(geom)

        active_widget = self.get_default_widget()
        if active_widget is not None:
            self.mdiArea.setActiveSubWindow(active_widget.subwindow)

    def check_default_settings(self) -> None:
        """Gives an warning if the default settings are checked in the
        settings tab.
        """
        if not self.obj.use_request_settings:
            self.warning_text.setText("Not using request setting values ("
                                      "default)")
            self.warning_text.setStyleSheet("background-color: yellow")
        else:
            self.warning_text.setText("")
            self.warning_text.setStyleSheet("")

