# coding=utf-8
"""
Created on 3.5.2013
Updated on 23.5.2013

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) Jarkko Aalto, Timo Konu, Samuli Kärkkäinen, Samuli Rahkonen and
Miika Raunio

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
__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen \n " \
             "Samuli Rahkonen \n Miika Raunio"
__versio__ = "1.0"

import os
import widgets.gui_utils as gutils

from pathlib import Path
from PyQt5 import QtGui, QtCore, QtWidgets


class IconManager:
    """Icon manager class to handle all icons for the program.
    """

    def __init__(self):
        """Inits IconManager class.
        """
        self.__icons = {}
        self.__load_icons()

    def get_icon(self, icon_name: str) -> QtGui.QIcon:
        """Get specific icon.

        Args:
            icon_name: String representing icon file name.

        Return:
            Returns QtGui.QIcon of icon_name and empty icon if not found.
        """
        return self.__icons.get(icon_name, QtGui.QIcon())

    def set_icon(self, target, icon_name: str, size=(20, 20)):
        """Set icon (icon_name) to target.

        Args:
            target: QtGui element that has icon. (setIcon method)
            icon_name: String representing filename of the icon.
            size: Icon size.
        """
        icon = self.get_icon(icon_name)
        target.setIcon(icon)
        if type(target) != QtWidgets.QAction:
            target.setIconSize(QtCore.QSize(size[0], size[1]))

    def __load_icons(self):
        """Load icons from ui_icons directory.
        """
        icon_directory_potku = gutils.get_icon_dir() / "potku"
        icon_directory_reinhardt = gutils.get_icon_dir() / "reinhardt"
        self.__load_icons_from_files(icon_directory_reinhardt)
        self.__load_icons_from_files(icon_directory_potku)

    def __load_icons_from_files(self, directory: Path):
        """Load icons from provided icon list.

        Args:
            directory: String representing directory where the icons are at.
        """
        with os.scandir(directory) as scdir:
            for entry in scdir:
                path = Path(entry.path)
                if path.is_file() and path.suffix != ".txt":
                    icon = QtGui.QIcon()
                    icon.addPixmap(
                        QtGui.QPixmap(str(path)), QtGui.QIcon.Normal,
                        QtGui.QIcon.Off)
                    self.__icons[path.name] = icon


def get_potku_icon(name: str) -> QtGui.QIcon:
    return QtGui.QIcon(str(gutils.get_icon_dir() / "potku" / name))


def get_reinhardt_icon(name: str) -> QtGui.QIcon:
    return QtGui.QIcon(str(gutils.get_icon_dir() / "reinhardt" / name))
