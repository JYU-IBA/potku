# coding=utf-8
"""
Created on 18.03.2020

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
__version__ = ""  # TODO

import os
import abc
import json

from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5.QtCore import QTime


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
