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
Sinikka Siironen, 2020 Juhani Sundell

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
             "Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen \n " \
             "Juhani Sundell"
__version__ = "2.0"

import os
from pathlib import Path
from typing import Optional, List, Dict, Tuple

from PyQt5 import QtWidgets
from PyQt5.QtGui import QGuiApplication
from matplotlib import offsetbox
from matplotlib.widgets import SpanSelector
from scipy import integrate

import modules.math_functions as mf
from dialogs.graph_ignore_elements import GraphIgnoreElements
from modules.base import Espe
from modules.element import Element
from modules.element_simulation import ElementSimulation
from modules.energy_spectrum import SumEnergySpectrum
from modules.enums import SumSpectrumType, SpectrumTab
from modules.measurement import Measurement
from modules.recoil_element import RecoilElement
from widgets.matplotlib.base import MatplotlibWidget


class MatplotlibEnergySpectrumWidget(MatplotlibWidget):
    """Energy spectrum widget
    """
    # By default, draw spectra lines with a solid line
    DEFAULT_LINESTYLE = "-"
    MEASURED_SUM_SPECTRUM_LINE_STYLE = "dashed"
    SIMULATED_SUM_SPECTRUM_LINE_STYLE = "dotted"
    SUM_SPECTRUM_LINE_WIDTH = 2
    SIMULATED_SUM_SPECTRUM_Z_ORDER = 102
    MEASURED_SUM_SPECTRUM_Z_ORDER = 101

    def __init__(self, parent, simulation_energy=None, measurement_energy=None,
                 rbs_list=None, spectrum_type=None, legend=True,
                 spectra_changed=None, disconnect_previous=False,
                 channel_width=None, simulated_sum_spectrum_is_selected=False,
                 measured_sum_spectrum_is_selected=False,
                 sum_spectra_directory=None):
        """Inits Energy Spectrum widget.
        Args:
            parent: EnergySpectrumWidget class object.
            simulation_energy: A list of calculated simulation energy spectrum
            files.
            measurement_energy: A list of calculated measurement energy spectrum
             files.
            rbs_list: A dictionary of RBS selection elements containing
                scatter elements.
            legend: Boolean representing whether to draw legend or not.
            spectra_changed: pyQtSignal that indicates a change in spectra
                that requires redrawing
            disconnect_previous: whether energy spectrum widgets that were
                previously connected to the spectra_changed signal will be
                disconnected
            channel_width: channel width used in spectra calculation
            simulated_sum_spectrum_is_selected: whether simulated sum
                spectrum is enabled
            measured_sum_spectrum_is_selected: whether measured sum
                spectrum is enabled
            sum_spectra_directory: output directory for sum spectra
        """
        super().__init__(parent)

        self.parent = parent
        self.draw_legend = legend
        self.simulation_energy = simulation_energy
        self.measurement_energy = measurement_energy
        self.spectrum_type = spectrum_type
        self.simulated_sum_spectrum_is_selected = \
            simulated_sum_spectrum_is_selected
        self.measured_sum_spectrum_is_selected = \
            measured_sum_spectrum_is_selected

        self.measured_sum_spectrum = SumEnergySpectrum()
        self.simulated_sum_spectrum = SumEnergySpectrum()
        self.sum_spectra_directory = sum_spectra_directory

        if self.spectrum_type == SpectrumTab.SIMULATION:
            # Simulated sum spectrum in Simulation tab
            if self.simulated_sum_spectrum_is_selected and \
                    self.simulation_energy:
                self.simulated_sum_spectrum = SumEnergySpectrum(
                    self.simulation_energy,
                    sum_spectra_directory, SumSpectrumType.SIMULATED)
            # Measured sum spectrum in Simulation tab
            if self.measured_sum_spectrum_is_selected and \
                    self.measurement_energy:
                # When a sum spectrum is generated for a simulation, both the
                # simulated and the measured sum spectra should be saved in the
                # simulation's folder.
                self.measured_sum_spectrum = SumEnergySpectrum(
                    self.measurement_energy,
                    sum_spectra_directory, SumSpectrumType.MEASURED)
        # Measured sum spectrum in Measurement
        if (self.spectrum_type == SpectrumTab.MEASUREMENT
                and self.measured_sum_spectrum_is_selected
                and self.measurement_energy):
            self.measured_sum_spectrum = SumEnergySpectrum(
                self.measurement_energy,
                sum_spectra_directory, SumSpectrumType.MEASURED)

        # List for files to draw for simulation
        self.simulation_energy_files_to_draw = \
            self.simulation_energy
        self.measurement_energy_files_to_draw = \
            self.measurement_energy

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

        # Set default filename for saving figure
        bin_width = str(parent.bin_width).replace(".", "_")
        name = parent.parent.obj.name
        default_filename = f"Energy_spectra_binw_{bin_width}MeV_{name}"
        self.canvas.get_default_filename = lambda: default_filename

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
                                              props=dict(alpha=0.5,
                                                             facecolor='red'),
                                              button=1, interactive=True)
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

        self.save_spectrums()

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
            all_areas.append(list(mf.get_continuous_range(
                points, a=start, b=end)))

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

        if self.simulated_sum_spectrum_is_selected or self.measured_sum_spectrum_is_selected:
            self.__check_draw_lines()
            return

        self.files_to_draw = self.simulation_energy_files_to_draw|self.measurement_energy_files_to_draw

        drawn_lines = self.__draw_line(self.files_to_draw)

        if len(drawn_lines) != 2:
            self.__check_draw_lines()
            return

        low_x = round(xmin, 3)
        high_x = round(xmax, 3)
        self.lines_of_area = []
        low_x, high_x = self.__find_max_and_min(drawn_lines, low_x, high_x)

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

    def __draw_line(self, files_to_draw):
        return {
            path: files_to_draw[path]
            for path, line in self.plots.items()
            if line.get_linestyle() != "None"
        }

    def __check_draw_lines(self):
        return QtWidgets.QMessageBox.critical(
            self.parent.parent, "Warning",
            "Limits can only be set when two elements are drawn.\n\n"
            "Please add or remove elements accordingly.",
            QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)

    def __find_max_and_min(self, drawn_lines, low_x, high_x):
        lowest = None
        highest = None
        for key, val in drawn_lines.items():
            first = float(val[0][0])
            last = float(val[-1][0])

            float_values = [(float(x[0]), float(x[1])) for x in val]
            self.lines_of_area.append({key: float_values})
            if not lowest:
                lowest = first
            if not highest:
                highest = last
            if first > lowest:
                lowest = first
            if highest > last:
                highest = last

        # Check that limits are not beyond files' min and max points
        if low_x < lowest:
            low_x = lowest
        if highest < high_x:
            high_x = highest
        return low_x, high_x

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

    def __find_used_recoils(self):
        """
        Find all the recoils that will be drawn.
        """
        recoils = []
        for elem_sim in self.parent.parent.obj.element_simulations:
            for recoil in elem_sim.recoil_elements:
                for used_file in {**self.simulation_energy,
                                  **self.measurement_energy}:
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
            if self.measured_sum_spectrum_is_selected:
                ignore_measurement_elements = IgnoreMeasurementElements(
                    self.measured_sum_spectrum.sum_spectrum_key,
                    self.measured_sum_spectrum.sum_spectrum,
                    self.measurement_energy,
                    self.__ignore_elements, self.__rbs_list,
                    self.__selection_colors)
                ignore_measurement_elements.iterate_keys_and_plot_them(
                    x_min, self.axes, self.plots)

            else:
                ignore_measurement_elements = IgnoreMeasurementElements(
                    None, None, self.measurement_energy,
                    self.__ignore_elements, self.__rbs_list,
                    self.__selection_colors)
                ignore_measurement_elements.iterate_keys_and_plot_them(
                    x_min, self.axes, self.plots)
            if self.measured_sum_spectrum_is_selected:
                self.plot_measured_sum_spectrum()
        else:
            if self.__ignore_elements:
                self.simulation_energy_files_to_draw = \
                    self.remove_ignored_elements()
                self.measurement_energy_files_to_draw = \
                    self.remove_ignored_elements()
            else:
                self.simulation_energy_files_to_draw = \
                    self.simulation_energy
                self.measurement_energy_files_to_draw = \
                    self.measurement_energy

            if self.spectrum_type == SpectrumTab.SIMULATION:
                if len(self.simulation_energy) > 0:
                    self.plot_energy_files(self.simulation_energy_files_to_draw, x_min)
                    if self.simulated_sum_spectrum_is_selected:
                        self.plot_simulated_sum_spectrum()
                if len(self.measurement_energy) > 0:
                    self.plot_energy_files(self.measurement_energy_files_to_draw, x_min)
                    if self.measured_sum_spectrum_is_selected:
                        self.plot_measured_sum_spectrum()

            if self.spectrum_type == SpectrumTab.MEASUREMENT:
                if self.measured_sum_spectrum_is_selected and len(
                        self.measurement_energy) \
                        > 0:
                    self.plot_energy_files(
                        self.measurement_energy_files_to_draw, x_min)
                    self.plot_measured_sum_spectrum()
                else:
                    self.plot_energy_files(
                        self.measurement_energy_files_to_draw, x_min)

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

        lower_lim = 0.09
        upper_lim = 1.01

        if lower_lim < x_max < upper_lim:  # This works...
            x_max = self.axes.get_xlim()[1]
        if lower_lim < y_max < upper_lim:
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

    def plot_energy_files(self, files_to_draw, x_min):
        for key, data in files_to_draw.items():
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
                                       linestyle=self.DEFAULT_LINESTYLE)
            else:
                line, = self.axes.plot(x, y, label=label, color=color,
                                       linestyle=self.DEFAULT_LINESTYLE)
            self.plots[key] = line

    def plot_simulated_sum_spectrum(self):
        if self.simulated_sum_spectrum_is_selected and \
                self.simulated_sum_spectrum.sum_spectrum:
            x, y = zip(*self.simulated_sum_spectrum.sum_spectrum)
            line, = self.axes.plot(x, y, label='SIMULATION_SUM',
                                   linestyle=self.SIMULATED_SUM_SPECTRUM_LINE_STYLE,
                                   linewidth=self.SUM_SPECTRUM_LINE_WIDTH,
                                   zorder=self.SIMULATED_SUM_SPECTRUM_Z_ORDER)
            self.plots[self.simulated_sum_spectrum.sum_spectrum_path] = line

    def plot_measured_sum_spectrum(self):
        if self.spectrum_type == SpectrumTab.SIMULATION:
            if self.measured_sum_spectrum_is_selected and \
                    self.measured_sum_spectrum.sum_spectrum:
                x, y = zip(*self.measured_sum_spectrum.sum_spectrum)
                line, = self.axes.plot(x, y, label='MEASUREMENT_SUM',
                                       linestyle=self.MEASURED_SUM_SPECTRUM_LINE_STYLE,
                                       linewidth=self.SUM_SPECTRUM_LINE_WIDTH,
                                       zorder=self.MEASURED_SUM_SPECTRUM_Z_ORDER)
                self.plots[self.measured_sum_spectrum.sum_spectrum_path] = line
        else:
            x, y = zip(*self.measured_sum_spectrum.sum_spectrum)
            line, = self.axes.plot(x, y, label='MEASUREMENT_SUM',
                                   linestyle=self.MEASURED_SUM_SPECTRUM_LINE_STYLE,
                                   linewidth=self.SUM_SPECTRUM_LINE_WIDTH,
                                   zorder=self.MEASURED_SUM_SPECTRUM_Z_ORDER)
            self.plots[self.measured_sum_spectrum.sum_spectrum_key] = line

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
        if self.spectrum_type == SpectrumTab.SIMULATION:  # SIMULATION TAB
            if self.simulated_sum_spectrum:  # SIMULATION SIMULATION
                elements_to_ignore = IgnoreElements(
                    simulation_energy_files_to_draw=self.simulation_energy_files_to_draw,
                    measurement_energy_files_to_draw=self.measurement_energy_files_to_draw,
                    simulated_sum_spectrum_path=self.simulated_sum_spectrum.sum_spectrum_path,
                    measured_sum_spectrum_path=self.measured_sum_spectrum.sum_spectrum_path,
                    ignored_set=self.__ignore_elements)
            else:  # SIMULATION MEASUREMENT
                elements_to_ignore = IgnoreElements(
                    simulation_energy_files_to_draw=self.simulation_energy_files_to_draw,
                    measurement_energy_files_to_draw=self.measurement_energy_files_to_draw,
                    simulated_sum_spectrum_path=None,
                    measured_sum_spectrum_path=None,
                    ignored_set=self.__ignore_elements)
            self.__ignore_elements = \
                elements_to_ignore.ignore_simulation_elements()

        elif self.spectrum_type == SpectrumTab.MEASUREMENT:  # MEASUREMENT TAB
            if self.measured_sum_spectrum_is_selected:  # WITH SUM SPECTRUM
                elements_to_ignore = IgnoreElements(
                    simulation_energy_files_to_draw=None,
                    measurement_energy_files_to_draw=self.measurement_energy_files_to_draw,
                    simulated_sum_spectrum_path=None,
                    measured_sum_spectrum_path=self.measured_sum_spectrum.sum_spectrum_path,
                    ignored_set=self.__ignore_elements)
                self.__ignore_elements = \
                    elements_to_ignore.ignore_measurement_elements(
                        self.measured_sum_spectrum.sum_spectrum_key,
                        self.measurement_energy_files_to_draw)
            else:  # WITHOUT SUM SPECTRUM
                elements_to_ignore = IgnoreElements(
                    simulation_energy_files_to_draw=None,
                    measurement_energy_files_to_draw=self.measurement_energy_files_to_draw,
                    simulated_sum_spectrum_path=None,
                    measured_sum_spectrum_path=None,
                    ignored_set=self.__ignore_elements)
                self.__ignore_elements = \
                    elements_to_ignore.ignore_measurement_elements(
                        measurement_elements_path=self.measurement_energy_files_to_draw)
        else:  # JUST IN CASE
            elements_to_ignore = IgnoreElements(
                simulation_energy_files_to_draw=self.simulation_energy_files_to_draw,
                measurement_energy_files_to_draw=self.measurement_energy_files_to_draw,
                simulated_sum_spectrum_path=None,
                measured_sum_spectrum_path=None,
                ignored_set=self.__ignore_elements)
            self.__ignore_elements = \
                elements_to_ignore.ignore_measurement_elements(
                    measurement_elements_path=self.measurement_energy_files_to_draw)
        self.hide_plots(self.__ignore_elements)

    def hide_plots(self, plots_to_hide):
        """Hides given plots from the graph.

        Args:
            plots_to_hide: collection of plot names that will be hidden.
        """
        for file_name, line in self.plots.items():
            if file_name in plots_to_hide:
                line.set_linestyle("None")
            elif "MEASURED_SUM" in str(file_name):
                line.set_linestyle(self.MEASURED_SUM_SPECTRUM_LINE_STYLE)
            elif "SIMULATED_SUM" in str(file_name):
                line.set_linestyle(self.SIMULATED_SUM_SPECTRUM_LINE_STYLE)
            else:
                # Any other plot will use the default style
                line.set_linestyle(self.DEFAULT_LINESTYLE)

        self.canvas.draw()
        self.canvas.flush_events()

    def update_spectra(self, rec_elem: RecoilElement,
                       elem_sim: ElementSimulation):
        """Update a spectra that belongs to given recoil element.

        Args:
            rec_elem: RecoilElement object
            elem_sim: ElementSimulation object that is used to calculate the
            spectrum
        """
        # TODO change plot range if necessary

        if rec_elem is None or elem_sim is None:
            return

        espe_file = Path(elem_sim.directory, f"{rec_elem.get_full_name()}.simu")

        if espe_file in self.plots:
            espe, _ = elem_sim.calculate_espe(rec_elem, ch=self.channel_width)
            data = get_axis_values(espe)
            self.plots[espe_file].set_data(data)
            self._update_sum_spectra(espe_file, espe)
            self.canvas.draw()
            self.canvas.flush_events()

    def _update_sum_spectra(self, espe_file: Path, espe: Espe) -> None:
        """Update an energy spectrum in a sum spectrum (measured or simulated)
        and update the plot GUI.

        Args:
            espe_file: path to the element spectrum
            espe: the element spectrum
        """
        if (self.simulated_sum_spectrum_is_selected
                and espe_file in self.simulated_sum_spectrum.spectra):
            self.simulated_sum_spectrum.add_or_update_spectra({espe_file: espe})

            data = get_axis_values(self.simulated_sum_spectrum.sum_spectrum)
            self.plots[self.simulated_sum_spectrum.sum_spectrum_path]\
                .set_data(data)
            return

        if (self.measured_sum_spectrum_is_selected
                and espe_file in self.measured_sum_spectrum.spectra):
            self.measured_sum_spectrum.add_or_update_spectra({espe_file: espe})

            data = get_axis_values(self.measured_sum_spectrum.sum_spectrum)
            self.plots[self.measured_sum_spectrum.sum_spectrum_path]\
                .set_data(data)

    def save_spectrums(self):
        """ Save plotted energy spectrums """
        separator = ';'
        default_value = 0.0
        spectrums_file = self.sum_spectra_directory / "espectra.hist"
        xs = set()
        y_values = []
        for spectrum in self.simulation_energy.values():
            x,y = zip(*spectrum)
            xs.update(set(x))
        for spectrum in self.measurement_energy.values():
            x,y = zip(*spectrum)
            xs.update(set(x))

        xs = list(xs)
        xs = sorted(xs)

        for spectrum in self.simulation_energy.values():
            x,y = zip(*spectrum)
            new_y = [y[x.index(all_x)] if (all_x in x) else default_value for all_x in xs]
            y_values.append(new_y)

        for spectrum in self.measurement_energy.values():
            x,y = zip(*spectrum)
            new_y = [y[x.index(all_x)] if (all_x in x) else default_value for all_x in xs]
            y_values.append(new_y)

        with open(spectrums_file, 'w') as file:
            file.write("#Energy")
            for title in self.simulation_energy.keys():
                file.write(f"{separator}{title.stem}")
            for title in self.measurement_energy.keys():
                file.write(f"{separator}{title.stem}")
            file.write("\n")

            file.write("#MeV")
            for _ in y_values:
                file.write(f"{separator}Count")
            file.write("\n")

            for i,x in enumerate(xs):
                file.write(f"{x}")
                for y in y_values:
                    if (y[i] != None):
                        file.write(f"{separator}{y[i]}")
                    else:
                        file.write(f"{separator}")
                file.write("\n")

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


