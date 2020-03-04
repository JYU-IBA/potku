# coding=utf-8
"""
Created on 28.02.2020

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
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program (file named 'LICENCE').
"""
__author__ = "Juhani Sundell"
__version__ = ""  # TODO

import abc

from matplotlib.figure import Figure


def _draw_and_flush(func):
    """Decorator function that draws and flushes the canvas object of the
    caller.
    """
    def wrapper(*args, **kwargs):
        res = func(*args, **kwargs)
        args[0].canvas.draw()
        args[0].canvas.flush_events()
        return res
    return wrapper


class FigureWrapper(abc.ABC):
    """FigureWrapper wraps around a Figure object and draws graphs on its
    canvas. It also provides a method to update the legend box of the figure.
    """
    # Default keyword arguments that are passed down to Figure and Legend
    # objects unless the caller overrides them
    FIGURE_KWARGS = {
        "figsize": (5.0, 3.0),
        "dpi": 75,
        "tight_layout": True
    }

    LEGEND_KWARGS = {
        "loc": 3,
        "bbox_to_anchor": (1, 0),
        "borderaxespad": 0,
        "prop": {'size': 12}
    }

    def __init__(self, figure=None, facecolor="white", **kwargs):
        if figure is None:
            figure_kwargs = dict(self.FIGURE_KWARGS)
            figure_kwargs.update(kwargs)
            self.figure = Figure(**figure_kwargs)
        else:
            self.figure = figure

        self.figure.patch.set_facecolor(facecolor)
        self.axes = self.figure.add_subplot(111)
        self.canvas = self.figure.canvas

    @abc.abstractmethod
    def update_graph(self, *args, **kwargs):
        """Updates the graph by adding new elements or updating existing
        elements.
        """
        pass

    @abc.abstractmethod
    def update_legend(self, *args, **kwargs):
        """Updates the legend.
        """
        pass


class LineChart(FigureWrapper):
    def __init__(self, figure=None, **kwargs):
        super().__init__(figure, **kwargs)
        self.lines = {}

    @_draw_and_flush
    def update_graph(self, line_elements):
        """Updates the line chart with given line elements.

        If graph element already exists, its values will be updated,
        otherwise a new line is added to the graph.

        Args:
            line_elements: iterable of dictionaries. Each dictionary
                must contain a 'line_id', and collections of 'x' and 'y'
                values. Dictionary can also contain any number of keyword
                arguments that will be passed on to a Line2D object.
        """
        # TODO make sure that the graph is resized properly after updating
        #      existing lines
        for ge in line_elements:
            self.__update_line(**ge)

    def __update_line(self, line_id, x, y, linestyle="-",
                      **kwargs):
        """Adds or updates a single line.

        Args:
            line_id: id of the line.
            x: values on the x axis.
            y: values on the y axis.
            linestyle: passed down to Line2D object.
            kwargs: additional keyword arguments passed down to the Line2D
                when it is initialized.
        """
        try:
            line = self.lines[line_id]
            line.set_xdata(x)
            line.set_ydata(y)
            line.set_linestyle(linestyle)
        except KeyError:
            line, = self.axes.plot(x, y, linestyle=linestyle, **kwargs)
            self.lines[line_id] = line

    @_draw_and_flush
    def update_legend(self, label_data, **kwargs):
        """Draws or updates a legend box.
        """
        # TODO map given label_data to existing handlers
        # TODO sort the labels
        # handles, labels = self.axes.get_legend_handles_labels()
        leg_kwargs = dict(self.LEGEND_KWARGS)
        leg_kwargs.update(**kwargs)
        self.axes.legend(**leg_kwargs)

    @_draw_and_flush
    def hide_lines(self, lines_to_hide, linestyle="-"):
        """Hides given lines from the graph. If the line is not
        in the lines_to_hide collection, its linestyle will be set
        to given linestyle.
        """
        for key, val in self.lines.items():
            if key in lines_to_hide:
                val.set_linestyle("None")
            else:
                val.set_linestyle(linestyle)

    @_draw_and_flush
    def remove_lines(self, lines_to_remove):
        pass

    @_draw_and_flush
    def set_scale(self, scale):
        self.axes.set_yscale(scale)


class LimitLines(abc.ABC):
    """Draws limit lines on the given axes.
    """
    def __init__(self, canvas, axes):
        self.canvas = canvas
        self.axes = axes
        self.limit_lines = ()

    @abc.abstractmethod
    def set_limits(self, *args, **kwargs):
        pass

    @abc.abstractmethod
    def get_range(self):
        pass


class AlternatingLimits(LimitLines):
    def __init__(self, canvas, axes):
        super().__init__(canvas, axes)

    def set_limits(self, *args, **kwargs):
        pass

    def get_range(self):
        return None, None
