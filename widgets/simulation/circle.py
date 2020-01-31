# coding=utf-8
"""
Created on 23.7.2018

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2018 Heta Rekilä

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
__author__ = "Heta Rekilä"
__version__ = "2.0"

from PyQt5 import QtGui
from PyQt5 import QtWidgets


class Circle(QtWidgets.QWidget):
    """
    Class to show a circle with certain color.
    """

    def __init__(self, color, size=None):
        """
        Initialize the class.

        Args:
            color: Color of circle, either a QColor object or a string
                   representation of the color (hex code or name)
            size: tuple representing the size of the circle (x, y, width,
                  height)
        """
        super().__init__()
        if isinstance(color, QtGui.QColor):
            self.color = color
        else:
            self.color = QtGui.QColor(color)

        if size is None:
            self.size = (1, 8, 8, 8)
        else:
            self.size = size

    def set_color(self, color):
        """
        Set a new color for the circle.

        Args:
             color: Color of circle, either a QColor object or a string
                    representation of the color (hex code or name)
        """
        if isinstance(color, QtGui.QColor):
            self.color = color
        else:
            self.color = QtGui.QColor(color)
        self.update()

    def paintEvent(self, event):
        """
        Draw the circle.

        Args:
             event: QPaintEvent.
        """
        painter = QtGui.QPainter()
        painter.begin(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setPen(self.color)
        painter.setBrush(self.color)
        painter.drawEllipse(*self.size)

        painter.end()
