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
Sinikka Siironen, 2020 Juhani Sundell, 2021 Aleksi Kauppi

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
             "Juhani Sundell \n Aleksi Kauppi"
__version__ = "2.0"

import modules.math_functions as mf

from typing import List, Dict, Optional, Set

from pathlib import Path

from dialogs.measurement.depth_profile_numeric_limits \
    import NumericLimitsDialog
from dialogs.measurement.depth_profile_ignore_elements \
    import DepthProfileIgnoreElements
    
from widgets.matplotlib.base import MatplotlibWidget
from widgets.matplotlib import mpl_utils
from widgets.matplotlib.mpl_utils import AlternatingLimits
from widgets.matplotlib.mpl_utils import LineChart
from widgets.icon_manager import IconManager

from modules.depth_files import DepthProfileHandler
from modules.depth_files import DepthProfile
from modules.element import Element
from modules.base import Range
from modules.enums import DepthProfileUnit
from modules.observing import ProgressReporter

from PyQt5 import QtCore
from PyQt5 import QtWidgets


class MatplotlibDepthProfileWidget(MatplotlibWidget):
    """Depth profile widget that handles drawing depth profiles.
    """

    def __init__(self, parent: QtWidgets.QWidget, depth_dir: Path,
                 elements: List[Element], rbs_list: Dict[str, Element],
                 icon_manager: IconManager, selection_colors: Dict[str, str],
                 x_units: DepthProfileUnit = DepthProfileUnit.NM,
                 depth_scale: Optional[Range] = None,
                 add_line_zero: bool = False, systematic_error: float = 3.0,
                 show_eff_files: bool = False,
                 used_eff_str: str = None,
                 progress: Optional[ProgressReporter] = None):
        """Inits depth profile widget.

        Args:
            parent: A DepthProfileWidget class object.
            depth_dir: A directory where the depth files are located.
            elements: A list of Element objects.
            rbs_list: A dictionary of RBS selection elements containing
                scatter elements.
            depth_scale: A tuple of depth scaling values.
            x_units: An unit to be used as x axis.
            add_line_zero: A boolean representing if vertical line is drawn at
                zero.
            show_eff_files: A boolean representing if used efficiency files
                are shown
            used_eff_str: A string representing used efficiency files   
            systematic_error: A double representing systematic error.
            progress: a ProgressReporter object
        """
        super().__init__(parent)

        self.canvas.manager.set_title("Depth Profile")
        self.axes.fmt_xdata = lambda x: f"{x:1.2f}"
        self.axes.fmt_ydata = lambda y: f"{y:1.2f}"
        self.axes.set_xlabel(f"Depth ({x_units})")
        self.axes.set_ylabel("Concentration (at.%)")

        self._elements = elements
        self._ignore_from_graph: Set[Element] = set()
        self._ignore_from_ratio: Set[Element] = set()
        self._systematic_error = systematic_error
        
        self._show_eff_files = show_eff_files
        self.used_eff_str = used_eff_str
        self.eff_text = None

        self._profile_handler = DepthProfileHandler()
        self._profile_handler.read_directory(
            depth_dir, self._elements, depth_units=x_units)

        if progress is not None:
            progress.report(50)

        self._selection_colors = selection_colors
        self._icon_manager = icon_manager

        self._lim_icons = {
            "a": "depth_profile_lim_all.svg",
            "b": "depth_profile_lim_in.svg",
            "c": "depth_profile_lim_ex.svg"
        }
        self._lim_mode = "a"

        self.canvas.mpl_connect("button_press_event", self.onclick)

        self._position_set = False
        self._relative_graph = False
        self._absolute_values = False
        self._rbs_list = rbs_list
        self._fork_toolbar_buttons()

        self._limit_lines = AlternatingLimits(
            self.canvas, self.axes, xs=self._profile_handler.get_depth_range(),
            colors=("blue", "red"))
        self._line_chart = self._create_depth_profile_chart()
        self.axes.set_ylim(bottom=0.0)
        self._make_legend_box()

        self.axes.axhline(y=0, color="#000000")
        if add_line_zero:
            self.axes.axvline(
                x=0, linestyle="-", linewidth=3, color="#C0C0C0", alpha=0.75)

        if depth_scale:
            self.axes.axvspan(
                *depth_scale, color="#C0C0C0", alpha=0.20, edgecolor=None)

        self.remove_axes_ticks()

        if progress is not None:
            progress.report(100)

    def onclick(self, event):
        """Handles clicks on the graph.

        Args:
            event: A click event on the graph
        """
        # Only inside the actual graph axes, else do nothing.
        if event.inaxes != self.axes:
            return
        cursor_location = [int(event.xdata), int(event.ydata)]
        
        if event.button == 1 and self.limButton.isChecked():
            self._limit_lines.update_graph(event.xdata)    
        if event.button == 3:
            self._numeric_limits_menu(event, cursor_location)
        
        self._make_legend_box()

    def _numeric_limits_menu(self, event, cursor_location):
        menu = QtWidgets.QMenu(self)

        action = QtWidgets.QAction(self.tr("Set limits numerically..."), self)
        action.triggered.connect(self.numeric_limits_dialog)
        menu.addAction(action)
        
        coords = self.canvas.geometry().getCoords()
        point = QtCore.QPoint(event.x, coords[3] - event.y - coords[1])
        # coords[1] from spacing
        menu.exec_(self.canvas.mapToGlobal(point))
        
    def numeric_limits_dialog(self):
        """Show numeric limits dialog and update graph if new limits are set.
        """
        lim_a, lim_b = self._limit_lines.get_range()
        limit_dialog = NumericLimitsDialog(lim_a, lim_b)
        
        if not limit_dialog.exec_():
            return
        
        self._limit_lines.update_graph(limit_dialog.limit_min)
        self._limit_lines.update_graph(limit_dialog.limit_max) 

    def get_profiles_to_use(self) -> Dict[str, DepthProfile]:
        """Determines what files to use for plotting. Either relative, absolute
        or a merger of the two.
        """
        lim_a, lim_b = self._limit_lines.get_range()

        if not self._relative_graph:
            profiles = self._profile_handler.get_absolute_profiles()
        elif self._lim_mode == "a":
            profiles = self._profile_handler.get_relative_profiles()
        elif self._lim_mode == "b":
            profiles = self._profile_handler.merge_profiles(
                lim_a, lim_b, method="abs_rel_abs")
        else:
            profiles = self._profile_handler.merge_profiles(
                lim_a, lim_b, method="rel_abs_rel")
        return {
            k: v for k, v in profiles.items() if k != "total"
        }

    def _create_depth_profile_chart(self) -> LineChart:
        profiles_to_use = self.get_profiles_to_use()
        lineargs = []
        for key, profile in sorted(
                profiles_to_use.items(), key=lambda tpl: tpl[1].element):

            # Check RBS selection
            element = profile.element
            if key in self._rbs_list.values():
                color_key = f"RBS_{element}0"
            else:
                color_key = f"{element}0"

            lineargs.append(LineChart.get_line_args(
                element, profile.depths, profile.concentrations,
                color=self._selection_colors.get(color_key, "red")))

        return LineChart(self.canvas, self.axes, lineargs)

    def _update_depth_profile_chart(self) -> None:
        profiles_to_use = self.get_profiles_to_use()
        lineargs = ({
            "key": v.element,
            "ys": v.concentrations
        } for v in profiles_to_use.values())
        self._line_chart.update_graph(lineargs)

    @mpl_utils.draw_and_flush
    def _make_legend_box(self) -> None:
        """Make legend box for the graph.
        """
        box = self.axes.get_position()
        if not self._position_set:
            self.axes.set_position(
                [box.x0, box.y0, box.width * 0.8, box.height])
            self._position_set = True
        handles, labels = self.axes.get_legend_handles_labels()

        # Calculate values to be displayed in the legend box
        # TODO make profile_handler use Element objects as keys so
        #   there is no need to do this conversion
        ignored_str = set(str(elem) for elem in self._ignore_from_ratio)
        lim_a, lim_b = self._limit_lines.get_range()
        if self._absolute_values:
            concentrations = self._profile_handler.integrate_concentrations(
                lim_a, lim_b)
            percentages, moes = {}, {}
        else:
            percentages, moes = self._profile_handler.calculate_ratios(
                ignored_str, lim_a, lim_b, self._systematic_error)
            concentrations = {}

        # Fix labels to proper format, with MoE
        labels_w_percentages = []
        rbs_values = {elem.symbol for elem in self._rbs_list.values()}
        for element_str in labels:
            element = Element.from_string(element_str)
            if element.isotope is None:
                element_isotope = ""
            else:
                element_isotope = str(element.isotope)

            rbs_asterisk = "*" if element_str in rbs_values else ""
            element_name = f"{element.symbol}{rbs_asterisk}"
            elem_lbl = f"$^{{{element_isotope}}}${element_name}"

            if not self._absolute_values and percentages[element_str] is not \
                    None:
                percentage = percentages[element_str]
                moe = moes[element_str]
                rounding = mf.get_rounding_decimals(moe)
                if rounding:
                    str_ratio = f"{round(percentage, rounding)}%"
                    str_err = f"± {round(moe, rounding)}%"
                else:
                    str_ratio = f"{int(percentage)}%"
                    str_err = f"± {int(moe)}%"
                lbl_str = f"{elem_lbl} {str_ratio:<6} {str_err}"
            else:
                lbl_str = f"{element_isotope:>3}{element_name:<3}"

            # Use absolute values for the elements instead of percentages.
            if self._absolute_values:
                conc = concentrations[element_str]
                lbl_str = f"{elem_lbl} {round(conc, 3):<7} at./1e15 at./cm²"
            labels_w_percentages.append(lbl_str)

        leg = self.axes.legend(
            handles, labels_w_percentages, loc=3, bbox_to_anchor=(1, 0),
            borderaxespad=0, prop={"size": 11, "family": "monospace"})
        
        # If "Show used efficiency files" is checked and text-object is not
        # yet created.
        if self._show_eff_files and self.eff_text is None:
            eff_str = self.used_eff_str.replace("\t","") 
            
            # Set position of text according to amount of lines in the string
            line_count = eff_str.count("\n") + 1
            yposition_txt = 1 - 0.08 * line_count
            xposition_txt = 1.01
            
            self.eff_text=self.axes.text(
                xposition_txt, yposition_txt, eff_str,
                transform=self.axes.transAxes,
                fontsize=11, fontfamily="monospace")
            self.axes.transData
        
        for handle in leg.legendHandles:
            handle.set_linewidth(3.0)

    def _fork_toolbar_buttons(self):
        """Custom toolbar buttons be here.
        """
        # But first, let's play around with the existing MatPlotLib buttons.
        _, self._button_drag, self._button_zoom = \
            mpl_utils.get_toolbar_elements(
                self.mpl_toolbar, drag_callback=self._uncheck_custom_buttons,
                zoom_callback=self._uncheck_custom_buttons)

        self.limButton = QtWidgets.QToolButton(self)
        self.limButton.clicked.connect(self._toggle_lim_lines)
        self.limButton.setCheckable(True)
        self.limButton.setToolTip(
            "Toggle the view of the limit lines on and off")
        self._icon_manager.set_icon(self.limButton, "amarok_edit.svg")
        self.mpl_toolbar.addWidget(self.limButton)

        self.modeButton = QtWidgets.QToolButton(self)
        self.modeButton.clicked.connect(self._toggle_lim_mode)
        self.modeButton.setToolTip(
            "Toggles between selecting the entire " +
            "histogram, area included in the limits and " +
            "areas included of the limits")
        self._icon_manager.set_icon(
            self.modeButton, "depth_profile_lim_all.svg")
        self.mpl_toolbar.addWidget(self.modeButton)

        self.viewButton = QtWidgets.QToolButton(self)
        self.viewButton.clicked.connect(self._toggle_rel)
        self.viewButton.setToolTip("Switch between relative and absolute view")
        self._icon_manager.set_icon(self.viewButton, "depth_profile_abs.svg")
        self.mpl_toolbar.addWidget(self.viewButton)

        # Log scale & ignore elements button
        self.mpl_toolbar.addSeparator()
        self._button_toggle_log = QtWidgets.QToolButton(self)
        self._button_toggle_log.clicked.connect(self._toggle_log_scale)
        self._button_toggle_log.setCheckable(True)
        self._button_toggle_log.setToolTip(
            "Toggle logarithmic Y axis scaling.")
        self._icon_manager.set_icon(
            self._button_toggle_log, "monitoring_section.svg")
        self.mpl_toolbar.addWidget(self._button_toggle_log)

        self._button_toggle_absolute = QtWidgets.QToolButton(self)
        self._button_toggle_absolute.clicked.connect(
            self._toggle_absolute_values)
        self._button_toggle_absolute.setCheckable(True)
        self._button_toggle_absolute.setToolTip(
            "Toggle absolute values for elements.")
        self._icon_manager.set_icon(self._button_toggle_absolute, "color.svg")
        self.mpl_toolbar.addWidget(self._button_toggle_absolute)

        self._button_ignores = QtWidgets.QToolButton(self)
        self._button_ignores.clicked.connect(self._ignore_elements_dialog)
        self._button_ignores.setToolTip(
            "Select elements which are included in "
            "ratio calculation.")
        self._icon_manager.set_icon(self._button_ignores, "gear.svg")
        self.mpl_toolbar.addWidget(self._button_ignores)

    def _uncheck_custom_buttons(self) -> None:
        """Uncheck custom buttons.
        """
        self.limButton.setChecked(False)

    def _toggle_lim_mode(self, *_) -> None:
        """Switch between the three modes:
        a = enable relative view throughout the histogram
        b = enable relative view only within limits
        c = enable relative view only outside limits

        Args:
            *_: unused event args
        """
        if self._lim_mode == "a":
            self._lim_mode = "b"
        elif self._lim_mode == "b":
            self._lim_mode = "c"
        else:
            self._lim_mode = "a"
        self._icon_manager.set_icon(
            self.modeButton, self._lim_icons[self._lim_mode])
        self._update_depth_profile_chart()

    def _toggle_lim_lines(self) -> None:
        """Toggles the usage of limit lines.
        """
        self._toggle_drag_zoom()
        self.mpl_toolbar.mode = "limit setting tool"

    def _toggle_rel(self) -> None:
        """Toggles between the absolute and relative views.
        """
        self._relative_graph = not self._relative_graph
        if self._relative_graph:
            self._icon_manager.set_icon(
                self.viewButton, "depth_profile_rel.svg")
        else:
            self._icon_manager.set_icon(
                self.viewButton, "depth_profile_abs.svg")

        self._update_depth_profile_chart()

    def _toggle_drag_zoom(self) -> None:
        """Toggles drag zoom.
        """
        if self._button_drag.isChecked():
            self.mpl_toolbar.pan()
        if self._button_zoom.isChecked():
            self.mpl_toolbar.zoom()

        self._button_drag.setChecked(False)
        self._button_zoom.setChecked(False)

    def _ignore_elements_dialog(self, *_) -> None:
        """Ignore elements from elements ratio calculation.
        """
        dialog = DepthProfileIgnoreElements(
            self._elements, self._ignore_from_graph, self._ignore_from_ratio)

        if not dialog.exec_():
            return

        self._ignore_from_graph = set(dialog.ignored_from_graph)
        self._ignore_from_ratio = set(dialog.ignored_from_ratio)
        self._line_chart.hide_lines(self._ignore_from_graph)
        self._make_legend_box()

    def _toggle_absolute_values(self) -> None:
        """Toggle absolute values for the elements in the graph.
        """
        self._absolute_values = self._button_toggle_absolute.isChecked()
        self._make_legend_box()

    def _toggle_log_scale(self, *_) -> None:
        """Toggle log scaling for Y axis in depth profile graph.
        """
        if self._button_toggle_log.isChecked():
            self._line_chart.set_yscale("symlog")
        else:
            self._line_chart.set_yscale("linear")
