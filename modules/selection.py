# coding=utf-8
"""
Created on 15.3.2013
Updated on 13.11.2018

Potku is a graphical user interface for analyzation and 
visualization of measurement data collected from a ToF-ERD 
telescope. For physics calculations Potku uses external 
analyzation components.  
Copyright (C) 2013-2018 Jarkko Aalto, Severi Jääskeläinen, Samuel Kaiponen,
Timo Konu, Samuli Kärkkäinen, Samuli Rahkonen, Miika Raunio, Heta Rekilä and
Sinikka Siironen, 2020 Juhani Sundell, Tuomas Pitkänen

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

Selection.py handles Selector and Selection objects.
"""
__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen " \
             "\n Samuli Rahkonen \n Miika Raunio \n Severi Jääskeläinen \n " \
             "Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen" \
             "Juhani Sundell \n Tuomas Pitkänen"
__version__ = "2.0"
# TODO move this module under widgets.matplotlib

import os
import itertools

from . import math_functions as mf
from . import general_functions as gf

import matplotlib as mpl

from dialogs.measurement.selection import SelectionSettingsDialog

from pathlib import Path

from .element import Element


class AxesLimits:
    """
    An AxesLimit class.
    """
    def __init__(self):
        """Inits axes limits
        """
        self.__used = False
        self.__x_min = None
        self.__x_max = None
        self.__y_min = None
        self.__y_max = None

    def update_limits(self, point):
        """Updates axes limits.
        
        Args:
            point: A point as list (x, y) representing point.
        """
        if self.__used:
            self.__x_min = min(point[0], self.__x_min)
            self.__x_max = max(point[0], self.__x_max)
            self.__y_min = min(point[1], self.__y_min)
            self.__y_max = max(point[1], self.__y_max)
        else:
            self.__used = True
            self.__x_min = point[0]
            self.__x_max = point[0]
            self.__y_min = point[1]
            self.__y_max = point[1]

    def is_inside(self, point):
        """Is point inside limits.
        
        Args:
            point: A point as list (x, y) representing point.
            
        Return:
            Returns True when point is within limits.
        """
        if not self.__used:
            return False
        if point[0] < self.__x_min:
            return False
        elif point[0] > self.__x_max:
            return False
        if point[1] < self.__y_min:
            return False
        elif point[1] > self.__y_max:
            return False
        return True


