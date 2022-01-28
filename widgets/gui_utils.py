# coding=utf-8
"""
Created on 2.2.2020

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
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program (file named 'LICENCE').
"""
__author__ = "Juhani Sundell"
__version__ = "2.0"

import abc
import platform
import functools

import modules.general_functions as gf

from pathlib import Path
from typing import Iterable
from typing import Optional
from typing import Union
from typing import Any
from typing import Callable

from modules.observing import ProgressReporter
from modules.observing import Observer
from modules.element import Element
from modules.measurement import Measurement
from modules.global_settings import GlobalSettings

from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5.QtCore import QSettings
from PyQt5.QtGui import QWheelEvent

NumSpinBox = Union[QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox]

# Potku uses QSettings to store non-portable settings such as window
# geometries and recently opened requests.
# For settings that can be ported from one installation to another, use global
# settings or PropertySavingWidget
# Note: the name 'Potku 2.0' is a relic from earlier development. Even if
# Potku's version number is changed to 2.1 or something, this key should remain
# the same so users can have the same settings they had previously. Only change
# this after a more major update (i.e. 'Potku 3')
_SETTINGS_KEY = ("JYU-IBA", "Potku 2.0")


def _get_potku_settings() -> QSettings:
    """Returns a QSettings object that can be used to store Potku's
    settings.
    """
    return QSettings(*_SETTINGS_KEY)


def remove_potku_setting(key: Optional[str] = None):
    """Removes a value stored for the given key. If key is None, all settings
    stored by Potku are removed.

    Args:
        key: a string identifying a value
    """
    if key is None:
        raise NotImplementedError("Removing all settings not yet implemented.")
    settings = _get_potku_settings()
    settings.remove(key)


def get_potku_setting(key: str, default_value, value_type=None) -> Any:
    """Returns a value that has been stored for the given key.

    Args:
        key: a string identifying a stored value
        default_value: value that is returned if the key has not been stored
        value_type: type of return value

    Return:
        object of type 'value_type'
    """
    settings = _get_potku_settings()
    if value_type is None:
        return settings.value(key, default_value)
    return settings.value(key, default_value, value_type)


def set_potku_setting(key: str, value: Any):
    """Stores a value for the given key. If a value has been previously stored
    with this key, the old value is overwritten.

    Args:
        key: a string identifying the value to be stored
        value: value to be stored
    """
    settings = _get_potku_settings()
    settings.setValue(key, value)


def get_ui_dir() -> Path:
    """Returns absolute path to directory that contains .ui files.
    """
    return gf.get_root_dir() / "ui_files"


def get_icon_dir() -> Path:
    """Returns absolute path to directory that contains Potku's icons.
    """
    return gf.get_root_dir() / "ui_icons"


def get_preset_dir(settings: Optional[GlobalSettings]) -> Optional[Path]:
    """Returns the absolute path to directory that contains presets.
    """
    if settings is None:
        return None
    return settings.get_config_dir() / "presets"


if platform.system() == "Darwin":
    # Mac needs event processing to display changes in the status bar
    # FIXME calling processEvents may cause problems with signal handling so
    #   we should get rid of this. Getting rid of this requires moving all
    #   long running operations away from the main thread.
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
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        res = func(*args, **kwargs)
        _process_event_loop()
        return res
    return wrapper


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
    # TODO this class could be a generic reporter instead of one that
    #   only updates a ProgressBar
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
    # TODO this class could itself be a ProgressReporter that takes a
    #   statusbar as its parameter

    @process_event_loop
    def __init__(self, statusbar: QtWidgets.QStatusBar, autoremove=True):
        """Initializes a new StatusBarHandler.

        Args:
            statusbar: PyQt statusbar
            autoremove: automatically hides the progress bar when its
                surpasses 99
        """
        # TODO remove previous progress bars
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
        self.reporter.report(0)

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
        # TODO let the progress bar stay on screen for a while after hitting 100
        try:
            self.progress_bar.valueChanged.disconnect(self.__check_progress)
        except (TypeError, AttributeError):
            # Signal was either already disconnected or progress bar was None
            pass
        self.reporter.report(100)
        if self.statusbar is not None:
            self.statusbar.removeWidget(self.progress_bar)
        if self.progress_bar is not None:
            self.progress_bar.hide()


