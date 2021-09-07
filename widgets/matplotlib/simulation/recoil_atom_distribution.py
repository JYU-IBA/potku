# coding=utf-8
"""
Created on 1.3.2018
Updated on 27.5.2019

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2018 Severi Jääskeläinen, Samuel Kaiponen, Heta Rekilä and
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

__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n " \
             "Sinikka Siironen \n Juhani Sundell"
__version__ = "2.0"

import matplotlib

import modules.general_functions as gf
import dialogs.dialog_functions as df

from widgets.matplotlib import mpl_utils
from pathlib import Path
from typing import Optional
from typing import Tuple
from typing import Dict
from typing import List

from dialogs.simulation.multiply_area import MultiplyAreaDialog
from dialogs.simulation.recoil_element_selection import \
    RecoilElementSelectionDialog
from dialogs.simulation.recoil_info_dialog import RecoilInfoDialog

from matplotlib import offsetbox
from matplotlib.widgets import RectangleSelector
from matplotlib.widgets import SpanSelector

from modules.element import Element
from modules.point import Point
from modules.enums import SimulationType
from modules.recoil_element import RecoilElement
from modules.element_simulation import ElementSimulation
from modules.simulation import Simulation
from modules.target import Target
from modules.global_settings import GlobalSettings

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5.QtCore import QLocale
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtCore import pyqtSignal

from widgets.matplotlib.mpl_utils import VerticalLimits
from widgets.matplotlib.mpl_utils import AlternatingLimits
from widgets.matplotlib.base import MatplotlibWidget
from widgets.matplotlib.simulation.element import ElementWidget
from widgets.simulation.controls import SimulationControlsWidget
from widgets.simulation.percentage_widget import PercentageWidget
from widgets.simulation.point_coordinates import PointCoordinatesWidget
from widgets.simulation.recoil_element import RecoilElementWidget
from widgets.base_tab import BaseTab
from widgets.icon_manager import IconManager


class ElementManager:
    """A class that manipulates the elements of the simulation.

    A Simulation can have 0...n ElementSimulations.
    Each ElementSimulation has 0..n RecoilElements.
    Each RecoilElement has 1 Element, 1 ElementWidget and 2...n Points.
    """

    def __init__(self, parent_tab, parent, icon_manager, simulation: Simulation,
                 statusbar=None):
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
        self.statusbar = statusbar
        self.element_simulations = self.simulation.element_simulations

    def get_element_simulation_with_recoil_element(
            self, recoil_element: RecoilElement) -> ElementSimulation:
        """Get element simulation with recoil element.

        Args:
             recoil_element: A RecoilElement object.

        Return:
            ElementSimulation.
        """
        # TODO no usages, may remove
        for element_simulation in self.element_simulations:
            if element_simulation.get_main_recoil() == recoil_element:
                return element_simulation

    def get_element_simulation_with_radio_button(
            self, radio_button) -> ElementSimulation:
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

    @staticmethod
    def get_recoil_element_with_radio_button(
            radio_button,
            element_simulation: ElementSimulation) -> RecoilElement:
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

    def add_new_element_simulation(
            self, element: Element, color: str, spectra_changed=None,
            recoil_name_changed=None, settings_updated=None,
            **kwargs) -> ElementSimulation:
        """
        Create a new ElementSimulation and RecoilElement with default points.

        Args:
            element: Element that tells the element to add.
            color: QColor object for recoil color.
            spectra_changed: pyqtSignal that is emitted when recoil element
                distribution is changed, causing the spectra to change also.
            recoil_name_changed: pyqtSignal that is emitted when recoil element
                name changes
            settings_updated: pyqtSignal that is emitted when settings are
                changed
            kwargs: keyword arguments passed down to SimulationControlsWidget

        Return:
            Created ElementSimulation
        """
        # TODO check that element does not exist
        
        # There is no y_2 if there is only one layer
        y_2 = None
        # Set first point
        xs = [0.00]
        first_layer = self.parent.target.layers[0]
        if element in first_layer.elements:
            ys = [element.amount]
        else: 
            ys = [self.parent.get_minimum_concentration()]
        
        # Make two points for each change between layers
        layer_index = 0
        for layer in self.parent.target.layers:
            # Set x-coordinates for the both points
            x_1 = layer.start_depth + layer.thickness 
            xs.append(x_1)
            x_2 = x_1 + self.parent.x_res
            xs.append(x_2)
            
            # Set y-coordinate for the first point
            for current_element in layer.elements:
                if (current_element.symbol == element.symbol and 
                        current_element.isotope == element.isotope):
                    y_1 = current_element.amount
                    break
                else:
                    y_1 = self.parent.get_minimum_concentration()
                    
            ys.append(y_1)

            # Set y-coordinate for the second point if not in the last layer
            if layer_index + 1 < len(self.parent.target.layers):
                next_layer = self.parent.target.layers[layer_index+1]
                current_symbol = element.symbol
                current_isotope = element.isotope
                
                for next_element in next_layer.elements:
                    if (next_element.symbol == current_symbol and
                            next_element.isotope == current_isotope):
                        y_2 = next_element.amount
                        break
                    else:
                        y_2 = self.parent.get_minimum_concentration()  
            
            if y_2 is not None:
                ys.append(y_2)
            layer_index += 1
            
        # Removes last point from the list
        if y_2 is not None:
            ys.pop()
        xs.pop()

        xys = list(zip(xs, ys))
        points = []
        for xy in xys:
            points.append(Point(xy))

        rec_type = self.simulation.request.default_element_simulation\
            .simulation_type.get_recoil_type()

        recoil_element = RecoilElement(
            element, points, color, rec_type=rec_type)
        element_simulation = self.simulation.add_element_simulation(
            recoil_element)
        element_widget = ElementWidget(
            self.parent, element, self.parent_tab, element_simulation, color,
            self.icon_manager, statusbar=self.statusbar,
            spectra_changed=spectra_changed,
            recoil_name_changed=recoil_name_changed,
            settings_updated=settings_updated)
        recoil_element.widgets.append(element_widget)

        # Add simulation controls widget
        simulation_controls_widget = SimulationControlsWidget(
            element_simulation, self.parent,
            recoil_name_changed=recoil_name_changed,
            settings_updated=settings_updated, **kwargs)
        self.parent_tab.contentsLayout.addWidget(simulation_controls_widget)
        element_simulation.get_main_recoil().widgets.append(
            simulation_controls_widget)

        return element_simulation

    def add_element_simulation(
            self, element_simulation: ElementSimulation, spectra_changed=None,
            recoil_name_changed=None, settings_updated=None, **kwargs):
        """
        Add an existing ElementSimulation.

        Args:
            element_simulation: ElementSimulation to be added.
            spectra_changed: pyqtSignal that is emitted when recoil element
                distribution is changed, causing the spectra to change also.
            recoil_name_changed: pyqtSignal that is emitted when recoil name
                changes.
            settings_updated: pyqtSignal that is emitted when simulation
                settings are updated
            kwargs: keyword arguments passed down to SimulationControl
        """
        main_element_widget = ElementWidget(
            self.parent, element_simulation.get_main_recoil().element,
            self.parent_tab, element_simulation,
            element_simulation.get_main_recoil().color, self.icon_manager,
            statusbar=self.statusbar, spectra_changed=spectra_changed,
            recoil_name_changed=recoil_name_changed,
            settings_updated=settings_updated)
        element_simulation.get_main_recoil().widgets.append(
            main_element_widget)

        # Add simulation controls widget
        simulation_controls_widget = SimulationControlsWidget(
            element_simulation, self.parent,
            recoil_name_changed=recoil_name_changed,
            settings_updated=settings_updated, **kwargs)
        self.parent_tab.contentsLayout.addWidget(simulation_controls_widget)
        element_simulation.get_main_recoil().widgets.append(
            simulation_controls_widget)

        # Add other recoil element widgets
        for i in range(1, len(element_simulation.recoil_elements)):
            self.add_secondary_recoil(
                element_simulation.recoil_elements[i],
                element_simulation, main_element_widget,
                spectra_changed=spectra_changed,
                recoil_name_changed=recoil_name_changed)

    def add_secondary_recoil(self, recoil_element, element_simulation,
                             main_element_widget, spectra_changed=None,
                             recoil_name_changed=None):
        """Adds an existing secondary RecoilElement to the given
        ElementSimulation object.
        """
        recoil_element_widget = RecoilElementWidget(
            self.parent, self.parent_tab, main_element_widget,
            element_simulation, recoil_element.color, recoil_element,
            statusbar=self.statusbar, spectra_changed=spectra_changed,
            recoil_name_changed=recoil_name_changed
        )
        recoil_element.widgets.append(recoil_element_widget)

        # Check if there are e.g. Default-1 named recoil elements. If so,
        # increase element.running_int_recoil
        recoil_name = recoil_element.name
        if recoil_name.startswith("Default-"):
            possible_int = recoil_name.split('-')[1]
            try:
                integer = int(possible_int)
                main_element_widget.running_int_recoil = integer + 1
            except ValueError:
                pass
        return recoil_element_widget

    def update_element_simulation(self, element_simulation: ElementSimulation,
                                  spectra_changed=None,
                                  recoil_name_changed=None):
        # TODO refactor and clean this up
        main_element_widget = next(
            (w for w in element_simulation.get_main_recoil().widgets
             if isinstance(w, ElementWidget)), None)
        rw = None

        for recoil in element_simulation.recoil_elements:
            # Check that the recoil does not already have a widget.
            secondary = next((w for w in
                              recoil.widgets
                              if isinstance(w, RecoilElementWidget) or
                              isinstance(w, ElementWidget)), None)
            if secondary is None:
                rw = self.add_secondary_recoil(
                    recoil, element_simulation, main_element_widget,
                    spectra_changed=spectra_changed,
                    recoil_name_changed=recoil_name_changed)

                self.parent.radios.addButton(rw.radio_button)
                self.parent.other_recoils.append(recoil)
                for i in range(self.parent.recoil_vertical_layout.count()):
                    if self.parent.recoil_vertical_layout.itemAt(i).widget() \
                            == main_element_widget:
                        self.parent.recoil_vertical_layout.insertWidget(
                            i + 1, rw)
                        break
        if rw is not None:
            rw.radio_button.setChecked(True)

    def remove_element_simulation(self, element_simulation: ElementSimulation):
        """Remove element simulation.

        Args:
            element_simulation: An ElementSimulation object to be removed.
        """
        element_simulation.get_main_recoil().delete_widgets()
        self.element_simulations.remove(element_simulation)

        # Delete all files that relate to element_simulation
        element_simulation.delete_all_files()

    @staticmethod
    def get_radio_buttons(element_simulation: ElementSimulation):
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

    def has_element(self, element: Element) -> bool:
        """Checks whether any ElementSimulation has an element that matches
        the given argument.
        """
        return next((True for elem_sim in self.element_simulations if
                     elem_sim.has_element(element)), False)


# setter and getter for full_edit_on property
def _full_edit_to_btn(instance, attr, value):
    btn = getattr(instance, attr)
    if value:
        btn.setText("Full edit unlocked")
    else:
        btn.setText("Unlock full edit")


def _full_edit_from_btn(instance, attr):
    btn = getattr(instance, attr)
    return btn.text() == "Full edit unlocked"


class RecoilAtomDistributionWidget(MatplotlibWidget):
    """Matplotlib simulation recoil atom distribution widget.
    Using this widget, the user can edit the recoil atom distribution
    for the simulation.
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
    # Signal that is emitted when recoil distribution changes
    recoil_dist_changed = pyqtSignal(RecoilElement, ElementSimulation)
    # Signal that is emitted when limit values are changed
    limit_changed = pyqtSignal()

    update_element_simulation = pyqtSignal(ElementSimulation)
    recoil_name_changed = pyqtSignal(ElementSimulation, RecoilElement)

    # TODO change this to minimum_concentration_changed
    full_edit_changed = pyqtSignal()

    @property
    def full_edit_on(self) -> bool:
        return _full_edit_from_btn(self, "edit_lock_push_button")

    @full_edit_on.setter
    def full_edit_on(self, value: bool):
        _full_edit_to_btn(self, "edit_lock_push_button", value)
        self.full_edit_changed.emit()

    def __init__(self, parent: "TargetWidget", simulation: Simulation,
                 target: Target, tab: BaseTab, icon_manager: IconManager,
                 settings: GlobalSettings,
                 statusbar: Optional[QtWidgets.QStatusBar] = None, **kwargs):
        """Inits recoil atom distribution widget.

        Args:
            parent: a TargetWidget class object.
            simulation: a Simulation object.
            target: a Target object.
            tab: a SimulationTabWidget
            icon_manager: an IconManager class object.
        """
        # TODO change the button text when full edit is on (or use radio btns)
        super().__init__(parent)
        self.parent = parent
        self.canvas.manager.set_title("Recoil Atom Distribution")
        self.axes.format_coord = mpl_utils.format_coord
        self.__icon_manager = icon_manager
        self.tab = tab
        self.simulation = simulation
        self._settings = settings

        self.current_element_simulation: Optional[ElementSimulation] = None
        self.current_recoil_element: Optional[RecoilElement] = None
        self.element_manager = ElementManager(
            self.tab, self, self.__icon_manager, self.simulation, statusbar)
        self.target = target
        self.layer_colors = [(0.9, 0.9, 0.9), (0.85, 0.85, 0.85)]

        # Setting up the element scroll area
        widget = QtWidgets.QWidget()
        self.recoil_vertical_layout = QtWidgets.QVBoxLayout()
        self.recoil_vertical_layout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(self.recoil_vertical_layout)

        scroll_vertical_layout = QtWidgets.QVBoxLayout()
        self.parent.recoilScrollAreaContents.setLayout(scroll_vertical_layout)

        scroll_vertical_layout.addWidget(widget)
        scroll_vertical_layout.addItem(
            QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum,
                                  QtWidgets.QSizePolicy.Expanding))

        self.parent.addPushButton.clicked.connect(
            lambda: self.add_element_with_dialog(**kwargs))
        self.parent.removePushButton.clicked.connect(
            self.remove_current_element)
        self.parent.removeallPushButton.clicked.connect(
            self.remove_all_elements)

        self.radios = QtWidgets.QButtonGroup(self)
        self.radios.buttonToggled[QtWidgets.QAbstractButton, bool].connect(
            self.choose_element)

        self.parent.editPushButton.clicked.connect(
            self.open_recoil_element_info)

        self.edit_lock_push_button = self.parent.editLockPushButton
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
        self.clicked_point: Optional[Point] = None
        # If point has been clicked
        self.point_clicked = False
        # Event for right clicking, used for either showing context menu of
        # rectangle select
        self.__rectangle_event_click = None
        # Event for releasing right click
        self.__rectangle_event_release = None
        # Interval that is common for all recoils
        self.common_interval: Optional[VerticalLimits] = None
        # Individual intervals for each recoil
        self.individual_intervals: Dict[RecoilElement, AlternatingLimits] = {}

        self.area_limits_for_all_on = False
        # Are individual limits for recoils on or not
        self.area_limits_individual_on = False
        # Save current points to backlog
        self.__save_points = True

        # Used in checking whether graph was clicked or span select was used
        self.__x_start = None
        self.__x_end = None

        self.annotations = []
        self.trans = matplotlib.transforms.blended_transform_factory(
            self.axes.transData, self.axes.transAxes)

        # Span selection tool (used to select all points within a range
        # on the x axis)
        self.span_selector = SpanSelector(
            self.axes, self.on_span_select, "horizontal", useblit=True,
            rectprops=dict(alpha=0.5, facecolor="red"), button=1,
            span_stays=True, onmove_callback=self.on_span_motion)
        self.span_selector.set_active(False)

        self.rectangle_selector = RectangleSelector(
            self.axes, self.on_rectangle_select, useblit=True, drawtype="box",
            rectprops=dict(alpha=0.5, facecolor="red"), button=3)

        # Connections and setup
        self.canvas.mpl_connect("button_press_event", self.on_click)
        self.canvas.mpl_connect("button_release_event", self.on_release)
        self.canvas.mpl_connect("motion_notify_event", self.on_motion)

        self.locale = QLocale.c()
        self.clipboard = QGuiApplication.clipboard()
        self.ratio_str = self.clipboard.text()
        self.clipboard.changed.connect(self.__update_multiply_action)

        self.__button_individual_limits = None
        self.coordinates_widget: Optional[PointCoordinatesWidget] = None
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

        # This holds all the recoils that aren't current ly selected
        self.other_recoils = []
        self.other_recoils_lines = []

        self.target_thickness = 0

        self.colormap = self._settings.get_element_colors()

        self.parent.percentButton.clicked.connect(self.__create_percent_widget)
        self.parent.percentButton.setEnabled(True)

        self.on_draw()

        if self.simulation.element_simulations:
            self.__update_figure(**kwargs)

        for button in self.radios.buttons():
            button.setChecked(True)
            break

        self.update_element_simulation.connect(
            lambda elem_sim: self.element_manager.update_element_simulation(
                elem_sim, spectra_changed=self.recoil_dist_changed,
                recoil_name_changed=self.recoil_name_changed))

    def emit_distribution_change(self):
        """Emits recoil distribution changed signal if recoil element
        and element simulation are selected.
        """
        # FIXME comes here twice after spinbox is edited
        if self.current_recoil_element is None:
            return
        if self.current_element_simulation is None:
            return
        self.recoil_dist_changed.emit(
            self.current_recoil_element, self.current_element_simulation)

    def get_current_main_recoil(self) -> Optional[RecoilElement]:
        """Returns the main recoil of currently selected ElementSimulation.
        """
        if self.current_element_simulation is not None:
            return self.current_element_simulation.get_main_recoil()
        return None

    def main_recoil_selected(self) -> bool:
        """Checks whether currently selected RecoilElement is also the main
        recoil.
        """
        if self.current_recoil_element is None:
            return False
        return self.current_recoil_element is self.get_current_main_recoil()

    def editing_restricted(self) -> bool:
        """Checks whether editing the distribution is restricted (due to full
        edit being off or main recoil not being selected).
        """
        return not self.full_edit_on or not self.main_recoil_selected()

    def first_point_selected(self) -> bool:
        """Checks whether currently selected point is first in the
        distribution.
        """
        return self.clicked_point is \
            self.current_recoil_element.get_first_point()

    def first_point_in_selection(self) -> bool:
        """Checks whether the first point of the distribution is in current
        selection of points.
        """
        return self.point_in_selection(
            self.current_recoil_element.get_first_point())

    def last_point_selected(self) -> bool:
        """Checks whether currently selected point is the last point in the
        distribution.
        """
        return self.clicked_point is \
            self.current_recoil_element.get_last_point()

    def last_point_in_selection(self) -> bool:
        """Checks whether the last point of the distribution is in current
        selection of points.
        """
        return self.point_in_selection(
            self.current_recoil_element.get_last_point())

    def point_in_selection(self, point: Point):
        """Checks whether the given point is in current selection of points.
        """
        return point in self.selected_points

    def zero_point_selected(self) -> bool:
        """Checks whether currently selected point is a zero point.
        """
        return self.clicked_point.get_y() == 0.0

    def zero_point_in_selection(self) -> bool:
        """Checks whether current selection contains a zero point.
        """
        return 0.0 in (p.get_y() for p in self.selected_points)

    def selected_between_zeros(self) -> bool:
        """Checks whether currently selected point is between two zero
        points.
        """
        return self.current_recoil_element.between_zeros(self.clicked_point)

    def get_minimum_concentration(self) -> float:
        """Returns the minimum concentration that points can be dragged to.
        """
        return self._settings.get_minimum_concentration()

    def get_current_interval(self) -> Optional[VerticalLimits]:
        return self.individual_intervals.get(
            self.current_recoil_element, None)

    def get_main_interval(self) -> Optional[VerticalLimits]:
        return self.individual_intervals.get(
            self.get_current_main_recoil(), None)

    def update_current_interval(self, x: Optional[float] = None):
        if x is not None and \
                self.current_recoil_element in self.individual_intervals:
            self.individual_intervals[
                self.current_recoil_element].update_graph(x)
        elif self.current_recoil_element not in self.individual_intervals:
            self.individual_intervals[self.current_recoil_element] = \
                AlternatingLimits(
                    self.canvas, self.axes,
                    xs=self.current_recoil_element.get_range(),
                    colors=("orange", "green"), flush=False
            )

    def set_individual_intervals_visible(self, b: bool):
        for interval in self.individual_intervals.values():
            interval.set_visible(b)

    def highlight_selected_interval(self):
        selected = self.get_current_interval()
        if selected is not None:
            selected.set_alpha(1.0)
        for interval in self.individual_intervals.values():
            if interval is not selected:
                interval.set_alpha(0.2)

    def get_individual_limits(self) -> Dict[RecoilElement, Tuple[float, float]]:
        """Returns individual area limits for each recoil element.
        """
        return {
            recoil: self.individual_intervals[recoil].get_range()
            for recoil in self.simulation.get_recoil_elements()
            if recoil in self.individual_intervals
        }

    def get_common_limits(self, rounding=None) \
            -> Tuple[Optional[float], Optional[float]]:
        """Returns a common are limit for all recoil elements.
        """
        if self.common_interval is None:
            return None, None
        xs = self.common_interval.get_range()
        if rounding is not None:
            return tuple(round(x, rounding) for x in xs)
        return tuple(xs)

    def get_all_limits(self) -> Dict:
        """Returns both common and individual area limits as a dictionary.
        """
        return {
            "common": self.get_common_limits(),
            **self.get_individual_limits()
        }

    def __update_figure(self, **kwargs):
        """Update figure.
        """
        for element_simulation in self.simulation.element_simulations:
            self.add_element(
                element_simulation.get_main_recoil().element,
                element_simulation=element_simulation, **kwargs)

        self.simulation.element_simulations[0].get_main_recoil(). \
            widgets[0].radio_button.setChecked(True)
        self.show_other_recoils()

    def __create_percent_widget(self):
        """Create a widget that calculates and shows the percentages of recoils
        on the same interval and their individual intervals.
        """
        recoils = self.simulation.get_recoil_elements()

        percentage_widget = PercentageWidget(
            recoils, self.__icon_manager,
            distribution_changed=self.recoil_dist_changed,
            interval_changed=self.limit_changed,
            get_limits=self.get_all_limits
        )
        self.tab.add_widget(percentage_widget)

    def open_recoil_element_info(self):
        """Open recoil element info.
        """
        dialog = RecoilInfoDialog(
            self.current_recoil_element, self.colormap,
            self.current_element_simulation)
        if dialog.isOk:
            new_values = dialog.get_properties()
            try:
                old_recoil_name = self.current_recoil_element.name
                self.current_element_simulation.update_recoil_element(
                    self.current_recoil_element,
                    new_values)
                # If name has changed
                if old_recoil_name != self.current_recoil_element.name:
                    # Delete energy spectra that use recoil
                    df.delete_recoil_espe(
                        self.tab,
                        f"{self.current_recoil_element.prefix}-"
                        f"{old_recoil_name}")

                    self.recoil_name_changed.emit(
                        self.current_element_simulation,
                        self.current_recoil_element)
                self.update_recoil_element_info_labels()
                self.update_colors()
            except KeyError:
                error_box = QtWidgets.QMessageBox()
                error_box.setIcon(QtWidgets.QMessageBox.Warning)
                error_box.addButton(QtWidgets.QMessageBox.Ok)
                error_box.setText(
                    "All recoil element information could not be saved.")
                error_box.setWindowTitle("Error")
                error_box.exec()

    def save_mcsimu_rec_profile(self, directory: Path, progress=None):
        """Save information to .mcsimu and .profile files.

        Args:
            directory: Directory where to save to.
            progress: ProgressReporter.
        """
        length = len(self.element_manager.element_simulations)
        for i, element_simulation in enumerate(
                self.element_manager.element_simulations):

            element_simulation.to_file(
                Path(directory, f"{element_simulation.get_full_name()}.mcsimu")
            )
            for recoil_element in element_simulation.recoil_elements:
                recoil_element.to_file(directory)

            element_simulation.profile_to_file(
                Path(directory,
                     f"{element_simulation.name_prefix}.profile"))

            if progress is not None:
                progress.report((i / length) * 100)

        if progress is not None:
            progress.report(100)

    def unlock_or_lock_edit(self):
        """Unlock or lock full edit.
        """
        if not self.full_edit_on:
            # TODO use the function in dialog functions
            # Check if current element simulation is running
            add = None
            if self.current_element_simulation.is_simulation_running() and not\
                    self.current_element_simulation.is_optimization_running():
                add = "Are you sure you want to unlock full edit for this" \
                      " running element simulation?\nIt will be stopped and " \
                      "all its simulation results will be deleted.\n\nUnlock " \
                      "full edit anyway?"
            elif self.current_element_simulation.is_simulation_finished() \
                    and not \
                    self.current_element_simulation.is_optimization_finished() \
                    and not \
                    self.current_element_simulation.is_optimization_running():
                add = "Are you sure you want to unlock full edit for this " \
                      "element simulation?\nAll its simulation results will " \
                      "be deleted.\n\nUnlock full edit anyway?"
            if add is not None:
                reply = QtWidgets.QMessageBox.warning(
                    self.parent, "Confirm", add,
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No |
                    QtWidgets.QMessageBox.Cancel, QtWidgets.QMessageBox.Cancel)
                if reply == QtWidgets.QMessageBox.No or reply == \
                        QtWidgets.QMessageBox.Cancel:
                    return

            self.current_element_simulation.unlock_edit()
            self.current_element_simulation.reset()

            self.full_edit_on = True

            if self.last_point_selected():
                self.point_remove_action.setEnabled(True)
            self.coordinates_widget.set_x_enabled(True)
        else:
            self.current_element_simulation.lock_edit()
            self.full_edit_on = False
        self.update_plot()

    def update_colors(self):
        """Update the view with current recoil element's color.
        """
        self.current_recoil_element.widgets[0].circle.set_color(
            self.current_recoil_element.color)
        self.update_plot()

    def choose_element(self, button: QtWidgets.QRadioButton, checked: bool):
        """Choose element from view.

        Args:
            button: Radio button.
            checked: Whether button is checked or not.
        """
        if not checked:
            return
        # Update limit and area parts
        # self.set_individual_intervals_visible(False)
        # if self.anchored_box is not None:
        #     self.anchored_box.set_visible(False)

        # Do necessary changes in adding and deleting recoil elements pt 1
        if self.current_recoil_element:
            self.other_recoils.append(self.current_recoil_element)
        current_element_simulation = self.element_manager \
            .get_element_simulation_with_radio_button(button)
        self.current_element_simulation = current_element_simulation
        self.current_recoil_element = \
            self.element_manager.get_recoil_element_with_radio_button(
                button, self.current_element_simulation)
        # pt 2
        try:
            self.other_recoils.remove(self.current_recoil_element)
        except ValueError:
            pass  # Not in list
        # Disable element simulation deletion button and full edit for
        # other than main recoil element
        if not self.main_recoil_selected():
            self.parent.removePushButton.setEnabled(False)
            self.edit_lock_push_button.setEnabled(False)
            # Update zero values and intervals for main recoil element
            self.get_current_main_recoil().update_zero_values()
            # If zero values changed, update them to current recoil element
            if self.get_current_main_recoil().zero_intervals_on_x != \
                    self.current_recoil_element.zero_intervals_on_x or \
                    self.get_current_main_recoil().zero_values_on_x != \
                    self.current_recoil_element.zero_values_on_x:
                # If zeros changed, destroy backlog
                self.current_recoil_element.delete_backlog()
                self.update_current_recoils_zeros()
                self.delete_and_add_possible_extra_points()
        else:
            self.parent.removePushButton.setEnabled(True)
            self.edit_lock_push_button.setEnabled(True)
        self.parent.elementInfoWidget.show()
        # Put full edit on if element simulation allows it
        self.full_edit_on = \
            self.current_element_simulation.get_full_edit_on()

        self.update_recoil_element_info_labels()
        self.dragged_points.clear()
        self.selected_points.clear()
        self.point_remove_action.setEnabled(False)

        self.highlight_selected_interval()
        self.set_individual_intervals_visible(self.area_limits_individual_on)

        # Update limit and area parts
        if self.area_limits_individual_on:
            self.__calculate_selected_area()

        # Make all other recoils grey
        self.show_other_recoils()

        self.update_plot()

    def show_other_recoils(self):
        """Show other recoils than current recoil in grey.
        """
        for line in self.other_recoils_lines:
            line.set_visible(False)
        # TODO it would be better to update the old lines rather than keep
        #   adding new lines
        self.other_recoils_lines = []
        for element_simulation in self.simulation.element_simulations:
            for recoil in element_simulation.recoil_elements:
                if recoil in self.other_recoils:
                    xs = recoil.get_xs()
                    ys = recoil.get_ys()
                    rec_line = self.axes.plot(
                        xs, ys, color=recoil.color, alpha=0.3, visible=True,
                        zorder=1)
                    self.other_recoils_lines.append(rec_line[0])
        self.fig.canvas.draw_idle()

    def delete_and_add_possible_extra_points(self):
        """If current recoil element has too many or too little points at the
        end to match the main recoil element, add or delete points accordingly.
        """
        main_points = \
            self.current_element_simulation.get_main_recoil().get_points()
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
            self.current_recoil_element.remove_point(p)

    def update_current_recoils_zeros(self):
        """Update current recoil element's points to match with current element
        simulation's first recoil element's zeros on the y axis.
        """
        # Add singular zeros
        for x in self.get_current_main_recoil().zero_values_on_x:
            if x not in self.current_recoil_element.zero_values_on_x:
                new_point = self.add_zero_point(x)
                # Fix neighbors
                self.fix_left_neighbor_of_zero(new_point)
                self.fix_right_neighbor_of_zero(new_point)
        # Remove singular zeros
        if self.get_current_main_recoil().zero_values_on_x != \
                self.current_recoil_element.zero_values_on_x:
            for val in reversed(self.current_recoil_element.zero_values_on_x):
                if val not in self.get_current_main_recoil().zero_values_on_x:
                    self.current_recoil_element.zero_values_on_x.remove(val)
                    xs = self.current_recoil_element.get_xs()
                    i = xs.index(val)
                    remove_point = self.current_recoil_element.get_point(i)
                    self.current_recoil_element.remove_point(remove_point)
        # Add intervals
        for interval in self.get_current_main_recoil().zero_intervals_on_x:
            interval_start = interval[0]
            interval_end = interval[1]
            points = self.current_recoil_element.get_points()
            for point in points:
                if interval_start <= point.get_x() <= interval_end:
                    point.set_y(0.0)
            if interval_start not in self.current_recoil_element.get_xs():
                new_point = self.add_zero_point(interval_start)
                self.fix_left_neighbor_of_zero(new_point)
            if interval_end not in self.current_recoil_element.get_xs():
                new_point = self.add_zero_point(interval_end)
                self.fix_right_neighbor_of_zero(new_point)
        # Remove intervals
        if self.get_current_main_recoil().zero_intervals_on_x != \
                self.current_recoil_element.zero_intervals_on_x:
            for interval2 in self.current_recoil_element.zero_intervals_on_x:
                if interval2 not in self.get_current_main_recoil().\
                                zero_intervals_on_x:
                    for point2 in self.current_recoil_element.get_points():
                        p_x = point2.get_x()
                        if interval2[0] <= p_x <= interval2[1]:
                            is_inside = False
                            for interval3 in self.get_current_main_recoil().\
                                    zero_intervals_on_x:
                                if interval3[0] <= p_x <= interval3[1]:
                                    is_inside = True
                                    break
                            if is_inside or p_x in \
                                    self.get_current_main_recoil().zero_values_on_x:
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
            self.current_recoil_element.remove_point(r_p)

    def fix_left_neighbor_of_zero(self, point: Point):
        """If there should be non-zero values between point and its left
        neighbor, add a new point between them.
        """
        self._fix_neigbor_of_zero(
            point, self.current_recoil_element.get_left_neighbor(point))

    def fix_right_neighbor_of_zero(self, point: Point):
        """If there should be non-zero values between point and its right
        neighbor, add a new point between them.
        """
        self._fix_neigbor_of_zero(
            point, self.current_recoil_element.get_right_neighbor(point))

    def _fix_neigbor_of_zero(self, point: Point, neighbor: Optional[Point]):
        """Checks if the neighbor Point is zero. If so, adds a non-zero
        point between point and neighbor.
        """
        if neighbor is not None and neighbor.get_y():
            x_place = round((point.get_x() + neighbor.get_x()) / 2, 2)
            self.add_point(Point(x_place, self.get_minimum_concentration()))

    def add_zero_point(self, x: float) -> Point:
        """Add new zero point with x as x coordinate.

        Args:
            x: X coordinate value.
        """
        new_point = Point((x, 0.0))
        xs = self.current_recoil_element.get_xs()
        if x in xs:
            i = xs.index(x)
            new_point = self.current_recoil_element.get_point(i)
        else:
            self.current_recoil_element.add_point(new_point)

        self.current_recoil_element.zero_values_on_x.append(x)
        self.current_recoil_element.zero_values_on_x = sorted(
            self.current_recoil_element.zero_values_on_x)

        left_neighbor, right_neighbor = \
            self.current_recoil_element.get_neighbors(new_point)

        # If points doesn't have right neighbor, return
        if right_neighbor is None or left_neighbor is None:
            return new_point

        left_neighbor_x = left_neighbor.get_x()
        right_neighbor_x = right_neighbor.get_x()

        # If too close to left
        if new_point.get_x() - left_neighbor_x < self.x_res:
            # Try to move left neighbor
            left_left_neighbor = \
                self.current_recoil_element.get_left_neighbor(left_neighbor)
            # If there is no space for left neighbor, remove it
            if round(left_left_neighbor and new_point.get_x() -
                     left_left_neighbor.get_x(), 2) < 2 * self.x_res:
                self.current_recoil_element.remove_point(left_neighbor)
            else:
                # Move left neighbor to make room for zero point
                left_neighbor.set_x(new_point.get_x() - self.x_res)
        elif round(right_neighbor_x - new_point.get_x(), 2) < self.x_res:
            # Try to move right neighbor
            right_right_neighbor = \
                self.current_recoil_element.get_right_neighbor(right_neighbor)
            # If there is no space for right neighbor, remove it
            if round(right_right_neighbor and right_right_neighbor.get_x() -
                     new_point.get_x(), 2) < 2 * self.x_res:
                self.current_recoil_element.remove_point(right_neighbor)
            else:
                # Move right neighbor to make room for zero point
                right_neighbor.set_x(new_point.get_x() + self.x_res)

        return new_point

    def update_recoil_element_info_labels(self):
        """Update recoil element info labels.
        """
        self.parent.nameLabel.setText(
            f"Name: {self.current_recoil_element.name}")
        self.parent.referenceDensityLabel.setText(
            f"Reference density: "
            f"{self.current_recoil_element.reference_density:1.2e} at./cm\xb3"
        )

    def recoil_element_info_on_switch(self):
        """Show recoil element info on switch.
        """
        if self.current_element_simulation is None:
            self.parent.elementInfoWidget.hide()
        else:
            self.parent.elementInfoWidget.show()

    def add_element_with_dialog(self, **kwargs):
        """Add new element simulation with dialog.
        """
        dialog = RecoilElementSelectionDialog(self)
        if not dialog.isOk:
            return
        isotope = dialog.isotope

        # Pass the color down as hex code
        element_simulation = self.add_element(Element(
            dialog.element, isotope), color=dialog.color.name(), **kwargs)
        if element_simulation is not None:
            element_simulation.get_main_recoil().widgets[0].radio_button \
                .setChecked(True)

    def add_element(self, element: Element,
                    element_simulation: Optional[ElementSimulation] = None,
                    color=None, **kwargs) -> Optional[ElementSimulation]:
        """Adds a new ElementSimulation based on the element. If elem_sim is
        not None, only UI widgets need to be added.

        Args:
            element: Element that is added.
            element_simulation: ElementSimulation that needs the UI widgets.
            color: A QColor object.
            kwargs: keyword arguments passed down to SimulationControlsWidget
        """
        if element_simulation is None:
            # Create new ElementSimulation
            try:
                element_simulation = \
                    self.element_manager.add_new_element_simulation(
                        element, color, spectra_changed=self.recoil_dist_changed,
                        recoil_name_changed=self.recoil_name_changed, **kwargs)
            except ValueError as e:
                QtWidgets.QMessageBox.critical(
                    self, "Error",
                    f"Could not add element {element}. Elements must be "
                    f"unique.",
                    QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
                return
        else:
            self.element_manager.add_element_simulation(
                element_simulation, spectra_changed=self.recoil_dist_changed,
                recoil_name_changed=self.recoil_name_changed, **kwargs)

        # Add recoil element widgets
        for recoil_element in element_simulation.recoil_elements:
            recoil_element_widget = recoil_element.widgets[0]
            self.radios.addButton(recoil_element_widget.radio_button)
            self.recoil_vertical_layout.addWidget(recoil_element_widget)
            self.other_recoils.append(recoil_element)

        return element_simulation

    def remove_element(self, element_simulation: ElementSimulation):
        """Remove element simulation.

        Args:
            element_simulation: An ElementSimulation object.
        """
        self.element_manager.remove_element_simulation(element_simulation)
        for recoil in element_simulation.recoil_elements:
            if recoil in self.individual_intervals:
                self.individual_intervals.pop(recoil).remove()

    def remove_recoil_element(
            self, recoil_widget,
            element_simulation: Optional[ElementSimulation] = None,
            recoil_element: Optional[RecoilElement] = None):
        """Remove recoil element that has the given recoil_widget.

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
        if recoil_to_delete is None or element_simulation is None:
            return

        if recoil_widget.radio_button.isChecked():
            element_simulation.get_main_recoil(). \
                widgets[0].radio_button.setChecked(True)
        # Remove radio button from list
        self.radios.removeButton(recoil_widget.radio_button)
        # Remove recoil widget from view
        recoil_widget.deleteLater()
        # Remove recoil element from element simulation
        element_simulation.recoil_elements.remove(recoil_to_delete)
        # Remove other recoil line
        try:
            self.other_recoils.remove(recoil_to_delete)
        except ValueError:
            pass  # Recoil was not in list
        self.show_other_recoils()
        # Delete rec, recoil and simu files.
        if element_simulation.simulation_type == SimulationType.ERD:
            rec_suffix = ".rec"
            recoil_suffix = ".recoil"
        else:
            rec_suffix = ".sct"
            recoil_suffix = ".scatter"
        rec_file = Path(
            element_simulation.directory,
            f"{recoil_to_delete.get_full_name()}{rec_suffix}")

        recoil_file = Path(
            element_simulation.directory,
            f"{recoil_to_delete.get_full_name()}{recoil_suffix}")

        simu_file = Path(
            element_simulation.directory,
            f"{recoil_to_delete.get_full_name()}.simu")

        gf.remove_files(rec_file, recoil_file, simu_file)
        if recoil_to_delete in self.individual_intervals:
            self.individual_intervals.pop(recoil_to_delete).remove()

    def remove_current_element(self, ignore_dialog=False, ignore_selection=False):
        """Remove current element simulation.
        
        Args:
             ignore_dialog: A boolean determining if confirmation dialogs are skipped
             ignore_selection: A boolean ignoring radio button selections
        """
        if self.current_element_simulation is None:
            return    
        if not ignore_selection:
            if not self.main_recoil_selected():
                return

        # Check if current element simulation is running
        if self.current_element_simulation.is_optimization_running() or \
                self.current_element_simulation.is_simulation_running():
            add = "\nAlso its simulation will be stopped."
        else:
            add = ""
            
        # TODO use the function from dialog_functions in here        
        if not ignore_dialog: 
            reply = QtWidgets.QMessageBox.question(
                self.parent, "Confirmation",
                "If you delete selected element simulation, all possible recoils "
                f"connected to it will be also deleted.{add} "
                f"This also applies to possible optimization.\n\n"
                "Are you sure you want to delete selected element simulation?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No |
                QtWidgets.QMessageBox.Cancel, QtWidgets.QMessageBox.Cancel)
            if reply == QtWidgets.QMessageBox.No or reply == \
                    QtWidgets.QMessageBox.Cancel:
                return  # If clicked Yes, then continue normally

        element_simulation = self.current_element_simulation

        # Stop simulation if running
        if add:
            self.current_element_simulation.stop()
            # Remove possible other recoil elements
            for recoil_elem in element_simulation.recoil_elements:
                if recoil_elem is element_simulation.get_main_recoil():
                    continue
                self.remove_recoil_element(recoil_elem.widgets[0],
                                           element_simulation, recoil_elem)
                # Delete energy spectra that use recoil
                df.delete_recoil_espe(self.tab, recoil_elem.get_full_name())

        # Remove recoil lines
        for recoil in element_simulation.recoil_elements:
            if recoil in self.other_recoils:
                self.other_recoils.remove(recoil)
            # Delete energy spectra that use recoil
            df.delete_recoil_espe(self.tab, recoil.get_full_name())

        # Handle optimization results
        if self.current_element_simulation.optimization_recoils:
            self.tab.del_widget(
                self.current_element_simulation.optimization_widget)
            # Delete energy spectra that use optimized recoils
            for opt_rec in self.current_element_simulation.optimization_recoils:
                df.delete_recoil_espe(self.tab, opt_rec.get_full_name())

        # Handle fluence optimization results deleting
        if self.current_element_simulation.optimization_widget:
            self.tab.del_widget(
                self.current_element_simulation.optimization_widget)

        self.current_recoil_element = None
        self.current_element_simulation = None
        self.remove_element(element_simulation)
        self.show_other_recoils()
        self.parent.elementInfoWidget.hide()
        self.update_plot()

    def remove_all_elements(self):
        """Removes all element simulations
        """
        # Confirmation dialog
        reply = QtWidgets.QMessageBox.question(
            self.parent, "Confirmation",
            "If you delete all element simulations, all possible recoils "
            f"connected to them will be deleted. "
            f"Their simulations will be stopped. "
            f"This also applies to possible optimizations.\n\n"
            "Are you sure you want to delete all element simulations?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No |
            QtWidgets.QMessageBox.Cancel, QtWidgets.QMessageBox.Cancel)
        if reply == QtWidgets.QMessageBox.No or reply == \
                QtWidgets.QMessageBox.Cancel:
            return  # If clicked Yes, then continue normally
            
        element_simulations = self.element_manager.element_simulations
        while len(element_simulations) >= 1:
            for element_simulation in element_simulations:
                self.current_element_simulation = element_simulations[0]
                self.remove_current_element(ignore_dialog=True, ignore_selection=True)

    def export_elements(self, **kwargs):
        """Export elements from target layers into element simulations if they
        do not already exist.
        """
        for layer in self.target.layers:
            for element in layer.elements:
                if not self.element_manager.has_element(element):
                    color = self.colormap[element.symbol]
                    self.add_element(element, color=color, **kwargs)

    def on_draw(self):
        """Draw method for matplotlib.
        """
        self.axes.clear()  # Clear old stuff

        self.axes.set_ylabel(self.name_y_axis)
        self.axes.set_xlabel(self.name_x_axis)

        if self.current_element_simulation:
            self.lines, = self.axes.plot(
                self.current_recoil_element.get_xs(),
                self.current_recoil_element.get_ys(),
                color=self.current_recoil_element.color)

            self.markers, = self.axes.plot(
                self.current_recoil_element.get_xs(),
                self.current_recoil_element.get_ys(),
                color=self.current_recoil_element.color, marker="o",
                markersize=10, linestyle="None")

            self.markers_selected, = self.axes.plot(
                0, 0, marker="o", markersize=10, linestyle="None",
                color="yellow", visible=False)
        else:
            self.lines, = self.axes.plot(0, 0, color="blue", visible=False)
            self.markers, = self.axes.plot(
                0, 0, color="blue", marker="o", markersize=10, linestyle="None",
                visible=False)
            self.markers_selected, = self.axes.plot(
                0, 0, marker="o", markersize=10, linestyle="None",
                color="yellow", visible=False)

        self.axes.set_xlim(-1, 40)
        self.axes.set_ylim(-0.1, 2)

        # Remove axis ticks and draw
        self.remove_axes_ticks()
        self.canvas.draw()

    def __toggle_tool_drag(self):
        """Toggle drag tool.
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

    def __fork_toolbar_buttons(self):
        """Fork navigation tool bar button into custom ones.
        """
        self.mpl_toolbar.mode_tool = 0
        self.__tool_label, self.__button_drag, self.__button_zoom = \
            mpl_utils.get_toolbar_elements(
                self.mpl_toolbar, drag_callback=self.__toggle_tool_drag,
                zoom_callback=self.__toggle_tool_zoom)

        # Make own buttons
        self.mpl_toolbar.addSeparator()

        # Coordinates widget
        self.coordinates_widget = PointCoordinatesWidget(
            self, full_edit_changed=self.full_edit_changed)
        self.coordinates_action = self.mpl_toolbar.addWidget(
            self.coordinates_widget)
        self.coordinates_widget.coord_changed.connect(
            self.emit_distribution_change)

        if self.current_element_simulation is None:
            self.coordinates_action.setVisible(False)
        else:
            self.coordinates_widget.set_y_enabled(False)
            self.coordinates_widget.set_x_enabled(False)

        # Point removal
        self.point_remove_action = QtWidgets.QAction("Remove point", self)
        self.point_remove_action.triggered.connect(self.remove_points)
        self.point_remove_action.setToolTip("Remove selected points")
        self.__icon_manager.set_icon(self.point_remove_action, "del.png")
        self.mpl_toolbar.addAction(self.point_remove_action)

        # Add separator
        self.mpl_toolbar.addSeparator()

        self.__button_span_limits = QtWidgets.QToolButton(self)
        self.__button_span_limits.setCheckable(True)
        self.__button_span_limits.clicked.connect(self.__toggle_span_limits)
        self.__button_span_limits.setToolTip(
            "Toggle limits that are used for all recoil elements")
        self.__icon_manager.set_icon(self.__button_span_limits,
                                     "recoil_toggle_span_limits.png")
        self.mpl_toolbar.addWidget(self.__button_span_limits)

        self.__button_individual_limits = QtWidgets.QToolButton(self)
        self.__button_individual_limits.setCheckable(True)
        self.__button_individual_limits.clicked.connect(
            self.__toggle_individual_limits)
        self.__button_individual_limits.setToolTip(
            "Toggle recoil element specific limits")
        self.__icon_manager.set_icon(self.__button_individual_limits,
                                     "recoil_toggle_individual_limits.png")
        self.mpl_toolbar.addWidget(self.__button_individual_limits)

    def __toggle_individual_limits(self):
        """Toggle individual limits visible and non-visible.
        """
        self.area_limits_individual_on = not self.area_limits_individual_on
        self.set_individual_intervals_visible(self.area_limits_individual_on)
        if self.anchored_box:
            self.anchored_box.set_visible(self.area_limits_individual_on)
        if self.current_recoil_element is None:
            return

        if self.area_limits_individual_on and self.current_recoil_element is \
                not None:
            self.__calculate_selected_area()

        self.__button_individual_limits.setChecked(
            self.area_limits_individual_on)
        self.limit_changed.emit()
        self.canvas.draw_idle()

    def __toggle_span_limits(self):
        """Toggle span limits visible and non-visible.
        """
        self.area_limits_for_all_on = not self.area_limits_for_all_on
        if self.common_interval is not None:
            self.common_interval.set_visible(self.area_limits_for_all_on)
        elif self.area_limits_for_all_on:
            self.common_interval = VerticalLimits(
                self.canvas, self.axes,
                xs=self.current_recoil_element.get_range(),
                colors=("blue", "red"), flush=False
            )
        self.span_selector.set_active(self.area_limits_for_all_on)

        self.limit_changed.emit()

        self.__button_span_limits.setChecked(self.area_limits_for_all_on)
        self.canvas.draw_idle()

    def __update_multiply_action(self):
        """Update the correct value to show from clipboard.
        """
        self.ratio_str = self.clipboard.text()

    def set_selected_point_x(self, x=None, clicked=None):
        """Sets the selected point's x coordinate
        to the value of the x spinbox.

        Args:
            x: New x coordinate.
            clicked: Clicked point.
        """
        if self.__save_points:
            # Make entry for backlog
            self.current_recoil_element.save_current_points(self.full_edit_on)
        if x is None:
            x = self.coordinates_widget.x_coord
        if clicked is None and self.clicked_point is not None:
            clicked = self.clicked_point
        else:
            return

        left_neighbor, right_neighbor = \
            self.current_recoil_element.get_neighbors(clicked)

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
        """Sets the selected point's y coordinate to the value of the y spinbox.

        Args:
            y: New y coordinate.
            clicked: Clicked point.
        """
        if self.__save_points:
            # Make entry for backlog
            self.current_recoil_element.save_current_points(self.full_edit_on)
        if y is None:
            y = self.coordinates_widget.y_coord
        if clicked is not None:
            clicked.set_y(y)
        elif self.clicked_point is not None:
            self.clicked_point.set_y(y)
        self.update_plot()

    def on_click(self, event):
        """ On click event above graph.

        Args:
            event: A MPL MouseEvent
        """
        if self.current_element_simulation is None:
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
                self.coordinates_widget.setVisible(True)
                i = marker_info['ind'][0]  # The clicked point's index
                clicked_point = self.current_recoil_element.get_point(i)

                if not self.point_in_selection(clicked_point):
                    self.selected_points = [clicked_point]
                self.dragged_points.extend(self.selected_points)
                self.clicked_point = clicked_point
                # If clicked point is first
                if self.first_point_selected():
                    self.point_remove_action.setEnabled(False)
                # If clicked point is last and full edit is not on
                elif self.last_point_selected() and not self.full_edit_on:
                    self.point_remove_action.setEnabled(False)
                else:
                    self.point_remove_action.setEnabled(True)
                # If clicked point is zero and full edit is not on
                if self.zero_point_selected():
                    if self.editing_restricted():
                        self.point_remove_action.setEnabled(False)
                        self.coordinates_widget.set_x_enabled(False)
                    else:
                        self.coordinates_widget.set_x_enabled(True)
                        self.coordinates_widget.set_y_enabled(True)
                elif self.editing_restricted():
                    # If point is between two zeros, cannot delete
                    if self.selected_between_zeros():
                        self.point_remove_action.setEnabled(False)
                    self.coordinates_widget.set_x_enabled(True)
                else:
                    self.coordinates_widget.set_x_enabled(True)
                self.set_on_click_attributes(event)

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
                            # Make a backlog entry
                            self.current_recoil_element.save_current_points(
                                self.full_edit_on, new_point)
                            self.selected_points = [new_point]
                            self.dragged_points = [new_point]
                            self.clicked_point = new_point

                            self.coordinates_widget.setVisible(True)

                            if new_point.get_y() == 0.0:
                                if self.editing_restricted():
                                    self.point_remove_action.setEnabled(False)
                                    self.coordinates_widget.set_y_enabled(False)
                            self.set_on_click_attributes(event)
                            self.update_plot()
                else:
                    self.__x_start = event.xdata

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

    def add_point(self, new_point, special=False, recoil=None, multiply=False):
        """Adds a point if there is space for it.
        Returns the point if a point was added, None if not.
        """
        if self.current_element_simulation is None:
            return

        if recoil is None:
            recoil = self.current_recoil_element
        if not isinstance(new_point, Point):
            new_point = Point(new_point)

        recoil.add_point(new_point)
        # FIXME crashes here after multiplying area
        #       - point gets added to main recoil of current element simulation
        #         instead of current recoil, which causes a crash as the point
        #         is not found.
        try:
            left_neighbor, right_neighbor = \
                self.current_recoil_element.get_neighbors(new_point)
        except ValueError as e:
            print(e)
            return

        # TODO can we assume that left_neighbor is not None?
        left_neighbor_x = left_neighbor.get_x()

        if right_neighbor is not None:
            right_neighbor_x = right_neighbor.get_x()

            error = False

            # If too close to left
            if round(new_point.get_x() - left_neighbor_x, 2) < self.x_res:
                # Need space to insert the new point
                if right_neighbor_x - new_point.get_x() < 2 * self.x_res:
                    error = True
                else:
                    # Insert the new point as close to its left neighbor as
                    # possible
                    new_point.set_x(left_neighbor_x + self.x_res)
            elif round(right_neighbor_x - new_point.get_x(), 2) < self.x_res:
                if new_point.get_x() - left_neighbor_x < 2 * self.x_res:
                    error = True
                else:
                    new_point.set_x(right_neighbor_x - self.x_res)

            if not multiply:
                if not self.full_edit_on or \
                        self.current_element_simulation.get_main_recoil() != \
                            recoil:
                    # Check if point is added between two zeros
                    if right_neighbor.get_y() == 0.0 and \
                            left_neighbor.get_y() == 0.0:
                        new_point.set_y(0.0)
                    elif new_point.get_y() < 0.0001:
                        new_point.set_y(0.0001)

            if error:
                recoil.remove_point(new_point)
                QtWidgets.QMessageBox.critical(
                    self.parent, "Error",
                    "Can't add a point here.\nThere is no space for it.",
                    QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
                return None
            else:
                return new_point

        elif special:
            # When adding a non-zero point at the end of the recoil
            if new_point.get_x() - left_neighbor_x < self.x_res:
                new_point.set_x(left_neighbor_x + self.x_res)
            return new_point

    def update_plot(self):
        """Updates marker and line data and redraws the plot.
        """
        if hasattr(self.parent, 'recoil_distribution_widget'):
            self.parent._save_target_and_recoils(True)
        if self.current_element_simulation is None:
            self.markers.set_visible(False)
            self.lines.set_visible(False)
            self.markers_selected.set_visible(False)
            self.fig.canvas.draw_idle()
            return

        self.markers.set_data(
            self.current_recoil_element.get_xs(),
            self.current_recoil_element.get_ys()
        )
        self.lines.set_data(
            self.current_recoil_element.get_xs(),
            self.current_recoil_element.get_ys()
        )

        self.markers.set_color(self.current_recoil_element.color)
        self.lines.set_color(self.current_recoil_element.color)

        self.markers.set_visible(True)
        self.lines.set_visible(True)

        if self.selected_points:  # If there are selected points
            self.coordinates_action.setVisible(True)
            self.markers_selected.set_visible(True)
            selected_xs = [p.get_x() for p in self.selected_points]
            selected_ys = [p.get_y() for p in self.selected_points]
            self.markers_selected.set_data(selected_xs, selected_ys)

            if self.clicked_point is not None:
                old_save_value = self.__save_points
                self.__save_points = False
                self.coordinates_widget.x_coord = self.clicked_point.get_x()
                self.coordinates_widget.set_y_min(self.clicked_point)
                self.coordinates_widget.y_coord = self.clicked_point.get_y()
                self.__save_points = old_save_value
                # Disable y coordinate if it's zero and full edit is not on
                if self.zero_point_selected():
                    if self.editing_restricted():
                        self.coordinates_widget.set_y_enabled(False)
                else:
                    self.coordinates_widget.set_y_enabled(True)
        else:
            self.markers_selected.set_data(
                self.current_recoil_element.get_xs(),
                self.current_recoil_element.get_ys()
            )
            self.markers_selected.set_visible(False)
            self.coordinates_action.setVisible(False)

        # Show all of recoil
        if self.__show_all_recoil:
            last_point = self.current_recoil_element.get_last_point()
            last_point_x = last_point.get_x()
            x_min, xmax = self.axes.get_xlim()
            if xmax < last_point_x:
                self.axes.set_xlim(x_min, last_point_x + 0.04 * last_point_x)

        self.fig.canvas.draw_idle()

    def update_layer_borders(self):
        """Update layer borders.
        """
        for annotation in self.annotations:
            annotation.set_visible(False)
        self.annotations = []
        last_layer_thickness = 0

        y = 0.95
        next_layer_position = 0
        self.target_thickness = 0
        for idx, layer in enumerate(self.target.layers):
            self.target_thickness += layer.thickness
            self.axes.axvspan(
                next_layer_position, next_layer_position + layer.thickness,
                facecolor=self.layer_colors[idx % 2]
            )

            # Put annotation in the middle of the rectangular patch.
            annotation = self.axes.text(
                layer.start_depth, y, layer.name, transform=self.trans,
                fontsize=10, ha="left")
            y -= 0.05
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

        if self.__show_all_recoil and self.current_recoil_element is not None:
            last_point = self.current_recoil_element.get_last_point()
            last_point_x = last_point.get_x()
            if end < last_point_x:
                end = last_point_x + 0.04 * last_point_x

        self.axes.set_xlim(start, end)
        self.fig.canvas.draw_idle()

    def on_span_motion(self, *_):
        """Check if there are no dragged points before showing the span.

        Args:
            *_: unused x and y coordinates
        """
        if self.dragged_points or self.point_clicked:
            self.span_selector.set_active(False)

        if not self.area_limits_for_all_on:
            self.span_selector.set_active(False)

    def on_motion(self, event):
        """Callback method for mouse motion event. Moves points that are being
        dragged.

        Args:
            event: A MPL MouseEvent
        """
        if self.current_element_simulation is None:
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

        if self.__save_points:
            self.current_recoil_element.save_current_points(self.full_edit_on)
            self.__save_points = False

        dr_ps = self.dragged_points

        new_coords = [
            [x, max(self.get_minimum_concentration(), y)]
            for x, y in self.get_new_checked_coordinates(event)
        ]

        # Check if the point's y coordinate is zero or it is the last or
        # first point. Move accordingly
        # When full edit is not on, zero y values stay zero, and start and
        # end points can only move in y direction
        for i in range(len(dr_ps)):
            # End point
            if dr_ps[i] == self.current_recoil_element.get_last_point() \
                    and self.editing_restricted():
                if dr_ps[i].get_y() == 0.0:
                    continue
                else:
                    dr_ps[i].set_y(new_coords[i][1])
            # Start point
            elif dr_ps[i] == self.current_recoil_element.get_first_point():
                if not self.full_edit_on and dr_ps[i].get_y() == 0.0:
                    continue
                else:
                    dr_ps[i].set_y(new_coords[i][1])
            else:
                if dr_ps[i].get_y() == 0.0 and not self.full_edit_on and \
                        self.main_recoil_selected():
                    dr_ps[i].set_coordinates((dr_ps[i].get_x(), 0.0))
                else:
                    if not self.main_recoil_selected() and \
                            dr_ps[i].get_y() == 0.0:
                        dr_ps[i].set_coordinates((dr_ps[i].get_x(), 0.0))
                    else:
                        dr_ps[i].set_coordinates(new_coords[i])

            if dr_ps[i] == self.current_recoil_element.get_last_point():
                if dr_ps[i].get_x() > self.target_thickness:
                    dr_ps[i].set_x(self.target_thickness)

            # Check that dragged point hasn't crossed with neighbors
            self.current_recoil_element.adjust_point(dr_ps[i], res=self.x_res)

            self.__calculate_selected_area()

        self.update_plot()

    def get_new_checked_coordinates(self, event):
        """Returns checked new coordinates for dragged points.
        They have been checked for neighbor or axis limit collisions.
        """
        # TODO needs refactor
        dr_ps = self.dragged_points

        leftmost_dr_p = dr_ps[0]
        rightmost_dr_p = dr_ps[-1]
        left_neighbor = self.current_recoil_element.get_left_neighbor(
            leftmost_dr_p)
        right_neighbor = self.current_recoil_element.get_right_neighbor(
            rightmost_dr_p)

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
        if not self.main_recoil_selected():
            y_min = 0.0001
        else:
            if self.current_element_simulation.get_full_edit_on():
                y_min = 0.0
            else:
                y_min = 0.0001
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
        if self.current_element_simulation is None:
            return
        ret = False
        if len(self.current_recoil_element.get_points()) - \
                len(self.selected_points) < 2:
            QtWidgets.QMessageBox.critical(
                self.parent, "Error",
                "You cannot delete this point.\n"
                "There must always be at least two points.",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            ret = True
        if self.first_point_in_selection():
            QtWidgets.QMessageBox.critical(
                self.parent, "Error", "You cannot delete the first point.",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            ret = True
        if self.last_point_in_selection() and not self.full_edit_on:
            QtWidgets.QMessageBox.critical(
                self.parent, "Error",
                "You cannot delete the last point when full edit is locked.",
                QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            ret = True
        if 0.0 in self.current_recoil_element.get_ys():
            reason = ""
            if not self.full_edit_on:
                reason = " when full edit is on."
            if not self.main_recoil_selected():
                reason = " from non-main recoil element."
            if reason:
                for point in self.selected_points:
                    if point.get_y() == 0.0:
                        QtWidgets.QMessageBox.critical(
                            self.parent, "Error",
                            f"You cannot delete a point that has 0 as a "
                            f"y coordinate {reason}",
                            QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
                        ret = True
                        break
        # Check if trying to delete a non-zero point from between two zero
        # points
        for point in self.selected_points:
            if point.get_y() and self.current_recoil_element.between_zeros(
                    point):
                QtWidgets.QMessageBox.critical(
                    self.parent, "Error",
                    "You cannot delete a point that has a non-zero y "
                    "coordinate from between two points that have 0 as "
                    "their y coordinate.",
                    QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
                ret = True
                break
        if not ret:
            # Make a backlog entry
            self.current_recoil_element.save_current_points(self.full_edit_on)

            for sel_point in self.selected_points:
                self.current_recoil_element.remove_point(sel_point)
            self.selected_points.clear()
            self.update_plot()

            self.emit_distribution_change()

    def on_release(self, event):
        """Callback method for mouse release event. Stops dragging.

        Args:
            event: A MPL MouseEvent
        """
        if self.current_element_simulation is None:
            return
        # Don't do anything if drag tool or zoom tool is active.
        if self.__button_drag.isChecked() or self.__button_zoom.isChecked():
            return
        if event.button == 1:
            self.__x_end = event.xdata
            self.dragged_points.clear()
            self.__save_points = True
            self.update_plot()

            if self.point_clicked:
                self.emit_distribution_change()
                self.span_selector.set_active(True)

            # If graph was clicked and span not used
            if self.__x_start and self.__x_end and self.__x_start == \
                    self.__x_end:
                # If possible, move individual area limits
                if self.area_limits_individual_on:
                    x = event.xdata
                    if x < 0.0:
                        x = 0.0
                    if x > self.target_thickness:
                        x = self.target_thickness
                    self.update_current_interval(x)
                    self.__calculate_selected_area()

                    self.limit_changed.emit()
                    self.canvas.draw_idle()

    def undo_recoil_changes(self):
        """Undo recoil changes.
        """
        self.current_recoil_element.save_current_points(
            self.full_edit_on, save_before_undo=True)
        self.current_recoil_element.change_points_to_previous()
        self.reset_movables()

    def reset_movables(self):
        """Reset values that are needed for moving points.
        """
        self.clicked_point = None
        self.dragged_points = []
        self.click_locations = []
        self.selected_points = []
        self.point_clicked = False
        self.coordinates_widget.setVisible(False)
        self.update_plot()

        self.emit_distribution_change()

    def redo_recoil_changes(self):
        """Redo recoil changes.
        """
        self.current_recoil_element.change_points_to_next()
        self.reset_movables()

    def __context_menu(self, event):
        """Create a menu for accessing the area multiplication tool and/or
        undoing and redoing recoil element's point moving.

        Args:
            event: An MPL Mouse event.
        """
        coords = self.canvas.geometry().getCoords()
        point = QtCore.QPoint(event.x, coords[3] - event.y - coords[1])

        menu = QtWidgets.QMenu(self)

        action = QtWidgets.QAction(self.tr("Undo changes"), self)
        action.triggered.connect(self.undo_recoil_changes)
        menu.addAction(action)

        if self.current_recoil_element.get_previous_backlog_index() < 0:
            action.setEnabled(False)
        if not self.full_edit_on:
            if self.current_recoil_element.previous_points_in_full_edit():
                action.setEnabled(False)

        action_3 = QtWidgets.QAction(self.tr("Redo changes"), self)
        action_3.triggered.connect(self.redo_recoil_changes)
        menu.addAction(action_3)

        if not self.current_recoil_element.next_backlog_entry_done():
            action_3.setEnabled(False)

        if not self.main_recoil_selected() and self.area_limits_for_all_on:
            action_2 = QtWidgets.QAction(self.tr("Multiply area..."), self)
            action_2.triggered.connect(self.multiply_area)
            menu.addAction(action_2)

        menu.exec_(self.canvas.mapToGlobal(point))

    def limits_match(self) -> bool:
        """Check if current recoil element and main recoil element area limits
        match.

        Return:
             True or False.
        """
        current_interval = self.get_current_interval()
        current_low, current_high = current_interval.get_range()

        main_interval = self.get_main_interval()
        main_low, main_high = main_interval.get_range()

        return current_low == main_low and current_high == main_high

    def _add_point_at_limit(self, points: List[Point], limit: float, **kwargs) \
            -> Optional[Point]:
        """Adds a Point at limit value if there is no point there yet.
        """
        if points:
            for p0, p1 in zip(points[:-1], points[1:]):
                if p0.get_x() < limit < p1.get_x():
                    new_point = p0.calculate_new_point(p1, limit)
                    return self.add_point(new_point, **kwargs)
                elif p0.get_x() >= limit:
                    return None
        return None

    def multiply_area(self):
        """Multiply recoil element area and change the distribution accordingly.
        """
        interval = self.get_main_interval()
        if interval is not None:
            low, high = interval.get_range()
        else:
            low, high = None, None
        dialog = MultiplyAreaDialog(self.get_current_main_recoil(), low, high)

        # If there are proper areas to handle
        if dialog.can_multiply():
            self.current_recoil_element.save_current_points(self.full_edit_on)
            # Delete/add points between limits to have matching number of points
            lower_limit, upper_limit = self.get_common_limits(rounding=2)

            # Add missing start and end
            self._add_point_at_limit(
                self.current_recoil_element.get_points(), lower_limit,
                multiply=True)

            self._add_point_at_limit(
                self.current_recoil_element.get_points(), upper_limit,
                multiply=True)

            # Delete
            for point in reversed(self.current_recoil_element.get_points()):
                x = point.get_x()
                if x <= lower_limit:
                    break
                if upper_limit <= x:
                    continue
                else:
                    self.current_recoil_element.remove_point(point)
            # Add
            points = self.get_current_main_recoil().get_points()
            main_y_lower = None
            main_y_lower_i = None
            main_y_upper = None
            main_y_upper_i = None
            main_points_to_add = []

            # Add lower and upper limit temporarily to main recoil points
            point = self._add_point_at_limit(
                self.get_current_main_recoil().get_points(), lower_limit,
                multiply=True, recoil=self.get_current_main_recoil()
            )
            if point is not None:
                main_points_to_add.append(point)
            point = self._add_point_at_limit(
                self.get_current_main_recoil().get_points(), upper_limit,
                multiply=True, recoil=self.get_current_main_recoil()
            )
            if point is not None:
                main_points_to_add.append(point)

            for i in range(len(points)):
                main_p_x = points[i].get_x()
                main_p_y = points[i].get_y()
                if main_p_x < lower_limit:
                    continue
                if upper_limit < main_p_x:
                    break
                else:
                    if main_p_x not in self.current_recoil_element.get_xs():
                        self.add_point((main_p_x, main_p_y), multiply=True)
                    if main_p_x == lower_limit:
                        main_y_lower = main_p_y
                        main_y_lower_i = i
                    if main_p_x == upper_limit:
                        main_y_upper = main_p_y
                        main_y_upper_i = i

            # Adjust the lower and upper limit ys
            if main_y_lower is not None:
                lower_point = self.current_recoil_element.get_point(
                    main_y_lower_i)
                lower_point.set_y(main_y_lower)
            if main_y_upper is not None:
                upper_point = self.current_recoil_element.get_point(
                    main_y_upper_i)
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

            for r_p in main_points_to_add:
                self.get_current_main_recoil().remove_point(r_p)

        self.__calculate_selected_area()
        self.update_plot()

    def on_span_select(self, xmin: float, xmax: float):
        """Select area to calculate the are of.

        Args:
             xmin: Start value of the mouse
             xmax: End value of the mouse.
        """
        if xmin == xmax or self.point_clicked:  # Do nothing if graph is clicked
            return

        low_x = round(xmin, 3)
        high_x = round(xmax, 3)

        # Check that limits don't go further than target dimensions
        if low_x < 0:
            low_x = 0
        if high_x > self.target_thickness:
            high_x = self.target_thickness

        ylim = self.axes.get_ylim()

        self.common_interval.update_graph(low_x, high_x)

        self.limit_changed.emit()

        self.axes.set_ybound(ylim[0], ylim[1])
        self.canvas.draw_idle()

    def __calculate_selected_area(self) -> float:
        """Calculate the recoil atom distribution's area inside limits.
        """
        if not self.area_limits_individual_on:
            return 0.0

        self.update_current_interval()
        interval = self.get_current_interval()
        low, high = interval.get_range()

        area = self.current_recoil_element.calculate_area(start=low, end=high)

        if self.anchored_box:
            self.anchored_box.set_visible(False)
            self.anchored_box = None

        text = f"Area: {round(area, 2)}"
        box = offsetbox.TextArea(
            text, textprops=dict(color="k", size=12, backgroundcolor="w"))

        self.anchored_box = offsetbox.AnchoredOffsetbox(
            loc=1, child=box, pad=0.5, frameon=False,
            bbox_to_anchor=(1.0, 1.0), bbox_transform=self.axes.transAxes,
            borderpad=0.0,
        )
        self.axes.add_artist(self.anchored_box)
        self.canvas.draw_idle()

        return area


    def on_rectangle_select(self, eclick, erelease):
        """Select multiple points.

        Args:
            eclick: Area start event.
            erelease: Area end event.
        """
        if self.current_element_simulation is None:
            return
        xmin = eclick.xdata
        xmax = erelease.xdata
        ymin = eclick.ydata
        ymax = erelease.ydata

        click_x = self.__rectangle_event_click.x

        if click_x == self.__rectangle_event_release.x \
                and round(self.__rectangle_event_click.xdata, 5) != \
                round(xmin, 5):
            # FIXME this does works really poorly on Windows. Context menu only
            #       gets opened when dragging from right to left when it should
            #       be opened after single click.
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
            if self.zero_point_selected():
                if self.editing_restricted():
                    self.coordinates_widget.set_x_enabled(False)
                else:
                    self.coordinates_widget.set_x_enabled(True)
                    self.coordinates_widget.set_y_enabled(True)
            else:
                self.coordinates_widget.set_x_enabled(True)
            if self.last_point_in_selection():
                self.point_remove_action.setEnabled(False)
                allow_delete = False
            if self.last_point_in_selection() and not self.full_edit_on and \
                    allow_delete:
                self.point_remove_action.setEnabled(False)
                allow_delete = False
            if 0.0 in self.current_recoil_element.get_ys() and allow_delete:
                if self.editing_restricted():
                    if self.zero_point_in_selection():
                        self.point_remove_action.setEnabled(False)
                        allow_delete = False
            # Check if trying to delete a non-zero point from between two zero
            # points
            if allow_delete:
                for point in self.selected_points:
                    if point.get_y() and \
                            self.current_recoil_element.between_zeros(point):
                        self.point_remove_action.setEnabled(False)
                        allow_delete = False
                        break

            if allow_delete:
                self.point_remove_action.setEnabled(True)

        self.update_plot()