class Selector:
    """Selector objects handles all selections within measurement.
    """
    def __init__(self, measurement: "Measurement", element_colormap):
        """Inits Selector.
        
        Inits Selector object.
        
        Args:
            measurement: Measurement object of this Selector.
            element_colormap: Default colors for new element selections.
        """
        self.element_colormap = element_colormap
        # self.settings = measurement.measurement_settings
        self.measurement = measurement
        self.measurement_name = measurement.name
        self.directory = self.measurement.get_data_dir()
        self.selection_file = Path(self.directory,
                                   f"{self.measurement_name}.selections")
        # List is sufficient enough
        self.selections = []
        self.new_selection_is_allowed = True
        self.is_transposed = False
        self.looseness = 10  # Default 40, looeness of the selection completion.
        self.axes = None
        self.axes_limits = AxesLimits()
        self.selected_id = None
        self.draw_legend = False

    def count(self):
        """Get count of selections.
        
        Return:
            Returns the count of selections in selector object.
        """
        return len(self.selections)

    def is_empty(self):
        """Check if no selections.
        
        Return:
            Returns True if no selections.
        """
        return self.count() == 0

    def get_at(self, index):  # Get selection at index
        """Get selection at index.
        
        Args:
            index: Integer of index we want to get from selections.
            
        Return:
            Returns Selection at said index. If index is out of range, returns
            None.
        """
        if index >= self.count() or index < 0:
            return None
        return self.selections[index]

    def get_selected(self):  # Get selection by id
        """Get currently selected selection.
        
        Return:
            Returns Selection of selected Selection on matplotlib graph. If
            none selected, returns None.
        """
        if self.selected_id is None:
            return None
        for selection in self.selections:
            if selection.id == self.selected_id:
                return selection
        return None

    def add_point(self, point, canvas):
        """Adds a new point.
        
        Adds a new point to last selection. If new selection is allowed, create
        a new selection to which point is added. If point is in close proximity
        of first point in (last) Selection, then close selection and allow new 
        selection to be made.
        
        Args:
            point: Point (x, y) to be added to selection.
            canvas: matplotlib's FigureCanvas where selections are drawn.
            
        Return:
            1: When point closes open selection and allows new selection to 
                be made.
            0: When point was added to open selection.
            -1: When new selection is not allowed and there are no selections.
        """
        if self.new_selection_is_allowed:
            sel = Selection(self.axes, self.element_colormap,
                            measurement=self.measurement)
            self.grey_out_except(sel.id)
            self.selections.append(sel)
            # Do not allow new selections without closing/purging
            self.new_selection_is_allowed = False
        elif not self.selections:  # Something went horribly wrong!
            return -1
        else:
            sel = self.selections[-1]  # Select last one

        # Check if closing selection
        if sel.count() >= 3:  # Requirement for there to be selection
            # If we are close enough, close selection
            if mf.distance(sel.get_first(), point) < self.looseness:
                selection_is_ok = sel.end_selection(canvas)
                # If selection was cancelled -> remove just made selection
                if not selection_is_ok:
                    self.__remove_last()
                self.reset_colors()
                self.auto_save()
                self.new_selection_is_allowed = True
                return 1
        # Do not allow selection of too close point
        if sel.count() >= 1:
            for point2 in sel.get_points():
                if mf.distance(point2, point) < self.looseness:
                    print("Point too close!")
                    return -1

        sel.add_point(point)
        return 0

    def undo_point(self):
        """Undo last point in open (last) selection.
        
        Undo last point in open (last) selection. If there are no selections, 
        do nothing.
        """
        if self.is_empty():
            return
        sel = self.selections[-1]  # [-1] = last one
        if not sel.is_closed:
            sel.undo_last()

    def update_references(self, measurement: "Measurement"):
        """
        Update references with values form Measurement.

         Args:
             measurement: Measurement object.
        """
        self.measurement_name = measurement.name
        self.directory = measurement.get_data_dir()

        selection_file_without_path = self.selection_file.name
        old_selection_file_in_new_path = Path(
            self.directory, selection_file_without_path)
        try:
            if old_selection_file_in_new_path.exists():
                new_file = gf.rename_file(old_selection_file_in_new_path,
                                          self.measurement_name + ".selections")
                self.selection_file = Path(self.directory, new_file)
        except OSError as e:
            e.args = f"Failed to rename selections: {e}",
            raise

    def purge(self):
        """Purges (removes) all open selections and allows new selection to be
        made.
        """
        for s in self.selections:
            if not s.is_closed:  # If selection is not closed -> purge
                s.delete()
                self.selections.remove(s)
        self.new_selection_is_allowed = True

    def remove_selected(self):
        """Remove selected selection.
        
        Removes selected selection if one is selected. Otherwise do nothing.
        """
        if self.selected_id is None:  # Can be 0.
            return
        for s in self.selections:
            if s.id == self.selected_id:
                s.delete()
                self.selections.remove(s)
        self.selected_id = None

    def __remove_last(self):
        """Remove last selection.
        """
        if self.is_empty():
            return
        selection_last = self.selections[-1]
        selection_last.delete()
        self.selections.remove(selection_last)
        # Purge everything just in case and allow new selection.
        self.purge()

    def remove_all(self):
        """Remove all selections in selector.
        """
        for s in self.selections:
            s.delete()
        self.selections.clear()
        self.selected_id = None

    def draw(self):
        """Draw selections.
        
        Issue draw to all selections in selector.
        """
        if self.axes:
            lines = {}
            for s in self.selections:
                s.draw()
                lines[s.element.symbol] = s.points
            if self.draw_legend:
                line_text = lines.keys()
                line_points = []
                for k in line_text:
                    line_points.append(lines[k])
                self.axes.legend(line_points, line_text, loc=0)

    def end_open_selection(self, canvas):
        """End last open selection.
        
        Ends last open selection. If selection is open, it will show dialog to 
        select element information and draws into canvas before opening the
        dialog.
        
        Args:
            canvas: Matplotlib's FigureCanvas

        Return:
            1: If selection closed
            0: Otherwise
        """
        if self.is_empty():
            return 0
        sel = self.selections[-1]  # Get last one
        if sel.count() < 3:  # Required point count
            message = "At least two points required to close selection"
            self.measurement.log_error(message)
            return 0
        elif not sel.is_closed:
            selection_is_ok = sel.end_selection(canvas)
            if not selection_is_ok:
                self.__remove_last()
            self.reset_colors()
            self.auto_save()
            if selection_is_ok:
                self.update_single_selection_points(sel)
            self.new_selection_is_allowed = True
            return 1
        return 0

    def select(self, point, highlight=True):
        """Select a selection based on point.
        
        Args:
            point: Point (x, y) which is clicked on the graph to select
            selection.
            highlight: Boolean to determine whether to highlight just this 
                       selection.
            
        Return:
            1: If point is within selection.
            0: If point is not within selection.
        """
        for selection in self.selections:
            path = mpl.path.Path(selection.get_points())
            if path.contains_point(point):
                self.selected_id = selection.id
                if highlight:
                    self.grey_out_except(selection.id)
                return 1
        return 0

    def reset_select(self):
        """Reset selection to None.
        
        Resets current selection to None and resets colors of all selections
        to their default values. 
        """
        self.selected_id = None
        self.reset_colors()

    def reset_colors(self):
        """Reset selection colors.
        
        Reset all selections' colors to their default values.
        """
        for sel in self.selections:
            sel.reset_color()

    def get_colors(self):
        """Get colors of each selection in selector.
        
        Return:
            Returns dictionary of all element selections and their colors.
        """
        color_dict = {}
        for sel in self.selections:
            element = sel.element.symbol
            isotope = sel.element.isotope
            if isotope is None:
                isotope = ""
            if sel.type == "RBS":
                element, isotope = sel.element_scatter.symbol, \
                                   sel.element_scatter.isotope
                prefix = "RBS_"
                if isotope is None:
                    isotope = ""
            else:
                prefix = ""
            color_string = self._find_next_color_string(
                prefix, isotope, element, color_dict)
            color_dict[color_string] = sel.default_color
        return color_dict

    @staticmethod
    def _find_next_color_string(prefix, isotope, element, color_dict) -> str:
        """Helper function for returning new color string.
        """
        def color_generator():
            for i in itertools.count(start=0):
                yield f"{prefix}{isotope}{element}{i}"

        return gf.find_next(color_generator(), lambda s: s not in color_dict)

    def grey_out_except(self, selected_id):
        """Grey out all selections except selected one.
        
        Sets all selections' colors to grey except selected, which is set to
        red.
        
        Args:
            selected_id: Integer of selected selection id 
        """
        for sel in self.selections:
            if sel.id == selected_id:
                sel.set_color("red")
            else:
                sel.set_color("grey")

    def auto_save(self):
        """Save all selections into a file.
        """
        if not self.directory.exists():
            os.makedirs(self.directory)
        # Truncate old .sel and write new one
        with open(self.selection_file, "wt+") as fp:
            for sel in self.selections:
                fp.write(sel.save_string(self.is_transposed) + "\n")

    def load(self, filename, progress=None):
        """Load selections from a file.
        
        Removes all current selections and loads selections from given filename.
        
        Args:
            filename: String representing (full) path to selection file.
            progress: ProgressReporter object.
        """
        self.remove_all()
        try:
            with open(filename) as fp:
                for line in fp:
                    # ['ONone', '16', 'red', '3436, 2964, 4054;2376, 3964, 3914']
                    split = line.strip().split("    ")
                    sel = Selection(self.axes, self.element_colormap,
                                    element_type=split[0],
                                    element=split[1],
                                    isotope=(split[2] if split[2] == ""
                                             else int(split[2])),
                                    weight_factor=float(split[3]),
                                    scatter=split[4],
                                    color=split[5],
                                    points=split[6],
                                    transposed=self.is_transposed,
                                    measurement=self.measurement)
                    self.selections.append(sel)
            message = f"Selection file {filename} was read successfully!"
            self.measurement.log(message)
        except OSError as e:
            message = f"Could not read selection file: {e}."
            self.measurement.log_error(message)
        except (ValueError, IndexError) as e:
            message = f"Could not read selection data from {filename}. " \
                      f"Reason: {e}. Check that the file contains valid data."
            self.measurement.log_error(message)
        self.update_axes_limits()
        self.draw()  # Draw all selections
        self.auto_save()
        self.update_selection_points(progress=progress)

    def update_axes_limits(self):
        """Update selector's axes limits based on all points in all selections.
        """
        for sel in self.selections:
            for point in sel.get_points():
                self.axes_limits.update_limits(point)

    def transpose(self, is_transposed):
        """Transpose graph axes.
        
        Args:
            is_transposed: Boolean representing whether axes are transposed.
        """
        self.is_transposed = is_transposed
        for selection in self.selections:
            selection.transpose(is_transposed)

    def update_single_selection_points(self, selection):
        """
        Update single selection points.

        Args:
            selection: Points to update.
        """
        selection.events_counted = False
        selection.event_count = 0
        data = self.measurement.data
        if not selection.is_closed:
            selection.events_counted = True
            return
        for n in range(len(data)):
            selection.point_inside(data[n])
        selection.events_counted = True

    def update_selection_points(self, progress=None):
        """Update all selections event counts.

        Args:
            progress: ProgressReporter object
        """
        data = self.measurement.data
        for selection in self.selections:
            selection.events_counted = False
            selection.event_count = 0

        for i, point in enumerate(data):
            for selection in self.selections:
                if selection.is_closed:
                    selection.point_inside(point)
            if progress is not None and i % 10_000 == 0:
                progress.report(i / len(data) * 100)

        for selection in self.selections:
            selection.events_counted = True

    def update_selection_beams(self):
        """Update all RBS selections' beam ions."""
        for selection in self.selections:
            if selection.type == "RBS":
                if selection.measurement.use_request_settings:
                    ion = self.measurement.request.default_measurement.run.beam\
                        .ion
                else:
                    ion = selection.measurement.run.beam.ion
                selection.element = ion


