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

from modules.observing import ProgressReporter

from PyQt5 import QtCore


def process_event_loop(func):
    """Decorator that processes QCoreApplication's event loop.
    after the function has been called.
    """
    def wrapper(*args, **kwargs):
        res = func(*args, **kwargs)
        QtCore.QCoreApplication.processEvents(
            QtCore.QEventLoop.AllEvents)
        return res
    return wrapper


def switch_buttons(func, button_a, button_b):
    """Decorator for that switches the status of two buttons.

    First button is switched before the execution of a function and
    second one is switched after the execution.
    """
    # This decorator may not be particularly useful as there must be
    # a reference to the buttons at the time the interpreter reads the
    # decorated function declaration. Also no thread safety in here.
    def wrapper(*args, **kwargs):
        button_a.setEnabled(not button_a.isEnabled())
        res = func(*args, **kwargs)
        button_b.setEnabled(not button_b.isEnabled())
        return res
    return wrapper


class QtABCMeta(type(QtCore.QObject), abc.ABCMeta):
    """A common metaclass for ABCs and QWidgets.

    QWidget has the metaclass 'sip.wrappertype' which causes a conflict
    in multi-inheritance with an ABC.

    Originally this was intended as a metaclass for QWidgets and Observers
    but since Observers are no longer ABCs, this class may not be needed.
    """
    pass


if platform.system() == "Darwin":
    # Mac needs event processing to display changes in the status bar
    def _process_event_loop():
        QtCore.QCoreApplication.processEvents(
            QtCore.QEventLoop.AllEvents)
else:
    def _process_event_loop():
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
        def __update_func(value):
            # Callback function that will be connected to the signal
            if progress_bar is not None:
                progress_bar.setValue(value)

                _process_event_loop()

        self.signaller = self.Signaller()
        ProgressReporter.__init__(self, self.signaller.sig.emit)
        self.signaller.sig.connect(__update_func)
