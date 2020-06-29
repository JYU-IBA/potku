# coding=utf-8
"""
Created on 27.06.2020

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

import os

import widgets.binding as bnd
import widgets.gui_utils as gutils

from pathlib import Path
from typing import Optional
from typing import Callable
from typing import List
from typing import Any

from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QObject
from PyQt5.QtCore import QEvent
from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QFocusEvent
from PyQt5 import uic


class PresetWidget(QWidget, bnd.PropertyBindingWidget,
                   metaclass=gutils.QtABCMeta):

    PRESET_SUFFIX = ".preset"
    MAX_COUNT = 10
    NONE_TEXT = "<None>"
    preset = bnd.bind("preset_combobox")
    status_msg = bnd.bind("status_label")

    save_file = pyqtSignal(Path)
    load_file = pyqtSignal(Path)

    def __init__(self, folder: Path, prefix: str, enable_load_btn=False):
        """Initializes a new PresetWidget.

        Args:
            folder: folder where preset files are stored
            prefix: default prefix for preset files
            enable_load_btn: whether 'Load preset' file is shown or not.
                If not, load_file signal is fired when the combobox
                index changes.
        """
        QWidget.__init__(self)
        uic.loadUi(gutils.get_ui_dir() / "ui_preset_widget.ui", self)

        self._folder = folder
        self._prefix = prefix

        self.save_btn: QPushButton
        self.load_btn: QPushButton
        self.preset_combobox: QComboBox

        self.save_btn.clicked.connect(self._emit_save_file)

        self._load_btn_enabled = enable_load_btn
        self.load_btn.setVisible(self._load_btn_enabled)
        self.load_btn.setEnabled(self._load_btn_enabled)
        if self._load_btn_enabled:
            self.load_btn.clicked.connect(
                lambda: self._emit_file_to_load(self.preset))

        self.status_label.setVisible(False)

        self.preset_combobox: QComboBox
        self.preset_combobox.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.preset_combobox.currentIndexChanged.connect(self._index_changed)

        self._action_rename = QAction(self.preset_combobox)
        self._action_rename.setText("Rename")
        self._action_rename.triggered.connect(self._rename_file)

        self._action_remove = QAction(self.preset_combobox)
        self._action_remove.setText("Remove")
        self._action_remove.triggered.connect(self._remove_file)

        self.preset_combobox.addAction(self._action_rename)
        self.preset_combobox.addAction(self._action_remove)

        self.preset_combobox.installEventFilter(self)

        self.load_files()
        self._activate_actions(self.preset)

    def _index_changed(self):
        """Event handler for index changes in the combobox. Actions are
        disabled if the selected item is 'None'. If 'Load preset' button
        is not enabled, this will also emit a load_file signal.
        '"""
        self.set_status_msg("")
        preset = self.preset
        self._activate_actions(preset)
        if not self._load_btn_enabled:
            self._emit_file_to_load(preset)

    def _activate_actions(self, preset: Optional[Path]):
        """Activates or deactives actions depending on whether the given
        preset is None or not.
        """
        self._action_remove.setEnabled(preset is not None)
        self._action_rename.setEnabled(preset is not None)

    def _emit_file_to_load(self, preset: Optional[Path]):
        """Emits a load file signal if the given preset is not 'None'.
        """
        if preset is not None:
            self.load_file.emit(preset)

    def _emit_save_file(self):
        """Emits save_file signal if new file name can be generated.
        """
        next_file = self.get_next_available_file(
            starting_index=self.preset_combobox.count() - 1)
        if next_file is None:
            self.set_status_msg("Could not generate a name for preset.")
        else:
            self.save_file.emit(next_file)

    def load_files(self, max_count=MAX_COUNT, selected: Optional[Path] = None):
        """Loads preset files to combobox.

        Args:
            max_count: maximum number of files to load
            selected: path to a file that will be selected after loading
        """
        def text_func(fp: Optional[Path]):
            if fp is None:
                return PresetWidget.NONE_TEXT
            return fp.stem

        preset_files = PresetWidget.get_preset_files(
            self._folder, max_count, keep=selected)
        if not self._load_btn_enabled:
            # If load button is not used, add 'None' as the first element in
            # the combobox
            preset_files = [None, *preset_files]

        gutils.fill_combobox(
            self.preset_combobox, preset_files, text_func=text_func,
            block_signals=True)
        self.preset = selected

    def _rename_file(self):
        """Activates edit if preset is selected.
        """
        self.preset_combobox: QComboBox
        self.preset_combobox.setEditable(self.preset is not None)

    def eventFilter(self, source: QObject, event: QEvent) -> bool:
        """Filters combobox events. If combobox is currently editable,
        capture FocusOut event and try to rename selected file.
        """
        self.preset_combobox: QComboBox
        if source is self.preset_combobox and isinstance(event, QFocusEvent):
            if self.preset_combobox.isEditable():
                cur_txt = self.preset_combobox.currentText()
                self.preset_combobox.setEditable(False)
                try:
                    cur_preset = self.preset
                    new_file = Path(
                        self._folder, f"{cur_txt}{PresetWidget.PRESET_SUFFIX}")
                    if new_file != cur_preset and self.is_valid_preset(
                            self._folder, new_file):
                        cur_preset.rename(new_file)
                        self.load_files(selected=new_file)
                except OSError as e:
                    self.set_status_msg(f"Failed to rename preset: {e}")
        return super().eventFilter(source, event)

    def _remove_file(self):
        """Removes file with a confirmation.
        """
        file = self.preset
        if file is None:
            return
        reply = QMessageBox.question(
            self, "Delete preset", "Delete selected preset?",
            QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Yes)

        if reply == QMessageBox.Yes:
            try:
                file.unlink()
            except OSError as e:
                self.set_status_msg(f"Failed to remove preset: {e}")
            self.load_files()
            self._activate_actions(self.preset)

    def set_status_msg(self, msg: Any):
        """Sets the status message and shows or hides the label.
        """
        self.status_msg = msg
        self.status_label.setVisible(bool(msg))

    @classmethod
    def add_preset_widget(cls, folder: Path, prefix, add_func: Callable,
                          save_callback: Optional[Callable] = None,
                          load_callback: Optional[Callable] = None) -> \
            "PresetWidget":
        """Creates a PresetWidget, adds it to a parent widget by calling the
        add_func and connects save and load callbacks if they are provided.
        Returns the created widget.
        """
        widget = cls(folder, prefix)
        add_func(widget)
        if save_callback is not None:
            widget.save_file.connect(save_callback)
        if load_callback is not None:
            widget.load_file.connect(load_callback)
        return widget

    def get_next_available_file(self, starting_index=0, max_iterations=100) \
            -> Optional[Path]:
        """Returns the next available file name or None, if no available
        file name was found within maximum number of iterations.
        """
        # TODO this could be generalized and moved to general_functions module
        for i in range(starting_index, max_iterations):
            fname = f"{self._prefix}-{i + 1:03}{PresetWidget.PRESET_SUFFIX}"
            fpath = self._folder / fname
            if not fpath.exists():
                return fpath
        return None

    @staticmethod
    def get_preset_files(folder: Path, max_count: int = MAX_COUNT,
                         keep: Optional[Path] = None) -> List[Path]:
        """Returns a sorted list of .preset files from the given folder.

        Args:
            folder: folder path
            max_count: maximum number of files to return
            keep: file that is guaranteed to be in the list as long as it is
                valid .preset file
        """
        if PresetWidget.is_valid_preset(folder, keep) and keep.is_file():
            files = [keep]
        else:
            files = []
        try:
            with os.scandir(folder) as scdir:
                for entry in scdir:
                    if len(files) >= max_count:
                        break
                    path = Path(entry.path)
                    if PresetWidget.is_valid_preset(folder, path) and \
                            path != keep and path.is_file():
                        files.append(path)
        except OSError:
            pass
        return sorted(files)

    @staticmethod
    def is_valid_preset(folder: Path, file: Optional[Path]) -> bool:
        """Checks if the given file is a valid .preset file.
        """
        # TODO might want to add checks for characters that are forbidden
        #   on one platform but allowed on another to ensure the portability
        #   of presets.
        if file is None:
            return False
        if not file.stem:
            return False
        if file.suffix != PresetWidget.PRESET_SUFFIX:
            return False
        return file.resolve().parent == folder.resolve()

