# coding=utf-8
"""
Created on 1.3.2018
Updated on 9.5.2019

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

import copy

from modules.element import Element
from modules.general_functions import calculate_new_point

from shapely.geometry import Polygon


class RecoilElement:
    """An element that has a list of points and a widget. The points are kept
    in ascending order by their x coordinate.
    """
    def __init__(self, element, points, color, name="Default", rec_type="rec"):
        """Inits recoil element.

        Args:
            element: An Element class object.
            points: A list of Point class objects.
            color: string representation of a color
            name: Name of the RecoilElement object anf file.
            rec_type: Type recoil element (rec or sct).
        """
        self.element = element
        self.name = name
        self.prefix = element.get_prefix()
        self.description = "These are default recoil settings."
        self.type = rec_type
        # This is multiplied by 1e22
        self.reference_density = 4.98
        self.multiplier = 1e22

        # TODO do something like this: https://code.activestate.com/recipes/
        #      577197-sortedcollection/ or use
        #      http://www.grantjenks.com/docs/sortedcontainers/ to store
        #      points in order
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

        self.modification_time = None

        # List for keeping track of intervals that are zero
        self.zero_intervals_on_x = []
        # List for keeping track of singular zero points
        self.zero_values_on_x = []

        # Area of certain limits
        self.area = None
        self.area_limits = []

        self.__common_area_points = []
        self.__individual_area_points = []

        # Color of the recoil
        self.color = color

        self.update_zero_values()

    def delete_widgets(self):
        """
        Delete all widgets.
        """
        for widget in self.widgets:
            widget.deleteLater()

    def lock_edit(self):
        """
        Lock full edit.
        """
        self._edit_lock_on = True

    def unlock_edit(self):
        """
        Unlock full edit.
        """
        self._edit_lock_on = False

    def previous_points_in_full_edit(self):
        """
        Check if previous points
        """
        prev_i = self.points_backlog_i_add - 1
        if prev_i >= 0:
            full_edit_used = self.entry_in_full_edit[prev_i]
            return full_edit_used

    def save_current_points(self, full_edit_used, exclude=None,
                            save_before_undo=False):
        """
        Save current points for undoing or redoing.

        Args:
            exclude: A point that needs to be excluded from backlog entry.
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

    def get_edit_lock_on(self):
        """
        Get if full edit is locked or not.

        Return:
            True or False.
        """
        return self._edit_lock_on

    def _sort_points(self):
        """Sorts the points in ascending order by their x coordinate."""
        self._points.sort()  # TODO what is the use of self._xs/self._ys?
        self._xs = [point.get_x() for point in self._points]
        self._ys = [point.get_y() for point in self._points]

    def get_xs(self):
        """Returns a list of the x coordinates of the points."""
        return [point.get_x() for point in self._points]

    def get_ys(self):
        """Returns a list of the y coordinates of the points."""
        return [point.get_y() for point in self._points]

    def get_point_by_i(self, i):
        """Returns the i:th point."""
        return self._points[i]

    def get_points(self):
        """
        Get points.

        Return:
             Points list.
        """
        return self._points

    def add_point(self, point):
        """Adds a point and maintains sort order."""
        self._points.append(point)
        self._sort_points()     # TODO use bisect.insort

    def remove_point(self, point):
        """Removes the given point."""
        self._points.remove(point)

    def get_left_neighbor(self, point):
        """Returns the point whose x coordinate is closest to but
        less than the given point's.
        """
        # TODO function that return both neighbours
        ind = self._points.index(point)
        if ind == 0:
            return None
        else:
            return self._points[ind - 1]

    def get_right_neighbor(self, point):
        """Returns the point whose x coordinate is closest to but
        greater than the given point's.
        """
        ind = self._points.index(point)
        if ind == len(self._points) - 1:
            return None
        else:
            return self._points[ind + 1]

    def write_recoil_file(self, recoil_file):
        """Writes a file of points that is given to MCERD and get_espe.

        Args:
            recoil_file: File path to recoil file that ends with ".recoil" or
            ".scatter".
        """
        with open(recoil_file, "w") as file_rec:
            # If there are not points all the way from 0 to 10, add this
            # small amount
            points = self.get_points()
            if 0 < points[0].get_x():
                point_x = round(points[0].get_x() - 0.01, 2)
                if points[0].get_x() <= 10.0:
                    file_rec.write("0.00 0.000001\n" + str(point_x) +
                                   " 0.000001\n")
                else:
                    file_rec.write("0.00 0.000001\n10.00 0.000001\n" +
                                   "10.01 0.0000\n" + str(point_x) +
                                   " 0.0000\n")

            for point in points:
                file_rec.write(
                    str(round(point.get_x(), 2)) + " " +
                    str(round(point.get_y(), 4)) + "\n")

            # MCERD requires the recoil atom distribution to end with these
            # points
            file_rec.write(
                str(round(self.get_points()[-1].get_x() + 0.01, 2)) +
                " 0.0\n" +
                str(round(self.get_points()[-1].get_x() + 0.02, 2)) +
                " 0.0\n")

    def calculate_area_for_interval(self, start=None, end=None):
        """
        Calculate area for given interval.

        Args:
            start: Start x.
            end: End x.

        Return:
            Area between intervals and recoil points and x axis.
        """
        # TODO maybe break this function down to couple of smaller functions
        if not start and not end:
            if not self.area_limits:
                start = self._points[0].get_x()
                end = self._points[-1].get_x()
            else:
                start = self.area_limits[0].get_xdata()[0]
                end = self.area_limits[-1].get_xdata()[0]
            self.__individual_area_points = []
            area_points = self.__individual_area_points
        else:
            self.__common_area_points = []
            area_points = self.__common_area_points

        for i, point in enumerate(self._points):
            x = point.get_x()
            y = point.get_y()
            if x < start:
                continue
            if start <= x:
                if i > 0:
                    previous_point = self._points[i - 1]
                    if previous_point.get_x() < start < x:
                        # Calculate new point to be added
                        calculate_new_point(previous_point, start,
                                            point, area_points)
                if x <= end:
                    area_points.append((x, y))
                else:
                    if i > 0:
                        previous_point = self._points[i - 1]
                        if previous_point.get_x() < end < x:
                            calculate_new_point(previous_point, end,
                                                point, area_points)
                    break

        # If common points are empty, no recoil inside area
        if not area_points:
            return 0.0

        if area_points[-1][0] < end:
            area_points.append((end, 0))

        polygon_points = []
        for value in area_points:
            polygon_points.append(value)

        # Add two points that have zero y coordinate to make a rectangle
        if not polygon_points[-1][1] == 0.0:
            point1_x = polygon_points[-1][0]
            point1 = (point1_x, 0.0)
            polygon_points.append(point1)

        point2_x = polygon_points[0][0]
        point2 = (point2_x, 0.0)

        polygon_points.append(point2)

        # Add the first point again to close the rectangle
        polygon_points.append(polygon_points[0])

        polygon = Polygon(polygon_points)
        area = polygon.area
        return area
