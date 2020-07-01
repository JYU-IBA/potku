# coding=utf-8
"""
Created on 15.5.2019
Updated on 17.5.2019

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2019 Heta Rekilä

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
__author__ = "Heta Rekilä"
__version__ = "2.0"

import matplotlib

from widgets.matplotlib import mpl_utils
from typing import Optional

from modules.element_simulation import ElementSimulation
from modules.concurrency import CancellationToken
from modules.target import Target
from modules.recoil_element import RecoilElement

from PyQt5 import QtWidgets
from PyQt5.QtCore import QLocale
from PyQt5.QtCore import pyqtSignal

from widgets.matplotlib.base import MatplotlibWidget
from widgets.simulation.point_coordinates import PointCoordinatesWidget


class RecoilAtomOptimizationWidget(MatplotlibWidget):
    """
    Class for showing optimized recoil elements.
    """
    color_scheme = {
        "Default color": "jet",
        "Greyscale": "Greys",
        "Greyscale (inverted)": "gray"
    }
    tool_modes = {
        0: "",
        1: "pan/zoom",  # Matplotlib's drag
        2: "zoom rect"  # Matplotlib's zoom
    }

    results_accepted = pyqtSignal(ElementSimulation)

    def __init__(self, parent, element_simulation: ElementSimulation,
                 target: Target, ct: Optional[CancellationToken] = None):
        super().__init__(parent)
        self.parent = parent
        self.element_simulation = element_simulation
        self.target = target
        self.locale = QLocale.c()

        self.trans = matplotlib.transforms.blended_transform_factory(
            self.axes.transData, self.axes.transAxes)
        self.layer_colors = [(0.9, 0.9, 0.9), (0.85, 0.85, 0.85)]
        self.axes.format_coord = mpl_utils.format_coord

        self.current_recoil: Optional[RecoilElement] = None

        self.radios = QtWidgets.QButtonGroup(self)
        self.radios.buttonToggled[QtWidgets.QAbstractButton, bool].connect(
            self.choose_recoil)

        widget = QtWidgets.QWidget()
        self.recoil_vertical_layout = QtWidgets.QVBoxLayout()
        self.recoil_vertical_layout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(self.recoil_vertical_layout)

        self.parent.recoilListLayout.addWidget(widget)

        # TODO move these to parent
        btn_txts = "First solution", "Median solution", "Last solution"
        for t in btn_txts:
            radio_btn = QtWidgets.QRadioButton(t)
            radio_btn.setEnabled(False)
            self.radios.addButton(radio_btn)
            self.recoil_vertical_layout.addWidget(radio_btn)

        self.move_results_btn = QtWidgets.QPushButton("Accept results")
        self.move_results_btn.setToolTip("Moves optimization results to recoil "
                                         "atom distribution view")
        self.move_results_btn.setEnabled(False)
        self.move_results_btn.clicked.connect(self._move_results)
        self.recoil_vertical_layout.addWidget(self.move_results_btn)

        self.stop_optim_btn = QtWidgets.QPushButton("Stop optimization")
        self.stop_optim_btn.setToolTip("Stops optimization after current "
                                       "generation has been evaluated.")
        self.stop_optim_btn.setEnabled(True)
        self.stop_optim_btn.clicked.connect(self._stop_optim)
        self.recoil_vertical_layout.addWidget(self.stop_optim_btn)

        self.cancellation_token = ct

        spacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum,
                                       QtWidgets.QSizePolicy.Expanding)
        self.recoil_vertical_layout.addItem(spacer)

        # A dictionary where keys are recoil elements and values are line
        # objects
        self.lines = {}
        self.selected_line = None
        self.highlighted_marker = None

        self.coordinates_widget = None
        self.coordinates_action = None

        # This customizes the toolbar buttons
        self.__fork_toolbar_buttons()

        self.name_y_axis = "Relative Concentration"
        self.name_x_axis = "Depth [nm]"

        self.canvas.mpl_connect('button_press_event', self.on_click)

        self.on_draw()

        if self.element_simulation.optimization_recoils:
            self.show_recoils()

    def choose_recoil(self, button, checked):
        if checked:
            try:
                self.current_recoil = button.recoil_element
            except AttributeError:
                return

        self.update_plot()

    def __fork_toolbar_buttons(self):
        """
        Fork navigation tool bar button into custom ones.
        """
        self.mpl_toolbar.mode_tool = 0

        self.__tool_label, self.__button_drag, self.__button_zoom = \
            mpl_utils.get_toolbar_elements(
                self.mpl_toolbar, drag_callback=self.__toggle_tool_drag,
                zoom_callback=self.__toggle_tool_zoom)

        # Make own buttons
        self.mpl_toolbar.addSeparator()

        # Coordinates widget
        self.coordinates_widget = PointCoordinatesWidget(self, optimize=True)
        self.coordinates_action = self.mpl_toolbar.addWidget(
            self.coordinates_widget)

        self.coordinates_widget.y_coordinate_box.setEnabled(False)
        self.coordinates_widget.x_coordinate_box.setEnabled(False)

    def on_click(self, event):
        """ On click event above graph.

        Args:
            event: A MPL MouseEvent
        """
        if not self.current_recoil:
            return
        # Don't do anything if drag tool or zoom tool is active.
        if self.__button_drag.isChecked() or self.__button_zoom.isChecked():
            return
        # Only inside the actual graph axes, else do nothing.
        if event.inaxes != self.axes:
            return
        if event.button == 1 and self.selected_line is not None:
            line_contains, line_info = self.selected_line.contains(event)
            if line_contains:
                i = line_info["ind"][0]
                clicked_point = self.current_recoil.get_point(i)

                if clicked_point is not None:
                    self.highlighted_marker.set_data(clicked_point.get_x(),
                                                     clicked_point.get_y())
                    self.highlighted_marker.set_visible(True)

                    self.coordinates_widget.x_coordinate_box.setValue(
                        clicked_point.get_x())
                    self.coordinates_widget.y_coordinate_box.setValue(
                        clicked_point.get_y())

                    self.canvas.draw()
                    self.canvas.flush_events()

    def on_draw(self):
        """
        Draw method for matplotlib.
        """
        self.axes.clear()  # Clear old stuff

        self.axes.set_ylabel(self.name_y_axis)
        self.axes.set_xlabel(self.name_x_axis)

        self.axes.set_xlim(-1, 40)
        self.axes.set_ylim(-0.1, 2)

        y = 0.95
        next_layer_position = 0
        target_thickness = 0
        for idx, layer in enumerate(self.target.layers):
            target_thickness += layer.thickness
            self.axes.axvspan(
                next_layer_position, next_layer_position + layer.thickness,
                facecolor=self.layer_colors[idx % 2]
            )

            # Put annotation in the middle of the rectangular patch.
            self.axes.text(layer.start_depth, y, layer.name,
                           transform=self.trans, fontsize=10, ha="left")
            y = y - 0.05
            if y <= 0.1:
                y = 0.95

            # Move the position where the next layer starts.
            next_layer_position += layer.thickness

        # Remove axis ticks and draw
        self.remove_axes_ticks()

        # TODO next line may show a warning 'Tight layout not applied. The left
        #      and right margins cannot be made large enough to accommodate all
        #      axes decorations.'
        self.canvas.draw()
        self.canvas.flush_events()

    def show_recoils(self):
        """
        Show optimized recoils in widget.
        """
        # Add radiobutton created in the beginning to match results
        for recoil, btn in zip(self.element_simulation.optimization_recoils,
                               self.radios.buttons()):
            # recoil.widgets.append(btn)
            btn.setEnabled(True)
            btn.recoil_element = recoil
            line, = self.axes.plot(recoil.get_xs(), recoil.get_ys(),
                                   color=recoil.color)
            self.lines[recoil] = line

        if self.element_simulation.optimization_recoils:
            self.move_results_btn.setEnabled(True)
            self.stop_optim_btn.setEnabled(False)

        self.selected_line, = self.axes.plot(
            0, 0, marker="o", markersize=10, linestyle="None", zorder=15,
            visible=False)
        self.highlighted_marker, = self.axes.plot(
            0, 0, marker="o", markersize=10, linestyle="None", color="yellow",
            zorder=20, visible=False)

        self.radios.buttons()[0].setChecked(True)

    def __toggle_tool_drag(self):
        """
        Toggle drag tool.
        """
        if self.__button_drag.isChecked():
            self.mpl_toolbar.mode_tool = 1
            self.__show_all_recoil = False
        else:
            self.mpl_toolbar.mode_tool = 0
            self.__show_all_recoil = True
        # self.canvas.draw_idle()

    def __toggle_tool_zoom(self):
        """
        Toggle zoom tool.
        """
        if self.__button_zoom.isChecked():
            self.mpl_toolbar.mode_tool = 2
        else:
            self.mpl_toolbar.mode_tool = 0
        # self.canvas.draw_idle()

    def update_plot(self):
        for recoil, line in self.lines.items():
            if recoil == self.current_recoil:
                line.set_alpha(1.0)
                line.set_zorder(5)
                self.selected_line.set_data(line.get_xdata(), line.get_ydata())
                self.selected_line.set_color(line.get_color())
                self.selected_line.set_visible(True)
            else:
                line.set_alpha(0.3)
                line.set_zorder(1)

        self.highlighted_marker.set_visible(False)

        last_point = self.current_recoil.get_last_point()
        last_point_x = last_point.get_x()
        x_min, x_max = self.axes.get_xlim()
        if x_max < last_point_x:
            self.axes.set_xlim(x_min, last_point_x + 0.04 * last_point_x)

        self.canvas.draw()
        self.canvas.flush_events()

    def _move_results(self, *_):
        """Moves the optimized results to regular recoils and closes the
        widget.
        """
        self.element_simulation.move_optimized_recoil_to_regular_recoils()
        self.move_results_btn.setEnabled(False)
        self.results_accepted.emit(self.element_simulation)

    def _stop_optim(self):
        if self.cancellation_token is not None:
            self.cancellation_token.request_cancellation()
        self.stop_optim_btn.setEnabled(False)


class RecoilAtomParetoFront(MatplotlibWidget):
    PADDING = 0.95, 1.05

    def __init__(self, parent):
        super().__init__(parent)
        self.pareto_front = None
        self.automatic_readjustment = True
        self.axes.set_yscale("symlog")
        self.x_range = None, None
        self.y_range = None, None
        self.home_btn = self.mpl_toolbar.children()[4]
        _, self.drag_btn, self.zoom_btn = mpl_utils.get_toolbar_elements(
            self.mpl_toolbar,
            drag_callback=lambda: self.set_autoadjustment(False),
            zoom_callback=lambda: self.set_autoadjustment(False))
        self.home_btn.clicked.connect(lambda: self.set_autoadjustment(True))

    def update_pareto_front(self, pareto_front):
        xs, ys = tuple(zip(*pareto_front))
        try:
            self.pareto_front.set_xdata(xs)
            self.pareto_front.set_ydata(ys)

            self.x_range = self._fix_range(
                self.x_range, xs, *RecoilAtomParetoFront.PADDING)
            self.y_range = self._fix_range(
                self.y_range, ys, *RecoilAtomParetoFront.PADDING)

            if self.automatic_readjustment:
                self.axes.set_xlim(self.x_range)
                self.axes.set_ylim(self.y_range)
        except AttributeError:
            self.pareto_front, = self.axes.plot(xs, ys, linestyle="None",
                                                marker="o")
            self.x_range = self.axes.get_xlim()
            self.y_range = self.axes.get_ylim()

        self.canvas.draw()
        self.canvas.flush_events()

    def set_autoadjustment(self, b):
        self.automatic_readjustment = b
        if b:
            self.mpl_toolbar.mode_tool = 0
            self.drag_btn.setChecked(False)
            self.zoom_btn.setChecked(False)

    @staticmethod
    def _fix_range(cur_range, axis, min_padding=1.0, max_padding=1.0):
        x0_min, x0_max = cur_range
        x1_min, x1_max = min(axis) * min_padding, max(axis) * max_padding

        if x0_min is None:
            x0_min = x1_min
        if x0_max is None:
            x0_max = x1_max

        return min(x0_min, x1_min), max(x0_max, x1_max)

