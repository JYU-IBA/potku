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

MatplotlibDepthProfileWidget handles the drawing and operation of the
depth profile graph.
"""
__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen \n " \
             "Samuli Rahkonen \n Miika Raunio \n Severi Jääskeläinen \n " \
             "Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen \n" \
             "Juhani Sundell"
__version__ = "2.0"

import modules.math_functions as mf

from typing import List
from typing import Optional
from typing import Dict

from pathlib import Path

from dialogs.measurement.depth_profile_ignore_elements \
    import DepthProfileIgnoreElements
from widgets.matplotlib.base import MatplotlibWidget
from widgets.matplotlib import mpl_utils
from widgets.matplotlib.mpl_utils import AlternatingLimits
from widgets.matplotlib.mpl_utils import LineChart

from modules.depth_files import DepthProfileHandler
from modules.depth_files import DepthProfile
from modules.element import Element
from modules.base import Range
from modules.enums import DepthProfileUnit

from PyQt5 import QtWidgets


class MatplotlibDepthProfileWidget(MatplotlibWidget):
    """Depth profile widget that handles drawing depth profiles.
    """

    def __init__(self, parent, depth_dir: Path, elements: List[Element],
                 rbs_list, x_units: DepthProfileUnit = DepthProfileUnit.NM,
                 depth_scale: Optional[Range] = None, add_legend=True,
                 add_line_zero=False, systematic_error=3.0,
                 progress=None):
        """Inits depth profile widget.

        Args:
            parent: A DepthProfileWidget class object.
            depth_dir: A directory where the depth files are located.
            elements: A list of Element objects.
            rbs_list: A dictionary of RBS selection elements containing
                scatter elements.
            depth_scale: A tuple of depth scaling values.
            x_units: An unit to be used as x axis.
            add_legend: A boolean of whether to show the legend.
            add_line_zero: A boolean representing if vertical line is drawn at
                zero.
            systematic_error: A double representing systematic error.
            progress: a ProgressReporter object
        """
        super().__init__(parent)

        self.canvas.manager.set_title("Depth Profile")
        self.axes.fmt_xdata = lambda x: "{0:1.2f}".format(x)
        self.axes.fmt_ydata = lambda y: "{0:1.2f}".format(y)
        self.elements = elements
        self.__systerr = systematic_error

        self.profile_handler = DepthProfileHandler()
        self.profile_handler.read_directory(
            depth_dir, self.elements, depth_units=x_units)
        if progress is not None:
            progress.report(50)

        self.__ignore_from_graph = set()
        self.__ignore_from_ratio = set()

        # TODO get selection colors and icon manager as parameters, not from
        #      parent
        self.selection_colors = parent.measurement.selector.get_colors()
        self.icon_manager = parent.icon_manager

        self.lim_icons = {
            "a": "depth_profile_lim_all.svg",
            "b": "depth_profile_lim_in.svg",
            "c": "depth_profile_lim_ex.svg"
        }
        self.lim_mode = "a"

        self.canvas.mpl_connect("button_press_event", self.onclick)

        self.__position_set = False
        self.__rel_graph = False
        self.__absolute_values = False
        self.__rbs_list = rbs_list
        self.__fork_toolbar_buttons()

        self.axes.set_xlabel(f"Depth ({x_units})")
        self.axes.set_ylabel('Concentration (at.%)')

        self.limit = AlternatingLimits(
            self.canvas, self.axes, xs=self.profile_handler.get_depth_range(),
            colors=("blue", "red"))
        self._line_chart = None
        self.depth_plots = {}
        self._update_depth_plots(self.get_profiles_to_use())
        self.axes.set_ylim(bottom=0.0)

        self.add_legend = add_legend
        if self.add_legend:
            self.__make_legend_box()

        self.axes.axhline(y=0, color="#000000")
        if add_line_zero:
            self._line_zero = self.axes.axvline(
                x=0, linestyle="-", linewidth=3, color="#C0C0C0", alpha=0.75)
        else:
            self._line_zero = None

        if depth_scale:
            self._vspan = self.axes.axvspan(
                *depth_scale, color="#C0C0C0", alpha=0.20, edgecolor=None)
        else:
            self._vspan = None

        self.remove_axes_ticks()

        if progress is not None:
            progress.report(100)

    def onclick(self, event):
        """Handles clicks on the graph.

        Args:
            event: A click event on the graph
        """
        if event.button == 1 and self.limButton.isChecked():
            self.limit.update_graph(event.xdata)
            if self.add_legend:
                self.__make_legend_box()

    def get_profiles_to_use(self) -> Dict[str, DepthProfile]:
        """Determines what files to use for plotting. Either relative, absolute
        or a merger of the two.
        """
        if not self.__rel_graph:
            return self.profile_handler.get_absolute_profiles()
        elif self.lim_mode == "a":
            return self.profile_handler.get_relative_profiles()

        lim_a, lim_b = self.limit.get_range()
        if self.lim_mode == "b":
            return self.profile_handler.merge_profiles(
                lim_a, lim_b, method="abs_rel_abs"
            )

        return self.profile_handler.merge_profiles(
            lim_a, lim_b, method="rel_abs_rel"
        )

    def _update_depth_plots(self, profiles: Dict[str, DepthProfile]):
        profiles_to_use = {
            k: v for k, v in profiles.items() if k != "total"
        }
        if self._line_chart is None:
            lineargs = []
            for key, profile in sorted(
                    profiles_to_use.items(), key=lambda tpl: tpl[1].element):

                # Check RBS selection
                element = profile.element
                if key in self.__rbs_list.values():
                    color_key = f"RBS_{element}0"
                else:
                    color_key = f"{element}0"

                lineargs.append(LineChart.get_line_args(
                    element, profile.depths, profile.concentrations,
                    color=self.selection_colors.get(color_key, "red")))

            self._line_chart = LineChart(self.canvas, self.axes, lineargs)
        else:
            lineargs = ({
                "key": v.element,
                "ys": v.concentrations
            } for v in profiles_to_use.values())
            self._line_chart.update_graph(lineargs)

    @mpl_utils.draw_and_flush
    def __make_legend_box(self):
        """Make legend box for the graph.
        """
        box = self.axes.get_position()
        if not self.__position_set:
            self.axes.set_position(
                [box.x0, box.y0, box.width * 0.8, box.height])
            self.__position_set = True
        handles, labels = self.axes.get_legend_handles_labels()

        # Calculate values to be displayed in the legend box
        # TODO make profile_handler use Element objects as keys so
        #   there is no need to do this conversion
        ignored_str = set(str(elem) for elem in self.__ignore_from_ratio)
        lim_a, lim_b = self.limit.get_range()
        if self.__absolute_values:
            concentrations = self.profile_handler.integrate_concentrations(
                lim_a, lim_b)
            percentages, moe = {}, {}
        else:
            percentages, moe = self.profile_handler.calculate_ratios(
                ignored_str, lim_a, lim_b, self.__systerr)
            concentrations = {}

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
            "Select elements which are included in "
            "ratio calculation.")
        self.icon_manager.set_icon(self.__button_ignores, "gear.svg")
        self.mpl_toolbar.addWidget(self.__button_ignores)

    def __uncheck_custom_buttons(self):
        """Uncheck custom buttons.
        """
        self.limButton.setChecked(False)

    def __uncheck_built_in_buttons(self):
        """Uncheck built.in buttons.
        """
        self.__button_drag.setChecked(False)
        self.__button_zoom.setChecked(False)

    def __toggle_lim_mode(self, *_):
        """Toggle lim mode.

        Args:
            *_: unused event args
        """
        self.__switch_lim_mode()

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
        self.icon_manager.set_icon(
            self.modeButton, self.lim_icons[self.lim_mode])
        self._update_depth_plots(self.get_profiles_to_use())

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

        self._update_depth_plots(self.get_profiles_to_use())

    def __toggle_drag_zoom(self):
        """Toggles drag zoom.
        """
        if self.__button_drag.isChecked():
            self.mpl_toolbar.pan()
        if self.__button_zoom.isChecked():
            self.mpl_toolbar.zoom()

        self.__button_drag.setChecked(False)
        self.__button_zoom.setChecked(False)

    def __ignore_elements_dialog(self, *_):
        """Ignore elements from elements ratio calculation.
        """
        dialog = DepthProfileIgnoreElements(
            self.elements, self.__ignore_from_graph, self.__ignore_from_ratio)

        if not dialog.exec_():
            return

        self._update_ignored(
            dialog.ignored_from_graph, dialog.ignored_from_ratio)

    def _update_ignored(self, ignored_graph, ignored_ratio):
        self.__ignore_from_graph = set(ignored_graph)
        self.__ignore_from_ratio = set(ignored_ratio)
        self._line_chart.hide_lines(self.__ignore_from_graph)
        if self.add_legend:
            self.__make_legend_box()

    def __toggle_absolute_values(self):
        """Toggle absolute values for the elements in the graph.
        """
        self.__absolute_values = self.__button_toggle_absolute.isChecked()
        if self.add_legend:
            self.__make_legend_box()

    def __toggle_log_scale(self, *_):
        """Toggle log scaling for Y axis in depth profile graph.
        """
        if self.__button_toggle_log.isChecked():
            self._line_chart.set_yscale("symlog")
        else:
            self._line_chart.set_yscale("linear")
