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
import modules.math_functions as mf

from dialogs.graph_ignore_elements import GraphIgnoreElements

from pathlib import Path
from matplotlib import offsetbox
from matplotlib.widgets import SpanSelector

from modules.element import Element
from modules.measurement import Measurement
from modules.recoil_element import RecoilElement
from modules.element_simulation import ElementSimulation

from PyQt5 import QtWidgets
from PyQt5.QtGui import QGuiApplication

from scipy import integrate

from widgets.matplotlib.base import MatplotlibWidget


class MatplotlibEnergySpectrumWidget(MatplotlibWidget):
    """Energy spectrum widget
    """
    # By default, draw spectra lines with a solid line
    default_linestyle = "-"

    def __init__(self, parent, histed_files, rbs_list, spectrum_type,
                 legend=True, spectra_changed=None, disconnect_previous=False,
                 channel_width=None):
        """Inits Energy Spectrum widget.

        Args:
            parent: EnergySpectrumWidget class object.
            histed_files: List of calculated energy spectrum files.
            rbs_list: A dictionary of RBS selection elements containing
                scatter elements.
            legend: Boolean representing whether to draw legend or not.
            spectra_changed: pyQtSignal that indicates a change in spectra
                that requires redrawing
            disconnect_previous: whether energy spectrum widgets that were
                previously connected to the spectra_changed signal will be
                disconnected
            channel_width: channel width used in spectra calculation
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
        self.__ignore_elements = set()
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

        self.limits = {
            "lower": None,
            "upper": None
        }
        self.limits_visible = False
        self.leg = None  # Original legend
        self.anchored_box = None
        self.lines_of_area = []
        self.clipboard = QGuiApplication.clipboard()

        # This stores the plotted lines so we can update individual spectra
        # separately
        self.plots = {}

        self.spectra_changed = spectra_changed
        if self.spectra_changed is not None:
            if disconnect_previous:
                # Disconnect previous slots so only the last spectra graph
                # gets updated
                try:
                    self.spectra_changed.disconnect()
                except (TypeError, AttributeError):
                    # signal had no previous connections, nothing to do
                    pass
            self.spectra_changed.connect(self.update_spectra)

        self.channel_width = channel_width
        self.on_draw()

    def closeEvent(self, evnt):
        """Disconnects the slot from the spectra_changed signal
        when widget is closed.
        """
        try:
            self.spectra_changed.disconnect(self.update_spectra)
        except (TypeError, AttributeError):
            # Signal was either already disconnected or None
            pass
        super().closeEvent(evnt)

    def __calculate_selected_area(self, start, end):
        """
        Calculate the ratio between the two spectra areas.

        Return:
            ratio, area(?) or None, None
        """
        # TODO move at least parts of this function to math_functions module
        all_areas = []
        for line_points in self.lines_of_area:
            points = list(line_points.values())[0]
            all_areas.append(list(mf.get_continuous_range(points,
                                                          a=start,
                                                          b=end)))

        area = mf.calculate_area(all_areas[0], all_areas[1])

        # Calculate also the ratio of the two curve's areas
        try:
            x_1, y_1 = zip(*all_areas[0])
            x_2, y_2 = zip(*all_areas[1])
        except ValueError:
            # one of the areas contains no points
            return None, None

        area_1 = integrate.simps(y_1, x_1)
        area_2 = integrate.simps(y_2, x_2)

        # Check if one of the self.lines_of_area is a hist file
        # If so, use it as the one which is compare to the other
        i = 0
        j = 0
        for line in self.lines_of_area:
            for key, values in line.items():
                if key.name.endswith(".hist"):
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

        return ratio, area

    def show_ratio(self):
        """Calculates the ratio of spectra areas between the current limit
        range and displays it on screen.
        """
        start, end = self.get_limit_range()
        ratio, area = self.__calculate_selected_area(start, end)
        self.show_ratio_box(ratio, area, start, end)

    def show_ratio_box(self, ratio, area, start, end, copy_to_clipboard=True):
        """Displays a text box that shows the ratio and of areas between two
        spectra within start and end.
        """
        if self.anchored_box:
            self.anchored_box.set_visible(False)
            self.anchored_box = None

        child_boxes = []

        if ratio is None:
            text = "Invalid selection, \nno ratio could \nbe calculated"
            child_boxes.append(offsetbox.TextArea(
                text, textprops=dict(color="k", size=12)))

        else:
            ratio_round = 9  # Round decimal number

            text = f"Difference: {round(area, 2)}\n" \
                   f"Ratio: {round(ratio, ratio_round)}\n" \
                   f"Interval: [{round(start, 2)}, {round(end, 2)}]"
            child_boxes.append(offsetbox.TextArea(
                text, textprops=dict(color="k", size=12)))

            if copy_to_clipboard:
                self.clipboard.setText(str(round(ratio, ratio_round)))
                text_2 = "\nRatio copied to clipboard."
                child_boxes.append(offsetbox.TextArea(
                    text_2, textprops=dict(color="k", size=10)))

        box = offsetbox.VPacker(children=child_boxes, align="center", pad=0,
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

        drawn_lines = {
            path: self.files_to_draw[path]
            for path, line in self.plots.items()
            if line.get_linestyle() != "None"
        }
        if len(drawn_lines) != 2:
            QtWidgets.QMessageBox.critical(self.parent.parent, "Warning",
                                           "Limits can only be set when two "
                                           "elements are drawn.\n\nPlease add"
                                           " or remove elements accordingly.",
                                           QtWidgets.QMessageBox.Ok,
                                           QtWidgets.QMessageBox.Ok)
            return

        low_x = round(xmin, 3)
        high_x = round(xmax, 3)

        lowest = None
        highest = None
        self.lines_of_area = []

        # Find the min and max of the files
        for key, val in drawn_lines.items():
            first = float(val[0][0])
            last = float(val[-1][0])

            float_values = [(float(x[0]), float(x[1])) for x in val]
            self.lines_of_area.append({key: float_values})
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

        ylim = self.axes.get_ylim()
        try:
            self.limits["lower"].set_xdata((low_x, low_x))
            self.limits["upper"].set_xdata((high_x, high_x))
        except AttributeError:
            self.limits["lower"] = self.axes.axvline(x=low_x, linestyle="--")
            self.limits["upper"] = self.axes.axvline(x=high_x, linestyle="--",
                                                     color='red')
        self.limits_visible = True

        self.axes.set_ybound(ylim[0], ylim[1])

        self.__button_area_calculation.setEnabled(True)
        self.canvas.draw_idle()

        self.show_ratio()

    def __toggle_area_limits(self):
        """
        Toggle the area limits on and off.
        """
        if self.limits_visible:
            for lim in self.limits.values():
                lim.set_linestyle('None')
            self.limits_visible = False
        else:
            for lim in self.limits.values():
                lim.set_linestyle('--')
            self.limits_visible = True
            self.show_ratio()
        self.canvas.draw_idle()

    def get_limit_range(self):
        """Returns the limit range between the two limit lines or None, None
        if no limits are displayed.
        """
        if not self.limits_visible:
            return None

        try:
            start = self.limits["lower"].get_xdata()[0]
            end = self.limits["upper"].get_xdata()[0]
            return start, end
        except AttributeError:
            return None

    @staticmethod
    def __sortt(key):
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
                for used_file in self.histed_files:
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
                    if key + ".cut" in self.__rbs_list:
                        element_object = self.__rbs_list[key + ".cut"]
                        element = element_object.symbol
                        isotope = element_object.isotope
                        rbs_string = "*"
                else:
                    if key in self.__rbs_list:
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
                line, = self.axes.plot(x, y, color=color, label=label,
                                       linestyle=self.default_linestyle)
                self.plots[key] = line

        else:  # Simulation energy spectrum
            if self.__ignore_elements:
                self.files_to_draw = self.remove_ignored_elements()
            else:
                self.files_to_draw = copy.deepcopy(self.histed_files)
            for key, data in self.files_to_draw.items():
                # Parse the element symbol and isotope.
                file_name = key.name
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
                        used_recoil_file_name = \
                            f"{used_recoil.get_full_name()}.simu"
                        if used_recoil_file_name == file_name:
                            color = used_recoil.color
                            break

                else:
                    label = file_name

                x, y = get_axis_values(data)
                x_min, x_min_changed = fix_minimum(x, x_min)

                if not color:
                    line, = self.axes.plot(x, y, label=label,
                                           linestyle=self.default_linestyle)
                else:
                    line, = self.axes.plot(x, y, label=label, color=color,
                                           linestyle=self.default_linestyle)
                self.plots[key] = line

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
            self.axes.set_yscale("symlog")

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
        if self.__log_scale:
            self.axes.set_yscale("symlog")
        else:
            self.axes.set_yscale("linear")

        self.canvas.draw()
        self.canvas.flush_events()

        if self.limits_visible:
            self.show_ratio()

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
            self.__ignore_elements = set(ignored_elements)
        else:
            elements = [item[0] for item in sorted(self.histed_files.items(),
                                                   key=lambda x: self.__sortt(
                                                    x[0]))]
            dialog = GraphIgnoreElements(elements, self.__ignore_elements)
            self.__ignore_elements = set(dialog.ignored_elements)

        self.hide_plots(self.__ignore_elements)

    def hide_plots(self, plots_to_hide):
        """Hides given plots from the graph.

        Args:
            plots_to_hide: collection of plot names that will be hidden.
        """
        for file_name, line in self.plots.items():
            if file_name in plots_to_hide:
                line.set_linestyle("None")
            else:
                # Any other plot will use the default style
                line.set_linestyle(self.default_linestyle)

        self.canvas.draw()
        self.canvas.flush_events()

    @gf.stopwatch()
    def update_spectra(self, rec_elem: RecoilElement,
                       elem_sim: ElementSimulation):
        """Updates spectra line that belongs to given recoil element.

        Args:
            rec_elem: RecoilElement object
            elem_sim: ElementSimulation object that is used to calculate
                the spectrum
        """
        # TODO this just assumes that the recoil is a simulated one,
        #      not optimized. This should perhaps be changed.
        # TODO add a checkbox that toggles automatic updates on and off
        # TODO might want to prevent two widgets running this simultaneously
        #      as they are writing/reading the same files
        # TODO change plot range if necessary

        if rec_elem is None or elem_sim is None:
            return

        espe_file = Path(elem_sim.directory, f"{rec_elem.get_full_name()}.simu")

        if espe_file in self.plots:
            espe, _ = elem_sim.calculate_espe(rec_elem, ch=self.channel_width)

            data = get_axis_values(espe)

            self.plots[espe_file].set_data(data)

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
