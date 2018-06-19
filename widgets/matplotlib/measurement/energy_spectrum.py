# coding=utf-8
"""
Created on 21.3.2013
Updated on 19.6.2018

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2013-2018 Jarkko Aalto, Severi Jääskeläinen, Samuel Kaiponen,
Timo Konu, Samuli Kärkkäinen, Samuli Rahkonen, Miika Raunio, Heta Rekilä and
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
"""

__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen " \
             "\n Samuli Rahkonen \n Miika Raunio \n Severi Jääskeläinen \n " \
             "Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"
__version__ = "2.0"

from PyQt5 import QtWidgets

from dialogs.graph_ignore_elements import GraphIgnoreElements
from modules.element import Element
from widgets.matplotlib.base import MatplotlibWidget
import modules.masses as masses
from modules.measurement import Measurement
import os
from matplotlib.widgets import SpanSelector
from matplotlib import patches
from shapely.geometry import Polygon
from modules.general_functions import find_nearest


class MatplotlibEnergySpectrumWidget(MatplotlibWidget):
    """Energy spectrum widget
    """

    def __init__(self, parent, histed_files, rbs_list, spectrum_type,
                 legend=True):
        """Inits Energy Spectrum widget.

        Args:
            parent: EnergySpectrumWidget class object.
            histed_files: List of calculated energy spectrum files.
            rbs_list: A dictionary of RBS selection elements containing
                      scatter elements.
            legend: Boolean representing whether to draw legend or not.
        """
        super().__init__(parent)
        super().fork_toolbar_buttons()
        self.parent = parent
        self.draw_legend = legend
        self.histed_files = histed_files
        self.__rbs_list = rbs_list
        self.__icon_manager = parent.icon_manager
        if isinstance(parent.parent.obj, Measurement):
            self.__selection_colors = parent.parent.obj.selector.get_colors()

        self.__initiated_box = False
        self.__ignore_elements = []
        self.__log_scale = False

        self.canvas.manager.set_title("Energy Spectrum")
        self.axes.fmt_xdata = lambda x: "{0:1.2f}".format(x)
        self.axes.fmt_ydata = lambda y: "{0:1.0f}".format(y)

        self.mpl_toolbar.addSeparator()
        self.__button_toggle_log = QtWidgets.QToolButton(self)
        self.__button_toggle_log.clicked.connect(self.__toggle_log_scale)
        self.__button_toggle_log.setCheckable(True)
        self.__button_toggle_log.setToolTip("Toggle logarithmic Y axis scaling")
        self.__icon_manager.set_icon(self.__button_toggle_log,
                                     "monitoring_section.svg")
        self.mpl_toolbar.addWidget(self.__button_toggle_log)

        if spectrum_type == "measurement":
            self.__button_ignores = QtWidgets.QToolButton(self)
            self.__button_ignores.clicked.connect(
                self.__ignore_elements_from_graph)
            self.__button_ignores.setToolTip(
                "Select elements which are included in the graph")
            self.__icon_manager.set_icon(self.__button_ignores, "gear.svg")
            self.mpl_toolbar.addWidget(self.__button_ignores)

        if spectrum_type == "simulation":
            self.__button_area_calculation = QtWidgets.QToolButton(self)
            self.__button_area_calculation.clicked.connect(
                self.__calculate_selected_area)
            self.__button_area_calculation.setToolTip(
                "Calculate the area ratio between the two spectra inside the "
                "selected interval")
            self.__icon_manager.set_icon(self.__button_area_calculation,
                                         "depth_profile_lim_in.svg")
            self.mpl_toolbar.addWidget(self.__button_area_calculation)

            self.span_selector = SpanSelector(self.axes, self.on_span_select,
                                              'horizontal', useblit=True,
                                              rectprops=dict(alpha=0.5,
                                                             facecolor='red'),
                                              button=1, span_stays=True)

        self.limits = []
        self.leg = None  # Original legend
        self.lines_of_area = []

        self.on_draw()

    def __calculate_selected_area(self):
        """
        Calculate the ratio between the two spectra areas.
        """
        lower_limit = self.limits[0].get_xdata()[0]
        upper_limit = self.limits[1].get_xdata()[0]

        # Create a list with points inside the limits
        limited_points = []
        for line_points in self.lines_of_area:
            lim_points = []
            for i in range(len(line_points)):
                # Add first point that is either corresponding directly to lower
                # limit or half of bin width bigger than the last point smaller
                # than lower limit.
                point = line_points[i]
                x_point = float(point[0])
                if lower_limit == x_point:
                    lim_points.append((x_point, float(point[1])))
                try:
                    next_point = line_points[i + 1]
                except IndexError:
                    continue
                if x_point < lower_limit < float(next_point[0]):
                    start_y_point = (float(point[1]) + float(next_point[1])) / 2
                    start_x_point = x_point + 0.5 * self.parent.bin_width
                    start_point = start_x_point, start_y_point
                    lim_points.append(start_point)
                if lower_limit < x_point < upper_limit:
                    lim_points.append((x_point, float(point[1])))
                # Add last point that is either corresponding directly to upper
                # limit or half of bin width smaller than the first point bigger
                # than upper limit.
                if upper_limit == x_point:
                    lim_points.append((x_point, float(point[1])))
                previous_point = line_points[i - 1]
                if float(previous_point[0]) < upper_limit < x_point:
                    end_y_point = (float(point[1]) +
                                   float(previous_point[1])) / 2
                    end_x_point = x_point - 0.5 * self.parent.bin_width
                    end_point = end_x_point, end_y_point
                    lim_points.append(end_point)
            limited_points.append(lim_points)

        # https://stackoverflow.com/questions/25439243/find-the-area-between-
        # two-curves-plotted-in-matplotlib-fill-between-area
        # Create a polygon points list from limited points
        polygon_points = []
        for value in limited_points[0]:
            polygon_points.append([value[0], value[1]])

        for value in limited_points[1][::-1]:
            polygon_points.append([value[0], value[1]])

        for value in limited_points[0][0:1]:
            polygon_points.append([value[0], value[1]])

        polygon = Polygon(polygon_points)
        area = polygon.area

        self.axes.legend(
            handles=[patches.Rectangle(xy=[1, 1], width=1, height=1,
                                       color='red', alpha=0.5,
                                       label="Difference: %f" % area)],
            loc=2,
            bbox_to_anchor=(1, 1),
            borderaxespad=0,
            prop={'size': 12})

        self.axes.add_artist(self.leg)
        self.canvas.draw_idle()

    def on_span_select(self, xmin, xmax):
        """
        Show selected area in the plot.

        Args:
            xmin: Area start.
            xmax: Area end.
        """
        # TODO: limit histed files inside the limits to only two
        first_line_lst = list(self.histed_files.values())[0]
        first_line = [float(x[0]) for x in first_line_lst]
        second_line_lst = list(self.histed_files.values())[1]
        second_line = [float(x[0]) for x in second_line_lst]

        self.lines_of_area = []
        self.lines_of_area.append(first_line_lst)
        self.lines_of_area.append(second_line_lst)

        low_x = round(xmin, 3)
        high_x = round(xmax, 3)

        # Find nearest point to low_x from hist_files
        nearest_low_1 = find_nearest(low_x, first_line)
        nearest_low_2 = find_nearest(low_x, second_line)

        if nearest_low_1 > nearest_low_2:
            nearest_lows = [nearest_low_2, nearest_low_1]
        else:
            nearest_lows = [nearest_low_1, nearest_low_2]

        nearest_low = find_nearest(low_x, nearest_lows)

        nearest_high_1 = find_nearest(high_x, first_line)
        nearest_high_2 = find_nearest(high_x, second_line)

        if nearest_high_1 > nearest_high_2:
            nearest_highs = [nearest_high_2, nearest_high_1]
        else:
            nearest_highs = [nearest_high_1, nearest_high_2]

        nearest_high = find_nearest(high_x, nearest_highs)

        # Always have low and high be different lines
        if nearest_high in first_line and nearest_low in first_line:
            if nearest_low_2 > nearest_high_1:
                nearest_high = nearest_low_2
                nearest_low = nearest_high_1
            else:
                nearest_low = nearest_low_2
        elif nearest_high in second_line and nearest_low in second_line:
            if nearest_low_1 > nearest_high_2:
                nearest_high = nearest_low_1
                nearest_low = nearest_high_2
            else:
                nearest_low = nearest_low_1

        for lim in self.limits:
            lim.set_linestyle('None')

        self.limits = []
        ylim = self.axes.get_ylim()
        self.limits.append(self.axes.axvline(x=nearest_low, linestyle="--"))
        self.limits.append(self.axes.axvline(x=nearest_high, linestyle="--",
                                             color='red'))

        self.axes.set_ybound(ylim[0], ylim[1])
        self.canvas.draw_idle()

    def __sortt(self, key):
        cut_file = key.split('.')
        element_object = Element.from_string(cut_file[0].strip())
        element = element_object.symbol
        isotope = element_object.isotope
        if not isotope:
            isotope = masses.get_standard_isotope(element)
        return isotope

    def on_draw(self):
        """Draw method for matplotlib.
        """
        # Values for zoom
        x_min, x_max = self.axes.get_xlim()
        y_min, y_max = self.axes.get_ylim()

        self.axes.clear()  # Clear old stuff

        self.axes.set_ylabel("Yield (counts)")
        self.axes.set_xlabel("Energy (MeV)")

        if isinstance(self.parent.parent.obj, Measurement):
            element_counts = {}
            keys = [item[0] for item in sorted(self.histed_files.items(),
                                               key=lambda x: self.__sortt(
                                                   x[0]))]
            for key in keys:
                cut_file = key.split('.')
                cut = self.histed_files[key]
                element_object = Element.from_string(cut_file[0])
                element = element_object.symbol
                isotope = element_object.isotope
                if key in self.__ignore_elements:
                    continue

                # Check RBS selection
                rbs_string = ""
                if len(cut_file) == 2:
                    if key + ".cut" in self.__rbs_list.keys():
                        element_object = self.__rbs_list[key + ".cut"]
                        element = element_object.symbol
                        isotope = element_object.isotope
                        rbs_string = "*"
                else:
                    if key in self.__rbs_list.keys():
                        element_object = self.__rbs_list[key]
                        element = element_object.symbol
                        isotope = element_object.isotope
                        rbs_string = "*"

                x = tuple(float(pair[0]) for pair in cut)
                y = tuple(float(pair[1]) for pair in cut)

                if isotope is None:
                    isotope = ""

                # Get color for selection
                dirtyinteger = 0
                while "{0}{1}{2}".format(isotope, element,
                                         dirtyinteger) in element_counts:
                    dirtyinteger += 1
                color_string = "{0}{1}{2}".format(isotope, element,
                                                  dirtyinteger)
                element_counts[color_string] = 1
                if color_string not in self.__selection_colors:
                    color = "red"
                else:
                    color = self.__selection_colors[color_string]

                if len(cut_file) == 2:
                    label = r"$^{" + str(isotope) + "}$" + element + rbs_string
                else:
                    label = r"$^{" + str(isotope) + "}$" + element \
                            + rbs_string + "$_{split: " + cut_file[2] + "}$"
                self.axes.plot(x, y,
                               color=color,
                               label=label)
        else:

            for key, data in self.histed_files.items():
                # Parse the element symbol and isotope.
                file_name = os.path.split(key)[1]
                isotope = ""
                symbol = ""
                if file_name.endswith(".hist"):
                    measurement_name, isotope_and_symbol, rest = \
                        file_name.split('.', 2)
                    element = Element.from_string(isotope_and_symbol)
                    isotope = element.isotope
                    if isotope is None:
                        isotope = ""
                    symbol = element.symbol

                    label = r"$^{" + str(isotope) + "}$" + symbol + " (" + \
                            measurement_name + ")"
                else:
                    for s in file_name:
                        if s != "-":
                            if s.isdigit():
                                isotope += s
                            else:
                                symbol += s
                        else:
                            break

                    label = r"$^{" + isotope + "}$" + symbol

                x = tuple(float(pair[0]) for pair in data)
                y = tuple(float(pair[1]) for pair in data)
                self.axes.plot(x, y, label=label)

        if self.draw_legend:
            if not self.__initiated_box:
                self.fig.tight_layout(pad=0.5)
                box = self.axes.get_position()
                self.axes.set_position([box.x0, box.y0,
                                        box.width * 0.9, box.height])
                self.__initiated_box = True

            handles, labels = self.axes.get_legend_handles_labels()
            self.leg = self.axes.legend(handles,
                                        labels,
                                        loc=3,
                                        bbox_to_anchor=(1, 0),
                                        borderaxespad=0,
                                        prop={'size': 12})
            for handle in self.leg.legendHandles:
                handle.set_linewidth(3.0)

        if 0.09 < x_max < 1.01:  # This works...
            x_max = self.axes.get_xlim()[1]
        if 0.09 < y_max < 1.01:
            y_max = self.axes.get_ylim()[1]

        # Set limits accordingly
        self.axes.set_ylim([y_min, y_max])
        self.axes.set_xlim([x_min, x_max])

        if self.__log_scale:
            self.axes.set_yscale('symlog')

        # Remove axis ticks
        self.remove_axes_ticks()

        # Draw magic
        self.canvas.draw()

    def __toggle_log_scale(self):
        """Toggle log scaling for Y axis in depth profile graph.
        """
        self.__log_scale = self.__button_toggle_log.isChecked()
        self.on_draw()

    def __ignore_elements_from_graph(self):
        """Ignore elements from elements ratio calculation.
        """
        elements = [item[0] for item in sorted(self.histed_files.items(),
                                               key=lambda x: self.__sortt(
                                                   x[0]))]
        dialog = GraphIgnoreElements(elements, self.__ignore_elements)
        self.__ignore_elements = dialog.ignored_elements
        self.on_draw()