class IgnoreElements:
    def __init__(self,
                 simulation_energy_files_to_draw: Dict[Path, Tuple] = None,
                 measurement_energy_files_to_draw: Dict[Path, Tuple] = None,
                 simulated_sum_spectrum_path: Optional[Path] = None,
                 measured_sum_spectrum_path: Optional[Path] = None,
                 ignored_set: Optional[set] = None):

        """
        Initializes the class for ignoring elements.

        Args:
         simulation_energy_files_to_draw: Simulation energy files to be drawn
         measurement_energy_files_to_draw: Dict[Path, Tuple] = Measurement
         energy files to be drawn
         simulated_sum_spectrum_path: Optional[Path] = The path for a simulated
         sum spectrum files
         measured_sum_spectrum_path: Optional[Path] = The path for a measured
         sum spectrum files
         ignored_set: Optional[set] = None): Ignored elements from the GUI
        """

        self._elements: Optional[List] = []
        self._paths: Optional[List] = []
        self._ignored_elements: Optional[List] = []
        self._ignore_elements_for_dialog: Optional[List] = []

        # Locations and energy files for the simulated and the measured spectrum
        self._simulated_sum_spectrum_path: Optional[Path] = \
            simulated_sum_spectrum_path
        self._measured_sum_spectrum_path: Optional[Path] = \
            measured_sum_spectrum_path
        self._simulation_energy_files_to_draw: Dict[Path, Tuple] = \
            simulation_energy_files_to_draw
        self._measurement_energy_files_to_draw: Dict[Path, Tuple] = \
            measurement_energy_files_to_draw
        self._ignored_set: Optional[set] = ignored_set

    def ignore_simulation_elements(self) -> Optional[set]:
        """Choose elements that will be shown / hidden on the GUI.
        Returns the set of elements that will be hidden on the GUI"""
        simulation_paths = []
        measurement_paths = []
        if self._simulation_energy_files_to_draw:
            """SIMULATION SIMULATION"""
            if self._simulated_sum_spectrum_path:
                self.elements_to_be_ignored(
                    simulation_paths,
                    self._simulation_energy_files_to_draw,
                    self._simulated_sum_spectrum_path)
            else:
                """SIMULATION MEASUREMENT"""
                self.elements_to_be_ignored(
                    simulation_paths,
                    self._simulation_energy_files_to_draw)
        if self._measurement_energy_files_to_draw:
            """MEASUREMENT MEASUREMENT"""
            if self._measured_sum_spectrum_path:
                self.elements_to_be_ignored(
                    measurement_paths,
                    self._measurement_energy_files_to_draw,
                    self._measured_sum_spectrum_path)
            else:
                """OTHER CASES"""
                self.elements_to_be_ignored(
                    measurement_paths,
                    self._measurement_energy_files_to_draw)

        dialog = GraphIgnoreElements(self._elements,
                                     self._ignore_elements_for_dialog)

        if self._simulation_energy_files_to_draw:
            self.add_ignored_elements(dialog, simulation_paths)
        if self._measurement_energy_files_to_draw:
            self.add_ignored_elements(dialog, measurement_paths)

        return set(self._ignored_elements)

    def add_ignored_elements(self, dialog, paths):
        """Add paths of ignored elements to the list.

        Args:
            dialog: GUI
            paths: Empty path list
        """
        if len(paths) == 0:
            return
        for elem in dialog.ignored_elements:
            for path in paths:
                file_name = path.name
                if elem in file_name:
                    index = file_name.find(elem)
                    if file_name[index + len(elem)] == ".":
                        # TODO this check seems a bit unnecessary
                        self._ignored_elements.append(path)

    def elements_to_be_ignored(self, paths: List[Path] = None,
                               energy_spectrum_paths: Dict[Path, Tuple] = None,
                               sum_spectrum_path: Optional[Path] = None):
        """Iterate element paths and add element keys to the list. Choose
        element that will be hidden on the GUI and add them to the
        list.

        Args:
            paths: Empty path list
            energy_spectrum_paths: The simulation or the measurement energy
            spectrum paths
            sum_spectrum_path: The sum spectrum path
        """

        for path in energy_spectrum_paths.keys():
            paths.append(path)
        if sum_spectrum_path:
            paths.append(sum_spectrum_path)
        for key in paths:
            file = os.path.split(key)[1]
            if file.endswith(".hist"):
                element = file.rsplit('.', 1)[0]
            elif file.endswith(".simu"):
                element = file.split('.')[0]
            else:
                element = file
            if key in self._ignored_set:
                self._ignore_elements_for_dialog.append(element)
            self._elements.append(element)

    def ignore_measurement_elements(
            self, measured_sum_spectrum_key: Optional[str] = "",
            measurement_elements_path: Path = None):
        """Iterate measurement's element paths and add element keys to the
        list. Choose elements that will be hidden on the GUI and add
        them to the list.

        Args:
            measured_sum_spectrum_key: The measured sum spectrum key
            measurement_elements_path: Measurement files path
        """

        keys = []
        for key in measurement_elements_path.keys():
            if "." or "-" in key:
                keys.append(key.split(".")[0])
        if measured_sum_spectrum_key:
            keys.append(measured_sum_spectrum_key)
        self._elements = [k for k in
                          sorted(keys, key=lambda x: element_sort_key(x))]
        dialog = GraphIgnoreElements(self._elements, self._ignored_set)
        return set(dialog.ignored_elements)


