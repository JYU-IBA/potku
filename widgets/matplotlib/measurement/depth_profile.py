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

import modules.depth_files as df
import modules.masses as masses
import os
import re

from dialogs.measurement.depth_profile_ignore_elements \
    import DepthProfileIgnoreElements

from modules.element import Element

from PyQt5 import QtWidgets

from widgets.matplotlib.base import MatplotlibWidget


class MatplotlibDepthProfileWidget(MatplotlibWidget):
    """Depth profile widget that handles drawing depth profiles.
    """

    def __init__(self, parent, depth_dir, elements, rbs_list, depth_scale,
                 used_cuts, x_units='nm', legend=True, line_zero=False,
                 line_scale=False, systematic_error=3.0):
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
        self.depth_files = df.get_depth_files(self.elements, self.depth_dir,
                                              self.__used_cuts)
        self.read_files = []
        self.rel_files = []
        self.hyb_files = []
        self.__ignore_from_graph = []
        self.__ignore_from_ratio = []
        self.selection_colors = parent.measurement.selector.get_colors()
        self.icon_manager = parent.icon_manager
        self.lim_a = 0.0
        self.lim_b = 0.0
        self.lim_icons = {'a': 'depth_profile_lim_all.svg',
                          'b': 'depth_profile_lim_in.svg',
                          'c': 'depth_profile_lim_ex.svg'}
        self.lim_mode = 'a'
        self.canvas.mpl_connect('button_press_event', self.onclick)
        self.__files_read = False
        self.__limits_set = False
        self.__position_set = False
        self.__rel_graph = False
        self.__show_limits = False
        self.__log_scale = False
        self.__absolute_values = False
        self.__enable_norm_over_range = False
        self.__use_limit = self.__Limit()
        self.__rbs_list = rbs_list
        self.__fork_toolbar_buttons()
        self.on_draw()

    def onclick(self, event):
        """Handles clicks on the graph.

        Args:
            event: A click event on the graph
        """
        if event.button == 1 and self.__show_limits:
            if self.__use_limit.get() == 'a':
                self.lim_a = event.xdata
                self.__use_limit.switch()
            elif self.__use_limit.get() == 'b':
                self.lim_b = event.xdata
                self.__use_limit.switch()
            else:
                self.lim_b = event.xdata
                self.__use_limit.switch()
            if self.lim_a and self.lim_a > self.lim_b:
                self.__use_limit.switch()
                tmp = self.lim_a
                self.lim_a = self.lim_b
                self.lim_b = tmp
            self.on_draw()

    def __sortt(self, key):
        """
        Get isotope for key.

        Args:
            key: String that represents an Element.

        Return:
            Isotope or -1 if not key is "total".
        """
        if key == "total":
            return -1
        if type(key) is Element:
            element_object = key
        else:
            element_object = Element.from_string(key)
        element = element_object.symbol
        isotope = element_object.isotope
        if not isotope:
            isotope = masses.get_standard_isotope(element)
        return isotope

    def on_draw(self):
        """Draws the depth profile graph
        """
        # Values for zoom
        x_min, x_max = self.axes.get_xlim()
        y_min, y_max = self.axes.get_ylim()

        # Clear axes for a new draw.
        self.axes.clear()

        # Select the units of the x-axis and what columns to read 
        # from the depth files
        y_column = 3
        if self.x_units == 'nm':
            x_column = 2
        else:
            x_column = 0
        self.axes.set_xlabel('Depth (%s)' % self.x_units)
        self.axes.set_ylabel('Concentration (at.%)')

        # If files have not been read before, they are now
        if not self.__files_read:
            full_paths = []
            for file in self.depth_files:
                full_path = os.path.join(self.depth_dir, file)
                full_paths.append(full_path)

            try:
                self.read_files = df.extract_from_depth_files(full_paths,
                                                              self.elements,
                                                              x_column,
                                                              y_column)
                self.__files_read = True
                self.rel_files = df.create_relational_depth_files(
                    self.read_files)
                # if not self.lim_a:
                self.lim_a = self.read_files[0][1][0]
                self.lim_b = self.read_files[0][1][-1]
                # self.__limits_set = not self.__limits_set
            except FileNotFoundError:
                self.__files_read = True

        # Determine what files to use for plotting
        if not self.__rel_graph:
            files_to_use = self.read_files
        elif self.lim_mode == 'a':
            files_to_use = self.rel_files
        else:
            tmp_a = list
            tmp_b = list
            if self.lim_mode == 'b':
                tmp_a = self.read_files
                tmp_b = self.rel_files
            else:
                tmp_a = self.rel_files
                tmp_b = self.read_files
            self.hyb_files = df.merge_files_in_range(tmp_a,
                                                     tmp_b,
                                                     self.lim_a,
                                                     self.lim_b)
            files_to_use = self.hyb_files

        # Plot the limits a and b
        if self.__show_limits:
            self.axes.axvline(x=self.lim_a, linestyle="--")
            if self.lim_b:  # TODO: Why is this sometimes null?
                self.axes.axvline(x=self.lim_b, linestyle="--")

        self.axes.axhline(y=0, color="#000000")
        if self.__line_zero:
            self.axes.axvline(x=0, linestyle="-", linewidth=3,
                              color="#C0C0C0", alpha=0.75)

        if self.__line_scale:
            self.axes.axvspan(self.__depth_scale[0], self.__depth_scale[1],
                              color='#C0C0C0', alpha=0.20, edgecolor=None)

        # Plot the lines
        files_to_use = sorted(files_to_use, key=lambda x: self.__sortt(x[0]))
        self.elements = sorted(self.elements, key=lambda x: self.__sortt(x))
        for file in files_to_use:
            if file[0] == 'total' or file[0] in self.__ignore_from_graph:
                continue
            element = re.sub("\d+", "", file[0])
            isotope = re.sub("\D", "", file[0])

            # Check RBS selection
            rbs_string = ""
            if file[0] in self.__rbs_list.values():
                rbs_string = "*"
                color_key = "{0}{1}{2}0".format("RBS_", isotope, element)
            else:
                color_key = "{0}{1}0".format(isotope, element)
            # TODO: erd_depth for multiple selections of same element.

            axe1 = file[1]
            axe2 = file[2]

            filler_length = 3 - len(isotope)
            filler_prefix = ""
            filler_suffix = ""
            for unused_i in range(0, filler_length):
                filler_prefix += "\ "
            filler_length = 4 - len(element) - len(rbs_string)
            for unused_i in range(0, filler_length):
                filler_suffix += "\ "
            # label = r"$^{\mathtt{" + filler_prefix + str(isotope) + \
            #        "}}\mathtt{" + element + rbs_string + filler_suffix + "}$"
            label = str(isotope) + element

            if len(axe1) > len(axe2):
                axe2.append(0.0)
            self.axes.plot(axe1, axe2, label=label,
                           color=self.selection_colors[color_key])

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

        # TODO don't calculate these if lim selection is unchanged
        # TODO don't calculate concentrations if self.__absolute_values is false
        concentrations = df.integrate_concentrations(self.read_files,
                                                     self.__ignore_from_ratio,
                                                     self.lim_a,
                                                     self.lim_b)
        percentages, moe = df.integrate_lists(self.read_files,
                                              self.__ignore_from_ratio,
                                              self.lim_a,
                                              self.lim_b,
                                              self.__systerr)
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
            if percentages[element_str] is not None:
                rounding = self.__physic_rounding_decimals(moe[element_str])
                # lbl_str = '%s %.3f%% ±%.3f%%' % (labels[i],
                #                             percentages[element_str],
                #                             moe[element_str])
                # Extra 5 from math text format for isotope index
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
                            round(sum(concentrations[element_str]), 3))
            labels_w_percentages.append(lbl_str)
        leg = self.axes.legend(handles, labels_w_percentages,
                               loc=3, bbox_to_anchor=(1, 0),
                               borderaxespad=0, prop={'size': 11,
                                                      'family': "monospace"})
        for handle in leg.legendHandles:
            handle.set_linewidth(3.0)

    def __physic_rounding_decimals(self, floater):
        """Find correct decimal count for rounding to 15-rule.
        """
        i = 0
        temp = floater
        if temp < 0.001:
            return 3
        while temp < 15:
            temp *= 10
            i += 1
        # At the index i the value is above 15 so return i - 1 
        # for correct decimal count.
        return i - 1

    def __fork_toolbar_buttons(self):
        """Custom toolbar buttons be here.
        """
        # But first, let's play around with the existing MatPlotLib buttons.
        self.__button_drag = self.mpl_toolbar.children()[12]
        self.__button_zoom = self.mpl_toolbar.children()[14]
        self.__button_drag.clicked.connect(self.__uncheck_custom_buttons)
        self.__button_zoom.clicked.connect(self.__uncheck_custom_buttons)

        self.limButton = QtWidgets.QToolButton(self)
        self.limButton.clicked.connect(self.__toggle_lim_lines)
        self.limButton.setCheckable(True)
        self.limButton.setToolTip(
            "Toggle the view of the limit lines on and off")
        self.icon_manager.set_icon(self.limButton, "amarok_edit.svg")
        self.mpl_toolbar.addWidget(self.limButton)

        self.modeButton = QtWidgets.QToolButton(self)
        self.modeButton.clicked.connect(self.__toggle_lim_mode)
        self.modeButton.setEnabled(False)
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
        if self.__show_limits:
            self.limButton.setChecked(False)
            self.__toggle_lim_lines()

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

        # Commented out self.axes.clear() because it resets zoom if called
        # here.
        #self.axes.clear()
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
        #TODO lim lines should not be toggled off when zoom or pan is selected
        self.__toggle_drag_zoom()
        self.__switch_lim_mode('a')
        self.__show_limits = not self.__show_limits
        self.modeButton.setEnabled(self.__show_limits)
        if self.__show_limits:
            self.__uncheck_built_in_buttons()
            self.mpl_toolbar.mode = "Limit setting tool"
        else:
            self.mpl_toolbar.mode = ""
        self.__enable_norm_over_range = False

        self.on_draw()

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
        """
        Toggle drag zoom.
        """
        # self.__tool_label.setText("")
        if self.__button_drag.isChecked():
            self.mpl_toolbar.pan()
        if self.__button_zoom.isChecked():
            self.mpl_toolbar.zoom()

        #TODO this should not be done when changing from lim tool to zoom or pan
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
        self.on_draw()

    def __toggle_log_scale(self):
        """Toggle log scaling for Y axis in depth profile graph.
        """
        self.__log_scale = self.__button_toggle_log.isChecked()
        self.on_draw()

    class __Limit:
        """Simple object to control when setting the integration
        limits in Depth Profile.
        """

        def __init__(self):
            """Inits __limit
            """
            self.limit = 'b'

        def switch(self):
            """ Switches limit between a and b.
            """
            if self.limit == 'b':
                self.limit = 'a'
            else:
                self.limit = 'b'

        def get(self):
            """ Returns the current limit.

            Return:
                The current limit a or b.
            """
            return self.limit
