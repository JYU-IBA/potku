# coding=utf-8
"""
Created on 23.3.2018
Updated on 1.6.2018

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2018 Severi Jääskeläinen, Samuel Kaiponen, Heta Rekilä and
Sinikka Siironen

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

Adds _views attribute to NavigationToolBar2QT
"""
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä " \
             "\n Sinikka Siironen"
__version__ = "2.0"
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as \
    NavigationToolbar


class NavigationToolBar2QTView(NavigationToolbar):
    """
    Class for adding an attibute to the navigation toolbar class.
    """

    def __init__(self, canvas, main_frame):
        """
        Initializes the NavigationToolBar2QTView object.

        Args:
            canvas: A Canvas object
            main_frame: Main frame for tool bar.
        """
        super().__init__(canvas, main_frame)
        self._views = [[0], [0]]
