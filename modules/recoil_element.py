# coding=utf-8
"""
Created on 1.3.2018
Updated on 3.8.2018

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

from modules.element import Element


class RecoilElement:
    """An element that has a list of points and a widget. The points are kept
    in ascending order by their x coordinate.
    """
    def __init__(self, element, points, color, name="Default", rec_type="rec"):
        """Inits recoil element.

        Args:
            element: An Element class object.
            points: A list of Point class objects.
            name: Name of the RecoilElement object anf file.
            rec_type: Type recoil element (rec or sct).
        """
        self.element = element
        self.name = name
        self.prefix = (Element.__str__(element)).split(" ")[0]
        self.description = "These are default recoil settings."
        self.type = rec_type
        # This is multiplied by 1e22
        self.reference_density = 4.98
        self.multiplier = 1e22
        self._points = sorted(points)

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
        self._points.sort()
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
        self._sort_points()

    def remove_point(self, point):
        """Removes the given point."""
        self._points.remove(point)

    def get_left_neighbor(self, point):
        """Returns the point whose x coordinate is closest to but
        less than the given point's.
        """
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
                str(round(self.get_points()[-1].get_x() + 10.02, 2)) +
                " 0.0\n" +
                str(round(self.get_points()[-1].get_x() + 10.03, 2)) +
                " 0.0\n")
