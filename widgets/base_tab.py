# coding=utf-8
"""
Created on 06.04.2020

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
__author__ = ""  # TODO
__version__ = ""  # TODO

import abc
import logging

from pathlib import Path

from widgets.log import LogWidget
from widgets.gui_utils import QtABCMeta

from modules.ui_log_handlers import CustomLogHandler

from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget


class BaseTab(abc.ABC, metaclass=QtABCMeta):
    """Base class for both Simulation and Measurement tabs.
    """
    def add_widget(self, widget: QWidget, minimized=None, has_close_button=True,
                   icon=None):
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
        if icon:
            subwindow.setWindowIcon(icon)
        subwindow.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        widget.subwindow = subwindow

        if minimized:
            widget.showMinimized()
        else:
            widget.show()

    def add_log(self):
        """Add the log to tab widget.

        Checks also if there's already some logging for this logging entity
        and appends the text field of the user interface with this log.
        """
        self.log = LogWidget()
        self.add_widget(self.log, minimized=True, has_close_button=False)
        self.add_ui_logger(self.log)

        # Checks for log file and appends it to the field.
        log_default = Path(self.obj.directory, "default.log")
        log_error = Path(self.obj.directory, "errors.log")
        self.__read_log_file(log_default, 1)
        self.__read_log_file(log_error, 0)

    def add_ui_logger(self, log_widget):
        """Adds handlers to logging entity so the entity can log the
        events to the user interface too.

        log_widget specifies which ui element will handle the logging. That
        should be the one which is added to this tab.
        """
        logger = logging.getLogger(self.obj.name)
        defaultformat = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S')
        widgetlogger_default = CustomLogHandler(logging.INFO,
                                                defaultformat,
                                                log_widget)
        logger.addHandler(widgetlogger_default)

    def del_widget(self, widget):
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

    def __read_log_file(self, file, state=1):
        """Read the log file into the log window.

        Args:
            file: A string representing log file.
            state: An integer (0, 1) representing what sort of log we read.
                   0 = error
                   1 = text (default)
        """
        p = Path(file)
        if p.exists():
            with open(p) as log_file:
                for line in log_file:
                    if state == 0:
                        self.log.add_error(line.strip())
                    else:
                        self.log.add_text(line.strip())