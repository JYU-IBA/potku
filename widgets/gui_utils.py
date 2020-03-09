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
from PyQt5 import QtWidgets

from PyQt5.QtCore import QTime
from PyQt5.QtWidgets import QTimeEdit
from PyQt5.QtWidgets import QComboBox


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


class StatusBarHandler(ProgressReporter):
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


def _fget(qobj):
    if isinstance(qobj, QTimeEdit):
        return qobj.time
    if isinstance(qobj, QComboBox):
        return qobj.currentText
    return qobj.value


def _fset(qobj):
    if isinstance(qobj, QTimeEdit):
        return lambda sec: qobj.setTime(QTime(0, 0, sec))
    return qobj.setValue


class BindingPropertyWidget(abc.ABC):
    """Base class for a widget that contains bindable properties.
    """
    def _get_properties(self):
        """Returns the names of all properties the widget has.
        """
        return [
            d for d in dir(self)
            if hasattr(type(self), d) and
            isinstance(getattr(type(self), d), property)
        ]

    def set_properties(self, **kwargs):
        for p in self._get_properties():
            if p in kwargs:
                try:
                    setattr(self, p, kwargs[p])
                except AttributeError:
                    pass

    def get_properties(self):
        """Returns a dictionary where key-value pairs are property names and
        their values.
        """
        return {
            p: getattr(self, p)
            for p in self._get_properties()
        }


def bind(qobj_name, func, twoway=True):
    """Returns a property that is bound to a QObject.

    Widget that uses this function has to have a reference to QObject with
    given attribute name.

    Args:
        qobj_name: name of an attribute that is a reference to a QObject
        func: function that is applied to the value of the QObject when
              it is returned
        twoway: whether binding is two-way (setting the property also sets
                the QObject value) or one-way.
    """
    def getter(self):
        qobj = getattr(self, qobj_name)
        return func(_fget(qobj)())

    def setter(self, value):
        if twoway:
            qobj = getattr(self, qobj_name)
            _fset(qobj)(value)

    return property(getter, setter)


def multi_bind(qobjs, funcs, twoway=True):
    # TODO refactor this with bind
    # TODO enable twoway binding with combobox
    def getter(self):
        return tuple(
            conv(_fget(getattr(self, qobj))())
            for qobj, conv in zip(qobjs, funcs)
        )

    def setter(self, values):
        if twoway:
            for qobj, value in zip(qobjs, values):
                obj = getattr(self, qobj)
                _fset(obj)(value)

    return property(getter, setter)
