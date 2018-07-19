# coding=utf-8
"""
Created on 1.3.2018
Updated on 19.7.2018

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2018 Severi Jääskeläinen, Samuel Kaiponen, Heta Rekilä and
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

__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n " \
             "Sinikka Siironen"
__version__ = "2.0"

import matplotlib
import modules.masses as masses
import os

from dialogs.simulation.element_simulation_settings import \
    ElementSimulationSettingsDialog
from dialogs.simulation.multiply_area import MultiplyAreaDialog
from dialogs.simulation.recoil_element_selection import \
    RecoilElementSelectionDialog
from dialogs.simulation.recoil_info_dialog import RecoilInfoDialog

from matplotlib import offsetbox
from matplotlib.widgets import RectangleSelector
from matplotlib.widgets import SpanSelector
from modules.element import Element
from modules.general_functions import find_nearest
from modules.general_functions import find_y_on_line
from modules.point import Point
from modules.recoil_element import RecoilElement

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5.QtCore import QLocale
from PyQt5.QtGui import QGuiApplication

from shapely.geometry import Polygon

from widgets.matplotlib.base import MatplotlibWidget
from widgets.matplotlib.simulation.element import ElementWidget
from widgets.simulation.controls import SimulationControlsWidget
from widgets.simulation.point_coordinates import PointCoordinatesWidget
from widgets.simulation.recoil_element import RecoilElementWidget


class ElementManager:
    """
    A class that manipulates the elements of the simulation.
    A Simulation can have 0...n ElementSimulations.
    Each ElementSimulation has 1 RecoilElement.
    Each RecoilElement has 1 Element, 1 ElementWidget and 2...n Points.
    """

    def __init__(self, parent_tab, parent, icon_manager, simulation):
        """
        Initializes element manager.

        Args:
            parent_tab: SimulationTabWidget object.
            parent: RecoilAtomDistributionWidget object.
            icon_manager: IconManager object.
            simulation: Simulation object.
        """
        self.parent_tab = parent_tab
        self.parent = parent
        self.icon_manager = icon_manager
        self.simulation = simulation
        self.element_simulations = self.simulation.element_simulations

    def get_element_simulation_with_recoil_element(self, recoil_element):
        """
        Get element simulation with recoil element.

        Args:
             recoil_element: A RecoilElement object.

        Return:
            ElementSimulation.
        """
        for element_simulation in self.element_simulations:
            if element_simulation.recoil_elements[0] == recoil_element:
                return element_simulation

    def get_element_simulation_with_radio_button(self, radio_button):
        """
        Get element simulation with radio button.

        Args:
             radio_button: A radio button widget.

        Return:
            ElementSimulation.
        """
        for element_simulation in self.element_simulations:
            for button in self.get_radio_buttons(element_simulation):
                if button == radio_button:
                    return element_simulation

    def get_recoil_element_with_radio_button(self, radio_button,
                                             element_simulation):
        """
        Get recoil element with radio button from given element simulation.

        Args:
            radio_button: A radio button widget.
            element_simulation: An ElementSimulation object.

        Return:
            RecoilElement.
        """
        for recoil_element in element_simulation.recoil_elements:
            if recoil_element.widgets[0].radio_button == radio_button:
                return recoil_element

    def add_new_element_simulation(self, element):
        """
        Create a new ElementSimulation and RecoilElement with default points.

        Args:
             element: Element that tells the element to add.

        Return:
            Created ElementSimulation
        """
        # Default points
        xs = [0.00]
        ys = [1.0]

        # Make two points for each change between layers
        for layer in self.parent.target.layers:
            x_1 = layer.start_depth + layer.thickness
            y_1 = 1.0
            xs.append(x_1)
            ys.append(y_1)

            x_2 = x_1 + self.parent.x_res
            y_2 = 1.0
            xs.append(x_2)
            ys.append(y_2)

        xs.pop()
        ys.pop()

        xys = list(zip(xs, ys))
        points = []
        for xy in xys:
            points.append(Point(xy))

        if element.isotope is None:
            element.isotope = int(round(masses.get_standard_isotope(
                element.symbol)))

        element_widget = ElementWidget(self.parent, element,
                                       self.parent_tab, None)
        recoil_element = RecoilElement(element, points)
        recoil_element.widgets.append(element_widget)
        element_simulation = self.simulation.add_element_simulation(
            recoil_element)
        element_widget.element_simulation = element_simulation
        element_widget.add_element_simulation_reference(element_simulation)

        # Add simulation controls widget
        simulation_controls_widget = SimulationControlsWidget(
            element_simulation)
        simulation_controls_widget.element_simulation = element_simulation
        self.parent_tab.ui.contentsLayout.addWidget(simulation_controls_widget)
        element_simulation.recoil_elements[0] \
            .widgets.append(simulation_controls_widget)

        return element_simulation

    def add_element_simulation(self, element_simulation):
        """
        Add an existing ElementSimulation.

        Args:
            element_simulation: ElementSimulation to be added.
        """
        main_element_widget = \
            ElementWidget(self.parent,
                          element_simulation.recoil_elements[0].element,
                          self.parent_tab, element_simulation)
        element_simulation.recoil_elements[0] \
            .widgets.append(main_element_widget)
        main_element_widget.element_simulation = element_simulation

        # Add simulation controls widget
        simulation_controls_widget = SimulationControlsWidget(
            element_simulation)
        simulation_controls_widget.element_simulation = element_simulation
        self.parent_tab.ui.contentsLayout.addWidget(simulation_controls_widget)
        element_simulation.recoil_elements[0] \
            .widgets.append(simulation_controls_widget)

        # Add other recoil element widgets
        i = 1
        while i in range(len(element_simulation.recoil_elements)):
            recoil_element_widget = RecoilElementWidget(
                self.parent,
                element_simulation.recoil_elements[i].element,
                self.parent_tab, main_element_widget, element_simulation)
            element_simulation.recoil_elements[i].widgets.append(
                recoil_element_widget)
            recoil_element_widget.element_simulation = element_simulation

            # Check if there are e.g. Default-1 named recoil elements. If so,
            #  increase element.running_int_recoil
            recoil_name = element_simulation.recoil_elements[i].name
            if recoil_name.startswith("Default-"):
                possible_int = recoil_name.split('-')[1]
                try:
                    integer = int(possible_int)
                    main_element_widget.running_int_recoil = integer + 1
                except ValueError:
                    pass
            i = i + 1

    def remove_element_simulation(self, element_simulation):
        """
        Remove element simulation.

        Args:
            element_simulation: An ElementSimulation object to be removed.
        """
        element_simulation.recoil_elements[0].delete_widgets()
        self.element_simulations.remove(element_simulation)

        # Delete all files that relate to element_simulation
        files_to_be_removed = []
        for file in os.listdir(element_simulation.directory):
            if file.startswith(element_simulation.name_prefix) and \
                    (file.endswith(".mcsimu") or file.endswith(".rec") or
                     file.endswith(".profile")):
                file_path = os.path.join(element_simulation.directory, file)
                files_to_be_removed.append(file_path)

        for file_path in files_to_be_removed:
            os.remove(file_path)

    def get_radio_buttons(self, element_simulation):
        """
        Get all radio buttons based on element simulation.

        Args:
            element_simulation: An ElementSimulation object.

        Return:
            List of buttons that have the same ElementSimulation reference.
        """
        radio_buttons = []
        for recoil_element in element_simulation.recoil_elements:
            radio_buttons.append(recoil_element.widgets[0].radio_button)
        return radio_buttons


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
        self.parent = parent
        self.canvas.manager.set_title("Recoil Atom Distribution")
        self.axes.format_coord = self.format_coord
        self.__icon_manager = icon_manager
        self.tab = tab
        self.simulation = simulation

        self.current_element_simulation = None
        self.current_recoil_element = None
        self.element_manager = ElementManager(self.tab, self,
                                              self.__icon_manager,
                                              self.simulation)
        self.target = target
        self.layer_colors = [(0.9, 0.9, 0.9), (0.85, 0.85, 0.85)]

        self.parent_ui = parent.ui
        # Setting up the element scroll area
        widget = QtWidgets.QWidget()
        self.recoil_vertical_layout = QtWidgets.QVBoxLayout()
        self.recoil_vertical_layout.setContentsMargins(0, 0, 0, 0)
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
        # self.parent_ui.settingsPushButton.clicked.connect(
        #     self.open_element_simulation_settings)

        self.radios = QtWidgets.QButtonGroup(self)
        self.radios.buttonToggled[QtWidgets.QAbstractButton, bool].connect(
            self.choose_element)

        self.parent_ui.editPushButton.clicked.connect(
            self.open_recoil_element_info)

        self.edit_lock_push_button = self.parent_ui.editLockPushButton
        self.edit_lock_push_button.clicked.connect(self.unlock_or_lock_edit)
        self.full_edit_on = True

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
        # self.y_min = 0.0001
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
        # Clicked point
        self.clicked_point = None
        # If point has been clicked
        self.point_clicked = False
        # Event for right clicking, used for either showing context menu of
        # rectangle select
        self.__rectangle_event_click = None
        # Event for releasing right click
        self.__rectangle_event_release = None

        self.annotations = []
        self.trans = matplotlib.transforms.blended_transform_factory(
            self.axes.transData, self.axes.transAxes)

        # Span selection tool (used to select all points within a range
        # on the x axis)
        self.span_selector = SpanSelector(self.axes, self.on_span_select,
                                          'horizontal', useblit=True,
                                          rectprops=dict(alpha=0.5,
                                                         facecolor='red'),
                                          button=1, span_stays=True,
                                          onmove_callback=self.on_span_motion)

        self.rectangle_selector = RectangleSelector(self.axes,
                                                    self.on_rectangle_select,
                                                    useblit=True,
                                                    drawtype='box',
                                                    rectprops=dict(
                                                        alpha=0.5,
                                                        facecolor='red'),
                                                    button=3)

        # Connections and setup
        self.canvas.mpl_connect('button_press_event', self.on_click)
        self.canvas.mpl_connect('button_release_event', self.on_release)
        self.canvas.mpl_connect('motion_notify_event', self.on_motion)

        self.locale = QLocale.c()
        self.clipboard = QGuiApplication.clipboard()
        self.ratio_str = self.clipboard.text()
        self.clipboard.changed.connect(self.__update_multiply_action)

        self.__button_area_calculation = None
        self.coordinates_widget = None
        self.coordinates_action = None
        self.point_remove_action = None

        # This customizes the toolbar buttons
        self.__fork_toolbar_buttons()

        # Remember x limits to set when the user has returned from Target view.
        self.original_x_limits = None

        self.name_y_axis = "Relative Concentration"
        self.name_x_axis = "Depth [nm]"

        self.anchored_box = None
        self.__show_all_recoil = True

        self.on_draw()

        if self.simulation.element_simulations:
            self.__update_figure()

        for button in self.radios.buttons():
            button.setChecked(True)
            break

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

    def __update_figure(self):
        """
        Update figure.
        """
        select_first_elem_sim = True
        for element_simulation in self.simulation.element_simulations:
            self.add_element(element_simulation.recoil_elements[0].element,
                             element_simulation)

            element_simulation.recoil_elements[0].widgets[0]. \
                radio_button.setChecked(select_first_elem_sim)
            select_first_elem_sim = False

    def open_element_simulation_settings(self):
        """
        Open element simulation settings.
        """
        if not self.current_element_simulation:
            return
        ElementSimulationSettingsDialog(self.current_element_simulation)

    def open_recoil_element_info(self):
        """
        Open recoil element info.
        """
        dialog = RecoilInfoDialog(
            self.current_recoil_element)
        if dialog.isOk:
            new_values = {"name": dialog.name,
                          "description": dialog.description,
                          "reference_density": dialog.reference_density}
            try:
                self.current_element_simulation.update_recoil_element(
                    self.current_recoil_element,
                    new_values)
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
        """
        Save information to .mcsimu and .profile files.
        """
        for element_simulation in self.element_manager \
                .element_simulations:

            element_simulation.mcsimu_to_file(
                os.path.join(directory, element_simulation.name_prefix + "-" +
                             element_simulation.name +
                             ".mcsimu"))
            for recoil_element in element_simulation.recoil_elements:
                element_simulation.recoil_to_file(directory, recoil_element)
            element_simulation.profile_to_file(
                os.path.join(directory, element_simulation.name_prefix +
                             ".profile"))

    def unlock_or_lock_edit(self):
        """
        Unlock or lock full edit.
        """
        if self.edit_lock_push_button.text() == "Unlock full edit":
            reply = QtWidgets.QMessageBox.warning(
                self.parent, "Confirm", "Are you sure you want to unlock full "
                                        "edit for this element simulation?\n"
                                        "All its previous results will be "
                                        "deleted.\n\nUnlock full edit anyway?",
                QtWidgets.QMessageBox.Yes |
                QtWidgets.QMessageBox.No |
                QtWidgets.QMessageBox.Cancel,
                QtWidgets.QMessageBox.Cancel)
            if reply == QtWidgets.QMessageBox.No or reply == \
                    QtWidgets.QMessageBox.Cancel:
                return
            self.current_element_simulation.unlock_edit()
            # TODO: Delete result files (erds, recoil, simu)
            self.full_edit_on = True
            self.edit_lock_push_button.setText("Full edit unlocked")
            self.current_element_simulation.y_min = 0.0
            if self.clicked_point is \
               self.current_recoil_element.get_points()[-1]:
                self.point_remove_action.setEnabled(True)
            self.coordinates_widget.x_coordinate_box.setEnabled(True)
        else:
            self.current_element_simulation.lock_edit()
            self.full_edit_on = False
            self.edit_lock_push_button.setText("Unlock full edit")
            self.current_element_simulation.y_min = 0.0001
        self.update_plot()

    def choose_element(self, button, checked):
        """
        Choose element from view.

        Args:
            button: Radio button.
            checked: Whether button is checked or not.
        """
        if checked:
            # Update limit and area parts
            if self.current_recoil_element and \
                    self.current_recoil_element.area_limits:
                for limit in self.current_recoil_element.area_limits:
                    limit.set_linestyle("None")
                if self.anchored_box:
                    self.anchored_box.set_visible(False)
            current_element_simulation = self.element_manager \
                .get_element_simulation_with_radio_button(button)
            self.current_element_simulation = \
                current_element_simulation
            self.current_recoil_element = \
                self.element_manager.get_recoil_element_with_radio_button(
                    button, self.current_element_simulation)
            # Disable element simulation deletion button and full edit for
            # other than main recoil element
            if self.current_recoil_element is not \
                    self.current_element_simulation.recoil_elements[0]:
                self.parent_ui.removePushButton.setEnabled(False)
                self.edit_lock_push_button.setEnabled(False)
                # Update zero values and intervals for main recoil element
                self.current_element_simulation.recoil_elements[0]. \
                    update_zero_values()
                # If zero values changed, update them to current recoil element
                if self.current_element_simulation.recoil_elements[0]. \
                        zero_intervals_on_x != \
                        self.current_recoil_element.zero_intervals_on_x or \
                        self.current_element_simulation.recoil_elements[0]. \
                        zero_values_on_x != \
                        self.current_recoil_element.zero_values_on_x:
                    self.update_current_recoils_zeros()
                    self.delete_and_add_possible_extra_points()
                # Copy limits for current recoil if it doesn't have them yet
                if not self.current_recoil_element.area_limits and \
                        self.current_element_simulation.recoil_elements[0].\
                        area_limits:
                    lower_limit = \
                        self.current_element_simulation.recoil_elements[0].\
                        area_limits[0].get_xdata()[0]
                    upper_limit = \
                        self.current_element_simulation.recoil_elements[0].\
                        area_limits[1].get_xdata()[0]
                    self.current_recoil_element.area_limits.append(
                        self.axes.axvline(
                            x=lower_limit, linestyle="--"))
                    self.current_recoil_element.area_limits.append(
                        self.axes.axvline(
                            x=upper_limit, linestyle="--", color='red'))
            else:
                self.parent_ui.removePushButton.setEnabled(True)
                self.edit_lock_push_button.setEnabled(True)
                if self.current_recoil_element.area_limits:
                    self.__button_area_calculation.setEnabled(True)
                else:
                    self.__button_area_calculation.setEnabled(False)
            self.parent_ui.elementInfoWidget.show()
            # Put full edit on if element simulation allows it
            if self.current_element_simulation.get_full_edit_on():
                self.full_edit_on = True
                self.edit_lock_push_button.setText("Full edit unlocked")
            else:
                self.full_edit_on = False
                self.edit_lock_push_button.setText("Unlock full edit")

            self.update_recoil_element_info_labels()
            self.dragged_points.clear()
            self.selected_points.clear()
            self.point_remove_action.setEnabled(False)

            # Update limit and area parts
            if self.current_recoil_element.area_limits:
                for lim in self.current_recoil_element.area_limits:
                    lim.set_linestyle("--")
                if self.anchored_box:
                    self.anchored_box.set_visible(True)
                self.__calculate_selected_area()
                text = "Area: %s" % str(round(
                    self.current_recoil_element.area, 2))
                box = self.anchored_box.get_child()
                box.set_text(text)
            self.update_plot()
            # self.axes.relim()
            # self.axes.autoscale()

    def delete_and_add_possible_extra_points(self):
        """
        If current recoil element has too many or too little points at the
        end to match the main recoil element, add or delete points accordingly.
        """
        main_points = self.current_element_simulation.recoil_elements[
            0].get_points()
        main_end = main_points[len(main_points) - 1]

        current_points = self.current_recoil_element.get_points()
        current_end = current_points[len(current_points) - 1]

        # main end is further
        main_end_x = main_end.get_x()
        current_end_x = current_end.get_x()

        main_end_y = main_end.get_y()
        if main_end_x > current_end_x:
            if main_end_y == 0.0:
                new_point = self.add_zero_point(main_end_x)
            else:
                new_point = self.add_point((current_end_x, main_end_y),
                                           special=True)
            self.fix_left_neighbor_of_zero(new_point)

        points_to_delete = []
        if main_end_x < current_end_x:
            # Delete all unnecessary points
            for point in current_points:
                if point.get_x() > main_end_x:
                    points_to_delete.append(point)
        for p in points_to_delete:
            self.current_element_simulation.remove_point(
                self.current_recoil_element, p)

    def update_current_recoils_zeros(self):
        """
         Update current recoil element's points to match with current element
         simulation's first recoil element's zeros on the y axis.
        """
        # Add singular zeros
        for x in self.current_element_simulation.recoil_elements[0]. \
                zero_values_on_x:
            if x not in self.current_recoil_element.zero_values_on_x:
                new_point = self.add_zero_point(x)
                # Fix neighbors
                self.fix_left_neighbor_of_zero(new_point)
                self.fix_right_neighbor_of_zero(new_point)
        # Remove singular zeros
        if self.current_element_simulation.recoil_elements[0].\
           zero_values_on_x != self.current_recoil_element.zero_values_on_x:
            for val in reversed(self.current_recoil_element.zero_values_on_x):
                if val not in self.current_element_simulation.\
                        recoil_elements[0].zero_values_on_x:
                    self.current_recoil_element.zero_values_on_x.remove(val)
                    xs = self.current_recoil_element.get_xs()
                    i = xs.index(val)
                    remove_point = self.current_recoil_element.get_point_by_i(i)
                    self.current_element_simulation.remove_point(
                        self.current_recoil_element, remove_point)
        # Add intervals
        for interval in self.current_element_simulation.recoil_elements[0].\
                zero_intervals_on_x:
            interval_start = interval[0]
            interval_end = interval[1]
            points = self.current_recoil_element.get_points()
            for point in points:
                x = point.get_x()
                y = point.get_y()
                if x == interval_start or x == interval_end:
                    point.set_y(0.0)
                elif interval_start < x < interval_end and y != 0.0:
                    point.set_y(0.0)
            if interval_start not in self.current_recoil_element.get_xs():
                new_point = self.add_zero_point(interval_start)
                self.fix_left_neighbor_of_zero(new_point)
            if interval_end not in self.current_recoil_element.get_xs():
                new_point = self.add_zero_point(interval_end)
                self.fix_right_neighbor_of_zero(new_point)
        # Remove intervals
        if self.current_element_simulation.recoil_elements[0].\
           zero_intervals_on_x != \
           self.current_recoil_element.zero_intervals_on_x:
            for interval2 in self.current_recoil_element.zero_intervals_on_x:
                if interval2 not in \
                   self.current_element_simulation.recoil_elements[0].\
                   zero_intervals_on_x:
                    for point2 in self.current_recoil_element.get_points():
                        p_x = point2.get_x()
                        if interval2[0] <= p_x <= interval2[1]:
                            is_inside = False
                            for interval3 in \
                                    self.current_element_simulation.\
                                    recoil_elements[0].zero_intervals_on_x:
                                if interval3[0] <= p_x <= interval3[1]:
                                    is_inside = True
                                    break
                            if is_inside or p_x in \
                                    self.current_element_simulation.\
                                    recoil_elements[0].zero_values_on_x:
                                continue
                            else:
                                point2.set_y(0.0001)

        # Update current recoil's zero lists
        self.current_recoil_element.update_zero_values()

        # Clean up unnecessary points inside zero intervals
        points_to_remove = []
        for inter in self.current_recoil_element.zero_intervals_on_x:
            for p in self.current_recoil_element.get_points():
                if inter[0] < p.get_x() < inter[1]:
                    points_to_remove.append(p)
        for r_p in points_to_remove:
            self.current_element_simulation.remove_point(
                self.current_recoil_element, r_p)

    def fix_left_neighbor_of_zero(self, point):
        """
        If there should be non-zero values between point and its left
        neighbor, add a new point between them.
        """
        left_n = self.current_element_simulation.get_left_neighbor(
            self.current_recoil_element, point)
        if not left_n:
            return
        left_n_y = left_n.get_y()
        if left_n_y == 0.0:
            x_place = round((point.get_x() + left_n.get_x()) / 2, 2)
            self.add_point((x_place, 0.0001))

    def fix_right_neighbor_of_zero(self, point):
        """
        If there should be non-zero values between point and its right
        neighbor, add a new point between them.
        """
        right_n = self.current_element_simulation.get_right_neighbor(
            self.current_recoil_element, point)
        if not right_n:
            return
        right_n_y = right_n.get_y()

        if right_n_y == 0.0:
            x_place = round((point.get_x() + right_n.get_x()) /
                            2, 2)
            self.add_point((x_place, 0.0001))

    def add_zero_point(self, x):
        """
        Add new zero point with x as x coordinate.

        Args:
            x: X coordinate value.
        """
        new_point = Point((x, 0.0))
        xs = self.current_recoil_element.get_xs()
        if x in xs:
            i = xs.index(x)
            new_point = self.current_recoil_element.get_point_by_i(i)
        else:
            self.current_element_simulation.add_point(
                self.current_recoil_element, new_point)

        self.current_recoil_element.zero_values_on_x.append(x)
        self.current_recoil_element.zero_values_on_x = sorted(
            self.current_recoil_element.zero_values_on_x)

        left_neighbor = self.current_element_simulation.get_left_neighbor(
            self.current_recoil_element, new_point)
        right_neighbor = self.current_element_simulation.get_right_neighbor(
            self.current_recoil_element, new_point)

        # If points doesn't have right neighbor, return
        if not right_neighbor or not left_neighbor:
            return new_point

        left_neighbor_x = left_neighbor.get_x()
        right_neighbor_x = right_neighbor.get_x()

        # If too close to left
        if new_point.get_x() - left_neighbor_x < self.x_res:
            # Try to move left neighbor
            left_left_neighbor = \
                self.current_element_simulation.get_left_neighbor(
                    self.current_recoil_element, left_neighbor)
            # If there is no space for left neighbor, remove it
            if round(left_left_neighbor and new_point.get_x() -
               left_left_neighbor.get_x(), 2) < 2 * self.x_res:
                self.current_element_simulation.remove_point(
                    self.current_recoil_element, left_neighbor)
            else:
                # Move left neighbor to make room for zero point
                left_neighbor.set_x(new_point.get_x() - self.x_res)
        elif round(right_neighbor_x - new_point.get_x(), 2) < self.x_res:
            # Try to move right neighbor
            right_right_neighbor = \
                self.current_element_simulation.get_right_neighbor(
                    self.current_recoil_element, right_neighbor)
            # If there is no space for right neighbor, remove it
            if round(right_right_neighbor and right_right_neighbor.get_x() -
               new_point.get_x(), 2) < 2 * self.x_res:
                self.current_element_simulation.remove_point(
                    self.current_recoil_element, right_neighbor)
            else:
                # Move right neighbor to make room for zero point
                right_neighbor.set_x(new_point.get_x() + self.x_res)

        return new_point

    def update_recoil_element_info_labels(self):
        """
        Update recoil element info labels.
        """
        self.parent_ui.nameLabel.setText(
            "Name: " + self.current_recoil_element.name)
        self.parent_ui.referenceDensityLabel.setText(
            "Reference density: " + "{0:1.2f}".format(
                self.current_recoil_element.reference_density) +
            "e22 at/cm\xb2"
        )

    def recoil_element_info_on_switch(self):
        """
        Show recoil element info on switch.
        """
        if self.current_element_simulation is None:
            self.parent_ui.elementInfoWidget.hide()
        else:
            self.parent_ui.elementInfoWidget.show()

    def add_element_with_dialog(self):
        """
        Add new element simulation with dialog.
        """
        dialog = RecoilElementSelectionDialog(self)
        if dialog.isOk:
            if dialog.isotope is None:
                isotope = int(round(masses.get_standard_isotope(
                    dialog.element)))
            else:
                isotope = dialog.isotope
            element_simulation = self.add_element(Element(
                dialog.element, isotope))

            self.current_element_simulation = element_simulation
            self.current_recoil_element = element_simulation. \
                recoil_elements[0]
            element_simulation.recoil_elements[0].widgets[0].radio_button \
                .setChecked(True)

    def add_element(self, element, element_simulation=None):
        """
        Adds a new ElementSimulation based on the element. If elem_sim is
         not None, only UI widgets need to be added.

         Args:
             element: Element that is added.
             element_simulation: ElementSimulation that needs the UI widgets.
        """
        if element_simulation is None:
            # Create new ElementSimulation
            element_simulation = self.element_manager \
                .add_new_element_simulation(element)
        else:
            element_simulation = element_simulation
            self.element_manager.add_element_simulation(element_simulation)

        # Add recoil element widgets
        for recoil_element in element_simulation.recoil_elements:
            recoil_element_widget = recoil_element.widgets[0]
            self.radios.addButton(recoil_element_widget.radio_button)
            self.recoil_vertical_layout.addWidget(recoil_element_widget)

        return element_simulation

    def remove_element(self, element_simulation):
        """
        Remove element simulation.

        Args:
            element_simulation: An ElementSimulation object.
        """
        self.element_manager.remove_element_simulation(element_simulation)

    def remove_recoil_element(self, recoil_widget, element_simulation=None,
                              recoil_element=None):
        """
        Remove recoil element that has the given recoil_widget.

        Args:
             recoil_widget: A RecoilElementWidget.
             element_simulation: An ElementSimulation object.
             recoil_element: A RecoilElement object.
        """
        recoil_to_delete = recoil_element
        element_simulation = element_simulation
        if not recoil_to_delete and not element_simulation:
            for elem_sim in self.element_manager.element_simulations:
                for recoil_element in elem_sim.recoil_elements:
                    if recoil_element.widgets[0] is recoil_widget:
                        recoil_to_delete = recoil_element
                        element_simulation = elem_sim
                        break
        if recoil_to_delete and element_simulation:
            if recoil_widget.radio_button.isChecked():
                element_simulation.recoil_elements[0]. \
                    widgets[0].radio_button.setChecked(True)
            # Remove radio button from list
            self.radios.removeButton(recoil_widget.radio_button)
            # Remove recoil widget from view
            recoil_widget.deleteLater()
            # Remove recoil element from element simulation
            element_simulation.recoil_elements.remove(recoil_to_delete)
            # Delete rec, recoil and simu files.
            rec_file = os.path.join(element_simulation.directory,
                                    recoil_to_delete.prefix + "-" +
                                    recoil_to_delete.name + ".rec")
            if os.path.exists(rec_file):
                os.remove(rec_file)
            recoil_file = os.path.join(element_simulation.directory,
                                       recoil_to_delete.prefix + "-" +
                                       recoil_to_delete.name + ".recoil")
            if os.path.exists(recoil_file):
                os.remove(recoil_file)
            simu_file = os.path.join(element_simulation.directory,
                                     recoil_to_delete.prefix + "-" +
                                     recoil_to_delete.name + ".simu")
            if os.path.exists(simu_file):
                os.remove(simu_file)

    def remove_current_element(self):
        """
        Remove current element simulation.
        """
        if not self.current_element_simulation:
            return
        if self.current_recoil_element is not \
                self.current_element_simulation.recoil_elements[0]:
            return
        reply = QtWidgets.QMessageBox.question(self.parent, "Confirmation",
                                               "If you delete selected "
                                               "element simulation, "
                                               "all possible recoils "
                                               "connected to it will be "
                                               "also deleted.\n\nAre you sure "
                                               "you want to delete selected "
                                               "element simulation?",
                                               QtWidgets.QMessageBox.Yes |
                                               QtWidgets.QMessageBox.No |
                                               QtWidgets.QMessageBox.Cancel,
                                               QtWidgets.QMessageBox.Cancel)
        if reply == QtWidgets.QMessageBox.No or reply == \
                QtWidgets.QMessageBox.Cancel:
            return  # If clicked Yes, then continue normally
        element_simulation = self.element_manager \
            .get_element_simulation_with_radio_button(
                self.radios.checkedButton())
        # Remove possible other recoil elements
        for recoil_elem in element_simulation.recoil_elements:
            self.remove_recoil_element(recoil_elem.widgets[0],
                                       element_simulation, recoil_elem)
        self.current_recoil_element = None
        self.remove_element(element_simulation)
        self.current_element_simulation = None
        self.parent_ui.elementInfoWidget.hide()
        self.update_plot()

    def export_elements(self):
        """
        Export elements from target layers into element simulations.
        """
        for layer in self.target.layers:
            for layer_element in layer.elements:
                already_exists = False

                for existing_element_simulation \
                        in self.element_manager.element_simulations:

                    for recoil_element \
                            in existing_element_simulation.recoil_elements:

                        if layer_element.isotope \
                                == recoil_element.element.isotope \
                                and layer_element.symbol \
                                == recoil_element.element.symbol:
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
                self.current_element_simulation.get_xs(
                    self.current_recoil_element),
                self.current_element_simulation.get_ys(
                    self.current_recoil_element),
                color="blue")

            self.markers, = self.axes.plot(
                self.current_element_simulation.get_xs(
                    self.current_recoil_element),
                self.current_element_simulation.get_ys(
                    self.current_recoil_element),
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

        self.axes.set_xlim(-1, 40)
        self.axes.set_ylim(-0.1, 2)

        # Remove axis ticks and draw
        self.remove_axes_ticks()
        self.canvas.draw()

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

    def __fork_toolbar_buttons(self):
        """
        Fork navigation tool bar button into custom ones.
        """
        super().fork_toolbar_buttons()
        self.mpl_toolbar.mode_tool = 0
        self.__tool_label = self.mpl_toolbar.children()[24]
        self.__button_drag = self.mpl_toolbar.children()[12]
        self.__button_zoom = self.mpl_toolbar.children()[14]
        self.__button_drag.clicked.connect(self.__toggle_tool_drag)
        self.__button_zoom.clicked.connect(self.__toggle_tool_zoom)

        # Make own buttons
        self.mpl_toolbar.addSeparator()

        # Coordinates widget
        self.coordinates_widget = PointCoordinatesWidget(self)
        self.coordinates_action = self.mpl_toolbar.addWidget(
            self.coordinates_widget)

        if not self.current_element_simulation:
            self.coordinates_action.setVisible(False)
        else:
            self.coordinates_widget.y_coordinate_box.setEnabled(False)
            self.coordinates_widget.x_coordinate_box.setEnabled(False)

        # Point removal
        self.point_remove_action = QtWidgets.QAction("Remove point", self)
        self.point_remove_action.triggered.connect(self.remove_points)
        self.point_remove_action.setToolTip("Remove selected points")
        # TODO: Temporary icon
        self.__icon_manager.set_icon(self.point_remove_action, "del.png")
        self.mpl_toolbar.addAction(self.point_remove_action)

        self.__button_area_calculation = QtWidgets.QToolButton(self)
        self.__button_area_calculation.clicked.connect(
            self.__calculate_selected_area)
        self.__button_area_calculation.setToolTip(
            "Calculate the area inside the selected interval")
        self.__icon_manager.set_icon(self.__button_area_calculation,
                                     "depth_profile_lim_in.svg")
        self.mpl_toolbar.addWidget(self.__button_area_calculation)
        self.__button_area_calculation.setEnabled(False)

    def __update_multiply_action(self):
        self.ratio_str = self.clipboard.text()
        self.coordinates_widget.actionXMultiply.setText(
            "Multiply with value in clipboard\n(" + self.ratio_str + ")")
        self.coordinates_widget.actionYMultiply.setText(
            "Multiply with value in clipboard\n(" + self.ratio_str + ")")

    def set_selected_point_x(self, x=None, clicked=None):
        """Sets the selected point's x coordinate
        to the value of the x spinbox.

        Args:
            x: New x coordinate.
            clicked: Clicked point.
        """
        if not x:
            x = self.coordinates_widget.x_coordinate_box.value()
        if not clicked:
            clicked = self.clicked_point
        left_neighbor = self.current_element_simulation.get_left_neighbor(
            self.current_recoil_element,
            clicked)
        right_neighbor = self.current_element_simulation.get_right_neighbor(
            self.current_recoil_element,
            clicked)

        # Can't move past neighbors. If tried, sets x coordinate to
        # distance x_res from neighbor's x coordinate.
        if left_neighbor is None:
            if x < right_neighbor.get_x():
                clicked.set_x(x)
            else:
                clicked.set_x(right_neighbor.get_x() - self.x_res)
        elif right_neighbor is None:
            if x > left_neighbor.get_x():
                clicked.set_x(x)
            else:
                clicked.set_x(left_neighbor.get_x() + self.x_res)
        elif left_neighbor.get_x() < x < right_neighbor.get_x():
            clicked.set_x(x)
        elif left_neighbor.get_x() >= x:
            clicked.set_x(left_neighbor.get_x() + self.x_res)
        elif right_neighbor.get_x() <= x:
            clicked.set_x(right_neighbor.get_x() - self.x_res)
        self.update_plot()

    def set_selected_point_y(self, y=None, clicked=None):
        """Sets the selected point's y coordinate
        to the value of the y spinbox.

        Args:
            y: New y coordinate.
            clicked: Clicked point.
        """
        if not y:
            y = self.coordinates_widget.y_coordinate_box.value()
        if not clicked:
            clicked = self.clicked_point
        clicked.set_y(y)
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
                self.point_clicked = True
                self.span_selector.set_active(False)
                i = marker_info['ind'][0]  # The clicked point's index
                clicked_point = \
                    self.current_element_simulation.get_point_by_i(
                        self.current_recoil_element, i)
                if clicked_point not in self.selected_points:
                    self.selected_points = [clicked_point]
                self.dragged_points.extend(self.selected_points)
                self.clicked_point = clicked_point
                # If clicked point is first
                if self.clicked_point is \
                        self.current_recoil_element.get_points()[0]:
                    self.point_remove_action.setEnabled(False)
                # If clicked point is last and full edit is not on
                elif self.clicked_point is \
                        self.current_recoil_element.get_points()[-1] and not \
                        self.full_edit_on:
                    self.point_remove_action.setEnabled(False)
                else:
                    self.point_remove_action.setEnabled(True)
                # If clicked point is zero and full edit is not on
                if self.clicked_point.get_y() == 0.0:
                    if not self.full_edit_on or self.current_recoil_element !=\
                       self.current_element_simulation.recoil_elements[0]:
                        self.point_remove_action.setEnabled(False)
                        self.coordinates_widget.x_coordinate_box.setEnabled(
                            False)
                    else:
                        self.coordinates_widget.x_coordinate_box.setEnabled(
                            True)
                        self.coordinates_widget.y_coordinate_box.setEnabled(
                            True)
                elif self.current_element_simulation.recoil_elements[0] != \
                        self.current_recoil_element or not self.full_edit_on:
                    # If point is between two zeros, cannot delete
                    left_neighbor = \
                        self.current_element_simulation.get_left_neighbor(
                            self.current_recoil_element,
                            self.clicked_point)
                    right_neighbor = \
                        self.current_element_simulation.get_right_neighbor(
                            self.current_recoil_element,
                            self.clicked_point)
                    if left_neighbor and right_neighbor:
                        if left_neighbor.get_y() == 0.0 and \
                                right_neighbor.get_y() == 0.0:
                            self.point_remove_action.setEnabled(False)
                    self.coordinates_widget.x_coordinate_box.setEnabled(True)
                else:
                    self.coordinates_widget.x_coordinate_box.setEnabled(True)
                self.set_on_click_attributes(event)

                # Check if undoing multiply is possible
                if self.clicked_point.previous_y:
                    self.coordinates_widget.actionYUndo.setEnabled(True)
                else:
                    self.coordinates_widget.actionYUndo.setEnabled(False)
                if self.clicked_point.previous_x:
                    self.coordinates_widget.actionXUndo.setEnabled(True)
                else:
                    self.coordinates_widget.actionXUndo.setEnabled(False)

                self.update_plot()
            else:
                self.point_clicked = False
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
                            self.clicked_point = new_point
                            if new_point.get_y() == 0.0:
                                if not self.full_edit_on or \
                                   self.current_recoil_element != \
                                   self.current_element_simulation.\
                                   recoil_elements[0]:
                                    self.point_remove_action.setEnabled(False)
                                    self.coordinates_widget.y_coordinate_box.\
                                        setEnabled(False)
                            self.set_on_click_attributes(event)
                            self.update_plot()

        elif event.button == 3:  # Right click
            self.__rectangle_event_click = event
            self.__rectangle_event_release = event

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
            if self.dragged_points[i].get_y() \
                    < self.dragged_points[self.lowest_dr_p_i].get_y():
                self.lowest_dr_p_i = i
        self.y_dist_lowest = [self.dragged_points[i].get_y()
                              - self.dragged_points[self.lowest_dr_p_i].get_y()
                              for i in range(len(self.dragged_points))]

    def add_point(self, coords, special=False):
        """Adds a point if there is space for it.
        Returns the point if a point was added, None if not.
        """
        if not self.current_element_simulation:
            return
        new_point = Point(coords)
        self.current_element_simulation.add_point(
            self.current_recoil_element, new_point)
        left_neighbor = self.current_element_simulation.get_left_neighbor(
            self.current_recoil_element, new_point)
        left_neighbor_x = left_neighbor.get_x()

        right_neighbor = self.current_element_simulation.get_right_neighbor(
            self.current_recoil_element, new_point)

        if right_neighbor:
            right_neighbor_x = right_neighbor.get_x()

            error = False

            # If too close to left
            if new_point.get_x() - left_neighbor_x < self.x_res:
                # Need space to insert the new point
                if right_neighbor_x - new_point.get_x() < 2 * self.x_res:
                    error = True
                else:
                    # Insert the new point as close to its left neighbor as
                    # possible
                    new_point.set_x(left_neighbor_x + self.x_res)
            elif right_neighbor_x - new_point.get_x() < self.x_res:
                if new_point.get_x() - left_neighbor_x < 2 * self.x_res:
                    error = True
                else:
                    new_point.set_x(right_neighbor_x - self.x_res)

            if not self.full_edit_on or \
               self.current_element_simulation.recoil_elements[0] != \
               self.current_recoil_element:
                # Check if point is added between two zeros
                if right_neighbor.get_y() == 0.0 and left_neighbor.get_y() ==\
                   0.0:
                    new_point.set_y(0.0)
                elif new_point.get_y() < 0.0001:
                    new_point.set_y(0.0001)

            if error:
                self.current_element_simulation.remove_point(
                    self.current_recoil_element, new_point)
                QtWidgets.QMessageBox.critical(self.parent, "Error",
                                               "Can't add a point here.\nThere "
                                               "is no space for it.",
                                               QtWidgets.QMessageBox.Ok,
                                               QtWidgets.QMessageBox.Ok)
                return None
            else:
                return new_point

        elif special:
            # When adding a non-zero point at the end of the recoil
            if new_point.get_x() - left_neighbor_x < self.x_res:
                new_point.set_x(left_neighbor_x + self.x_res)
            return new_point

    def update_plot(self):
        """ Updates marker and line data and redraws the plot. """
        if not self.current_element_simulation:
            self.markers.set_visible(False)
            self.lines.set_visible(False)
            self.markers_selected.set_visible(False)
            self.fig.canvas.draw_idle()
            return

        self.markers.set_data(self.current_element_simulation.get_xs(
            self.current_recoil_element),
            self.current_element_simulation.get_ys(
                self.current_recoil_element))
        self.lines.set_data(self.current_element_simulation.get_xs(
            self.current_recoil_element),
            self.current_element_simulation.get_ys(
                self.current_recoil_element))

        self.markers.set_visible(True)
        self.lines.set_visible(True)

        if self.selected_points:  # If there are selected points
            self.coordinates_action.setVisible(True)
            self.markers_selected.set_visible(True)
            selected_xs = []
            selected_ys = []
            for point in self.selected_points:
                selected_xs.append(point.get_x())
                selected_ys.append(point.get_y())
            self.markers_selected.set_data(selected_xs, selected_ys)

            if self.clicked_point:
                self.coordinates_widget.x_coordinate_box.setValue(
                    self.clicked_point.get_x())
                self.coordinates_widget.y_coordinate_box.setValue(
                    self.clicked_point.get_y())
                # Disable y coordinate if it's zero and full edit is not on
                if self.clicked_point.get_y() == 0.0:
                    if not self.full_edit_on or \
                       self.current_element_simulation.recoil_elements[0]\
                       != self.current_recoil_element:
                        self.coordinates_widget.y_coordinate_box.setEnabled(
                            False)
                else:
                    self.coordinates_widget.y_coordinate_box.setEnabled(True)
        else:
            self.markers_selected.set_data(
                self.current_element_simulation.get_xs(
                    self.current_recoil_element),
                self.current_element_simulation.get_ys(
                    self.current_recoil_element))
            self.markers_selected.set_visible(False)
            self.coordinates_action.setVisible(False)

        # Show all of recoil
        if self.__show_all_recoil:
            last_point = self.current_recoil_element.get_point_by_i(len(
                self.current_recoil_element.get_points()) - 1)
            last_point_x = last_point.get_x()
            x_min, xmax = self.axes.get_xlim()
            if xmax < last_point_x:
                self.axes.set_xlim(x_min, last_point_x + 0.04 * last_point_x)

        self.fig.canvas.draw_idle()

    def update_layer_borders(self):
        """
        Update layer borders.
        """
        for annotation in self.annotations:
            annotation.set_visible(False)
        self.annotations = []
        last_layer_thickness = 0

        y = 0.95
        next_layer_position = 0
        for idx, layer in enumerate(self.target.layers):
            self.axes.axvspan(
                next_layer_position, next_layer_position + layer.thickness,
                facecolor=self.layer_colors[idx % 2]
            )

            # Put annotation in the middle of the rectangular patch.
            annotation = self.axes.text(layer.start_depth, y,
                                        layer.name,
                                        transform=self.trans,
                                        fontsize=10,
                                        ha="left")
            y = y - 0.05
            if y <= 0.1:
                y = 0.95
            self.annotations.append(annotation)
            last_layer_thickness = layer.thickness

            # Move the position where the next layer starts.
            next_layer_position += layer.thickness

        if self.original_x_limits:
            start = self.original_x_limits[0]
            end = self.original_x_limits[1]
        else:
            end = next_layer_position - last_layer_thickness * 0.7
            start = 0 - end * 0.05

        if self.__show_all_recoil:
            last_point = self.current_recoil_element.get_point_by_i(len(
                self.current_recoil_element.get_points()) - 1)
            last_point_x = last_point.get_x()
            if end < last_point_x:
                end = last_point_x + 0.04 * last_point_x

        self.axes.set_xlim(start, end)
        self.fig.canvas.draw_idle()

    def on_span_motion(self, xmin, xmax):
        """
        Check if there are no dragged points before showing the span.
        """
        if self.dragged_points or self.point_clicked:
            self.span_selector.set_active(False)

    def on_motion(self, event):
        """Callback method for mouse motion event. Moves points that are being
        dragged.

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

        # Check if the point's y coordinate is zero or it is the last or
        # first point. Move accordingly
        # When full edit is not on, zero vy values stay zero, and start and
        # end points can only move in y direction
        for i in range(0, len(dr_ps)):
            # End point
            if dr_ps[i] == self.current_recoil_element.get_points()[-1] \
               and (not self.full_edit_on or self.current_recoil_element
               != self.current_element_simulation.recoil_elements[0]):
                if dr_ps[i].get_y() == 0.0:
                    continue
                else:
                    dr_ps[i].set_y(new_coords[i][1])
            # Start point
            elif dr_ps[i] == self.current_recoil_element.get_points()[0]:
                if not self.full_edit_on and dr_ps[i].get_y() == 0.0:
                    continue
                else:
                    dr_ps[i].set_y(new_coords[i][1])
            else:
                if dr_ps[i].get_y() == 0.0 and not self.full_edit_on and \
                        self.current_recoil_element == \
                        self.current_element_simulation.recoil_elements[0]:
                    dr_ps[i].set_coordinates((dr_ps[i].get_x(), 0.0))
                else:
                    if self.current_recoil_element != \
                            self.current_element_simulation.recoil_elements[0] \
                            and dr_ps[i].get_y() == 0.0:
                        dr_ps[i].set_coordinates((dr_ps[i].get_x(), 0.0))
                    else:
                        dr_ps[i].set_coordinates(new_coords[i])
            # Check that dragged point hasn't crossed with neighbors
            left_neighbor = \
                self.current_element_simulation.get_left_neighbor(
                    self.current_recoil_element, dr_ps[i])
            if left_neighbor:
                l_n_x = left_neighbor.get_x()
                if dr_ps[i].get_x() <= l_n_x:
                    dr_ps[i].set_x(l_n_x + self.x_res)

            right_neighbor = \
                self.current_element_simulation.get_right_neighbor(
                    self.current_recoil_element, dr_ps[i])
            if right_neighbor:
                r_n_x = right_neighbor.get_x()
                if r_n_x <= dr_ps[i].get_x():
                    dr_ps[i].set_x(r_n_x - self.x_res)

            self.__calculate_selected_area()

        self.update_plot()

    def get_new_checked_coordinates(self, event):
        """Returns checked new coordinates for dragged points.
        They have been checked for neighbor or axis limit collisions.
        """
        dr_ps = self.dragged_points

        leftmost_dr_p = dr_ps[0]
        rightmost_dr_p = dr_ps[-1]
        left_neighbor = self.current_element_simulation.get_left_neighbor(
            self.current_recoil_element, leftmost_dr_p)
        right_neighbor = self.current_element_simulation.get_right_neighbor(
            self.current_recoil_element, rightmost_dr_p)

        new_coords = self.get_new_unchecked_coordinates(event)

        if left_neighbor is None and right_neighbor is None:
            pass  # No neighbors to limit movement
        # Check for neighbor collisions:
        elif left_neighbor is None and right_neighbor is not None:
            if new_coords[-1][0] >= right_neighbor.get_x() - self.x_res:
                new_coords[-1][0] = right_neighbor.get_x() - self.x_res
                for i in range(0, len(dr_ps) - 1):
                    new_coords[i][0] = right_neighbor.get_x() \
                                       - self.x_res - self.x_dist_right[i]
        elif right_neighbor is None and left_neighbor is not None:
            if new_coords[0][0] <= left_neighbor.get_x() + self.x_res:
                new_coords[0][0] = left_neighbor.get_x() + self.x_res
                for i in range(1, len(dr_ps)):
                    new_coords[i][0] = left_neighbor.get_x() + self.x_res \
                                       + self.x_dist_left[i - 1]
        elif left_neighbor.get_x() + self.x_res >= new_coords[0][0]:
            new_coords[0][0] = left_neighbor.get_x() + self.x_res
            for i in range(1, len(dr_ps)):
                new_coords[i][0] = left_neighbor.get_x() + self.x_res \
                                   + self.x_dist_left[i - 1]
        elif right_neighbor.get_x() - self.x_res <= new_coords[-1][0]:
            new_coords[-1][0] = right_neighbor.get_x() - self.x_res
            for i in range(0, len(dr_ps) - 1):
                new_coords[i][0] = right_neighbor.get_x() - self.x_res \
                                   - self.x_dist_right[i]

        # Check for axis limit collisions:
        if new_coords[0][0] < 0:
            new_coords[0][0] = 0
            for i in range(1, len(dr_ps)):
                new_coords[i][0] = self.x_dist_left[i - 1]

        # Check that y_min is not crossed
        if self.current_recoil_element != \
                self.current_element_simulation.recoil_elements[0]:
            y_min = 0.0001
        else:
            y_min = self.current_element_simulation.y_min
        if new_coords[self.lowest_dr_p_i][1] < y_min:
            new_coords[self.lowest_dr_p_i][1] = y_min
            for i in range(0, len(dr_ps)):
                new_coords[i][1] = y_min + self.y_dist_lowest[i]

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
        ret = False
        if len(self.current_recoil_element.get_points()) - \
           len(self.selected_points) < 2:
            QtWidgets.QMessageBox.critical(self.parent, "Error",
                                           "You cannot delete this "
                                           "point.\nThere must always be at "
                                           "least two points.",
                                           QtWidgets.QMessageBox.Ok,
                                           QtWidgets.QMessageBox.Ok)
            ret = True
        if self.current_recoil_element.get_points()[0] in \
           self.selected_points:
            QtWidgets.QMessageBox.critical(self.parent, "Error",
                                           "You cannot delete the first "
                                           "point.",
                                           QtWidgets.QMessageBox.Ok,
                                           QtWidgets.QMessageBox.Ok)
            ret = True
        if self.current_recoil_element.get_points()[-1] in \
           self.selected_points and not self.full_edit_on:
            QtWidgets.QMessageBox.critical(self.parent, "Error",
                                           "You cannot delete the last "
                                           "point when full edit is locked.",
                                           QtWidgets.QMessageBox.Ok,
                                           QtWidgets.QMessageBox.Ok)
            ret = True
        if 0.0 in self.current_recoil_element.get_ys():
            show_msg = False
            reason = "."
            if not self.full_edit_on:
                reason = " when full edit is on."
                show_msg = True
            if self.current_recoil_element != \
                    self.current_element_simulation.recoil_elements[0]:
                reason = " from non-main recoil element."
                show_msg = True
            if show_msg:
                for point in self.selected_points:
                    if point.get_y() == 0.0:
                        QtWidgets.QMessageBox.critical(self.parent, "Error",
                                                       "You cannot delete a "
                                                       "point that has 0 as a "
                                                       "y coordinate" + reason,
                                                       QtWidgets.QMessageBox.Ok,
                                                       QtWidgets.QMessageBox.Ok)
                        ret = True
                        break
        # Check if trying to delete a non-zero point from between two zero
        # points
        for point in self.selected_points:
            left_neighbor = self.current_element_simulation.get_left_neighbor(
                self.current_recoil_element, point)
            right_neighbor = \
                self.current_element_simulation.get_right_neighbor(
                    self.current_recoil_element, point)
            if left_neighbor and right_neighbor:
                if left_neighbor.get_y() == 0.0and right_neighbor.get_y() == \
                   0.0 and point.get_y() != 0.0:
                    QtWidgets.QMessageBox.critical(self.parent, "Error",
                                                   "You cannot delete a "
                                                   "point that has a non-zero y"
                                                   " coordinate from between "
                                                   "two points that have 0 as "
                                                   "their y coordinate.",
                                                   QtWidgets.QMessageBox.Ok,
                                                   QtWidgets.QMessageBox.Ok)
                    ret = True
                    break
        if not ret:
            for sel_point in self.selected_points:
                self.current_element_simulation.remove_point(
                    self.current_recoil_element, sel_point)
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
            self.span_selector.set_active(True)
            self.update_plot()

    def __context_menu(self, event):
        """
        Create a menu for accessing the area multiplication tool.

        Args:
            event: An MPL Mouse event.
        """
        if self.current_recoil_element is \
                self.current_element_simulation.recoil_elements[0]:
            return
        if not self.current_recoil_element.area_limits:
            return

        menu = QtWidgets.QMenu(self)

        action = QtWidgets.QAction(self.tr("Multiply area..."), self)
        action.triggered.connect(self.multiply_area)
        menu.addAction(action)

        coords = self.canvas.geometry().getCoords()
        point = QtCore.QPoint(event.x, coords[3] - event.y - coords[1])

        if self.current_element_simulation.recoil_elements[0].area and \
                self.limits_match():
            action.setEnabled(True)
        else:
            action.setEnabled(False)

        menu.exec_(self.canvas.mapToGlobal(point))

    def limits_match(self):
        """
        Check if current recoil element and main recoil element area limits
        match.

        Return:
             True or False.
        """
        current_low = self.current_recoil_element.area_limits[0].get_xdata()[0]
        current_high = self.current_recoil_element.area_limits[1].get_xdata()[0]

        main_low = self.current_element_simulation.recoil_elements[0].\
            area_limits[0].get_xdata()[0]
        main_high = self.current_element_simulation.recoil_elements[0].\
            area_limits[1].get_xdata()[0]

        return current_low == main_low and current_high == main_high

    def multiply_area(self):
        """
        Multiply recoil element area and change the distribution accordingly.
        """
        dialog = MultiplyAreaDialog(
            self.current_element_simulation.recoil_elements[0])

        # If there are proper areas to handle
        if dialog.reference_area and dialog.new_area:
            # Delete/add points between limits to have matching number of points
            # Delete
            lower_limit = self.current_recoil_element.area_limits[0]. \
                get_xdata()[0]
            upper_limit = self.current_recoil_element.area_limits[1]. \
                get_xdata()[0]
            for point in reversed(self.current_recoil_element.get_points()):
                x = point.get_x()
                if x <= lower_limit:
                    break
                if upper_limit <= x:
                    continue
                else:
                    self.current_element_simulation.remove_point(
                        self.current_recoil_element, point)
            # Add
            points = self.current_element_simulation.\
                recoil_elements[0].get_points()
            main_y_lower = None
            main_y_lower_i = None
            main_y_upper = None
            main_y_upper_i = None

            for i in range(len(points)):
                main_p_x = points[i].get_x()
                main_p_y = points[i].get_y()
                if main_p_x < lower_limit:
                    continue
                if upper_limit < main_p_x:
                    break
                else:
                    if main_p_x not in self.current_recoil_element.get_xs():
                        self.add_point((main_p_x, main_p_y))
                    if main_p_x == lower_limit:
                        main_y_lower = main_p_y
                        main_y_lower_i = i
                    if main_p_x == upper_limit:
                        main_y_upper = main_p_y
                        main_y_upper_i = i

            # Adjust the lower and upper limit ys
            if main_y_lower and main_y_upper:
                lower_point = self.current_element_simulation.get_point_by_i(
                    self.current_recoil_element, main_y_lower_i)
                lower_point.set_y(main_y_lower)
                upper_point = self.current_element_simulation.get_point_by_i(
                    self.current_recoil_element, main_y_upper_i)
                upper_point.set_y(main_y_upper)

            # If fraction is defined, use it to calculate new y coordinates
            # for points between limits
            if dialog.fraction:
                for sec_p in self.current_recoil_element.get_points():
                    current_y = sec_p.get_y()
                    x = sec_p.get_x()
                    if lower_limit <= x <= upper_limit:
                        new_y = current_y * dialog.fraction
                        if 0.00 < new_y < 0.0001:
                            new_y = 0.0001
                        sec_p.set_y(new_y)
        self.__calculate_selected_area()
        self.update_plot()

    def on_span_select(self, xmin, xmax):
        """
        Select area to calculate the are of.

        Args:
             xmin: Start value of the mouse
             xmax: End value of the mouse.
        """
        if xmin == xmax or self.point_clicked:  # Do nothing if graph is clicked
            return

        low_x = round(xmin, 3)
        high_x = round(xmax, 3)

        # Find the nearest points matching the low_x and high_x
        points_x = self.current_recoil_element.get_xs()
        nearest_start = find_nearest(low_x, points_x)
        nearest_end = find_nearest(high_x, points_x)

        if nearest_start == nearest_end:
            start_i = points_x.index(nearest_start)
            if start_i == len(points_x) - 1:
                nearest_start_point = self.current_element_simulation. \
                    get_point_by_i(
                        self.current_recoil_element, start_i - 1)
                nearest_start = nearest_start_point.get_x()
            else:
                nearest_end_point = \
                    self.current_element_simulation.get_point_by_i(
                        self.current_recoil_element, start_i + 1)
                nearest_end = nearest_end_point.get_x()

        for lim in self.current_recoil_element.area_limits:
            lim.set_linestyle('None')

        self.current_recoil_element.area_limits = []

        ylim = self.axes.get_ylim()
        self.current_recoil_element.area_limits.append(self.axes.axvline(
            x=nearest_start, linestyle="--"))
        self.current_recoil_element.area_limits.append(self.axes.axvline(
            x=nearest_end, linestyle="--", color='red'))

        self.axes.set_ybound(ylim[0], ylim[1])
        self.__button_area_calculation.setEnabled(True)
        self.canvas.draw_idle()

    def __calculate_selected_area(self):
        """
        Calculate the recoil atom distribution's area inside limits.
        """
        if not self.current_recoil_element.area_limits:
            return
        lower_limit = self.current_recoil_element.area_limits[0].\
            get_xdata()[0]
        upper_limit = self.current_recoil_element.area_limits[1].\
            get_xdata()[0]

        limited_points = []
        # Get the points that are used in calculating the area
        for point in self.current_recoil_element.get_points():
            if lower_limit <= point.get_x() <= upper_limit:
                limited_points.append((point.get_x(), point.get_y()))

        # Add points if limits are not part of current recoil element's points
        if lower_limit not in self.current_element_simulation.get_xs(
                self.current_recoil_element):
            self.add_area_point(lower_limit, limited_points)

        if upper_limit not in self.current_element_simulation.get_xs(
                self.current_recoil_element):
            self.add_area_point(upper_limit, limited_points)

        polygon_points = []
        for value in limited_points:
            polygon_points.append([value[0], value[1]])

        # Add two points that have zero y coordinate to make a rectangle
        point1_x = polygon_points[len(polygon_points) - 1][0]
        point1 = (point1_x, 0.0)

        point2_x = polygon_points[0][0]
        point2 = (point2_x, 0.0)

        polygon_points.append(point1)
        polygon_points.append(point2)

        polygon_points.append((polygon_points[0][0], polygon_points[0][1]))

        polygon = Polygon(polygon_points)
        area = polygon.area
        self.current_recoil_element.area = area

        if self.anchored_box:
            self.anchored_box.set_visible(False)
            self.anchored_box = None

        text = "Area: %s" % str(round(area, 2))
        box = offsetbox.TextArea(text, textprops=dict(color="k", size=12,
                                                      backgroundcolor='w'))

        self.anchored_box = offsetbox.AnchoredOffsetbox(
                loc=1,
                child=box, pad=0.5,
                frameon=False,
                bbox_to_anchor=(1.0, 1.0),
                bbox_transform=self.axes.transAxes,
                borderpad=0.,
        )
        self.axes.add_artist(self.anchored_box)
        self.canvas.draw_idle()

    def add_area_point(self, x, points_list):
        """
        Add a point to points list.

        Args:
             x: X coordinate.
             points_list: Tuple list of points.
        """
        i = 0
        points = self.current_recoil_element.get_points()
        while i + 1 in range(len(points)):
            c_p = points[i].get_x()
            n_p = points[i + 1].get_x()
            if c_p < x < n_p:
                y = find_y_on_line(points[i], points[i + 1], x)
                # Add point to limited_points
                points_list.insert(i + 1, (x, y))
                break
            i = i + 1

    def on_rectangle_select(self, eclick, erelease):
        """
        Select multiple points.

        Args:
            eclick: Area start event.
            erelease: Area end event.
        """
        if not self.current_element_simulation:
            return
        xmin = eclick.xdata
        xmax = erelease.xdata
        ymin = eclick.ydata
        ymax = erelease.ydata

        click_x = self.__rectangle_event_click.x

        if click_x == self.__rectangle_event_release.x\
           and round(self.__rectangle_event_click.xdata, 5) != \
           round(xmin, 5):
            self.__context_menu(self.__rectangle_event_click)
            return

        sel_points = []
        for point in self.current_recoil_element.get_points():
            if xmin <= point.get_x() <= xmax and ymin <= point.get_y() <= ymax:
                sel_points.append(point)

        self.selected_points = sel_points
        if sel_points:
            allow_delete = True
            self.clicked_point = sel_points[0]
            if self.clicked_point.get_y() == 0.0:
                if not self.full_edit_on or \
                   self.current_element_simulation.recoil_elements[0] !=\
                   self.current_recoil_element:
                    self.coordinates_widget.x_coordinate_box.setEnabled(False)
                else:
                    self.coordinates_widget.x_coordinate_box.setEnabled(True)
                    self.coordinates_widget.y_coordinate_box.setEnabled(True)
            else:
                self.coordinates_widget.x_coordinate_box.setEnabled(True)
            if self.current_recoil_element.get_points()[0] in \
                    self.selected_points:
                self.point_remove_action.setEnabled(False)
                allow_delete = False
            if self.current_recoil_element.get_points()[-1] in \
               self.selected_points and not self.full_edit_on and allow_delete:
                self.point_remove_action.setEnabled(False)
                allow_delete = False
            if 0.0 in self.current_recoil_element.get_ys() and allow_delete:
                if not self.full_edit_on or self.current_recoil_element != \
                        self.current_element_simulation.recoil_elements[0]:
                    for point in self.selected_points:
                        if point.get_y() == 0.0:
                            self.point_remove_action.setEnabled(False)
                            allow_delete = False
                            break
            # Check if trying to delete a non-zero point from between two zero
            # points
            if allow_delete:
                for point in self.selected_points:
                    left_neighbor = \
                        self.current_element_simulation.get_left_neighbor(
                            self.current_recoil_element, point)
                    right_neighbor = \
                        self.current_element_simulation.get_right_neighbor(
                            self.current_recoil_element, point)
                    if left_neighbor and right_neighbor:
                        if left_neighbor.get_y() == 0.0 and right_neighbor.\
                                get_y() == 0.0 and point.get_y() != 0.0:
                            self.point_remove_action.setEnabled(False)
                            allow_delete = False
                            break

            if allow_delete:
                self.point_remove_action.setEnabled(True)

        self.update_plot()
