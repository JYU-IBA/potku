# coding=utf-8
"""
Created on 17.4.2013
Updated on 20.11.2018

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

MatplotlibDepthProfileWidget handles the drawing and operation of the
depth profile graph.
"""
__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen \n " \
             "Samuli Rahkonen \n Miika Raunio \n Severi Jääskeläinen \n " \
             "Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"
__version__ = "2.0"

import modules.math_functions as mf

from dialogs.measurement.depth_profile_ignore_elements \
    import DepthProfileIgnoreElements
from widgets.matplotlib.base import MatplotlibWidget
from widgets.matplotlib import mpl_utils

from modules.depth_files import DepthProfileHandler
from modules.element import Element

from PyQt5 import QtWidgets


class MatplotlibDepthProfileWidget(MatplotlibWidget):
    """Depth profile widget that handles drawing depth profiles.
    """

    def __init__(self, parent, depth_dir, elements, rbs_list, depth_scale,
                 used_cuts, x_units='nm', legend=True, line_zero=False,
                 line_scale=False, systematic_error=3.0, progress=None):
        """Inits depth profile widget.

        Args:
            parent: A DepthProfileWidget class object.
            depth_dir: A directory where the depth files are located.
            elements: A list of Element objects.
            rbs_list: A dictionary of RBS selection elements containing
                      scatter elements.
            depth_scale: A tuple of depth scaling values.
            used_cuts: List of cut file paths that are sed to create depth
            profile.
            x_units: An unit to be used as x axis.
            legend: A boolean of whether to show the legend.
            line_zero: A boolean representing if vertical line is drawn at zero.
            line_scale: A boolean representing if horizontal line is drawn at
                        the defined depth scale.
            systematic_error: A double representing systematic error.
            progress: a ProgressReporter object
        """
        super().__init__(parent)

        self.canvas.manager.set_title("Depth Profile")
        self.axes.fmt_xdata = lambda x: "{0:1.2f}".format(x)
        self.axes.fmt_ydata = lambda y: "{0:1.2f}".format(y)
        self.x_units = x_units
        self.draw_legend = legend
        self.elements = elements
        self.depth_dir = depth_dir
        self.__depth_scale = depth_scale
        self.__used_cuts = used_cuts
        self.__line_zero = line_zero
        self.__line_scale = line_scale
        self.__systerr = systematic_error

        self.profile_handler = DepthProfileHandler()
        self.profile_handler.read_directory(self.depth_dir,
                                            self.elements,
                                            depth_units=self.x_units)
        if progress is not None:
            progress.report(50)

        lim_a, lim_b = self.profile_handler.get_depth_range()
        if lim_a is not None and lim_b is not None:
            self.limit = LimitLines(a=lim_a, b=lim_b)
        else:
            self.limit = LimitLines()
        self.energy_plots = {}

        self.__ignore_from_graph = set()
        self.__ignore_from_ratio = set()

        # TODO get selection colors and icon manager as parameters, not from
        #      parent
        self.selection_colors = parent.measurement.selector.get_colors()
        self.icon_manager = parent.icon_manager

        self.lim_icons = {'a': 'depth_profile_lim_all.svg',
                          'b': 'depth_profile_lim_in.svg',
                          'c': 'depth_profile_lim_ex.svg'}
        self.lim_mode = 'a'

        self.canvas.mpl_connect('button_press_event', self.onclick)

        self.__limits_set = False
        self.__position_set = False
        self.__rel_graph = False
        self.__log_scale = False
        self.__absolute_values = False
        self.__enable_norm_over_range = False
        self.__rbs_list = rbs_list
        self.__fork_toolbar_buttons()
        self.on_draw()

        if progress is not None:
            progress.report(100)

    def onclick(self, event):
        """Handles clicks on the graph.

        Args:
            event: A click event on the graph
        """
        if event.button == 1 and self.limButton.isChecked():
            self.limit.set(event.xdata)
            self.on_draw()

    def get_profiles_to_use(self):
        """Determines what files to use for plotting. Either relative, absolute
        or a merger of the two.
        """
        if not self.__rel_graph:
            return self.profile_handler.get_absolute_profiles()
        elif self.lim_mode == 'a':
            return self.profile_handler.get_relative_profiles()

        lim_a, lim_b = self.limit.get_limits()
        if self.lim_mode == 'b':
            return self.profile_handler.merge_profiles(
                lim_a, lim_b, method="abs_rel_abs"
            )

        return self.profile_handler.merge_profiles(
            lim_a, lim_b, method="rel_abs_rel"
        )

    def on_draw(self):
        """Draws the depth profile graph
        """
        # Values for zoom
        x_min, x_max = self.axes.get_xlim()
        y_min, y_max = self.axes.get_ylim()

        # Clear axes for a new draw.
        self.axes.clear()

        self.axes.set_xlabel('Depth (%s)' % self.x_units)
        self.axes.set_ylabel('Concentration (at.%)')

        # Plot the limits a and b
        # if self.__show_limits:
        # Currently limits are always drawn
        self.limit.draw(self.axes)

        self.axes.axhline(y=0, color="#000000")
        if self.__line_zero:
            self.axes.axvline(x=0, linestyle="-", linewidth=3,
                              color="#C0C0C0", alpha=0.75)

        if self.__line_scale:
            self.axes.axvspan(self.__depth_scale[0], self.__depth_scale[1],
                              color='#C0C0C0', alpha=0.20, edgecolor=None)

        self.__update_energy_plots(self.get_profiles_to_use(),
                                   draw_first_time=True)

        if not self.__position_set:
            self.fig.tight_layout(pad=0.5)

        # Set up the legend
        if self.draw_legend:
            self.__make_legend_box()

        # If drawing for "the first time", get limits from the drawn data.
        if 0.09 < x_max < 1.01:  # This works...
            x_min, x_max = self.axes.get_xlim()
        if 0.09 < y_max < 1.01:
            y_max = self.axes.get_ylim()[1]

        # Set limits accordingly
        self.axes.set_ylim([y_min, y_max])
        self.axes.set_xlim([x_min, x_max])

        if self.__log_scale:
            self.axes.set_yscale('symlog')

        self.remove_axes_ticks()
        self.canvas.draw()

    def __update_energy_plots(self, profiles_to_use, draw_first_time=False):
        sorted_profile_names = sorted(filter(lambda x: x != "total",
                                             profiles_to_use),
                                      key=lambda x: profiles_to_use[x].element)

        for profile_name in sorted_profile_names:
            if profile_name == "total":
                continue
            if profile_name in self.__ignore_from_graph:
                continue

            element = profiles_to_use[profile_name].element

            # Check RBS selection
            if profile_name in self.__rbs_list.values():
                color_key = "RBS_{0}0".format(str(element))
            else:
                color_key = "{0}0".format(str(element))
            # TODO: erd_depth for multiple selections of same element.

            axe1 = profiles_to_use[profile_name].depths
            axe2 = profiles_to_use[profile_name].concentrations

            label = str(element)        # TODO rbs string

            if draw_first_time:
                self.energy_plots[profile_name] = self.axes.plot(
                    axe1, axe2, label=label,
                    color=self.selection_colors[color_key])
            else:
                # TODO testing plot updating
                self.energy_plots[profile_name].set_ydata(axe2)
                self.canvas.draw()
                self.canvas.flush_events()

    def __make_legend_box(self):
        """Make legend box for the graph.
        """
        box = self.axes.get_position()
        if not self.__position_set:
            self.axes.set_position([box.x0, box.y0,
                                    box.width * 0.8, box.height])
            self.__position_set = True
        handles, labels = self.axes.get_legend_handles_labels()
        # self.__ignore_from_ratio = ["Si"]

        # TODO don't recalculate these if lim selection is unchanged

        # Calculate values to be displayed in the legend box
        lim_a, lim_b = self.limit.get_limits()
        if self.__absolute_values:
            concentrations = self.profile_handler.integrate_concentrations(
                lim_a, lim_b)
        else:
            percentages, moe = self.profile_handler.calculate_ratios(
                self.__ignore_from_ratio, lim_a, lim_b, self.__systerr)

        # Fix labels to proper format, with MoE
        labels_w_percentages = []
        for i in range(0, len(labels)):
            element = Element.from_string(labels[i])
            element_str = labels[i]
            element_isotope = str(element.isotope)

            if element_isotope == "None":
                element_isotope = ""

            element_name = element.symbol
            for elem in self.__rbs_list.values():
                if element_str == elem.symbol:
                    element_name += "*"
            str_element = "{0:>3}{1:<3}".format(element_isotope, element_name)
            # str_element = labels[i]
            # percentages[element_str] can be 0 which results false
            # None when element is ignored from ratio calculation.
            if not self.__absolute_values and percentages[element_str] is not \
                    None:
                rounding = mf.get_rounding_decimals(moe[element_str])
                if rounding:
                    str_ratio = "{0}%".format(round(percentages[element_str],
                                                    rounding))
                    str_err = "± {0}%".format(round(moe[element_str], rounding))
                else:
                    str_ratio = "{0}%".format(int(percentages[element_str]))
                    str_err = "± {0}%".format(int(moe[element_str]))
                lbl_str = "{0} {1:<6} {2}".format(r"$^{" + element_isotope +
                                                  "}$" +
                                                  element_name,
                                                  str_ratio, str_err)
            else:
                lbl_str = '{0}'.format(str_element)

            # Use absolute values for the elements instead of percentages.
            if self.__absolute_values:
                lbl_str = "{0} {1:<7} at./1e15 at./cm²"\
                    .format(r"$^{" + element_isotope + "}$" + element.symbol,
                            round(concentrations[element_str], 3))
            labels_w_percentages.append(lbl_str)

        leg = self.axes.legend(handles, labels_w_percentages,
                               loc=3, bbox_to_anchor=(1, 0),
                               borderaxespad=0, prop={'size': 11,
                                                      'family': "monospace"})
        for handle in leg.legendHandles:
            handle.set_linewidth(3.0)

    def __fork_toolbar_buttons(self):
        """Custom toolbar buttons be here.
        """
        # But first, let's play around with the existing MatPlotLib buttons.
        _, self.__button_drag, self.__button_zoom = \
            mpl_utils.get_toolbar_elements(
                self.mpl_toolbar, drag_callback=self.__uncheck_custom_buttons,
                zoom_callback=self.__uncheck_custom_buttons)

        self.limButton = QtWidgets.QToolButton(self)
        self.limButton.clicked.connect(self.__toggle_lim_lines)
        self.limButton.setCheckable(True)
        self.limButton.setToolTip(
            "Toggle the view of the limit lines on and off")
        self.icon_manager.set_icon(self.limButton, "amarok_edit.svg")
        self.mpl_toolbar.addWidget(self.limButton)

        self.modeButton = QtWidgets.QToolButton(self)
        self.modeButton.clicked.connect(self.__toggle_lim_mode)
        self.modeButton.setToolTip(
            "Toggles between selecting the entire " +
            "histogram, area included in the limits and " +
            "areas included of the limits")
        self.icon_manager.set_icon(self.modeButton, "depth_profile_lim_all.svg")
        self.mpl_toolbar.addWidget(self.modeButton)

        self.viewButton = QtWidgets.QToolButton(self)
        self.viewButton.clicked.connect(self.__toggle_rel)
        # self.viewButton.setCheckable(True)
        self.viewButton.setToolTip("Switch between relative and absolute view")
        self.icon_manager.set_icon(self.viewButton, "depth_profile_abs.svg")
        self.mpl_toolbar.addWidget(self.viewButton)

        # Log scale & ignore elements button
        self.mpl_toolbar.addSeparator()
        self.__button_toggle_log = QtWidgets.QToolButton(self)
        self.__button_toggle_log.clicked.connect(self.__toggle_log_scale)
        self.__button_toggle_log.setCheckable(True)
        self.__button_toggle_log.setToolTip(
            "Toggle logarithmic Y axis scaling.")
        self.icon_manager.set_icon(self.__button_toggle_log,
                                   "monitoring_section.svg")
        self.mpl_toolbar.addWidget(self.__button_toggle_log)

        self.__button_toggle_absolute = QtWidgets.QToolButton(self)
        self.__button_toggle_absolute.clicked.connect(
            self.__toggle_absolute_values)
        self.__button_toggle_absolute.setCheckable(True)
        self.__button_toggle_absolute.setToolTip(
            "Toggle absolute values for elements.")
        self.icon_manager.set_icon(self.__button_toggle_absolute, "color.svg")
        self.mpl_toolbar.addWidget(self.__button_toggle_absolute)

        self.__button_ignores = QtWidgets.QToolButton(self)
        self.__button_ignores.clicked.connect(self.__ignore_elements_dialog)
        self.__button_ignores.setToolTip(
            "Select elements which are included in" +
            " ratio calculation.")
        self.icon_manager.set_icon(self.__button_ignores, "gear.svg")
        self.mpl_toolbar.addWidget(self.__button_ignores)

    def __uncheck_custom_buttons(self):
        """
        Uncheck custom buttons.
        """
        self.limButton.setChecked(False)

    def __uncheck_built_in_buttons(self):
        """
        Uncheck built.in buttons.
        """
        self.__button_drag.setChecked(False)
        self.__button_zoom.setChecked(False)

    def __toggle_lim_mode(self):
        """
        Toggle lim mode.
        """
        self.__switch_lim_mode()
        self.on_draw()

    def __switch_lim_mode(self, mode=""):
        """Switch between the three modes:
        a = enable relative view throughout the histogram
        b = enable relative view only within limits
        c = enable relative view only outside limits
        """
        if mode != "":
            self.lim_mode = mode
        elif self.lim_mode == "a":
            self.lim_mode = "b"
        elif self.lim_mode == "b":
            self.lim_mode = "c"
        else:
            self.lim_mode = "a"
        self.icon_manager.set_icon(self.modeButton,
                                   self.lim_icons[self.lim_mode])

    def __toggle_lim_lines(self):
        """Toggles the usage of limit lines.
        """
        self.__toggle_drag_zoom()
        self.mpl_toolbar.mode = "limit setting tool"

    def __toggle_rel(self):
        """Toggles between the absolute and relative views.
        """
        self.__rel_graph = not self.__rel_graph
        if self.__rel_graph:
            self.icon_manager.set_icon(self.viewButton, "depth_profile_rel.svg")
        else:
            self.icon_manager.set_icon(self.viewButton, "depth_profile_abs.svg")

        self.on_draw()

    def __toggle_drag_zoom(self):
        """Toggles drag zoom.
        """
        if self.__button_drag.isChecked():
            self.mpl_toolbar.pan()
        if self.__button_zoom.isChecked():
            self.mpl_toolbar.zoom()

        self.__button_drag.setChecked(False)
        self.__button_zoom.setChecked(False)

    def __ignore_elements_dialog(self):
        """Ignore elements from elements ratio calculation.
        """
        dialog = DepthProfileIgnoreElements(self.elements,
                                            self.__ignore_from_graph,
                                            self.__ignore_from_ratio)
        self.__ignore_from_graph = dialog.ignore_from_graph
        self.__ignore_from_ratio = dialog.ignore_from_ratio
        self.on_draw()

    def __toggle_absolute_values(self):
        """Toggle absolute values for the elements in the graph.
        """
        self.__absolute_values = self.__button_toggle_absolute.isChecked()
        self.on_draw()  # TODO dont redraw everything, just update legend

    def __toggle_log_scale(self):
        """Toggle log scaling for Y axis in depth profile graph.
        """
        self.__log_scale = self.__button_toggle_log.isChecked()
        self.on_draw()


