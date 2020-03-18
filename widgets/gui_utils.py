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


def from_qtime(qtime: QTime) -> int:
    """Converts QTime object to seconds.
    """
    return qtime.hour() * 60 * 60 + qtime.minute() * 60 + qtime.second()


def to_qtime(seconds: int) -> QTime:
    """Converts seconds to QTime.
    """
    t = QTime(0, 0, 0).addSecs(seconds)
    return t


def _fget(instance, qobj_name):
    """Returns a default getter method based on the type of the given
    QObject.
    """
    qobj = getattr(instance, qobj_name)
    if isinstance(qobj, QtWidgets.QTimeEdit):
        return lambda: from_qtime(qobj.time())
    if isinstance(qobj, QtWidgets.QLineEdit):
        return qobj.text
    if isinstance(qobj, QtWidgets.QComboBox):
        return qobj.currentText
    if isinstance(qobj, QtWidgets.QTextEdit):
        return qobj.toPlainText
    if isinstance(qobj, QtWidgets.QCheckBox):
        return qobj.isChecked
    if isinstance(qobj, QtWidgets.QPlainTextEdit):
        return qobj.toPlainText
    if isinstance(qobj, QtWidgets.QLabel):
        return qobj.text
    return qobj.value


def _fset(instance, qobj_name):
    """Returns a default setter method based on the type of the given
    QObject.
    """
    qobj = getattr(instance, qobj_name)
    if isinstance(qobj, QtWidgets.QTimeEdit):
        return lambda sec: qobj.setTime(to_qtime(sec))
    if isinstance(qobj, QtWidgets.QLineEdit):
        return qobj.setText
    if isinstance(qobj, QtWidgets.QComboBox):
        return lambda value: qobj.setCurrentIndex(qobj.findText(
            value, QtCore.Qt.MatchFixedString))
    if isinstance(qobj, QtWidgets.QTextEdit):
        return qobj.setText
    if isinstance(qobj, QtWidgets.QCheckBox):
        return qobj.setChecked
    if isinstance(qobj, QtWidgets.QPlainTextEdit):
        return qobj.setPlainText
    if isinstance(qobj, QtWidgets.QLabel):
        return qobj.setText
    return qobj.setValue


class BindingPropertyWidget(abc.ABC):
    """Base class for a widget that contains bindable properties.
    """
    def __init__(self):
        self._original_property_values = {}

    def _get_properties(self):
        """Returns the names of all properties the widget has.
        """
        return (
            d for d in dir(self)
            if hasattr(type(self), d) and
            isinstance(getattr(type(self), d), property)
        )

    def set_properties(self, **kwargs):
        """Sets property values.

        Args:
            kwargs: properties and values as keyword arguments.
        """
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

    def are_values_changed(self):
        return any(getattr(type(self), p).is_value_changed(self)
                   for p in self.get_properties())


class PropertySavingWidget(BindingPropertyWidget, abc.ABC):
    """Property widget that saves the current state of its properties
    to file. Saving is done automatically when the widget closes, unless
    the inheriting widget overrides the closeEvent function.

    Loading is done by calling the load_properties_from_file function.

    Property values must be JSON encodable.
    """
    # TODO maybe do loading in showEvent function

    @abc.abstractmethod
    def get_property_file_path(self):
        """Returns Path object to the file that is used to save and load
        properties.
        """
        pass

    def closeEvent(self, event):
        """Overrides QWidgets closeEvent. Saves the properties to default
        file.
        """
        self.save_properties_to_file(file_path=self.get_property_file_path())
        event.accept()

    def save_properties_to_file(self, file_path=None):
        """Saves properties to a file.

        Args:
            file_path: Path object to a file that is used for saving. If None,
                widget's default property file location is used.
        """
        if file_path is None:
            file_path = self.get_property_file_path()

        os.makedirs(file_path.parent, exist_ok=True)
        params = self.get_properties()
        try:
            with open(file_path, "w") as file:
                json.dump(params, file, indent=4)
        except (PermissionError, IsADirectoryError):
            pass

    def load_properties_from_file(self, file_path=None):
        """Loads properties from a file.

        Args:
            file_path: Path object to a file that is used for loading. If None,
                widget's default property file location is used.
        """
        if file_path is None:
            file_path = self.get_property_file_path()
        try:
            with open(file_path) as file:
                params = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError,
                PermissionError, IsADirectoryError):
            return

        self.set_properties(**params)


class BindingProperty(property):
    def __init__(self, *args, prop_name=None, track_change=False, **kwargs):
        super().__init__(*args, **kwargs)

        if track_change and prop_name is None:
            raise ValueError("If changes in property value are to be "
                             "tracked, property name must not be None.")

        self.__prop_name = prop_name
        self.__track_change = track_change

    def __set__(self, instance, value):
        self.fset(instance, value)
        if self.__track_change and isinstance(instance, BindingPropertyWidget):
            set_val = self.fget(instance)
            if set_val is None:
                return

            orig_props = getattr(instance, "_original_property_values", None)
            if orig_props is None:
                instance._original_property_values = {
                    self.__prop_name: set_val
                }
            elif self.__prop_name not in orig_props:
                instance._original_property_values[self.__prop_name] = set_val

    def is_value_changed(self, instance):
        if self.__track_change:
            orig_props = getattr(instance, "_original_property_values", {})
            orig_value = orig_props.get(self.__prop_name, None)
            return self.fget(instance) != orig_value
        return False


def bind(prop_name, fget=None, fset=None, twoway=True,
         track_change=False):
    """Returns a property that is bound to an attribute.

    Args:
        prop_name: name of an attribute that the property will be bound to
        fget: function that takes the QObject as parameter and returns the
            value of the property
        fset: function that takes the QObject and a value as parameters and
            sets the value of the QObject to the given value
        twoway: whether binding is two-way (setting the property also sets
                the QObject value) or one-way.
    """
    def getter(instance):
        if fget is None:
            return _fget(instance, prop_name)()
        return fget(instance, prop_name)

    if not twoway:
        return BindingProperty(getter)

    def setter(instance, value):
        try:
            if fset is None:
                _fset(instance, prop_name)(value)
            else:
                fset(instance, prop_name, value)
        except TypeError:
            pass

    return BindingProperty(getter, setter, prop_name=prop_name,
                           track_change=track_change)


def multi_bind(qobjs, funcs, twoway=True):
    # TODO refactor this with bind
    # TODO enable twoway binding with combobox
    def getter(instance):
        return tuple(
            conv(_fget(instance, qobj)())
            for qobj, conv in zip(qobjs, funcs)
        )

    if not twoway:
        return BindingProperty(getter)

    def setter(instance, values):
        for qobj, value in zip(qobjs, values):
            try:
                _fset(instance, qobj)(value)
            except TypeError:
                pass

    return BindingProperty(getter, setter)
