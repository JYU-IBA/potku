# coding=utf-8
"""
Created on 22.06.2020

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

This module contains various utility functions for dealing with MatPlotLib
graphs.
"""

__author__ = "Juhani Sundell"
__version__ = "2.0"

from typing import Tuple

from PyQt5.QtWidgets import QToolButton
from PyQt5.QtWidgets import QLabel


def format_coord(x: float, y: float) -> str:
    """Format mouse coordinates to string.

    Args:
        x: X coordinate.
        y: Y coordinate.

    Return:
        Formatted text.
    """
    x_part = f"\nx:{x:1.2f},"
    y_part = f"\ny:{y:1.4f}"
    return x_part + y_part


def format_x(x: float, _) -> str:
    """Format mouse coordinates.

    Args:
        x: X coordinate.
        _: unused y coordinate.

    Return:
        Formatted text.
    """
    return f"x:{x:1.4f}"


def get_toolbar_elements(toolbar, drag_callback=None, zoom_callback=None) -> \
        Tuple[QLabel, QToolButton, QToolButton]:
    """Returns tool label, drag button and zoom button from given
    NavigationToolBar.
    """
    # Toolbar element indexes:
    #   24  tool_label
    #   12  drag button
    #   14  zoom button
    #   4   home    (not currently returned)
    children = toolbar.children()
    tool_lbl, drag_btn, zoom_btn = children[24], children[12], children[14]
    if drag_callback is not None:
        drag_btn.clicked.connect(drag_callback)
    if zoom_callback is not None:
        zoom_btn.clicked.connect(zoom_callback)
    return tool_lbl, drag_btn, zoom_btn
