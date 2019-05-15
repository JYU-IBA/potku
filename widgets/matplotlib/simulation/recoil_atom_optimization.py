# coding=utf-8
"""
Created on 15.5.2019
Updated on 15.5.2019

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

from modules.general_functions import to_superscript

from PyQt5 import QtWidgets
from PyQt5.QtCore import QLocale

from widgets.matplotlib.base import MatplotlibWidget
from widgets.simulation.point_coordinates import PointCoordinatesWidget


class RecoilAtomOptimizationWidget(MatplotlibWidget):
    """
    Class for showing optimized recoil elements.
    """
    tool_modes = {0: "",
                  1: "pan/zoom",  # Matplotlib's drag
                  2: "zoom rect"  # Matplotlib's zoom
                  }

    def __init__(self, parent, element_simulation):
        super().__init__(parent)
        self.parent = parent
        self.element_simulation = element_simulation
        self.locale = QLocale.c()

        self.axes.format_coord = self.format_coord

        self.current_recoil = None

        self.radios = QtWidgets.QButtonGroup(self)
        self.radios.buttonToggled[QtWidgets.QAbstractButton, bool].connect(
            self.choose_recoil)

        widget = QtWidgets.QWidget()
        self.recoil_vertical_layout = QtWidgets.QVBoxLayout()
        self.recoil_vertical_layout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(self.recoil_vertical_layout)

        self.parent.ui.recoilListLayout.addWidget(widget)

        self.first_sol_btn = QtWidgets.QRadioButton("First solution")
        self.first_sol_btn.setEnabled(False)
        self.last_sol_btn = QtWidgets.QRadioButton("Last solution")
        self.last_sol_btn.setEnabled(False)
        self.radios.addButton(self.first_sol_btn)
        self.radios.addButton(self.last_sol_btn)
        self.recoil_vertical_layout.addWidget(self.first_sol_btn)
        self.recoil_vertical_layout.addWidget(self.last_sol_btn)

        spacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum,
                                       QtWidgets.QSizePolicy.Expanding)
        self.recoil_vertical_layout.addItem(spacer)

        # Markers representing points
        self.markers = None
        # Lines connecting markers
        self.lines = None
        # Markers representing selected points
        self.markers_selected = None
        # Clicked point
        self.clicked_point = None

        self.coordinates_widget = None
        self.coordinates_action = None

        # This customizes the toolbar buttons
        self.__fork_toolbar_buttons()

        self.name_y_axis = "Relative Concentration"
        self.name_x_axis = "Depth [nm]"

        # This holds the other recoil not currently selected
        self.other_recoil = None
        self.other_recoil_line = None

        self.__show_all_recoil = True

        self.canvas.mpl_connect('button_press_event', self.on_click)

        self.on_draw()

        if self.element_simulation.optimization_recoils:
            self.show_recoils()

    def choose_recoil(self, button, checked):
        for recoil_element in self.element_simulation.optimization_recoils:
            b = recoil_element.widgets[0]
            if b == button:
                self.current_recoil = recoil_element
            else:
                self.other_recoil = recoil_element

        self.clicked_point = None
        if self.markers_selected:
            self.markers_selected.set_visible(False)
            self.coordinates_widget.x_coordinate_box.setEnabled(False)
            self.coordinates_widget.y_coordinate_box.setEnabled(False)

        self.update_plot()
        self.__update_figure()

    def __fork_toolbar_buttons(self):
        """
        Fork navigation tool bar button into custom ones.
        """
        self.mpl_toolbar.mode_tool = 0
        self.__tool_label = self.mpl_toolbar.children()[24]
        self.__button_drag = self.mpl_toolbar.children()[12]
        self.__button_zoom = self.mpl_toolbar.children()[14]
        self.__button_drag.clicked.connect(self.__toggle_tool_drag)
        self.__button_zoom.clicked.connect(self.__toggle_tool_zoom)

        # Make own buttons
        self.mpl_toolbar.addSeparator()

        # Coordinates widget
        self.coordinates_widget = PointCoordinatesWidget(self, optimize=True)
        self.coordinates_action = self.mpl_toolbar.addWidget(
            self.coordinates_widget)

        self.coordinates_widget.y_coordinate_box.setEnabled(False)
        self.coordinates_widget.x_coordinate_box.setEnabled(False)

    def format_coord(self, x, y):
        """
        Format mouse coordinates.

        Args:
            x: X coordinate.
            y: Y coordinate.

        Return:
            Formatted text.
        """
        x_part = "\nx:{0:1.2f},".format(x)
        y_part = "\ny:{0:1.4f}".format(y)
        return x_part + y_part

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
        if event.button == 1:  # Left click
            marker_contains, marker_info = self.markers.contains(event)
            if marker_contains:  # If clicked a point
                self.coordinates_widget.x_coordinate_box.setEnabled(True)
                self.coordinates_widget.y_coordinate_box.setEnabled(True)
                i = marker_info['ind'][0]  # The clicked point's index
                clicked_point = self.current_recoil.get_point_by_i(i)
                self.clicked_point = clicked_point

                self.update_plot()

    def on_draw(self):
        """
        Draw method for matplotlib.
        """
        self.axes.clear()  # Clear old stuff

        self.axes.set_ylabel(self.name_y_axis)
        self.axes.set_xlabel(self.name_x_axis)

        self.axes.set_xlim(-1, 40)
        self.axes.set_ylim(-0.1, 2)

        # Remove axis ticks and draw
        self.remove_axes_ticks()
        self.canvas.draw()

    def show_recoils(self):
        """
        Show optimized recoils in widget.
        """
        self.current_recoil = self.element_simulation.optimization_recoils[0]
        self.other_recoil = self.element_simulation.optimization_recoils[-1]
        # Add radiobutton created in the beginning to match results
        self.current_recoil.widgets.append(self.first_sol_btn)
        self.other_recoil.widgets.append(self.last_sol_btn)

        # Create necessary lines and markers
        color = str(self.current_recoil.color.name())
        self.lines, = self.axes.plot(self.current_recoil.get_xs(),
                                     self.current_recoil.get_ys(),
                                     color=color)

        self.markers, = self.axes.plot(self.current_recoil.get_xs(),
                                       self.current_recoil.get_ys(),
                                       color=color, marker="o",
                                       markersize=10, linestyle="None")

        self.markers_selected, = self.axes.plot(0, 0, marker="o",
                                                markersize=10,
                                                linestyle="None",
                                                color='yellow',
                                                visible=False)

        self.first_sol_btn.setEnabled(True)
        self.last_sol_btn.setEnabled(True)
        self.first_sol_btn.setChecked(True)

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
        self.canvas.draw_idle()

    def __toggle_tool_zoom(self):
        """
        Toggle zoom tool.
        """
        if self.__button_zoom.isChecked():
            self.mpl_toolbar.mode_tool = 2
            self.__show_all_recoil = False
        else:
            self.mpl_toolbar.mode_tool = 0
            self.__show_all_recoil = True
        self.canvas.draw_idle()

    def __toggle_drag_zoom(self):
        """
        Toggle drag zoom.
        """
        self.__tool_label.setText("")
        if self.__button_drag.isChecked():
            self.mpl_toolbar.pan()
        if self.__button_zoom.isChecked():
            self.mpl_toolbar.zoom()
        self.__button_drag.setChecked(False)
        self.__button_zoom.setChecked(False)

    def __update_figure(self):
        """
        Update figure.
        """
        if self.other_recoil_line:
            self.other_recoil_line.set_visible(False)

        xs = self.other_recoil.get_xs()
        ys = self.other_recoil.get_ys()
        line = self.axes.plot(xs, ys, color=str(
            self.other_recoil.color.name()),
                       alpha=0.3, visible=True, zorder=1)
        self.other_recoil_line = line[0]

        self.fig.canvas.draw_idle()

    def update_plot(self):
        self.markers.set_data(self.current_recoil.get_xs(),
                              self.current_recoil.get_ys())
        self.lines.set_data(self.current_recoil.get_xs(),
                            self.current_recoil.get_ys())

        self.markers.set_color("red")
        self.lines.set_color("red")

        self.markers.set_visible(True)
        self.lines.set_visible(True)

        if self.clicked_point:
            self.markers_selected.set_visible(True)
            selected_xs = self.clicked_point.get_x()
            selected_ys = self.clicked_point.get_y()
            self.markers_selected.set_data(selected_xs, selected_ys)

            self.coordinates_widget.x_coordinate_box.setValue(
                self.clicked_point.get_x())
            self.coordinates_widget.y_coordinate_box.setValue(
                self.clicked_point.get_y())

        last_point = self.current_recoil.get_point_by_i(len(
            self.current_recoil.get_points()) - 1)
        last_point_x = last_point.get_x()
        x_min, x_max = self.axes.get_xlim()
        if x_max < last_point_x:
            self.axes.set_xlim(x_min, last_point_x + 0.04 * last_point_x)

        self.fig.canvas.draw_idle()
