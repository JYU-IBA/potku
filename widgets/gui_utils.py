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

from pathlib import Path
from typing import Iterable
from typing import Optional

from modules.observing import ProgressReporter
from modules.observing import Observer
from modules.element import Element

from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5.QtCore import QSettings

# TODO check the preferred name for the org
# Potku uses QSettings to store non-portable settings such as window
# geometries and recently opened requests.
# For settings that can be ported from one installation to another, use global
# settings or PropertySavingWidget
_SETTINGS_KEY = ("JYU-IBA", f"Potku {__version__}")


def _get_potku_settings() -> QSettings:
    """Returns a QSettings object that can be used to store Potku's
    settings.
    """
    # TODO decide on app name given. Either with or without the version number:
    #   'Potku' => all versions of Potku use the same settings
    #   'Potku 2' => all Potku versions 2.* use the same settings
    #   'Potku 2.0' (currently in use) => Potku only uses the settings that
    #       strictly match the version
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


def get_potku_setting(key: str, default_value, value_type=None):
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


def set_potku_setting(key: str, value):
    """Stores a value for the given key. If a value has been previously stored
    with this key, the old value is overwritten.

    Args:
        key: a string identifying the value to be stored
        value: value to be stored
    """
    # TODO check which types are supported by QSettings
    settings = _get_potku_settings()
    settings.setValue(key, value)


if platform.system() == "Darwin":
    # Mac needs event processing to display changes in the status bar
    # TODO calling processEvents may cause problems with signal handling so
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


# TODO this is for debugging purposes. Remove or comment out this code once
#   it is no longer needed
_debug_progress = False
if _debug_progress:
    from collections import defaultdict
    _p_bars = defaultdict(list)
else:
    _p_bars = None


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
        # TODO remove progress_bar argument and just make this a generic
        #  reporter that does its reporting in main thread
        @process_event_loop
        def __update_func(value):
            # Callback function that will be connected to the signal
            if progress_bar is not None:
                if _p_bars is not None:
                    # TODO for debugging purposes save values to a dict
                    #   so it easier to inspect them later
                    vals = _p_bars.get(progress_bar, [-1])
                    if vals[-1] > value or value > 100 or value < 0:
                        print("Value was smaller than previous value or out "
                              "of range.")
                    _p_bars[progress_bar].append(value)

                # TODO make transitions smoother when gaps between values are
                #   big
                progress_bar.setValue(value)

        self.signaller = self.Signaller()
        ProgressReporter.__init__(self, self.signaller.sig.emit)
        self.signaller.sig.connect(__update_func)


class StatusBarHandler:
    """Helper class to show, hide and update a progress bar in the
    given statusbar.
    """
    # TODO make this a ProgressReporter

    @process_event_loop
    def __init__(self, statusbar: QtWidgets.QStatusBar, autoremove=True):
        """Initializes a new StatusBarHandler.

        Args:
            statusbar: PyQt statusbar
            autoremove: automatically hides the progress bar when its
                surpasses 99
        """
        # TODO could also use a remove_at parameter that defines when
        #      the progress bar is removed
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


def load_isotopes(symbol, combobox, current_isotope=None, show_std_mass=False):
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


def fill_cuts_treewidget(measurement, treewidget, use_elemloss=False,
                         checked_files=None):
    """ Fill QTreeWidget with cut files.

    Args:
        measurement: Measurement object
        treewidget: A QtGui.QTreeWidget, where cut files are added to.
        use_elemloss: A boolean representing whether to add elemental losses.
        checked_files: A list of previously checked files.
    """
    if checked_files is None:
        checked_files = []
    treewidget.clear()
    cuts, cuts_elemloss = measurement.get_cut_files()
    for cut in cuts:
        item = QtWidgets.QTreeWidgetItem([cut])
        item.directory = Path(measurement.directory, measurement.directory_cuts)
        item.file_name = cut
        if not checked_files or item.file_name in checked_files:
            item.setCheckState(0, QtCore.Qt.Checked)
        else:
            item.setCheckState(0, QtCore.Qt.Unchecked)
        treewidget.addTopLevelItem(item)
    if use_elemloss and cuts_elemloss:
        elem_root = QtWidgets.QTreeWidgetItem(["Elemental Losses"])
        for elemloss in cuts_elemloss:
            item = QtWidgets.QTreeWidgetItem([elemloss])
            item.directory = Path(
                measurement.directory,
                measurement.directory_composition_changes,
                "Changes")
            item.file_name = elemloss
            if item.file_name in checked_files:
                item.setCheckState(0, QtCore.Qt.Checked)
            else:
                item.setCheckState(0, QtCore.Qt.Unchecked)
            elem_root.addChild(item)
        treewidget.addTopLevelItem(elem_root)


def block_treewidget_signals(func):
    """Decorator that blocks signals from an instance's treeWidget so that
    the tree can be edited.
    """
    def wrapper(instance, *args, **kwargs):
        instance.treeWidget.blockSignals(True)
        res = func(instance, *args, **kwargs)
        instance.treeWidget.blockSignals(False)
        return res
    return wrapper


def fill_combobox(combobox: QtWidgets.QComboBox, values: Iterable):
    """Fills the combobox with given values. Stores the values as user data
    and displays the string representations as item labels. Previous items
    are removed from the combobox.
    """
    combobox.clear()
    for value in values:
        combobox.addItem(str(value), userData=value)


def set_btn_group_data(button_group: QtWidgets.QButtonGroup, values: Iterable):
    btns = button_group.buttons()
    if len(btns) != len(values):
        raise ValueError(
            "Button group and data must have the same number of items")
    for btn, value in zip(button_group.buttons(), values):
        btn.setText(str(value))
        btn.data_item = value
