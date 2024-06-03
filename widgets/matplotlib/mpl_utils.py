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
from typing import Dict
from typing import Iterable
from typing import Set
from typing import Optional
from typing import Any
from typing import Hashable
from typing import List
from typing import Callable
from modules.base import Range
from modules.base import StrTuple

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
        Tuple[Optional[QLabel], QToolButton, QToolButton]:
    """Returns tool label, drag button and zoom button from given
    NavigationToolBar.
    """
    # Toolbar element indexes:
    #   24  tool_label  (not always present)
    #   12  drag button
    #   14  zoom button
    #   4   home    (not currently returned)
    children = toolbar.children()
    try:
        tool_lbl = children[24]
    except IndexError:
        tool_lbl = None
    drag_btn, zoom_btn = children[12], children[14]
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
    def wrapper(canvas_wrapper: Any, *args, **kwargs):
        res = func(canvas_wrapper, *args, **kwargs)
        # TODO using getattr here as this function could be used by classes
        #   other than GraphWrapper. If in the future all plotting is done
        #   via GraphWrapper class, this should just be a regular attribute
        #   check
        if isinstance(canvas_wrapper, GraphWrapper):
            if getattr(canvas_wrapper, "do_flush", False):
                canvas_wrapper.canvas.draw()
                canvas_wrapper.canvas.flush_events()
        else:
            canvas_wrapper.canvas.draw()
            canvas_wrapper.canvas.flush_events()
        return res

    return wrapper


class GraphWrapper(abc.ABC):
    """Class that wraps Matplotlib canvas and axes and draws plots on them.
    """

    def __init__(self, canvas, axes, flush=True):
        """Initializes a new GraphWrapper.
        Args:
            canvas: mpl canvas
            axes: mpl axes
            flush: whether canvas.draw and canvas.flush_events are called
                after every function that update graph
        """
        self.canvas = canvas
        self.axes = axes
        self.do_flush = flush

    @abc.abstractmethod
    def update_graph(self, *args, **kwargs):
        pass


class VerticalLimits(GraphWrapper):
    """Draws two vertical limit lines on the given axes.
    """
    DEFAULT_LINESTYLE = "--"
    _DEFAULT_X = 0.0
    _DEFAULT_COLOR = "blue"

    def __init__(
            self, canvas, axes, xs: Optional[Range] = None,
            colors: Optional[StrTuple] = None, **kwargs):
        """Initializes a new VerticalLimits object

        Args:
            canvas: Matplotlib canvas
            axes: Matplotlib axes
            xs: tuple of values that define the position of the limit lines
                on the x axis. If None or empty, default value is used. If
                only one value is provided, both lines will be drawn at that
                x coordinate. If more than two values are provided, rest are
                discarded.
            colors: tuple of strings that define the colors of each limit line.
                Values are unpacked in the same way as x coordinates.
        """
        GraphWrapper.__init__(self, canvas, axes, **kwargs)
        self._visible = True
        self._limit_lines = self._init_draw(xs, colors)

    @draw_and_flush
    def _init_draw(self, xs, colors):
        x0, x1 = self._unpack_args(xs, VerticalLimits._DEFAULT_X)
        x0_col, x1_col = self._unpack_args(
            colors, VerticalLimits._DEFAULT_COLOR)

        return (
            self.axes.axvline(
                x=x0, linestyle=self.DEFAULT_LINESTYLE, color=x0_col),
            self.axes.axvline(
                x=x1, linestyle=self.DEFAULT_LINESTYLE, color=x1_col)
        )

    @staticmethod
    def _unpack_args(tpl: Tuple, default_value: Any) -> Tuple[Any, Any]:
        """Helper method for unpacking tuple arguments.
        """
        if not tpl:
            return default_value, default_value
        elif len(tpl) == 1:
            return tpl[0], tpl[0]
        # Any extra parameters are discarded
        x0, x1, *_ = tpl
        return x0, x1

    @draw_and_flush
    def update_graph(self, x0: float, x1: float):
        """Updates the x coordinates of both limit lines.
        """
        self._limit_lines[0].set_xdata([x0])
        self._limit_lines[1].set_xdata([x1])

    def get_range(self) -> Range:
        """Returns the x-axis values of each limit line.
        """
        x0, xn = sorted([line.get_xdata()[0] for line in self._limit_lines])
        return x0, xn

    @draw_and_flush
    def set_visible(self, b: bool):
        """Sets the visibility of the limit lines.
        """
        self._visible = b
        linestyle = self.DEFAULT_LINESTYLE if b else "None"
        for line in self._limit_lines:
            line.set_linestyle(linestyle)

    @draw_and_flush
    def set_alpha(self, alpha: float):
        for line in self._limit_lines:
            line.set_alpha(alpha)

    @draw_and_flush
    def remove(self):
        for line in self._limit_lines:
            line.remove()

    def is_visible(self):
        """Returns whether the limit lines are currently visible.
        """
        return self._visible


class AlternatingLimits(VerticalLimits):
    """Draws limit lines in an alternating pattern.
    """

    def __init__(self, *args, **kwargs):
        VerticalLimits.__init__(self, *args, **kwargs)
        self._next_limit_idx = 1

    @draw_and_flush
    def update_graph(self, x: float):
        """Moves the limit line that is next in turn to the position x on the
        x axis.
        """
        self._next_limit_idx = abs(1 - self._next_limit_idx)
        self._limit_lines[self._next_limit_idx].set_xdata([x])


class LineChart(GraphWrapper):
    _DEFAULT_LINESTYLE = "-"

    def __init__(self, canvas, axes, lineargs: Iterable[Dict]):
        GraphWrapper.__init__(self, canvas, axes)
        self._lines = self._init_draw(lineargs)

    @draw_and_flush
    def _init_draw(self, lineargs: Iterable[Dict]) -> Dict:
        def _inner_draw(key, xs, ys, **kwargs):
            line, = self.axes.plot(xs, ys, **kwargs)
            return key, line

        return dict([
            _inner_draw(**kwargs)
            for kwargs in lineargs
        ])

    @staticmethod
    def get_line_args(key: Hashable, xs: List[float], ys: List[float],
                      label_func: Callable = str, **kwargs) -> Dict:
        return {
            "key": key,
            "label": label_func(key),
            "xs": xs,
            "ys": ys,
            **kwargs
        }

    def get_keys(self) -> Set:
        return set(self._lines.keys())

    @draw_and_flush
    def update_graph(self, lineargs: Iterable[Dict]):
        for arg in lineargs:
            line = self._lines[arg["key"]]
            if "xs" in arg:
                line.set_xdata(arg["xs"])
            line.set_ydata(arg["ys"])

    @draw_and_flush
    def hide_lines(self, lines_to_hide: Set):
        for label, line in self._lines.items():
            if label in lines_to_hide:
                line.set_linestyle("None")
            else:
                line.set_linestyle(LineChart._DEFAULT_LINESTYLE)
                
    @draw_and_flush
    def hide_legend(self, legends_to_hide: Set):
        for label, line in self._lines.items():
            if label in legends_to_hide:
                # Underscore in front of a label hides it
                if not line.get_label().startswith("_"):
                    line.set_label("_" + line.get_label())
            else:
                line.set_label(line.get_label().replace("_",""))

    @draw_and_flush
    def set_yscale(self, y_scale: str):
        self.axes.set_yscale(y_scale)
