# coding=utf-8
"""
Created on 1.3.2018
Updated on 5.6.2018

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
    def __init__(self, element, points):
        """Inits recoil element.

        Args:
            element: An Element class object.
            points: A list of Point class objects.
        """
        self.element = element
        self.name = "Default"
        self.prefix = (Element.__str__(element)).split(" ")[0]
        self.description = "These are default recoil settings."
        self.type = "rec"
        # This is multiplied by 1e22
        self.reference_density = 4.98
        self._points = sorted(points)

        # Contains ElementWidget and SimulationControlsWidget.
        self.widgets = []
        self._edit_lock_on = True

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
        """Get the i:th point.

        Args:
            i: Index of the point.

        Return:
           Point at index i.
        """
        return self._points[i]

    def get_points(self):
        """
        Get points.

        Return:
             Points list.
        """
        return self._points

    def add_point(self, point):
        """Adds a point and maintains sort order.

        Args:
            point: Point to add.
        """
        self._points.append(point)
        self._sort_points()

    def remove_point(self, point):
        """Removes the given point."""
        self._points.remove(point)

    def get_left_neighbor(self, point):
        """Returns the point whose x coordinate is closest to but
        less than the given point's.

        Args:
            point: Point object.

        Return:
            Point's left neighbor.
        """
        ind = self._points.index(point)
        if ind == 0:
            return None
        else:
            return self._points[ind - 1]

    def get_right_neighbor(self, point):
        """Returns the point whose x coordinate is closest to but
        greater than the given point's.

        Args:
            point: Point object.

        Return:
            Point's right neighbor.
        """
        ind = self._points.index(point)
        if ind == len(self._points) - 1:
            return None
        else:
            return self._points[ind + 1]

    def write_recoil_file(self, recoil_file):
        """Writes a file of points that is given to MCERD and get_espe.

        Args:
            recoil_file: File path to recoil file that ends with ".recoil".
        """
        with open(recoil_file, "w") as file_rec:
            # MCERD requires the recoil atom distribution to start with these
            # points
            file_rec.write(
                "0.00 0.000001\n10.00 0.000001\n")

            for point in self.get_points():
                file_rec.write(
                    str(round(point.get_x() + 10.01, 2)) + " " +
                    str(round(point.get_y(), 4)) + "\n")

            # MCERD requires the recoil atom distribution to end with these
            # points
            file_rec.write(
                str(round(self.get_points()[-1].get_x() + 10.02, 2)) +
                " 0.0\n" +
                str(round(self.get_points()[-1].get_x() + 10.03, 2)) +
                " 0.0\n")
