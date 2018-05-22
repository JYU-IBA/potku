# coding=utf-8
"""
Created on 1.3.2018
Updated on 22.5.2018
"""
from PyQt5.QtGui import QIcon

from dialogs.energy_spectrum import EnergySpectrumParamsDialog, \
    EnergySpectrumWidget

__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n " \
             "Sinikka Siironen"
__version__ = "2.0"

import os

from PyQt5 import QtCore, QtWidgets, QtGui
from matplotlib.widgets import SpanSelector

from modules.element import Element
from widgets.matplotlib.simulation.element_widget import ElementWidget

from dialogs.simulation.recoil_element_selection import \
    RecoilElementSelectionDialog
from dialogs.simulation.recoil_info_dialog import RecoilInfoDialog
from widgets.matplotlib.base import MatplotlibWidget
from dialogs.simulation.element_simulation_settings import \
    ElementSimulationSettingsDialog
from modules.point import Point
from modules.recoil_element import RecoilElement
from widgets.simulation.controls import SimulationControlsWidget


class ElementManager:
    """
    A class that manipulates the elements of the simulation.
    A Simulation can have 0...n ElementSimulations.
    Each ElementSimulation has 1 RecoilElement.
    Each RecoilElement has 1 Element, 1 ElementWidget and 2...n Points.

    Args:
        parent: A RecoilAtomDistributionWidget.
    """

    def __init__(self, parent, icon_manager, simulation):
        self.parent = parent
        self.icon_manager = icon_manager
        self.simulation = simulation
        self.element_simulations = self.simulation.element_simulations

    def get_element_simulation_with_recoil_element(self, recoil_element):
        for element_simulation in self.element_simulations:
            if element_simulation.recoil_element == recoil_element:
                return element_simulation

    def get_element_simulation_with_radio_button(self, radio_button):
        for element_simulation in self.element_simulations:
            if self.get_radio_button(element_simulation) == radio_button:
                return element_simulation

    def add_element_simulation(self, element):
        # Default points
        xs = [0.00, 35.00]
        ys = [1.0, 1.0]
        xys = list(zip(xs, ys))
        points = []
        for xy in xys:
            points.append(Point(xy))

        widget = ElementWidget(self.parent, element, self.icon_manager)
        recoil_element = RecoilElement(element, points, widget)
        element_simulation = self.simulation.add_element_simulation(
            recoil_element)
        widget.element_simulation = element_simulation

        return element_simulation

    def remove_element_simulation(self, element_simulation):
        element_simulation.recoil_element.delete_widget()
        self.element_simulations.remove(element_simulation)

    def get_radio_button(self, element_simulation):
        return element_simulation.recoil_element.widget\
            .radio_button


