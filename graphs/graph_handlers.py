# coding=utf-8
"""
Created on 29.02.2020

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
__author__ = ""  # TODO
__version__ = ""  # TODO

import abc

from graphs.base_graphs import LineChart
from graphs.base_graphs import AlternatingLimits
from modules.depth_files import DepthProfileHandler


class GraphHandler(abc.ABC):
    """Provides a higher level interface for interacting with a FigureWrapper
    object. Transforms raw data into a format that the wrapper can use to
    plot data.
    """
    @abc.abstractmethod
    def plot_data(self, *args, **kwargs):
        pass

    @abc.abstractmethod
    def show_legend(self, *args, **kwargs):
        pass

    @abc.abstractmethod
    def set_callback(self, event, callback):
        pass

    @abc.abstractmethod
    def remove_callback(self, callback_id):
        pass


class DepthProfileGraphHandler(GraphHandler):
    def __init__(self, figure, elements, depth_directory, color_map=None,
                 rbs_selection=None):
        super().__init__()
        self.line_chart = LineChart(figure)
        self.profile_handler = DepthProfileHandler()
        self.profile_handler.read_directory(elements, depth_directory)
        self.limit_lines = AlternatingLimits(self.line_chart.canvas,
                                             self.line_chart.axes)
        if color_map is None:
            self.colors = {}
        else:
            self.colors = color_map

        if rbs_selection is None:
            self.rbs_selection = set()
        else:
            self.rbs_selection = rbs_selection

    def plot_data(self, mode="abs"):
        if mode == "abs":
            profiles = self.profile_handler.get_absolute_profiles()
        elif mode == "rel":
            profiles = self.profile_handler.get_relative_profiles()
        else:
            raise ValueError(f"Unexpected profile mode: {mode}.")

        graph_elems = (
            {
                "line_id": key,
                "x": val.depths,
                "y": val.concentrations,
                "label": f"{val.element}"
            }
            for key, val in profiles.items() if key != "total"
        )
        self.line_chart.update_graph(graph_elems)

    def show_legend(self):
        self.line_chart.update_legend()

    def get_profile_ids(self):
        return self.line_chart.lines.keys()

    def hide_profiles(self, profiles_to_hide):
        self.line_chart.hide_lines(profiles_to_hide)

    def set_scale(self, scale):
        self.line_chart.set_scale(scale)

    def set_callback(self, event, callback):
        """Connects a callback to a matplotlib canvas event.

        Args:
            event: name of a matplotlib canvas event
            callback: function that is called when the event happens

        Return:
            callback id
        """
        return self.line_chart.canvas.mpl_connect(event, callback)

    def remove_callback(self, callback_id):
        self.line_chart.canvas.mpl_disconnect(callback_id)


if __name__ == "__main__":
    # Script for testing purposes.
    # Disable 'Show plot tools in window' in 'File' > 'Settings' > 'Tools' >
    # 'Python scientific' before running this on Pycharm
    from modules.element import Element
    from pathlib import Path
    import matplotlib.pyplot as plt
    from graphs.base_graphs import FigureWrapper
    from graphs.graph_handlers import DepthProfileGraphHandler

    fig = plt.figure(1, **FigureWrapper.FIGURE_KWARGS)
    depth_dir = Path("..", "sample_data", "Ecaart-11-mini",
                     "Tof-E_65-mini", "depthfiles")
    elems_str = ["C", "F", "H", "Li", "Mn", "O", "Si"]
    elems = [Element.from_string(e) for e in elems_str]

    g = DepthProfileGraphHandler(fig, depth_dir, elems)
    g.plot_data("rel")
    plt.pause(1)

    g.plot_data("abs")
    plt.pause(1)
    plt.show()
