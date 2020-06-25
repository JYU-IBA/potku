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

import abc
import functools

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


def draw_and_flush(func):
    """Decorator function that draws and flushes the canvas object of the
    caller.
    """
    @functools.wraps(func)
    def wrapper(canvas_wrapper: GraphWrapper, *args, **kwargs):
        res = func(*args, **kwargs)
        canvas_wrapper.canvas.draw()
        canvas_wrapper.canvas.flush_events()
        return res
    return wrapper


class GraphWrapper(abc.ABC):
    def __init__(self, canvas, axes):
        self.canvas = canvas
        self.axes = axes

    @abc.abstractmethod
    def update_graph(self, *args, **kwargs):
        pass


class VerticalLimits(GraphWrapper):
    """Draws vertical limit lines on the given axes.
    """
    _LINE_STYLE = "--"

    def __init__(self, canvas, axes, x0: float, x1: float, *colors):
        GraphWrapper.__init__(self, canvas, axes)
        self._visible = True

        col = tuple(colors)
        if not col:
            x0_col, x1_col = "blue", "blue"
        elif len(col) == 1:
            x0_col, x1_col = col[0], col[0]
        else:
            x0_col, x1_col = col

        self._limit_lines = (
            self.axes.axvline(
                x=x0, linestyle=self._LINE_STYLE, color=x0_col),
            self.axes.axvline(
                x=x1, linestyle=self._LINE_STYLE, color=x1_col)
        )

    def update_graph(self, x0: float, x1: float):
        self._limit_lines[0].set_xdata([x0])
        self._limit_lines[1].set_xdata([x1])

    def get_range(self) -> Tuple[float, float]:
        xs = tuple(line.get_xdata()[0] for line in self._limit_lines)
        return tuple(sorted(xs))

    def set_visible(self, b: bool):
        self._visible = b
        linestyle = self._LINE_STYLE if b else "None"
        for line in self._limit_lines:
            line.set_linestyle(linestyle)

    def is_visible(self):
        return self._visible


class AlternatingLimits(VerticalLimits):
    """Draws limit lines in an alternating pattern.
    """
    def __init__(self, canvas, axes, x0: float, x1: float, *colors):
        VerticalLimits.__init__(self, canvas, axes, x0, x1, *colors)
        self._next_limit_idx = 1

    def update_graph(self, x: float):
        self._next_limit_idx = abs(1 - self._next_limit_idx)
        self._limit_lines[self._next_limit_idx].set_xdata([x])
