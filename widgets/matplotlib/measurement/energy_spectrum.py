# coding=utf-8
"""
Created on 21.3.2013
Updated on 17.12.2018

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

import copy
import os

import modules.general_functions as gf

from dialogs.graph_ignore_elements import GraphIgnoreElements

from pathlib import Path
from matplotlib import offsetbox
from matplotlib.widgets import SpanSelector

from modules.element import Element
from modules.general_functions import calculate_new_point
from modules.measurement import Measurement

from PyQt5 import QtWidgets
from PyQt5.QtGui import QGuiApplication

from scipy import integrate
from shapely.geometry import Polygon

from widgets.matplotlib.base import MatplotlibWidget

from tests.utils import stopwatch


class MatplotlibEnergySpectrumWidget(MatplotlibWidget):
    """Energy spectrum widget
    """

    def __init__(self, parent, histed_files, rbs_list, spectrum_type,
                 legend=True, spectra_changed=None):
        """Inits Energy Spectrum widget.

        Args:
            parent: EnergySpectrumWidget class object.
            histed_files: List of calculated energy spectrum files.
            rbs_list: A dictionary of RBS selection elements containing
                      scatter elements.
            legend: Boolean representing whether to draw legend or not.
            spectra_changed: pyQtSignal that indicates a change in spectra
                             that requires redrawing
        """
        super().__init__(parent)
        self.parent = parent
        self.draw_legend = legend
        self.histed_files = copy.deepcopy(histed_files)
        self.spectrum_type = spectrum_type

        # List for files to draw for simulation
        self.files_to_draw = histed_files

        self.__rbs_list = rbs_list
        self.__icon_manager = parent.icon_manager
        if isinstance(parent.parent.obj, Measurement):
            self.__selection_colors = parent.parent.obj.selector.get_colors()

        self.__initiated_box = False
        self.__ignore_elements = []     # TODO should be a set
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

        self.__button_ignores = QtWidgets.QToolButton(self)
        self.__button_ignores.clicked.connect(
            self.__ignore_elements_from_graph)
        self.__button_ignores.setToolTip(
            "Select elements which are included in the graph")
        self.__icon_manager.set_icon(self.__button_ignores, "gear.svg")
        self.mpl_toolbar.addWidget(self.__button_ignores)

        if self.spectrum_type == "simulation":
            self.__button_area_calculation = QtWidgets.QToolButton(self)
            self.__button_area_calculation.clicked.connect(
                self.__toggle_area_limits)
            self.__button_area_calculation.setToolTip(
                "Toggle the area limits")
            self.__icon_manager.set_icon(self.__button_area_calculation,
                                         "depth_profile_lim_lines.svg")
            self.mpl_toolbar.addWidget(self.__button_area_calculation)
            self.__button_area_calculation.setEnabled(False)

            self.span_selector = SpanSelector(self.axes, self.on_span_select,
                                              'horizontal', useblit=True,
                                              rectprops=dict(alpha=0.5,
                                                             facecolor='red'),
                                              button=1, span_stays=True)
            self.__used_recoils = self.__find_used_recoils()

        self.limits = []
        self.limits_visible = False
        self.leg = None  # Original legend
        self.anchored_box = None
        self.lines_of_area = []
        self.clipboard = QGuiApplication.clipboard()

        # This stores the plotted lines so we can update individual spectra
        # separately
        self.plots = {}
        if spectra_changed is not None:
            # Disconnect previous slots so only the last spectra graph
            # gets updated
            try:
                spectra_changed.disconnect()
            except TypeError:
                # signal had no previous connections, nothing to do
                pass
            spectra_changed.connect(self.update_spectra)

        self.on_draw()

    def __calculate_selected_area(self):
        """
        Calculate the ratio between the two spectra areas.
        """
        if not self.limits:
            return
        if not self.limits_visible:
            return

        start = self.limits[0].get_xdata()[0]
        end = self.limits[1].get_xdata()[0]

        all_areas = []
        for line_points in self.lines_of_area:
            area_points = []
            points = list(line_points.values())[0]
            for i, point in enumerate(points):
                x = point[0]
                y = point[1]
                if x < start:
                    continue
                if start <= x:
                    if i > 0:
                        previous_point = points[i - 1]
                        if previous_point[0] < start < x:
                            # Calculate new point to be added
                            calculate_new_point(previous_point, start,
                                                       point, area_points)
                    if x <= end:
                        area_points.append((x, y))
                    else:
                        if i > 0:
                            previous_point = points[i - 1]
                            if previous_point[0] < end < x:
                                calculate_new_point(previous_point, end,
                                                           point, area_points)
                        break

            all_areas.append(area_points)

        # https://stackoverflow.com/questions/25439243/find-the-area-between-
        # two-curves-plotted-in-matplotlib-fill-between-area
        # Create a polygon points list from limited points
        polygon_points = []
        for value in all_areas[0]:
            polygon_points.append((value[0], value[1]))

        for value in all_areas[1][::-1]:
            polygon_points.append((value[0], value[1]))

        # Add the first point again to close the rectangle
        polygon_points.append(polygon_points[0])

        polygon = Polygon(polygon_points)
        area = polygon.area

        # Calculate also the ratio of the two curve's areas
        x_1, y_1 = zip(*all_areas[0])
        x_2, y_2 = zip(*all_areas[1])

        area_1 = integrate.simps(y_1, x_1)
        area_2 = integrate.simps(y_2, x_2)

        # Check if one of the self.lines_of_area is a hist file
        # If so, use it as the one which is compare to the other
        i = 0
        j = 0
        for line in self.lines_of_area:
            for key, values in line.items():
                if key.endswith(".hist"):
                    i += 1
                    break
            if i != 0:
                break
            j += 1

        if i != 0:
            if j == 1 and i == 1 and area_2 != 0:
                ratio = area_2 / area_1
            else:
                ratio = area_1 / area_2
        else:
            if area_1 > area_2:
                ratio = area_2 / area_1
            else:
                ratio = area_1 / area_2

        # Copy ratio to clipboard
        ratio_round = 9  # Round decimal number
        self.clipboard.setText(str(round(ratio, ratio_round)))

        if self.anchored_box:
            self.anchored_box.set_visible(False)
            self.anchored_box = None

        text = f"Difference: {round(area, 2)}\n" \
               f"Ratio: {round(ratio, ratio_round)}\n" \
               f"Interval: [{round(start, 2)}, {round(end, 2)}]"
        box1 = offsetbox.TextArea(text, textprops=dict(color="k", size=12))

        text_2 = "\nRatio copied to clipboard."
        box2 = offsetbox.TextArea(text_2, textprops=dict(color="k", size=10))
        box = offsetbox.VPacker(children=[box1, box2], align="center", pad=0,
                                sep=0)

        self.anchored_box = offsetbox.AnchoredOffsetbox(
                loc=2,
                child=box, pad=0.5,
                frameon=False,
                bbox_to_anchor=(1.0, 1.0),
                bbox_transform=self.axes.transAxes,
                borderpad=0.,
            )
        self.axes.add_artist(self.anchored_box)
        self.axes.add_artist(self.leg)
        self.canvas.draw_idle()

    def on_span_select(self, xmin, xmax):
        """
        Show selected area in the plot.

        Args:
            xmin: Area start.
            xmax: Area end.
        """
        if xmin == xmax:  # Do nothing if graph is clicked
            return

        # Limit files_to_draw to only two
        if len(self.files_to_draw) != 2:
            QtWidgets.QMessageBox.critical(self.parent.parent, "Warning",
                                           "Limits can only be set when two "
                                           "elements are drawn.\n\nPlease add"
                                           " or remove elements accordingly.",
                                           QtWidgets.QMessageBox.Ok,
                                           QtWidgets.QMessageBox.Ok)
            return

        low_x = round(xmin, 3)
        high_x = round(xmax, 3)

        for lim in self.limits:
            lim.set_linestyle('None')

        lowest = None
        highest = None
        self.lines_of_area = []

        # Find the min and max of the files
        for key, val in self.files_to_draw.items():
            first = float(val[0][0])
            last = float(val[-1][0])

            float_values = [(float(x[0]), float(x[1])) for x in val]
            self.lines_of_area.append({key : float_values})
            if not lowest:
                lowest = first
            if not highest:
                highest = last
            if first < lowest:
                lowest = first
            if highest < last:
                highest = last

        # Check that limits are not beyond files' min and max points
        if low_x < lowest:
            low_x = lowest
        if highest < high_x:
            high_x = highest

        self.limits = []
        ylim = self.axes.get_ylim()
        self.limits.append(self.axes.axvline(x=low_x, linestyle="--"))
        self.limits.append(self.axes.axvline(x=high_x, linestyle="--",
                                             color='red'))
        self.limits_visible = True

        self.axes.set_ybound(ylim[0], ylim[1])

        self.__button_area_calculation.setEnabled(True)
        self.canvas.draw_idle()

        self.__calculate_selected_area()

    def __toggle_area_limits(self):
        """
        Toggle the area limits on and off.
        """
        if self.limits_visible:
            for lim in self.limits:
                lim.set_linestyle('None')
            self.limits_visible = False
            self.anchored_box.set_visible(False)
            self.anchored_box = None
            self.canvas.draw_idle()
        else:
            for lim in self.limits:
                lim.set_linestyle('--')
            if self.limits:
                self.limits_visible = True
                self.__calculate_selected_area()

    def __sortt(self, key):
        cut_file = key.split('.')
        # TODO sort by RBS selection
        # TODO provide elements as parameters, do not initialize them here
        return Element.from_string(cut_file[0].strip())

    def __find_used_recoils(self):
        """
        Find all the recoils that will be drawn.
        """
        recoils = []
        for elem_sim in self.parent.parent.obj.element_simulations:
            for recoil in elem_sim.recoil_elements:
                for used_file in self.histed_files.keys():
                    used_file_name = os.path.split(used_file)[1]
                    if used_file_name == recoil.prefix + "-" + recoil.name + \
                            ".simu":
                        recoils.append(recoil)
                        break
        return recoils

    def on_draw(self):
        """Draw method for matplotlib.
        """
        # Values for zoom
        x_min, x_max = self.axes.get_xlim()
        y_min, y_max = self.axes.get_ylim()
        x_min_changed = False

        self.axes.clear()  # Clear old stuff

        self.axes.set_ylabel("Yield (counts)")
        self.axes.set_xlabel("Energy (MeV)")

        # TODO refactor the draw function so that measurement and simulation
        #      do not use so many lines of different code
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
                if len(cut_file) == 3:
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

                x, y = get_axis_values(cut)
                x_min, x_min_changed = fix_minimum(x, x_min)

                if isotope is None:
                    isotope = ""

                # Get color for selection
                dirtyinteger = 0
                if rbs_string == "*":
                    color_string = "{0}{1}{2}{3}".format("RBS_", isotope,
                                                         element, dirtyinteger)
                else:
                    color_string = "{0}{1}{2}".format(isotope, element,
                                                      dirtyinteger)

                while color_string in element_counts:
                    dirtyinteger += 1
                    if rbs_string == "*":
                        color_string = "{0}{1}{2}{3}".format("RBS_", isotope,
                                                             element,
                                                             dirtyinteger)
                    else:
                        color_string = "{0}{1}{2}".format(isotope, element,
                                                          dirtyinteger)

                element_counts[color_string] = 1
                if color_string not in self.__selection_colors:
                    color = "red"
                else:
                    color = self.__selection_colors[color_string]

                if len(cut_file) == 3:
                    label = r"$^{" + str(isotope) + "}$" + element + rbs_string
                else:
                    label = r"$^{" + str(isotope) + "}$" + element \
                            + rbs_string + "$_{split: " + cut_file[2] + "}$"
                self.plots[key] = self.axes.plot(x, y,
                                                 color=color,
                                                 label=label)

        else:  # Simulation energy spectrum
            if self.__ignore_elements:
                self.files_to_draw = self.remove_ignored_elements()
            else:
                self.files_to_draw = copy.deepcopy(self.histed_files)
            for key, data in self.files_to_draw.items():
                # Parse the element symbol and isotope.
                file_name = os.path.split(key)[1]
                isotope = ""
                symbol = ""
                color = None
                suffix = ""

                if file_name.endswith(".hist"):
                    measurement_name, isotope_and_symbol, erd_or_rbs, rest = \
                        file_name.split('.', 3)
                    if "ERD" in erd_or_rbs:
                        element = Element.from_string(isotope_and_symbol)
                    else:
                        if "RBS_" in erd_or_rbs:
                            i = erd_or_rbs.index("RBS_")
                            scatter_element_str = erd_or_rbs[i + len("RBS_"):]
                            element = Element.from_string(scatter_element_str)
                        else:
                            element = Element("")
                        suffix = "*"

                    isotope = element.isotope
                    if isotope is None:
                        isotope = ""
                    symbol = element.symbol

                    rest_split = rest.split(".")
                    if "no_foil" in rest_split:
                        # TODO make a function that splits all the necessary
                        #      parts from a file name at once so there is no
                        #      need to do these kinds of checks
                        rest_split.remove("no_foil")

                    if len(rest_split) == 2:  # regular hist file
                        label = r"$^{" + str(isotope) + "}$" + symbol + suffix \
                            + " (exp)"
                    else:  # split
                        label = r"$^{" + str(isotope) + "}$" + symbol + suffix \
                            + "$_{split: " + rest_split[1] + "}$"" (exp)"
                elif file_name.endswith(".simu"):
                    for s in file_name:
                        if s != "-":
                            if s.isdigit():
                                isotope += s
                            else:
                                symbol += s
                        else:
                            break
                    recoil_name_with_end = file_name.split('-', 1)[1]
                    recoil_name = recoil_name_with_end.split('.')[0]

                    label = r"$^{" + isotope + "}$" + symbol + " " + recoil_name

                    for used_recoil in self.__used_recoils:
                        used_recoil_file_name = used_recoil.prefix + "-" + \
                                                used_recoil.name + ".simu"
                        if used_recoil_file_name == file_name:
                            color = used_recoil.color

                else:
                    label = file_name

                x, y = get_axis_values(data)
                x_min, x_min_changed = fix_minimum(x, x_min)

                if not color:
                    self.plots[key] = self.axes.plot(x, y, label=label)
                else:
                    self.plots[key] = self.axes.plot(x, y, label=label,
                                                     color=color)

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
        if x_min_changed:
            self.axes.set_xlim([x_min - self.parent.bin_width, x_max])
        else:
            self.axes.set_xlim([x_min, x_max])

        if self.__log_scale:
            self.axes.set_yscale('symlog')

        # Remove axis ticks
        self.remove_axes_ticks()

        # Draw magic
        self.canvas.draw()

    def remove_ignored_elements(self):
        """
        Find entries from self.histed_files that don't correspond to keys in
        self.__ignore_elements.

        Return:
            Dictionary with the entries and keys that are not ignored.
        """
        files_to_draw = {}
        for key, val in self.histed_files.items():
            if key in self.__ignore_elements:
                continue
            files_to_draw[key] = val
        return files_to_draw

    def __toggle_log_scale(self):
        """Toggle log scaling for Y axis in depth profile graph.
        """
        self.__log_scale = self.__button_toggle_log.isChecked()
        self.on_draw()
        if self.limits:
            self.axes.add_artist(self.limits[0])
            self.axes.add_artist(self.limits[1])
        if self.limits_visible:
            self.__calculate_selected_area()

    def __ignore_elements_from_graph(self):
        """Ignore elements from elements ratio calculation.
        """
        if self.spectrum_type == "simulation":
            elements = []
            paths = []
            ignored_elements = []
            ignore_elements_for_dialog = []
            for key in self.histed_files:
                paths.append(key)
                file = os.path.split(key)[1]
                if file.endswith(".hist"):
                    element = file.rsplit('.', 1)[0]
                elif file.endswith(".simu"):
                    element = file.split('.')[0]
                else:
                    element = file
                if key in self.__ignore_elements:
                    ignore_elements_for_dialog.append(element)
                elements.append(element)
            dialog = GraphIgnoreElements(elements, ignore_elements_for_dialog)
            for elem in dialog.ignored_elements:
                for path in paths:
                    file_name = path.name
                    if elem in file_name:
                        index = file_name.find(elem)
                        if file_name[index + len(elem)] == ".":
                            # TODO this check seems a bit unnecessary
                            ignored_elements.append(path)
            self.__ignore_elements = ignored_elements
        else:
            elements = [item[0] for item in sorted(self.histed_files.items(),
                                                   key=lambda x: self.__sortt(
                                                    x[0]))]
            dialog = GraphIgnoreElements(elements, self.__ignore_elements)
            self.__ignore_elements = dialog.ignored_elements
        self.on_draw()
        self.limits = []

    @stopwatch
    def update_spectra(self, rec_elem, elem_sim):
        """Updates spectra from given hist_files"""
        # TODO update only happens when one of the points is moved along the
        #      x axis. Update should also happen when a point is moved along
        #      the y axis or gets removed, or change gets undone
        # TODO this just assumes that the recoil is a simulated one,
        #      not optimized. This should perhaps be changed.
        # TODO add a checkbox that toggles automatic updates on and off

        spectrum_file = Path(elem_sim.directory,
                             f"{rec_elem.get_full_name()}.simu")

        if spectrum_file in self.plots:
            elem_sim.calculate_espe(rec_elem)
            espe_data = gf.read_espe_file(spectrum_file)

            _, y = get_axis_values(espe_data)

            # TODO change plot range if necessary
            self.plots[spectrum_file][0].set_ydata(y)

            self.canvas.draw()
            self.canvas.flush_events()


def get_axis_values(data):
    """Returns the x and y axis values from given data."""
    return (
        tuple(float(pair[0]) for pair in data),
        tuple(float(pair[1]) for pair in data)
    )


def fix_minimum(lst, minimum):
    if lst and lst[0] < minimum:
        return lst[0], True
    return minimum, False