class LimitLines:
    """Stores values for limits used in depth calculations. Also used to draw
    lines on canvas.
    """

    def __init__(self, a=0.0, b=0.0):
        """Inits LimitLines object

        Args:
            a: position of the first limit line on x-axis
            b: position of the second limit line on x-axis
        """

        # Internally, LimitLine object does not care if a is bigger than b
        # or vice versa so we just store them in a list without sorting
        # them.
        self.__limits = [a, b]
        self.__next_limit = 1

    def __switch(self):
        """Switches the current limit between first and last.
        """
        self.__next_limit = abs(1 - self.__next_limit)

    def set(self, value, switch=True):
        """Sets the value for current limit.

        Args:
            value: float value for the current limit
            switch: sets if the current limit is switched after setting
            the value
        """
        self.__limits[self.__next_limit] = value
        if switch:
            self.__switch()

    def draw(self, axes, highlight_last=False):
        """Draws limit lines on the given axes.

        Args:
            axes: axes object that the lines will be drawn
            highlight_last: highlights the last set limit with a different
                            color
        """
        # TODO better highlighting OR draggable 2d lines
        for i in range(len(self.__limits)):
            if highlight_last and self.__next_limit != i:
                axes.axvline(x=self.__limits[i], linestyle="-",
                             color="yellow")
                axes.axvline(x=self.__limits[i], linestyle="--")
            else:
                axes.axvline(x=self.__limits[i], linestyle="--")

    def get_limits(self):
        """Returns limits sorted by value (lowest first).
        """
        # Here we check the order of limits and return smaller one first
        # and bigger one last
        if self.__limits[0] <= self.__limits[1]:
            return self.__limits[0], self.__limits[1]
        return self.__limits[1], self.__limits[0]
