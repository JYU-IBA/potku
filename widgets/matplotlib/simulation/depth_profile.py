# coding=utf-8
"""
Created on 1.3.2018
Updated on 13.3.2018
"""
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"

from matplotlib import cm
from matplotlib.colors import LogNorm
import matplotlib.lines as lines
from PyQt5 import QtCore, QtWidgets

from dialogs.measurement.selection import SelectionSettingsDialog
from dialogs.graph_settings import TofeGraphSettingsWidget
from modules.general_functions import open_file_dialog
from widgets.matplotlib.base import MatplotlibWidget
from modules.point import Point
from matplotlib.backend_bases import MouseEvent
import math


class MatplotlibSimulationDepthProfileWidget(MatplotlibWidget):
    """Matplotlib simulation depth profile widget. Using this widget, the user
    can edit the depth profile of the target for the simulation.
    """
    selectionsChanged = QtCore.pyqtSignal("PyQt_PyObject")
    saveCuts = QtCore.pyqtSignal("PyQt_PyObject")
    color_scheme = {"Default color": "jet",
                    "Greyscale": "Greys",
                    "Greyscale (inverted)": "gray"}

    tool_modes = {0: "",
                  1: "pan/zoom",  # Matplotlib's drag
                  2: "zoom rect",  # Matplotlib's zoom
                  3: "selection tool",
                  4: "selection select tool"
                  }

    def __init__(self, parent, simulation_data, masses, icon_manager):
        """Inits target and recoiling atoms widget.

        Args:
            parent: A SimulationDepthProfileWidget class object.
            simulation_data: Data of the simulation that needs to be drawn (elements).
            masses: A masses class object.
            icon_manager: An iconmanager class object.
        """

        super().__init__(parent)
        self.canvas.manager.set_title("Depth Profile")
        self.axes.fmt_xdata = lambda x: "{0:1.0f}".format(x)
        self.axes.fmt_ydata = lambda y: "{0:1.0f}".format(y)
        self.__masses = masses
        self.__icon_manager = icon_manager

        self.list_points = []
        self.simulation = simulation_data
        self.elements = { "He": [[0.00, 50.00], [50.00, 50.00]] }
        self.dragging_point = None  # Just one point right now

        # Connections and setup
        self.canvas.mpl_connect('button_press_event', self.on_click)
        self.canvas.mpl_connect('button_release_event', self.on_release)
        self.canvas.mpl_connect('motion_notify_event', self.on_motion)

        # This customizes the toolbar buttons
        # self.__fork_toolbar_buttons()

        # Put all x-coordinates to one list and all y-coordinates to one list.
        # There are needed later when we calculates the range of the axes.
        self.__x_data = []
        self.__y_data = []
        for points in self.elements.values():
            for point in points:
                self.__x_data.append(point[0])
                self.__y_data.append(point[1])

        self.name_y_axis = "Concentration?"
        self.name_x_axis = "Depth"

        self.on_draw()

    def on_draw(self):
        """Draw method for matplotlib.
        """
        self.axes.clear()  # Clear old stuff
        line1 = self.elements["He"]
        line1_xs, line1_ys = zip(*line1) # Divide the coordinate data into x and y data

        # Values for zoom
        x_min, x_max = self.axes.get_xlim()
        y_min, y_max = self.axes.get_ylim()

        self.axes.set_ylabel(self.name_y_axis.title())
        self.axes.set_xlabel(self.name_x_axis.title())

        # Remove axis ticks and draw
        self.remove_axes_ticks()
        self.canvas.draw()
        self.update_plot()

    def __toggle_tool_drag(self):
        if self.__button_drag.isChecked():
            self.mpl_toolbar.mode_tool = 1
        else:
            self.mpl_toolbar.mode_tool = 0
            # self.elementSelectionButton.setChecked(False)
        # self.elementSelectUndoButton.setEnabled(False)
        # self.elementSelectionSelectButton.setChecked(False)
        self.canvas.draw_idle()

    def __toggle_tool_zoom(self):
        if self.__button_zoom.isChecked():
            self.mpl_toolbar.mode_tool = 2
        else:
            self.mpl_toolbar.mode_tool = 0
            # self.elementSelectionButton.setChecked(False)
        # self.elementSelectUndoButton.setEnabled(False)
        # self.elementSelectionSelectButton.setChecked(False)
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

        # Selection undo button
        self.elementSelectUndoButton = QtWidgets.QToolButton(self)
        self.elementSelectUndoButton.clicked.connect(self.undo_point)
        self.__icon_manager.set_icon(self.elementSelectUndoButton, "undo.png")
        self.elementSelectUndoButton.setToolTip(
            "Undo last point in open selection")
        self.elementSelectUndoButton.setEnabled(False)
        self.mpl_toolbar.addWidget(self.elementSelectUndoButton)
        self.mpl_toolbar.addSeparator()

        # Selection delete button
        self.elementSelectDeleteButton = QtWidgets.QToolButton(self)
        self.elementSelectDeleteButton.setEnabled(False)
        self.elementSelectDeleteButton.clicked.connect(self.remove_selected)
        self.__icon_manager.set_icon(self.elementSelectDeleteButton, "del.png")
        self.elementSelectDeleteButton.setToolTip("Delete selected selection")
        self.mpl_toolbar.addWidget(self.elementSelectDeleteButton)
        self.mpl_toolbar.addSeparator()

    def find_clicked_point(self, x, y):
        """ If an existing point is clicked, return it.
        Args:
            x: x coordinate of click
            y: y coordinate of click
        """
        # Display coordinates (relative to the screen)
        x_y_disp = self.axes.transData.transform((x, y))
        for p in self.elements["He"]:
            elem_x_y_disp = self.axes.transData.transform((p[0], p[1]))
            if self.distance(elem_x_y_disp[0], elem_x_y_disp[1], x_y_disp[0], x_y_disp[1]) < 20:
                return p
        return None

    def on_click(self, event):
        """ On click event above graph.

        Args:
            event: A MPL MouseEvent
        """
        # Only inside the actual graph axes, else do nothing.
        if event.inaxes != self.axes:
            return

        if event.button == 1:  # Left click
            x = event.xdata
            y = event.ydata
            clicked_point = self.find_clicked_point(x, y)
            if clicked_point: # Dragging a point
                self.dragging_point = clicked_point
                self.remove_point(clicked_point)
            else: # Adding a point
                self.add_point_on_click(x, y)

            self.update_plot()

    def distance(self, x1, y1, x2, y2):
        """ Calculates the distance between two points. """
        dist = math.hypot(x2 - x1, y2 - y1)
        return dist

    def point_on_line(self, xa, ya, xadd, yadd, xb, yb):
        """ Checks if a point is on the line connecting
        two other points. """
        distance_a_add = self.distance(xa, ya, xadd, yadd)
        distance_b_add = self.distance(xb, yb, xadd, yadd)
        distance_a_b = self.distance(xa, ya, xb, yb)
        threshold = 3
        on_line = distance_a_add + distance_b_add - distance_a_b < threshold
        return on_line

    def add_point_on_click(self, x, y=None):
        """ Adds a point to the list when clicked close enough to a line. """
        point = [x, y]
        elems = self.elements["He"]
        for i in range(len(elems)):
            if elems[i][0] > x:
                xa, ya = elems[i-1][0], elems[i-1][1]
                xb, yb = elems[i][0], elems[i][1]
                if not self.point_on_line(xa, ya, x, y, xb, yb):
                    return None
                else:
                    elems.insert(i, point)
                    return point

    def add_point_on_motion(self, x, y=None):
        """ Adds a point to the list when it is moved.
        """
        # TODO: Maybe there could be an index as a parameter, so we know the place of the point immediately?
        if isinstance(x, MouseEvent):
            x, y = x.xdata, x.ydata
        point = [x, y]
        # If the x coord of the point to be added is less than the x coord of
        # any of the existing points, this loop catches it
        for index, p in enumerate(self.elements["He"]):
            if p[0] > x:
                self.elements["He"].insert(index, point)
                return point
        # Otherwise the point is added to the end of the list
        self.elements["He"].append(point)
        return point

    def update_plot(self):
        """ Clears the graph and replots every point. """
        # if not self.list_points:
        #     return
        # Add new plot
        self.axes.clear()  # Clear old stuff, this might cause trouble if you only want to clear one line?

        line1 = self.elements["He"]
        line1_xs, line1_ys = zip(*line1)  # Divide the coordinate data into x and y data
        self.axes.plot(line1_xs, line1_ys, "b", marker="o", markersize=7)

        self.canvas.draw_idle()

        # TODO: These set fixed axis ranges, which probably isn't correct
        self.axes.set_ylim(-10, 110)
        self.axes.set_xlim(-10, 110)

    def on_motion(self, event):
        """ Callback method for mouse motion event

        Args:
            event: A MPL MouseEvent
        """
        if not self.dragging_point:
            return
        self.remove_point(self.dragging_point)
        self.dragging_point = self.add_point_on_motion(event)
        self.update_plot()

    def remove_point(self, point):
        """ Removes a point from the list. """
        if point in self.elements["He"]:
            self.elements["He"].remove(point)

    def on_release(self, event):
        """ Callback method for mouse release event

        Args:
            event: A MPL MouseEvent
        """
        if event.button == 1 and event.inaxes in [self.axes] and self.dragging_point:
            self.add_point_on_motion(event)
            self.dragging_point = None
            self.update_plot()
