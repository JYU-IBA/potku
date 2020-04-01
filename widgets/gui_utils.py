# coding=utf-8
"""
Created on 2.2.2020

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
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program (file named 'LICENCE').
"""
__author__ = "Juhani Sundell"
__version__ = "2.0"

import abc
import platform
import os
import json

from modules.observing import ProgressReporter

from PyQt5 import QtCore
from PyQt5 import QtWidgets

from PyQt5.QtCore import QTime


if platform.system() == "Darwin":
    # Mac needs event processing to display changes in the status bar
    def _process_event_loop():
        QtCore.QCoreApplication.processEvents(
            QtCore.QEventLoop.AllEvents)
else:
    def _process_event_loop():
        pass


def process_event_loop(func):
    """Decorator that processes QCoreApplication's event loop.
    after the function has been called.
    """
    def wrapper(*args, **kwargs):
        res = func(*args, **kwargs)
        _process_event_loop()
        return res
    return wrapper


def switch_buttons(button_a, button_b):
    """Decorator for that switches the status of two buttons.

    This decorator must be used in an object instance that has reference
    to button_a and button_b.

    Args:
        button_a: name of a reference to a Qt button.
        button_b: name of a reference to a Qt button.
    """
    def outer(func):
        def inner(self, *args, **kwargs):
            # TODO exception handling
            btn_a = getattr(self, button_a)
            btn_a.setEnabled(not btn_a.isEnabled())
            _process_event_loop()

            res = func(self, *args, **kwargs)

            btn_b = getattr(self, button_b)
            btn_b.setEnabled(not btn_b.isEnabled())
            _process_event_loop()
            return res
        return inner
    return outer


class QtABCMeta(type(QtCore.QObject), abc.ABCMeta):
    """A common metaclass for ABCs and QObjects.

    QObject has the metaclass 'sip.wrappertype' which causes a conflict
    in multi-inheritance with an ABC. This metaclass fixes that issue.
    """
    pass


class GUIReporter(ProgressReporter):
    """GUI Progress reporter that updates the value of a progress bar.

    Uses pyqtSignal to ensure that the progress bar is updated in the
    Main thread.
    """
    class Signaller(QtCore.QObject):
        # Helpers class that has a signal for emitting status bar updates
        sig = QtCore.pyqtSignal(float)

    def __init__(self, progress_bar):
        """Initializes a new GUIReporter that updates the value of a given
        progress bar.

        Args:
            progress_bar: GUI progress bar that will be updated
        """
        @process_event_loop
        def __update_func(value):
            # Callback function that will be connected to the signal
            if progress_bar is not None:
                progress_bar.setValue(value)

        self.signaller = self.Signaller()
        ProgressReporter.__init__(self, self.signaller.sig.emit)
        self.signaller.sig.connect(__update_func)


class StatusBarHandler:
    """Helper class to show, hide and update a progress bar in the
    given statusbar.
    """
    @process_event_loop
    def __init__(self, statusbar, autoremove=True):
        """Initializes a new StatusBarHandler.

        Args:
            statusbar: PyQt statusbar
            autoremove: automatically hides the progress bar when its
                        surpasses 99
        """
        # TODO could also use a remove_at parameter that defines when
        #      the progress bar is removed
        self.statusbar = statusbar
        if self.statusbar is not None:
            self.progress_bar = QtWidgets.QProgressBar()
            self.statusbar.addWidget(
                self.progress_bar, 1)
            self.progress_bar.show()
            if autoremove:
                self.progress_bar.valueChanged.connect(self.__check_progress)
        else:
            self.progress_bar = None
        self.reporter = GUIReporter(self.progress_bar)

    def __check_progress(self, value):
        """Checks if the value of progress bar is over 99 and calls
        remove_progress_bar if so.

        Args:
            value: current value of the progress bar
        """
        if value > 99:
            self.remove_progress_bar()

    @process_event_loop
    def remove_progress_bar(self):
        """Removes progress bar from status bar.
        """
        if self.statusbar is not None:
            self.statusbar.removeWidget(self.progress_bar)
        if self.progress_bar is not None:
            self.progress_bar.hide()