class Selection:
    """Selection object which knows all selection points.
    """
    LINE_STYLE = '-'  # Default line style for selections
    LINE_MARKER = 'o'  # Default node style for selections
    LINE_MARKER_SIZE = 3.0
    GLOBAL_ID = 0
    
    def __init__(self, axes, element_colormap, measurement, element=None,
                 isotope=None,
                 element_type="ERD", color=None, points=None, scatter=None,
                 weight_factor=1.0, transposed=False):
        """Inits Selection class.
        
        Args:
            axes: Matplotlib FigureCanvas's subplot
            element_colormap: Default colors for new element selections.
            measurement: Measurement object.
            element: String representing element
            isotope: Integer representing isotope
            element_type: "ERD" or "RBS"
            color: String representing color for the element
            points: String list representing points in selection.
                    "X1, X2, X3;Y1, Y2, Y3"
            scatter: String representing scatter element.
            weight_factor: Weight factor for the element.
            transposed: Boolean representing if axes are transposed.
        """
        self.id = Selection.GLOBAL_ID
        self.element_colormap = element_colormap
        self.measurement = measurement

        if color is not None:
            self.default_color = color
        elif element is not None:
            self.default_color = self.element_colormap[element]
        else:  # By change that color is not in element_colormap
            self.default_color = "red"

        self.type = element_type
        self.element = Element(element, isotope)  # If RBS, this holds beam ion
        self.weight_factor = weight_factor
        if scatter and scatter != "":
            self.element_scatter = Element.from_string(scatter)
        else:
            self.element_scatter = ""

        self.events_counted = False
        self.event_count = 0
        self.__is_transposed = False
        self.is_closed = False
        self.points = None
        self.axes = axes
        self.axes_limits = AxesLimits()

        Selection.GLOBAL_ID += 1

        if points is not None:
            points = points.split(';')
            if transposed:
                points[0], points[1] = points[1], points[0]
            x = [int(i) for i in points[0].split(',')]
            y = [int(i) for i in points[1].split(',')]
            point_count = len(x)  #
            for i in range(point_count):  #
                self.add_point((x[i], y[i]))
            self.end_selection()

        self.masses = None

    def add_point(self, point):
        """Adds a point to selection.

        Adds a point to selection. If selection is closed, do nothing.

        Args:
            point: Point (x, y) to be added to selection.

        Return:
            0: Point was added.
            -1: If selection is closed.
        """
        if self.is_closed:
            return -1
        else:
            if self.points is None:
                self.points = mpl.lines.Line2D(
                    [point[0]], [point[1]],
                    linestyle=Selection.LINE_STYLE,
                    marker=Selection.LINE_MARKER,
                    markersize=Selection.LINE_MARKER_SIZE,
                    color=self.default_color)
            else:
                x, y = self.points.get_data()
                x.append(point[0])
                y.append(point[1])
                self.points.set_data(x, y)
            self.axes.add_line(self.points)
            return 0

    def undo_last(self):
        """Undo last point in selection.

        Return:
            1: If selection is closed or there are no points in selection.
            0: If everything is ok.
        """
        if self.is_closed:
            return 1
        # After this, purge the last points so no duplicates should be inside.
        x, y = self.points.get_data()
        if not x:
            return 1
        x.pop()
        y.pop()
        self.points.set_data(x, y)
        return 0

    def get_points(self):
        """Get points in selection

        Get points in selection in list. Format: ((x1,y1), (x2,y2), ...).
        If no points, empty list is returned

        Return:
           ((x1, y1), (x2, y2), ...)
        """
        points = self.points.get_data()
        pointlist = []
        for i in range(len(points[0])):
            pointlist.append([points[0][i], points[1][i]])
        return pointlist

    def get_first(self):
        """Get first point in selection

        Return:
            None: If no point in selection
            (x, y): Otherwise
        """
        if self.count() > 0:
            x, y = self.points.get_data()
            return x[0], y[0]  # TODO: Should this be tuple or a class?
        else:
            return None

    def get_last(self):
        """Get last point in selection

        Return:
            None: If no point in selection
            (x, y): Otherwise
        """
        if self.count() > 0:
            x, y = self.points.get_data()
            return x[-1], y[-1]  # TODO: Should this be tuple or a class?
        else:
            return None

    def count(self):
        """Get the count of node points in selection.

        Return
            Returns the count of node points in selection.
        """
        if self.points is None:  # No data yet, "empty" list
            return 0
        return len(self.points.get_data()[0])  # X data count is fine.

    def end_selection(self, canvas=None):
        """End selection.

        Ends selection. If selection is open and canvas is not None, it will
        show dialog to select element information and draws into canvas
        before opening the dialog.

        Args:
            canvas: Matplotlib's FigureCanvas or None when we don't want
                    to new selection window. None, when loading selections
                    so we do not want to open new selection settings dialog.

        Return:
            True: Selection was completed
            False: Selection settings was not set (cancel button)
        """
        for point in self.get_points():
            self.axes_limits.update_limits(point)

        # Add first point again, so drawing the line is closed.
        # Then remove it, so no duplicates in points. (roundabout)
        self.add_point(self.get_first())
        x, y = self.points.get_data()
        x.pop()
        y.pop()

        selection_completed = True
        if canvas is not None:
            canvas.draw_idle()
            selection_settings_dialog = SelectionSettingsDialog(self)
            # True = ok, False = cancel -> delete selection
            selection_completed = selection_settings_dialog.isOk
        self.is_closed = True
        return selection_completed

    def delete(self):
        """Delete this selection.
        """
        self.points.set_data(((), ()))
        self.points = None
        self.masses = None
        self.element_colormap = None

    def draw(self):
        """Draw selection points into graph (matplotlib) axes
        """
        self.axes.add_line(self.points)

    def set_color(self, color):
        """Set selection color

        Args:
            color: String representing color.
                   Format is whatever QtGui.QColor(string) understands.
        """
        self.points.set_color(color)

    def reset_color(self):
        """Reset selection color to default color.
        """
        self.set_color(self.default_color)

    def __save_points(self, is_transposed):
        """Get selection points in format for saving.

        Args:
            is_transposed: Boolean representing if axes are transposed.

        Return:
            Returns string representing current points in selection.
        """
        # [1, 4, 2, 6]
        # to
        # 1,4,2,6
        x, y = self.points.get_data()
        x = ','.join(str(i) for i in x)
        y = ','.join(str(j) for j in y)
        # x = str(x).strip('[').strip(']').strip(' ')  # TODO: format?
        # y = str(y).strip('[').strip(']').strip(' ')  # TODO: format?
        if is_transposed:
            x, y = y, x
        s = (x, y)
        return ';'.join(s)

    def save_string(self, is_transposed):
        """Get selection in string format for selection file save.

        Args:
            is_transposed: Boolean representing if axes are transposed.

        Return:
            String representing current selection object.
        """
        save_string = ""
        if self.element:
            if self.element.symbol != "Select":
                symbol = self.element.symbol
            else:
                symbol = ""
            isotope = self.element.isotope
            if self.element_scatter != "":
                element_scatter = self.element_scatter.__str__()
            else:
                element_scatter = ""
            if isotope is None:
                isotope = ""
            save_string = "{0}    {1}    {2}    {3}    {4}    {5}    {6}".\
                format(
                    self.type,
                    symbol,
                    isotope,
                    self.weight_factor,
                    element_scatter,
                    self.default_color,
                    self.__save_points(is_transposed))
        return save_string

    def transpose(self, transpose):
        """Transpose selection points.

        Args:
            transpose: Boolean representing whether to transpose selection
            points.
        """
        if transpose:  # and not self.__is_transposed
            self.__is_transposed = True
            x, y = self.points.get_data()
            x.append(x[0])
            y.append(y[0])
            self.points.set_data(y, x)
        elif not transpose:  # and self.__is_transposed
            self.__is_transposed = False
            x, y = self.points.get_data()
            x.append(x[0])
            y.append(y[0])
            self.points.set_data(y, x)

    def get_event_count(self):
        """Get the count of event points within the selection.

        Return:
            Returns an integer representing the count of event points within
            the selection.
        """
        return self.event_count

    def point_inside(self, point):
        """Check if point is inside selection.

        Args:
            point: [X, Y] representing a point.

        Return:
            Returns True if point is within selection. False otherwise.
        """
        if not self.axes_limits.is_inside(point):
            return False
        inside = mf.point_inside_polygon((point[0], point[1]),
                                         self.get_points())
        # While at it, increase event point counts if not counted already.
        if inside and not self.events_counted:
            self.event_count += 1
        return inside
