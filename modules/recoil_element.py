# coding=utf-8
"""
Created on 1.3.2018
Updated on 9.5.2019

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

import copy
import json
import itertools
import time

from pathlib import Path
from typing import List
from typing import Optional
from typing import Tuple

from . import file_paths as fp
from . import math_functions as mf

from .base import Serializable
from .base import MCERDParameterContainer
from .element import Element
from .point import Point
from .parsing import CSVParser

from modules.global_settings import GlobalSettings


class RecoilElement(MCERDParameterContainer, Serializable):
    """An element that has a list of points and a widget. The points are kept
    in ascending order by their x coordinate.
    """
    def __init__(self, element: Element, points: List[Point], color="red",
                 name="Default", rec_type="rec",
                 description="These are default recoil settings.",
                 reference_density=None, modification_time=None,
                 channel_width=None):
        """Inits recoil element.

        Args:
            element: An Element class object.
            points: A list of Point class objects.
            color: string representation of a color
            name: Name of the RecoilElement object anf file.
            rec_type: Type recoil element (rec or sct).
        """
        self.element = element
        if not name:
            self.name = "Default"
        else:
            self.name = name
        self.prefix = element.get_prefix()
        self.description = description
        self.type = rec_type
        
        if reference_density is None:
            self.reference_density = GlobalSettings().get_default_reference_density()
        else:
            self.reference_density = reference_density

        self.manual_reference_density_checked = False
            
        self.channel_width = channel_width

        # TODO might want to use some sort of sorted collection instead of a
        #  list, although this depends on the number of elements in the list.
        #  A linked list would make finding neighbors faster.
        self._points = sorted(points)
        self.points_backlog = []
        # This is out of bounds if no undo is done, telss the index of the
        # next points to be added
        self.points_backlog_i_add = 0
        # List corresponding to poins backlog entry, tells if entry was done
        # in full edit or not
        self.entry_in_full_edit = []

        # Contains ElementWidget and SimulationControlsWidget.
        self.widgets = []
        self._edit_lock_on = False

        self.modification_time = modification_time

        # List for keeping track of intervals that are zero
        self.zero_intervals_on_x = []
        # List for keeping track of singular zero points
        self.zero_values_on_x = []

        # Color of the recoil
        self.color = color

        self.update_zero_values()

    def __lt__(self, other):
        """Comparison is delegated to Element object.
        """
        if not isinstance(other, RecoilElement):
            return NotImplemented

        return self.element < other.element

    def get_full_name(self):
        """Returns the prefixed name of the RecoilElement.
        """
        return f"{self.prefix}-{self.name}"

    def delete_widgets(self):
        """Delete all widgets.
        """
        for widget in self.widgets:
            widget.deleteLater()

    def lock_edit(self):
        """Lock full edit.
        """
        self._edit_lock_on = True

    def unlock_edit(self):
        """Unlock full edit.
        """
        self._edit_lock_on = False

    def previous_points_in_full_edit(self):
        """Check if previous points
        """
        prev_i = self.points_backlog_i_add - 1
        if prev_i >= 0:
            full_edit_used = self.entry_in_full_edit[prev_i]
            return full_edit_used

    def save_current_points(self, full_edit_used, exclude=None,
                            save_before_undo=False):
        """Save current points for undoing or redoing.

        Args:
            full_edit_used: TODO
            exclude: A point that needs to be excluded from backlog entry.
            save_before_undo: TODO
        """
        points = []
        if exclude:
            for p in self._points:
                if p is exclude:
                    continue
                else:
                    points.append(p)
        else:
            points = self._points

        copy_points = copy.deepcopy(points)

        # Check that copied points differ form the last added one
        are_same = False
        if self.points_backlog_i_add - 1 >= 0:
            previous = self.points_backlog[self.points_backlog_i_add - 1]
            if len(copy_points) == len(previous):
                for j in range(len(copy_points)):
                    c_p = copy_points[j]
                    p_p = previous[j]
                    if not c_p.get_x() == p_p.get_x() or not c_p.get_y() == \
                            p_p.get_y():
                        are_same = False
                        break
                    else:
                        are_same = True
        if are_same:
            return

        if save_before_undo:
            try:
                self.points_backlog[self.points_backlog_i_add]
            except IndexError:
                self.points_backlog.append(copy_points)
            return

        # Remove obsolete entries
        removed_points = []
        i = len(self.points_backlog) - 1
        while i >= 0:
            collection = self.points_backlog[i]
            if i == self.points_backlog_i_add - 1:
                break
            else:
                removed_points.append(collection)
            i -= 1

        self.entry_in_full_edit = \
            self.entry_in_full_edit[:self.points_backlog_i_add]

        for r in removed_points:
            self.points_backlog.remove(r)

        self.points_backlog.append(copy_points)
        self.entry_in_full_edit.append(full_edit_used)
        self.points_backlog_i_add += 1

    def next_backlog_entry_done(self):
        """
        Check if next backlog entry has been done.

        Return:
             True or False.
        """
        try:
            self.points_backlog[self.points_backlog_i_add + 1]
        except IndexError:
            return False
        return True

    def change_points_to_previous(self):
        """
        Change the points list reference to another list.
        """
        self._points = self.points_backlog[self.points_backlog_i_add - 1]
        self.points_backlog_i_add -= 1

    def change_points_to_next(self):
        """
        Change the points list reference to another list.
        """
        self._points = self.points_backlog[self.points_backlog_i_add + 1]
        self.points_backlog_i_add += 1

    def delete_backlog(self):
        """
        Delete backlog.
        """
        self.points_backlog = []
        self.points_backlog_i_add = 0
        self.entry_in_full_edit = []

    def get_previous_backlog_index(self):
        """
        Return:
             Index where previous points are in the backlog list.
        """
        return self.points_backlog_i_add - 1

    def update_zero_values(self):
        """
        Update recoil element's zero value lists.
        """
        self.zero_values_on_x = []
        self.zero_intervals_on_x = []
        start_zero_point = None
        end_zero_point = None
        for point in self._points:
            if point.get_y() == 0.0 and start_zero_point is None:
                start_zero_point = point
                end_zero_point = point
            elif point.get_y() == 0.0 and start_zero_point is not None:
                end_zero_point = point
            elif start_zero_point and end_zero_point:
                # Add one zero point's x to values list
                if start_zero_point is end_zero_point:
                    self.zero_values_on_x.append(start_zero_point.get_x())
                # Add start x and end x of zero interval to interval list
                else:
                    self.zero_intervals_on_x.append(
                        (start_zero_point.get_x(), end_zero_point.get_x())
                    )
                start_zero_point = None
                end_zero_point = None
        if start_zero_point and end_zero_point:
            if start_zero_point is end_zero_point:
                self.zero_values_on_x.append(start_zero_point.get_x())
                # Add start x and end x of zero interval to interval list
            else:
                self.zero_intervals_on_x.append(
                    (start_zero_point.get_x(), end_zero_point.get_x())
                )

    def get_edit_lock_on(self) -> bool:
        """
        Get if full edit is locked or not.

        Return:
            True or False.
        """
        return self._edit_lock_on

    def _sort_points(self):
        """Sorts the points in ascending order by their x coordinate."""
        self._points.sort()

    def get_xs(self) -> List[float]:
        """Returns a list of the x coordinates of the points."""
        return [point.get_x() for point in self._points]

    def get_ys(self) -> List[float]:
        """Returns a list of the y coordinates of the points."""
        return [point.get_y() for point in self._points]

    def get_xs_and_ys(self) -> Tuple[List[float], List[float]]:
        """Returns a tuple where first one contains the values on the
        x axis and second one contains the values on the y axis.
        """
        xs, ys = zip(*(p.get_coordinates() for p in self._points))
        return xs, ys

    def get_point(self, i: int) -> Point:
        """Returns the i:th point.
        """
        return self._points[i]

    def get_points(self) -> List[Point]:
        """Get points.

        Return:
             Points list.
        """
        # TODO maybe return shallow copy
        return self._points

    def get_first_point(self) -> Point:
        """Returns the first point in the distribution.
        """
        return self.get_point(0)

    def get_last_point(self) -> Point:
        """Returns the last point in the distribution.
        """
        return self.get_point(-1)

    def get_range(self) -> Tuple[float, float]:
        """Returns first and last points of the distribution.
        """
        return self.get_first_point().get_x(), self.get_last_point().get_x()

    def distribution_length(self) -> float:
        """Returns the distance between first and last point.
        """
        low, high = self.get_range()
        return high - low

    def add_point(self, point: Point):
        """Adds a point and maintains sort order."""
        self._points.append(point)
        self._sort_points()

    def remove_point(self, point: Point):
        """Removes the given point.
        """
        self._points.remove(point)

    def get_left_neighbor(self, point: Point) -> Optional[Point]:
        """Returns the point whose x coordinate is closest to but
        less than the given point's.
        """
        ind = self._points.index(point)
        if ind == 0:
            return None
        else:
            return self._points[ind - 1]

    def get_right_neighbor(self, point: Point) -> Optional[Point]:
        """Returns the point whose x coordinate is closest to but
        greater than the given point's.
        """
        ind = self._points.index(point)
        if ind == len(self._points) - 1:
            return None
        else:
            return self._points[ind + 1]

    def get_neighbors(self, point: Point) \
            -> Tuple[Optional[Point], Optional[Point]]:
        """Returns point's left and right neighbour.

        Args:
            point: Point object

        Return:
            left and right neighbour as a tuple
        """
        ind = self._points.index(point)

        if ind == 0:
            ln = None
        else:
            ln = self._points[ind - 1]

        if ind == len(self._points) - 1:
            rn = None
        else:
            rn = self._points[ind + 1]

        return ln, rn

    def between_zeros(self, point: Point) -> bool:
        """Checks whether point is between two zero Points.

        Args:
            point: Point object.

        Return:
            boolean
        """
        ln, rn = self.get_neighbors(point)

        if ln is not None and rn is not None:
            return ln.get_y() == 0.0 and rn.get_y() == 0.0
        return False

    def adjust_point(self, point: Point, res: float = 0.01):
        """Adjusts a point so that it stays between its neighbours.
        """
        ln, rn = self.get_neighbors(point)

        if ln is not None:
            if point.get_x() <= ln.get_x():
                point.set_x(ln.get_x() + res)

        if rn is not None:
            if point.get_x() >= rn.get_x():
                point.set_x(rn.get_x() - res)

    def update(self, new_values):
        """Updates the values of the RecoilElement with the given values

        Raises KeyError if new_values does not contain necessary keys.

        Args:
            new_values: dictionary
        """
        try:
            self.name = new_values["name"]
            self.description = new_values["description"]
            self.reference_density = new_values["reference_density"]
            self.color = new_values["color"]
        except KeyError:
            raise

    def to_file(self, simulation_folder: Path):
        """Save recoil settings to file.

        Args:
            simulation_folder: Path to simulation folder in which ".rec" or
                               ".sct" files are stored.
        """
        # TODO is it necessary to have the recoil type ('rec' or 'sct') in the
        #  file extension? Currently Potku always has to delete the other types
        #  of files when the simulation type is changed.
        recoil_file_path = fp.get_recoil_file_path(self, simulation_folder)

        timestamp = time.time()

        # Multiplier is saved to maintain backwards compatibility with old
        # save files
        obj = {
            "name": self.name,
            "description": self.description,
            "modification_time": time.strftime("%c %z %Z", time.localtime(
                timestamp)),
            "modification_time_unix": timestamp,
            "simulation_type": self.type,
            "element":  self.element.get_prefix(),
            "reference_density": self.reference_density,
            "multiplier": 1,
            "profile": [
                {
                    "Point": str(point)
                }
                for point in self.get_points()
            ],
            "color": self.color
        }

        with recoil_file_path.open("w") as file:
            json.dump(obj, file, indent=4)

    @classmethod
    def from_file(cls, file_path: Path, channel_width=None, rec_type="rec") \
            -> "RecoilElement":
        """Returns a RecoilElement from a json file.

        Args:
            file_path: path to a file
            channel_width: TODO
            rec_type: type of recoil, either 'rec' or 'sct'

        Return:
            RecoilElement object
        """
        with file_path.open("r") as rec_file:
            reco = json.load(rec_file)

        # Pop the values that need conversion and/or are provided as positional
        # arguments.
        element = Element.from_string(reco.pop("element"))
        reco["modification_time"] = reco.pop("modification_time_unix")

        # Multiply reference density with multiplier in case the recoil file
        # is of the old format
        reco["reference_density"] *= reco.pop("multiplier")
        # TODO do something with simulation_type
        reco.pop("simulation_type")

        # Profile is a list of dicts where each dict is in the form of
        # { 'Point': 'x y' }. itertools.chain produces a flattened list of
        # the values.
        profile = reco.pop("profile")
        p_iter = itertools.chain.from_iterable(p.values() for p in profile)

        # Use parser to convert values to float
        # TODO smarter parser that can parse multiple columns at once
        parser = CSVParser((0, float), (1, float))
        points = (
            Point(xy)
            for xy in parser.parse_strs(p_iter, method="row")
        )

        return cls(element, list(points), channel_width=channel_width,
                   rec_type=rec_type, **reco)

    def get_mcerd_params(self):
        """Returns the parameters used in MCERD calculations as a list of
        strings.
        """
        params = []

        # If there are not points all the way from 0 to 10, add this
        # small amount
        points = self.get_points()
        if 0 < points[0].get_x():
            point_x = round(points[0].get_x() - 0.01, 2)
            if points[0].get_x() <= 10.0:
                params.append(f"0.00 0.000001\n{point_x} 0.000001")
            else:
                params.append(f"0.00 0.000001\n10.00 0.000001\n"
                              f"10.01 0.0000\n{point_x} 0.0000")

        for point in points:
            params.append(point.get_mcerd_params())

        # MCERD requires the recoil atom distribution to end with these
        # points
        params.append(f"{round(self.get_last_point().get_x() + 0.01, 2)} "
                      f"0.0")
        params.append(f"{round(self.get_last_point().get_x() + 0.02, 2)} "
                      f"0.0\n")

        return params

    def calculate_area(self, start: Optional[float] = None,
                       end: Optional[float] = None) -> float:
        """Calculates the area of the recoil distribution.

        If start and end values are defined, area is calculated between those
        two values on the x axis, otherwise the entire length of the
        distribution is used.

        Args:
            start: Start x.
            end: End x.

        Return:
            Area between intervals and recoil points and x axis.
        """
        if start is None:
            start = self.get_first_point().get_x()
        if end is None:
            end = self.get_last_point().get_x()

        area_points = list(mf.get_continuous_range(
            *self.get_xs_and_ys(), a=start, b=end))
        return mf.calculate_area(area_points)