class IgnoreMeasurementElements:
    def __init__(self, sum_spectrum_key: Optional[str] = None,
                 sum_spectrum: Dict[List, Tuple] = None,
                 spectrum_files: Optional[object] = None,
                 ignored_set: Optional[set] = None,
                 rbs_list: Optional[List] = None,
                 selection_colors=None) -> None:
        """
        Initializes the class that iterates element keys and shows them
        on the GUI.
        Args:
            sum_spectrum_key = The sum spectrum key
            sum_spectrum = The sum spectrum energy files for the GUI
            spectrum_files = Other spectrum files
            ignored_set = Elements that are hidden on the GUI
            rbs_list = Separates beam scatters from other recoil files
            selection_colors = Graph colors on the GUI
        """

        self.sum_spectrum_key = sum_spectrum_key
        self.sum_spectrum = sum_spectrum
        self.spectrum_files = spectrum_files
        self.ignored_set = ignored_set
        self.rbs_list = rbs_list
        self.selection_colors = selection_colors
        self.sum_spectrum_dictionary = {
            self.sum_spectrum_key: sum_spectrum}
        self.measurement_keys_and_points = \
            {**self.spectrum_files, **self.sum_spectrum_dictionary}
        self.element_counts: Optional[Dict] = {}

    # FIXME: Simplify me :)
    def iterate_keys_and_plot_them(self, x_min, axes, plots):
        """Iterate element keys and plot them on the GUI.

        Args:
            x_min: The current minimum x-value
            axes: Axes that will on the GUI
            plots: Plots the will be on the GUI
        """
        for key, points in self.measurement_keys_and_points.items():
            if key is None or key is self.sum_spectrum_key:
                continue
            if "." or "-" in key:
                key = key.split(".")[0]
            element_object = Element.from_string(key)
            element = element_object.symbol
            isotope = element_object.isotope
            if key in self.ignored_set:
                continue
            # Check RBS selection
            rbs_string = ""
            if len(key) == 3:
                if key + ".cut" in self.rbs_list:
                    element_object = self.rbs_list[key + ".cut"]
                    element = element_object.symbol
                    isotope = element_object.isotope
                    rbs_string = "*"
            else:
                if key in self.rbs_list:
                    element_object = self.rbs_list[key]
                    element = element_object.symbol
                    isotope = element_object.isotope
                    rbs_string = "*"

            x, y = get_axis_values(points)
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

            while color_string in self.element_counts:
                dirtyinteger += 1
                if rbs_string == "*":
                    color_string = "{0}{1}{2}{3}".format("RBS_", isotope,
                                                         element,
                                                         dirtyinteger)
                else:
                    color_string = "{0}{1}{2}".format(isotope, element,
                                                      dirtyinteger)

            self.element_counts[color_string] = 1
            if color_string not in self.selection_colors:
                color = "red"
            else:
                color = self.selection_colors[color_string]

            if True: #len(key) == 3: # TODO: printing splits properly
                label = r"$^{" + str(isotope) + "}$" + element + rbs_string
            else:
                label = r"$^{" + str(isotope) + "}$" + element \
                        + rbs_string + "$_{split: " + key + "}$"
            line, = axes.plot(x, y, color=color, label=label,
                              linestyle=MatplotlibEnergySpectrumWidget.DEFAULT_LINESTYLE)
            plots[key] = line


def element_sort_key(key):
    # TODO sort by RBS selection
    # TODO provide elements as parameters, do not initialize them here.
    #   Better yet, use CutFile objects here.
    # TODO is measurement removed from the cut file at this point? If
    #   not, this sorts by measurement instead of element
    return Element.from_string(key.strip())
