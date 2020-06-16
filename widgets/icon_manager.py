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

from os import listdir, path
from PyQt5 import QtGui, QtCore, QtWidgets


class IconManager:
    """Icon manager class to handle all icons for the program.
    """

    def __init__(self):
        """Inits IconManager class.
        """
        self.__icons = {}
        self.__load_icons()

    def get_icon(self, icon_name):
        """Get specific icon.

        Args:
            icon_name: String representing icon file name.

        Return:
            Returns QtGui.QIcon of icon_name and empty icon if not found.
        """
        return self.__icons.get(icon_name, QtGui.QIcon())

    def set_icon(self, target, icon_name, size=(20, 20)):
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
        icon_directory = "ui_icons"
        icon_directory_potku = path.join(icon_directory, "potku")
        icon_directory_reinhardt = path.join(icon_directory, "reinhardt")
        self.__load_icons_from_files(icon_directory_reinhardt)
        self.__load_icons_from_files(icon_directory_potku)

    def __load_icons_from_files(self, directory):
        """Load icons from provided icon list.

        Args:
            directory: String representing directory where the icons are at.
        """
        file_list = [file for file in listdir(directory)
                     if path.isfile(path.join(directory, file))
                     and path.splitext(file)[1] != ".txt"]
        for icon_file in file_list:
            icon = QtGui.QIcon()
            icon.addPixmap(QtGui.QPixmap(path.join(directory, icon_file)),
                           QtGui.QIcon.Normal,
                           QtGui.QIcon.Off)
            self.__icons[icon_file] = icon