def change_visibility(qwidget: QtWidgets.QWidget, visibility=None, key=None):
    """Changes the visibility of given QWidget. Visibility is stored
    to QSettings object if a key is given.

    Args:
        qwidget: QWidget whose visibility will be set
        visibility: boolean or None. If None, current visibility will be set
            to opposite of current visibility.
        key: key that is used to store the visibility in a QSettings object.
    """
    if visibility is None:
        visibility = not qwidget.isVisible()
    qwidget.setVisible(visibility)
    if key is not None:
        set_potku_setting(key, visibility)


def change_arrow(qbutton: QtWidgets.QPushButton, arrow=None):
    """Changes the arrow icon on a QPushButton.

    Args:
        qbutton: QPushButton
        arrow: either '<', '>' or None. If value is None, current arrow icon
            is switched.
    """
    if arrow is None:
        arrow = "<" if qbutton.text() == ">" else ">"
    elif arrow not in "><":
        raise ValueError(f"change_arrow function expected either a '<', "
                         f"'>' or None, '{arrow}' given.")
    qbutton.setText(arrow)


def load_isotopes(symbol: str, combobox: QtWidgets.QComboBox,
                  current_isotope=None, show_std_mass=False):
    """Load isotopes of given element into given combobox.

    Args:
        symbol: string representation of an element, e.g. 'He'.
        combobox: QComboBox to which items are added.
        current_isotope: Current isotope to select it on combobox by default.
        show_std_mass: if True, std mass is added as the first element
    """
    combobox.clear()
    # Sort isotopes based on their natural abundance
    isotopes = Element.get_isotopes(symbol, include_st_mass=show_std_mass)

    for idx, iso in enumerate(isotopes):
        if iso["element"].isotope is None:
            # Standard mass option
            txt = f"{round(iso['element'].get_mass())} (st. mass)"
        else:
            # Isotope specific options
            txt = f"{iso['element'].isotope} ({round(iso['abundance'], 3)}%)"
        combobox.addItem(txt, userData=iso)
        if current_isotope == iso["element"].isotope:
            combobox.setCurrentIndex(idx)


class GUIObserver(Observer, abc.ABC, metaclass=QtABCMeta):
    """GUIObserver is an implementation of the modules.observing.Observer
    class. It is an abstract class that defines three abstract handler
    methods that are invoked when an observable publishes some message.

    The handler methods will be executed in the main thread so it is safe to
    alter GUI elements within those methods.

    GUIObserver can be used to observe both modules.observing.Observables and
    rx.Observables.
    """
    class Signaller(QtCore.QObject):
        on_next_sig = QtCore.pyqtSignal(object)
        on_error_sig = QtCore.pyqtSignal(object)
        on_completed_sig = QtCore.pyqtSignal([], [object])

    def __init__(self):
        """Initializes a new GUIObserver.
        """
        # The GUIObserver itself is not a QObject so we use a helper class to
        # connect the signals. Note: this may change in the future.
        self.__signaller = GUIObserver.Signaller()
        self.__signaller.on_next_sig.connect(self.on_next_handler)
        self.__signaller.on_error_sig.connect(self.on_error_handler)

        # rx.observables do not report anything when they complete, but
        # modules.observing.Observables do so we have to have an overloaded
        # signal.
        self.__signaller.on_completed_sig.connect(self.on_completed_handler)
        self.__signaller.on_completed_sig[object].connect(
            self.on_completed_handler)

    @abc.abstractmethod
    def on_next_handler(self, msg):
        """Method that is invoked when an observable reports a new message.
        """
        pass

    @abc.abstractmethod
    def on_error_handler(self, err):
        """Method that is invoked when an observable reports an error.
        """
        pass

    @abc.abstractmethod
    def on_completed_handler(self, msg=None):
        """Method that is invoked when an observable reports that is has
        completed its process.
        """
        pass

    def on_next(self, msg):
        """Inherited from modules.observing.Observable.
        """
        self.__signaller.on_next_sig.emit(msg)

    def on_error(self, err):
        """Inherited from modules.observing.Observable.
        """
        self.__signaller.on_error_sig.emit(err)

    def on_completed(self, msg=None):
        """Inherited from modules.observing.Observable.
        """
        if msg is not None:
            self.__signaller.on_completed_sig[object].emit(msg)
        else:
            self.__signaller.on_completed_sig.emit()


