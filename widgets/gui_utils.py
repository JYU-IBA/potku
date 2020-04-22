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

from modules.observing import ProgressReporter
from modules.element import Element

from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5.QtCore import QSettings

# TODO check the preferred name for the org
_SETTINGS_KEY = ("JYU-IBA", f"Potku {__version__}")


def get_potku_settings() -> QSettings:
    """Returns a QSettings object that can be used to store Potku's
    settings.
    """
    # TODO decide on app name given. Either with or without the version number:
    #   'Potku' => all versions of Potku use the same settings
    #   'Potku 2' => all Potku versions 2.* use the same settings
    #   'Potku 2.0' (currently in use) => Potku only uses the settings that
    #       strictly match the version
    return QSettings(*_SETTINGS_KEY)


def remove_potku_settings(key=None):
    """Removes settings stored for the given key.
    """
    # TODO if key is 'None', this should remove all settings stored by Potku
    settings = get_potku_settings()
    settings.remove(key)


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
        settings = get_potku_settings()
        settings.setValue(key, visibility)


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
    # TODO this function could be moved to gui_utils
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


def fill_cuts_treewidget(measurement, treewidget, use_elemloss=False,
                         checked_files=None):
    """ Fill QTreeWidget with cut files.

    Args:
        measurement: Measurement object
        treewidget: A QtGui.QTreeWidget, where cut files are added to.
        use_elemloss: A boolean representing whether to add elemental
                      losses.
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