class RecoilAtomDistributionWidget(MatplotlibWidget):
    """Matplotlib simulation recoil atom distribution widget.
    Using this widget, the user can edit the recoil atom distribution
    for the simulation.
    """
    selectionsChanged = QtCore.pyqtSignal("PyQt_PyObject")
    saveCuts = QtCore.pyqtSignal("PyQt_PyObject")
    color_scheme = {"Default color": "jet",
                    "Greyscale": "Greys",
                    "Greyscale (inverted)": "gray"}

    tool_modes = {0: "",
                  1: "pan/zoom",  # Matplotlib's drag
                  2: "zoom rect"  # Matplotlib's zoom
                  }

    def __init__(self, parent, simulation, target, tab, icon_manager):
        """Inits recoil atom distribution widget.

        Args:
            parent: A TargetWidget class object.
            icon_manager: An IconManager class object.
        """

        super().__init__(parent)
        self.canvas.manager.set_title("Recoil Atom Distribution")
        self.axes.fmt_xdata = lambda x: "{0:1.2f}".format(x)
        self.axes.fmt_ydata = lambda y: "{0:1.4f}".format(y)
        self.__icon_manager = icon_manager
        self.tab = tab
        self.simulation = simulation

        self.current_element_simulation = None
        self.element_manager = ElementManager(self.tab, self.__icon_manager,
                                              self.simulation)
        self.target = target
        self.layer_colors = [(0.9, 0.9, 0.9), (0.85, 0.85, 0.85)]

        self.parent_ui = parent.ui
        # Setting up the element scroll area
        widget = QtWidgets.QWidget()
        self.recoil_vertical_layout = QtWidgets.QVBoxLayout()
        widget.setLayout(self.recoil_vertical_layout)

        scroll_vertical_layout = QtWidgets.QVBoxLayout()
        self.parent_ui.recoilScrollAreaContents.setLayout(
            scroll_vertical_layout)

        scroll_vertical_layout.addWidget(widget)
        scroll_vertical_layout.addItem(
            QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum,
                                  QtWidgets.QSizePolicy.Expanding))

        self.parent_ui.addPushButton.clicked.connect(
            self.add_element_with_dialog)
        self.parent_ui.removePushButton.clicked.connect(
            self.remove_current_element)
        self.parent_ui.settingsPushButton.clicked.connect(
            self.open_element_simulation_settings)

        self.radios = QtWidgets.QButtonGroup(self)
        self.radios.buttonToggled[QtWidgets.QAbstractButton, bool].connect(
            self.choose_element)

        self.parent_ui.editPushButton.clicked.connect(
            self.open_recoil_element_info)

        # TODO: Set lock on only when simulation has been run
        self.edit_lock_push_button = self.parent_ui.editLockPushButton
        self.edit_lock_push_button.setEnabled(False)
        self.edit_lock_push_button.clicked.connect(self.unlock_edit)
        self.edit_lock_on = True

        # Locations of points about to be dragged at the time of click
        self.click_locations = []
        # Distances between points about to be dragged
        self.x_dist_left = []  # x dist to leftmost point
        self.x_dist_right = []  # x dist to rightmost point
        self.y_dist_lowest = []  # y dist to lowest point
        # Index of lowest point about to be dragged
        self.lowest_dr_p_i = 0
        # Minimum x distance between points
        self.x_res = 0.01
        # Minimum y coordinate for points
        self.y_min = 0.0001
        # Markers representing points
        self.markers = None
        # Lines connecting markers
        self.lines = None
        # Markers representing selected points
        self.markers_selected = None
        # Points that are being dragged
        self.dragged_points = []
        # Points that have been selected
        self.selected_points = []

        # Span selection tool (used to select all points within a range
        # on the x axis)
        self.span_selector = SpanSelector(self.axes, self.on_span_select,
                                          'horizontal', useblit=True,
                                          rectprops=dict(alpha=0.5,
                                                         facecolor='red'),
                                          button=3)

        # Connections and setup
        self.canvas.mpl_connect('button_press_event', self.on_click)
        self.canvas.mpl_connect('button_release_event', self.on_release)
        self.canvas.mpl_connect('motion_notify_event', self.on_motion)

        # This customizes the toolbar buttons
        self.__fork_toolbar_buttons()

        self.name_y_axis = "Relative Concentration"
        self.name_x_axis = "Depth [nm]"

        if self.simulation.element_simulations:
            self.__update_figure()

        self.on_draw()

    def __update_figure(self):
        for element_simulation in self.simulation.element_simulations:
            self.add_element(element_simulation.recoil_element.element)

    def open_element_simulation_settings(self):
        if not self.current_element_simulation:
            return
        ElementSimulationSettingsDialog(self.current_element_simulation)

    def open_recoil_element_info(self):
        dialog = RecoilInfoDialog(
            self.current_element_simulation.recoil_element)
        if dialog.isOk:
            new_values = {"name": dialog.name,
                          "description": dialog.description,
                          "reference_density": dialog.reference_density}
            try:
                self.current_element_simulation.update_recoil_element(new_values)
                self.update_recoil_element_info_labels()
            except KeyError:
                error_box = QtWidgets.QMessageBox()
                error_box.setIcon(QtWidgets.QMessageBox.Warning)
                error_box.addButton(QtWidgets.QMessageBox.Ok)
                error_box.setText("All recoil element information could not "
                                  "be saved.")
                error_box.setWindowTitle("Error")
                error_box.exec()

    def save_mcsimu_rec_profile(self, directory):
        for element_simulation in self.element_manager \
                .element_simulations:
            element = element_simulation.recoil_element.element
            if element.isotope:
                element_str = "{0}{1}".format(element.isotope, element.symbol)
            else:
                element_str = element.symbol

            element_simulation.mcsimu_to_file(
                os.path.join(directory, element_simulation.name + ".mcsimu"))
            element_simulation.recoil_to_file(
                os.path.join(directory, element_str + ".rec"))
            element_simulation.profile_to_file(
                os.path.join(directory, element_str + ".profile"))

    def unlock_edit(self):
        confirm_box = QtWidgets.QMessageBox()
        confirm_box.setIcon(QtWidgets.QMessageBox.Warning)
        yes_button = confirm_box.addButton(QtWidgets.QMessageBox.Yes)
        confirm_box.addButton(QtWidgets.QMessageBox.Cancel)
        confirm_box.setText("Are you sure you want to unlock full edit for this"
                            " element?\nAll previous results of this element's"
                            " simulation will be deleted!")
        confirm_box.setInformativeText("When full edit is unlocked, you can"
                                       " change the x coordinate of the"
                                       " rightmost point.")
        confirm_box.setWindowTitle("Confirm")

        confirm_box.exec()
        if confirm_box.clickedButton() == yes_button:
            self.current_element_simulation.unlock_edit()
            self.edit_lock_on = False
            self.edit_lock_push_button.setText("Full edit unlocked")
            self.edit_lock_push_button.setEnabled(False)
        self.update_plot()

    def choose_element(self, button, checked):
        if checked:
            current_element_simulation = self.element_manager\
                .get_element_simulation_with_radio_button(button)
            self.current_element_simulation = \
                current_element_simulation
            self.parent_ui.elementInfoWidget.show()
            if self.current_element_simulation.get_edit_lock_on():
                self.edit_lock_on = True
                self.edit_lock_push_button.setText("Unlock full edit")
                self.edit_lock_push_button.setEnabled(True)
            else:
                self.edit_lock_on = False
                self.edit_lock_push_button.setText("Full edit unlocked")
                self.edit_lock_push_button.setEnabled(False)

            self.update_recoil_element_info_labels()
            self.dragged_points.clear()
            self.selected_points.clear()
            self.update_plot()
            # self.axes.relim()
            # self.axes.autoscale()

    def update_recoil_element_info_labels(self):
        self.parent_ui.nameLabel.setText(
            "Name: " + self.current_element_simulation.recoil_element.name)
        self.parent_ui.referenceDensityLabel.setText(
            "Reference density: " + "{0:1.2f}".
            format(self.current_element_simulation.recoil_element
                   .reference_density) + "e22 at/cm\xb2"
        )

    def recoil_element_info_on_switch(self):
        if self.current_element_simulation is None:
            self.parent_ui.elementInfoWidget.hide()
        else:
            self.parent_ui.elementInfoWidget.show()

    def add_element_with_dialog(self):
        dialog = RecoilElementSelectionDialog(self)
        if dialog.isOk:
            element_simulation = self.add_element(Element(
                dialog.element, dialog.isotope))

            if self.current_element_simulation is None:
                self.current_element_simulation = element_simulation
                element_simulation.recoil_element.widget.radio_button\
                    .setChecked(True)

    def add_element(self, element):
        # Create new ElementSimulation
        element_simulation = self.element_manager\
            .add_element_simulation(element)

        # Add simulation controls widget
        simulation_controls_widget = SimulationControlsWidget(
            element_simulation)
        simulation_controls_widget.element_simulation = element_simulation
        self.tab.ui.contentsLayout.addWidget(simulation_controls_widget)

        # Add recoil element widget
        recoil_element_widget = element_simulation.recoil_element \
            .widget

        self.radios.addButton(recoil_element_widget.radio_button)
        self.recoil_vertical_layout.addWidget(recoil_element_widget)

        return element_simulation

    def remove_element(self, element_simulation):
        self.element_manager.remove_element_simulation(element_simulation)

    def remove_current_element(self):
        if not self.current_element_simulation:
            return
        confirm_box = QtWidgets.QMessageBox()
        confirm_box.setIcon(QtWidgets.QMessageBox.Warning)
        yes_button = confirm_box.addButton(QtWidgets.QMessageBox.Yes)
        confirm_box.addButton(QtWidgets.QMessageBox.Cancel)
        confirm_box.setText("Are you sure you want to remove the element?")
        confirm_box.setWindowTitle("Confirm")

        confirm_box.exec()
        if confirm_box.clickedButton() == yes_button:
            element_simulation = self.element_manager \
                .get_element_simulation_with_radio_button(
                self.radios.checkedButton())
            self.remove_element(element_simulation)
            self.current_element_simulation = None
            self.parent_ui.elementInfoWidget.hide()
            self.update_plot()
        else:
            return

    def import_elements(self):
        for layer in self.target.layers:
            for layer_element in layer.elements:
                already_exists = False
                for existing_element_simulation in \
                        self.element_manager.element_simulations:
                    if layer_element == existing_element_simulation \
                            .recoil_element.element:
                        already_exists = True
                        break
                if not already_exists:
                    self.add_element(layer_element)

    def on_draw(self):
        """Draw method for matplotlib.
        """
        self.axes.clear()  # Clear old stuff

        self.axes.set_ylabel(self.name_y_axis)
        self.axes.set_xlabel(self.name_x_axis)

        if self.current_element_simulation:
            self.lines, = self.axes.plot(
                self.current_element_simulation.get_xs(),
                self.current_element_simulation.get_ys(),
                color="blue")
            self.markers, = self.axes.plot(
                self.current_element_simulation.get_xs(),
                                          self.current_element_simulation.get_ys(),
                                           color="blue", marker="o",
                                           markersize=10, linestyle="None")
            self.markers_selected, = self.axes.plot(0, 0, marker="o",
                                                    markersize=10,
                                                    linestyle="None",
                                                    color='yellow',
                                                    visible=False)
        else:
            self.lines, = self.axes.plot(0, 0, color="blue", visible=False)
            self.markers, = self.axes.plot(0, 0, color="blue", marker="o",
                                           markersize=10, linestyle="None",
                                           visible=False)
            self.markers_selected, = self.axes.plot(0, 0, marker="o",
                                                    markersize=10,
                                                    linestyle="None",
                                                    color='yellow',
                                                    visible=False)

        # self.text_axes = self.fig.add_axes([0.8, 0.05, 0.1, 0.075])
        # self.text_box = TextBox(self.text_axes, 'Coordinates', initial="Testi")

        self.axes.set_xlim(-1, 40)
        self.axes.set_ylim(-0.1, 2)
        # self.text = self.fig.text(0.1, 0.9, "Selected point coordinates:",
        #                           transform=self.fig.transFigure, va="top", ha="left")

        # Remove axis ticks and draw
        self.remove_axes_ticks()
        self.canvas.draw()

    def __toggle_tool_drag(self):
        if self.__button_drag.isChecked():
            self.mpl_toolbar.mode_tool = 1
        else:
            self.mpl_toolbar.mode_tool = 0
        self.canvas.draw_idle()

    def __toggle_tool_zoom(self):
        if self.__button_zoom.isChecked():
            self.mpl_toolbar.mode_tool = 2
        else:
            self.mpl_toolbar.mode_tool = 0
        self.canvas.draw_idle()

    def __toggle_drag_zoom(self):
        self.__tool_label.setText("")
        if self.__button_drag.isChecked():
            self.mpl_toolbar.pan()
        if self.__button_zoom.isChecked():
            self.mpl_toolbar.zoom()
        self.__button_drag.setChecked(False)
        self.__button_zoom.setChecked(False)

    def __fork_toolbar_buttons(self):
        super().fork_toolbar_buttons()
        self.mpl_toolbar.mode_tool = 0
        self.__tool_label = self.mpl_toolbar.children()[24]
        self.__button_drag = self.mpl_toolbar.children()[12]
        self.__button_zoom = self.mpl_toolbar.children()[14]
        self.__button_drag.clicked.connect(self.__toggle_tool_drag)
        self.__button_zoom.clicked.connect(self.__toggle_tool_zoom)

        # Make own buttons
        self.mpl_toolbar.addSeparator()

        # Point x coordinate spinbox
        self.x_coordinate_box = QtWidgets.QDoubleSpinBox(self)
        self.x_coordinate_box.setToolTip("X coordinate of selected point")
        self.x_coordinate_box.setSingleStep(0.1)
        self.x_coordinate_box.setDecimals(2)
        self.x_coordinate_box.setMinimum(0)
        self.x_coordinate_box.setMaximum(1000000000000)
        self.x_coordinate_box.setMaximumWidth(62)
        self.x_coordinate_box.setKeyboardTracking(False)
        self.x_coordinate_box.valueChanged.connect(self.set_selected_point_x)
        # self.x_coordinate_box.setLocale()
        self.mpl_toolbar.addWidget(self.x_coordinate_box)
        self.x_coordinate_box.setEnabled(False)

        # Point y coordinate spinbox
        self.y_coordinate_box = QtWidgets.QDoubleSpinBox(self)
        self.y_coordinate_box.setToolTip("Y coordinate of selected point")
        self.y_coordinate_box.setSingleStep(0.1)
        self.y_coordinate_box.setDecimals(4)
        self.y_coordinate_box.setMaximum(1000000000000)
        self.y_coordinate_box.setMaximumWidth(62)
        self.y_coordinate_box.setMinimum(self.y_min)
        self.y_coordinate_box.setKeyboardTracking(False)
        self.y_coordinate_box.valueChanged.connect(self.set_selected_point_y)
        # self.y_coordinate_box.setFixedWidth(40)
        self.mpl_toolbar.addWidget(self.y_coordinate_box)
        self.y_coordinate_box.setEnabled(False)

        # Point removal
        point_remove_action = QtWidgets.QAction("Remove point", self)
        point_remove_action.triggered.connect(self.remove_points)
        point_remove_action.setToolTip("Remove selected points")
        # TODO: Temporary icon
        self.__icon_manager.set_icon(point_remove_action, "del.png")
        self.mpl_toolbar.addAction(point_remove_action)

    def set_selected_point_x(self):
        """Sets the selected point's x coordinate
        to the value of the x spinbox.
        """
        x = self.x_coordinate_box.value()
        leftmost_sel_point = self.selected_points[0]
        left_neighbor = self.current_element_simulation.get_left_neighbor(
            leftmost_sel_point)
        right_neighbor = self.current_element_simulation.get_right_neighbor(
            leftmost_sel_point)

        # Can't move past neighbors. If tried, sets x coordinate to
        # distance x_res from neighbor's x coordinate.
        if left_neighbor is None:
            if x < right_neighbor.get_x():
                leftmost_sel_point.set_x(x)
            else:
                leftmost_sel_point.set_x(right_neighbor.get_x() - self.x_res)
        elif right_neighbor is None:
            if x > left_neighbor.get_x():
                leftmost_sel_point.set_x(x)
            else:
                leftmost_sel_point.set_x(left_neighbor.get_x() + self.x_res)
        elif left_neighbor.get_x() < x < right_neighbor.get_x():
                leftmost_sel_point.set_x(x)
        elif left_neighbor.get_x() >= x:
            leftmost_sel_point.set_x(left_neighbor.get_x() + self.x_res)
        elif right_neighbor.get_x() <= x:
            leftmost_sel_point.set_x(right_neighbor.get_x() - self.x_res)
        self.update_plot()

    def set_selected_point_y(self):
        """Sets the selected point's y coordinate
        to the value of the y spinbox.
        """
        y = self.y_coordinate_box.value()
        leftmost_sel_point = self.selected_points[0]
        leftmost_sel_point.set_y(y)
        self.update_plot()

    def on_click(self, event):
        """ On click event above graph.

        Args:
            event: A MPL MouseEvent
        """
        if not self.current_element_simulation:
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
                i = marker_info['ind'][0]  # The clicked point's index
                clicked_point = self.current_element_simulation.get_point_by_i(i)
                if clicked_point not in self.selected_points:
                    self.selected_points = [clicked_point]
                self.dragged_points.extend(self.selected_points)

                self.set_on_click_attributes(event)

                self.update_plot()
            else:
                # Ctrl-click to add a point
                modifiers = QtGui.QGuiApplication.queryKeyboardModifiers()
                if modifiers == QtCore.Qt.ControlModifier:
                    self.selected_points.clear()
                    self.update_plot()
                    line_contains, line_info = self.lines.contains(event)
                    if line_contains:  # If clicked a line
                        x = event.xdata
                        y = event.ydata
                        new_point = self.add_point((x, y))
                        if new_point:
                            self.selected_points = [new_point]
                            self.dragged_points = [new_point]
                            self.set_on_click_attributes(event)
                            self.update_plot()

    def set_on_click_attributes(self, event):
        """Sets the attributes needed for dragging points."""
        locations = []
        for point in self.dragged_points:
            x0, y0 = point.get_coordinates()
            locations.append((x0, y0, event.xdata, event.ydata))
        self.click_locations = locations

        self.x_dist_left = [self.dragged_points[i].get_x()
                            - self.dragged_points[0].get_x()
                            for i in range(1, len(self.dragged_points))]
        self.x_dist_right = [self.dragged_points[-1].get_x()
                             - self.dragged_points[i].get_x()
                             for i in range(0, len(self.dragged_points) - 1)]
        self.lowest_dr_p_i = 0
        for i in range(1, len(self.dragged_points)):
            if self.dragged_points[i].get_y()\
                    < self.dragged_points[self.lowest_dr_p_i].get_y():
                self.lowest_dr_p_i = i
        self.y_dist_lowest = [self.dragged_points[i].get_y()
                              - self.dragged_points[self.lowest_dr_p_i].get_y()
                              for i in range(len(self.dragged_points))]

    def add_point(self, coords):
        """Adds a point if there is space for it.
        Returns the point if a point was added, None if not.
        """
        if not self.current_element_simulation:
            return
        new_point = Point(coords)
        self.current_element_simulation.add_point(new_point)
        left_neighbor_x = self.current_element_simulation.get_left_neighbor(
            new_point).get_x()
        right_neighbor_x = self.current_element_simulation.get_right_neighbor(
            new_point).get_x()

        error = False

        # If too close to left
        if new_point.get_x() - left_neighbor_x < self.x_res:
            # Need space to insert the new point
            if right_neighbor_x - new_point.get_x() < 2 * self.x_res:
                error = True
            else:
                # Insert the new point as close to its left neighbor as possible
                new_point.set_x(left_neighbor_x + self.x_res)
        elif right_neighbor_x - new_point.get_x() < self.x_res:
            if new_point.get_x() - left_neighbor_x < 2 * self.x_res:
                error = True
            else:
                new_point.set_x(right_neighbor_x - self.x_res)

        if error:
            self.current_element_simulation.remove_point(new_point)
            # TODO: Add an error message text label
            print("Can't add a point here. There is no space for it.")
            return None
        else:
            return new_point

    def update_plot(self):
        """ Updates marker and line data and redraws the plot. """
        if not self.current_element_simulation:
            self.markers.set_visible(False)
            self.lines.set_visible(False)
            self.markers_selected.set_visible(False)
            self.fig.canvas.draw_idle()
            return

        self.markers.set_data(self.current_element_simulation.get_xs(),
                              self.current_element_simulation.get_ys())
        self.lines.set_data(self.current_element_simulation.get_xs(),
                            self.current_element_simulation.get_ys())

        self.markers.set_visible(True)
        self.lines.set_visible(True)

        if self.selected_points:  # If there are selected points
            self.markers_selected.set_visible(True)
            selected_xs = []
            selected_ys = []
            for point in self.selected_points:
                selected_xs.append(point.get_x())
                selected_ys.append(point.get_y())
            self.markers_selected.set_data(selected_xs, selected_ys)
            if self.selected_points[0] == \
                    self.current_element_simulation.get_points()[-1]\
                    and self.edit_lock_on:
                self.x_coordinate_box.setEnabled(False)
            else:
                self.x_coordinate_box.setEnabled(True)
            self.x_coordinate_box.setValue(self.selected_points[0].get_x())
            self.y_coordinate_box.setEnabled(True)
            self.y_coordinate_box.setValue(self.selected_points[0].get_y())
            # self.text.set_text('selected: %d %d' % (self.selected_points[0].get_coordinates()[0],
            #                                     self.selected_points[0].get_coordinates()[1]))
        else:
            self.markers_selected.set_data(
                self.current_element_simulation.get_xs(),
                self.current_element_simulation.get_ys())
            self.markers_selected.set_visible(False)
            self.x_coordinate_box.setEnabled(False)
            self.y_coordinate_box.setEnabled(False)

        self.fig.canvas.draw_idle()

    def update_layer_borders(self):
        next_layer_position = 0
        for idx, layer in enumerate(self.target.layers):
            self.axes.axvspan(
                next_layer_position, next_layer_position + layer.thickness,
                facecolor=self.layer_colors[idx % 2]
            )

            # Put annotation in the middle of the rectangular patch.
            self.axes.annotate(layer.name,
                               (next_layer_position + layer.thickness / 2, 0.5),
                               ha="center")

            # Move the position where the next layer starts.
            next_layer_position += layer.thickness

        self.axes.set_xlim(0, next_layer_position + 3)
        self.fig.canvas.draw_idle()

    def on_motion(self, event):
        """Callback method for mouse motion event. Moves points that are being dragged.

        Args:
            event: A MPL MouseEvent
        """
        if not self.current_element_simulation:
            return
        # Don't do anything if drag tool or zoom tool is active.
        if self.__button_drag.isChecked() or self.__button_zoom.isChecked():
            return
        # Only inside the actual graph axes, else do nothing.
        if event.inaxes != self.axes:
            return
        # Only if there are points being dragged.
        if not self.dragged_points:
            return
        if not self.click_locations:
            return

        dr_ps = self.dragged_points

        new_coords = self.get_new_checked_coordinates(event)

        for i in range(0, len(dr_ps)):
            if dr_ps[i] == self.current_element_simulation.get_points()[-1] \
                    and self.edit_lock_on:
                dr_ps[i].set_y(new_coords[i][1])
            else:
                dr_ps[i].set_coordinates(new_coords[i])

        self.update_plot()

    def get_new_checked_coordinates(self, event):
        """Returns checked new coordinates for dragged points.
        They have been checked for neighbor or axis limit collisions.
        """
        dr_ps = self.dragged_points

        leftmost_dr_p = dr_ps[0]
        rightmost_dr_p = dr_ps[-1]
        left_neighbor = self.current_element_simulation.get_left_neighbor(
            leftmost_dr_p)
        right_neighbor = self.current_element_simulation.get_right_neighbor(
            rightmost_dr_p)

        new_coords = self.get_new_unchecked_coordinates(event)
        new_x_left = new_coords[0][0]
        new_x_right = new_coords[-1][0]

        if left_neighbor is None and right_neighbor is None:
            pass  # No neighbors to limit movement
        # Check for neighbor collisions:
        elif left_neighbor is None and right_neighbor is not None:
            if new_coords[-1][0] >= right_neighbor.get_x() - self.x_res:
                new_coords[-1][0] = right_neighbor.get_x() - self.x_res
                for i in range(0, len(dr_ps) - 1):
                    new_coords[i][0] = right_neighbor.get_x()\
                                       - self.x_res - self.x_dist_right[i]
        elif right_neighbor is None and left_neighbor is not None:
            if new_coords[0][0] <= left_neighbor.get_x() + self.x_res:
                new_coords[0][0] = left_neighbor.get_x() + self.x_res
                for i in range(1, len(dr_ps)):
                    new_coords[i][0] = left_neighbor.get_x() + self.x_res\
                                       + self.x_dist_left[i - 1]
        elif left_neighbor.get_x() + self.x_res >= new_coords[0][0]:
            new_coords[0][0] = left_neighbor.get_x() + self.x_res
            for i in range(1, len(dr_ps)):
                new_coords[i][0] = left_neighbor.get_x() + self.x_res\
                                   + self.x_dist_left[i - 1]
        elif right_neighbor.get_x() - self.x_res <= new_coords[-1][0]:
            new_coords[-1][0] = right_neighbor.get_x() - self.x_res
            for i in range(0, len(dr_ps) - 1):
                new_coords[i][0] = right_neighbor.get_x() - self.x_res\
                                   - self.x_dist_right[i]

        # Check for axis limit collisions:
        if new_coords[0][0] < 0:
            new_coords[0][0] = 0
            for i in range(1, len(dr_ps)):
                new_coords[i][0] = self.x_dist_left[i - 1]

        if new_coords[self.lowest_dr_p_i][1] < self.y_min:
            new_coords[self.lowest_dr_p_i][1] = self.y_min
            for i in range(0, len(dr_ps)):
                new_coords[i][1] = self.y_min + self.y_dist_lowest[i]

        return new_coords

    def get_new_unchecked_coordinates(self, event):
        """Returns new coordinates for dragged points.
        These coordinates come from mouse movement and they haven't been checked
        for neighbor or axis limit collisions.
        """
        new_unchecked_coords = []
        for i, point in enumerate(self.dragged_points):
            x0, y0, xclick, yclick = self.click_locations[i]
            dx = event.xdata - xclick
            dy = event.ydata - yclick
            new_x = x0 + dx
            new_y = y0 + dy
            new_unchecked_coords.append([new_x, new_y])
        return new_unchecked_coords

    def update_location(self, event):
        """Updates the location of points that are being dragged."""
        for point in self.dragged_points:
            point.set_coordinates((event.xdata, event.ydata))
        self.update_plot()

    def remove_points(self):
        """Removes all selected points, but not if there would be
        less than two points left.
        """
        if not self.current_element_simulation:
            return
        if len(self.current_element_simulation.get_points()) - \
                len(self.selected_points) < 2:
            # TODO: Add an error message text label
            print("There must always be at least two points")
        else:
            for sel_point in self.selected_points:
                self.current_element_simulation.remove_point(sel_point)
            self.selected_points.clear()
            self.update_plot()

    def on_release(self, event):
        """Callback method for mouse release event. Stops dragging.

        Args:
            event: A MPL MouseEvent
        """
        if not self.current_element_simulation:
            return
        # Don't do anything if drag tool or zoom tool is active.
        if self.__button_drag.isChecked() or self.__button_zoom.isChecked():
            return
        if event.button == 1:
            self.dragged_points.clear()
            self.update_plot()

    def on_span_select(self, xmin, xmax):
        if not self.current_element_simulation:
            return
        sel_points = []
        for point in self.current_element_simulation.get_points():
            if xmin <= point.get_x() <= xmax:
                sel_points.append(point)
        self.selected_points = sel_points
        self.update_plot()