def fill_cuts_treewidget(measurement: Measurement,
                         root: QtWidgets.QTreeWidgetItem,
                         use_elemloss: bool = False):
    """Fill QTreeWidget with cut files.

    Args:
        measurement: Measurement object
        root: root node of the QTreeWidget.
        use_elemloss: A boolean representing whether to add elemental losses.
    """
    cuts, cuts_elemloss = measurement.get_cut_files()

    def text_func(fp: Path):
        return fp.name

    fill_tree(root, cuts, text_func=text_func)

    if use_elemloss:
        elem_root = QtWidgets.QTreeWidgetItem(["Elemental Losses"])
        fill_tree(elem_root, cuts_elemloss, text_func=text_func)
        root.addChild(elem_root)

    root.setExpanded(True)


def fill_tree(root: QtWidgets.QTreeWidgetItem, data: Iterable[Any],
              data_func: Callable = lambda x: x, text_func: Callable = str,
              column=0):
    """Fills a QTreeWidget with given data.

    Args:
        root: root node to fill in the QTreeWidget.
        data: data used to fill the widget.
        data_func: function applied to each data point as they are added to
            the tree.
        text_func: function that determines how a data point is represented
            in the GUI.
        column: column number to use in the QTreeWidget.
    """
    for datapoint in data:
        item = QtWidgets.QTreeWidgetItem()
        item.setText(column, text_func(datapoint))
        item.setData(column, QtCore.Qt.UserRole, data_func(datapoint))
        root.addChild(item)


def block_treewidget_signals(func: Callable):
    """Decorator that blocks signals from an instance's treeWidget so that
    the tree can be edited.
    """
    @functools.wraps(func)
    def wrapper(instance, *args, **kwargs):
        instance.treeWidget.blockSignals(True)
        res = func(instance, *args, **kwargs)
        instance.treeWidget.blockSignals(False)
        return res
    return wrapper


def fill_combobox(combobox: QtWidgets.QComboBox, values: Iterable[Any],
                  text_func: Callable = str, block_signals=False):
    """Fills the combobox with given values. Stores the values as user data
    and displays the string representations as item labels. Previous items
    are removed from the combobox.

    Args:
        combobox: combobox to fill
        values: collection of values to be added to the combobox
        text_func: function that detenmines how values are presented in
            text form
        block_signals: whether signals from combobox are blocked during filling
    """
    if block_signals:
        combobox.blockSignals(True)
    combobox.clear()
    for value in values:
        combobox.addItem(text_func(value), userData=value)
    if block_signals:
        combobox.blockSignals(False)


def set_btn_group_data(button_group: QtWidgets.QButtonGroup, values:
                       Iterable[Any]):
    """Adds a data_item attribute for all buttons in the button group. The
    value of the data_item is taken from the given values.

    No buttons are added or removed. button_group has to contain the same
    number of buttons as there are values.
    """
    btns = button_group.buttons()
    if len(btns) != len(values):
        raise ValueError(
            "Button group and data must have the same number of items")
    for btn, value in zip(button_group.buttons(), values):
        btn.setText(str(value))
        btn.data_item = value


def set_min_max_handlers(lower_box: NumSpinBox, upper_box: NumSpinBox,
                         min_diff=0):
    """Adds valueChanged handlers that automatically adjust the minimum
    and maximum values of spin boxes. Automatically adjusts current values
    if lower_box has a higher value than upper_box.

    Args:
        lower_box: spin box whose current value should be the minimum value of
            the upper_box.
        upper_box: spin box whose current value should be the maximum value of
            the lower_box
        min_diff: minimum difference allowed between the two values.
    """
    lower_box.setMaximum(upper_box.value() + min_diff)
    upper_box.setMinimum(lower_box.value() - min_diff)
    lower_box.valueChanged.connect(lambda x: upper_box.setMinimum(x + min_diff))
    upper_box.valueChanged.connect(lambda x: lower_box.setMaximum(x - min_diff))


def disable_widget(func: Callable):
    """Decorator that disables a QWidget for the duration of the function.
    The decorated function must take the QWidget as its first argument (for
    example decorating an instance method works fine).
    """
    @functools.wraps(func)
    def wrapper(qwidget: QtWidgets.QWidget, *args, **kwargs):
        qwidget.setEnabled(False)
        try:
            return func(qwidget, *args, **kwargs)
        finally:
            qwidget.setEnabled(True)
    return wrapper


def disable_scrolling_in_spin_boxes() -> None:
    """Disables mouse wheel scrolling in all QSpinBoxes,
    QDoubleSpinBoxes and ScientificSpinBoxes.
    """
    def ignore_wheel_event(
            _: QtWidgets.QAbstractSpinBox, e: QWheelEvent) -> None:
        e.ignore()

    QtWidgets.QAbstractSpinBox.wheelEvent = ignore_wheel_event
