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

from Dialogs.SelectionDialog import SelectionSettingsDialog
from Dialogs.GraphSettingsDialog import TofeGraphSettingsWidget
from Modules.Functions import open_file_dialog
from Widgets.MatplotlibWidget import MatplotlibWidget
from Modules.Point import Point
from matplotlib.backend_bases import MouseEvent
import math
import numpy as np
from numpy.random import rand
from matplotlib.lines import Line2D
import bisect


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
        self.xs = (100 * rand(20)).tolist()
        self.ys = (100 * rand(20)).tolist()
        self.xs.sort()
        self.ys.sort()
        self.xys = zip(self.xs, self.ys)
        # self.xys = sorted(self.xys, key=lambda x: x[0])
        self.selected_x = 0
        self.selected_y = 0

        self.lines = None
        self.points = None
        self.selected = None
        self.drag_i = None
        self.lastind = 0

        # Connections and setup
        self.canvas.mpl_connect('button_press_event', self.on_click)
        self.canvas.mpl_connect('button_release_event', self.on_release)
        self.canvas.mpl_connect('motion_notify_event', self.on_motion)
        # self.canvas.mpl_connect('pick_event', self.onpick2)
        # self.canvas.mpl_connect('pick_event', self.onpick1)


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

        # self.__x_data = [x[0] for x in self.simulation.data[0]]
        # self.__y_data = [x[1] for x in self.simulation.data[0]]

        # Get settings from global settings
        # self.__global_settings = self.main_frame.simulation.project.global_settings
        # self.invert_Y = self.__global_settings.get_tofe_invert_y()
        # self.invert_X = self.__global_settings.get_tofe_invert_x()
        # self.transpose_axes = self.__global_settings.get_tofe_transposed()
        # self.simulation.color_scheme = self.__global_settings.get_tofe_color()
        # self.compression_x = self.__global_settings.get_tofe_compression_x()
        # self.compression_y = self.__global_settings.get_tofe_compression_y()
        # self.axes_range_mode = self.__global_settings.get_tofe_bin_range_mode()
        # x_range = self.__global_settings.get_tofe_bin_range_x()
        # y_range = self.__global_settings.get_tofe_bin_range_y()
        # self.axes_range = [x_range, y_range]
        #
        # self.__x_data_min, self.__x_data_max = self.__fix_axes_range(
        #     (min(self.__x_data), max(self.__x_data)),
        #     self.compression_x)
        # self.__y_data_min, self.__y_data_max = self.__fix_axes_range(
        #     (min(self.__y_data), max(self.__y_data)),
        #     self.compression_y)

        self.name_y_axis = "Concentration?"
        self.name_x_axis = "Depth"

        self.on_draw()

    def on_draw(self):
        """Draw method for matplotlib.
        """
        self.axes.clear()  # Clear old stuff
        line1 = self.elements["He"]
        line1_xs, line1_ys = zip(*line1) # Divide the coordinate data into x and y data
        # self.list_points.append(Point(self, line1_xs[0], line1_ys[0], 1))
        # self.list_points.append(Point(self, line1_xs[1], line1_ys[1], 1))

        # self.axes.add_line(lines.Line2D(line1_xs, line1_ys, linewidth=2, color="green", marker='o'))
        # self.axes.plot(10, 0.5, linewidth=2, color="green", marker='o', markersize=10)
        # Values for zoom
        x_min, x_max = self.axes.get_xlim()
        y_min, y_max = self.axes.get_ylim()

        # self.axes.set_title('ToF Histogram\n\n')
        self.axes.set_ylabel(self.name_y_axis.title())
        self.axes.set_xlabel(self.name_x_axis.title())

        self.lines, = self.axes.plot(self.xs, self.ys, "b")
        self.points, = self.axes.plot(self.xs, self.ys, "b", marker="o", markersize=7, picker=5,
                                      linestyle="None")
        self.selected, = self.axes.plot(self.selected_x, self.selected_y, 'o', ms=12, alpha=0.4,
                                        color='yellow', visible=False)

        # self.axes.set_xlim(-10, 110)
        # self.axes.set_ylim(-10, 110)
        self.axes.autoscale(enable=False)

        # Remove axis ticks and draw
        self.remove_axes_ticks()
        self.canvas.draw()
        self.update_plot()

    def __fix_axes_range(self, axes_range, compression):
        """Fixes axes' range to be divisible by compression.
        """
        rmin, rmax = axes_range
        mod = (rmax - rmin) % compression
        if mod == 0:  # Everything is fine, return.
            return axes_range
        # More data > less data
        rmax += compression - mod
        return rmin, rmax

    def __set_y_axis_on_right(self, yes):
        if yes:
            # self.axes.spines['left'].set_color('none')
            self.axes.spines['right'].set_color('black')
            self.axes.yaxis.tick_right()
            self.axes.yaxis.set_label_position("right")
        else:
            self.axes.spines['left'].set_color('black')
            # self.axes.spines['right'].set_color('none')
            self.axes.yaxis.tick_left()
            self.axes.yaxis.set_label_position("left")

    def __set_x_axis_on_top(self, yes):
        if yes:
            # self.axes.spines['bottom'].set_color('none')
            self.axes.spines['top'].set_color('black')
            self.axes.xaxis.tick_top()
            self.axes.xaxis.set_label_position("top")
        else:
            self.axes.spines['bottom'].set_color('black')
            # self.axes.spines['top'].set_color('none')
            self.axes.xaxis.tick_bottom()
            self.axes.xaxis.set_label_position("bottom")

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
        # xlim = self.axes.get_xlim()
        # xrange = xlim[1] - xlim[0]
        # ylim = self.axes.get_ylim()
        # yrange = ylim[1]-ylim[0]

        # Display coordinates (relative to the screen)
        x_y_disp = self.axes.transData.transform((x, y))
        for p in self.elements["He"]:
            elem_x_y_disp = self.axes.transData.transform((p[0], p[1]))
            if self.distance(elem_x_y_disp[0], elem_x_y_disp[1], x_y_disp[0], x_y_disp[1]) < 20:
                # if abs(elem_x_y_disp[0] - x_y_disp[0]) < 100 and abs(elem_x_y_disp[1] - x_y_disp[1]) < 100:
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
        contains, info = self.points.contains(event)
        if contains:
            # TODO: leftmost point can't be dragged
            i = info['ind'][0]
            self.lastind = i
            self.update_plot()
            self.drag_i = i
        else:
            x = event.xdata
            y = event.ydata
            self.add_point_on_click(x, y)
            return

        # if event.artist != self.points:
        #     return

        # N = len(event.ind)
        # if not N:
        # #     return
        #
        #
        # print(self.xs[event.ind], self.ys[event.ind])
        # # the click locations
        # x = event.mouseevent.xdata
        # y = event.mouseevent.ydata
        #
        # distances = np.hypot(x - self.xs[event.ind], y - self.ys[event.ind])
        # indmin = distances.argmin()
        # dataind = event.ind[indmin]
        #
        # self.lastind = dataind
        # self.update_plot()
        #
        # # if event.button == 1:
        # #     x = event.xdata
        # #     y = event.ydata
        # #     contains, info = self.points.contains(event)
        # #     if contains:
        # #         i = info['ind'][0]
        # #         self.dragging_point = info
        # #         self.remove_point(self.points[i])
        # #     else: # Adding a point
        # #         self.add_point_on_click(x, y)
        # if event.button == 1:  # Left click
        #     x = event.xdata
        #     y = event.ydata
        #     clicked_point = self.find_clicked_point(x, y)
        #     if clicked_point: # Dragging a point
        #         self.dragging_point = clicked_point
        #         self.remove_point(clicked_point)
        #     else: # Adding a point
        #         self.add_point_on_click(x, y)
        #
        #     self.update_plot()

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
        i = bisect.bisect(self.xs, x)
        self.xs.insert(i, x)
        self.ys.insert(i, y)

        self.update_plot()
        # point = [x, y]
        # elems = self.elements["He"]
        # for i in range(len(elems)):
        #     if elems[i][0] > x:
        #         xa, ya = elems[i-1][0], elems[i-1][1]
        #         xb, yb = elems[i][0], elems[i][1]
        #         if not self.point_on_line(xa, ya, x, y, xb, yb):
        #             return None
        #         else:
        #             elems.insert(i, point)
        #             return point
        # if p[0] > x: # Fix this, now you can't add a point to the end of list
        #     if p[1] != round(y, 3):
        #         return
        # else:
        #     point[1] = p[1]
        #     self.elements["He"].insert(index, point)
        #     # for e in self.elements["He"]:
        #     #     print(e)
        #     return point

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
        #self.axes.clear()  # Clear old stuff, this might cause trouble if you only want to clear one line?
        #
        # line1 = self.elements["He"]
        # line1_xs, line1_ys = zip(*line1)  # Divide the coordinate data into x and y data
        # #self.axes.plot(line1_xs, line1_ys, "b", marker="o", markersize=7, picker=self.line_picker)
        #
        # self.canvas.draw_idle()

        if self.lastind is None:
            return

        dataind = self.lastind

        self.points.set_data(self.xs, self.ys)
        self.lines.set_data(self.xs, self.ys)

        self.selected.set_visible(True)
        self.selected.set_data(self.xs[dataind], self.ys[dataind])

        self.fig.canvas.draw()

        # # TODO: These set fixed axis ranges, which probably isn't correct
        # self.axes.set_ylim(-10, 110)
        # self.axes.set_xlim(-10, 110)

    def line_picker(self, line, mouseevent):
        """
        find the points within a certain distance from the mouseclick in
        data coords and attach some extra attributes, pickx and picky
        which are the data points that were picked
        """
        if mouseevent.xdata is None:
            return False, dict()
        xdata = line.get_xdata()
        ydata = line.get_ydata()
        maxd = self.fig.dpi / 72. * 5
        d = np.sqrt((xdata - mouseevent.xdata)**2. + (ydata - mouseevent.ydata)**2.)

        ind = np.nonzero(np.less_equal(d, maxd))
        if len(ind):
            pickx = np.take(xdata, ind)
            picky = np.take(ydata, ind)
            props = dict(ind=ind, pickx=pickx, picky=picky)
            return True, props
        else:
            return False, dict()

    def onpick2(self, event):
        print('onpick2 line:', event.pickx, event.picky)
        self.selected_x = event.pickx
        self.selected_y = event.picky

    def onpick1(self, event):
        if event.artist != self.points:
            return True

        N = len(event.ind)
        if not N:
            return True

        print(self.xs[event.ind], self.ys[event.ind])
        # the click locations
        x = event.mouseevent.xdata
        y = event.mouseevent.ydata

        distances = np.hypot(x - self.xs[event.ind], y - self.ys[event.ind])
        indmin = distances.argmin()
        dataind = event.ind[indmin]

        self.lastind = dataind
        self.update_plot()
        #
        # if isinstance(event.artist, Line2D):
        #     thisline = event.artist
        #     xdata = thisline.get_xdata()
        #     ydata = thisline.get_ydata()
        #     ind = event.ind
        #     self.selected_x = np.take(xdata, ind)
        #     self.selected_y = np.take(ydata, ind)
        #     self.selected.set_data(self.selected_x, self.selected_y)
        #     print('onpick1 line:', np.take(xdata, ind), np.take(ydata, ind))
        #     self.update_plot()


    def on_motion(self, event):
        """ callback method for mouse motion event

        Args:
            event: A MPL MouseEvent
        """
        # if not isinstance(event, MouseEvent):
        #     return
        # x = round(event.xdata, 4)
        # y = round(event.ydata, 4)
        # if not self.dragging_point:
        #     return
        # self.dragging_point[0] = x
        # self.dragging_point[1] = y
        # if not self.dragging_point:
        #     return
        # self.remove_point(self.dragging_point)
        # self.dragging_point = self.add_point_on_motion(event)
        # self.update_plot()
        if not self.drag_i:
            return
        # TODO: Sorting
        if self.xs[self.drag_i - 1] < event.xdata < self.xs[self.drag_i + 1]:
            self.xs[self.drag_i] = event.xdata
            self.ys[self.drag_i] = event.ydata
            self.update_plot()

    def remove_point(self, point):
        """ Removes a point from the list. """
        if point in self.elements["He"]:
            self.elements["He"].remove(point)

    def on_release(self, event):
        """ callback method for mouse release event

        Args:
            event: A MPL MouseEvent
        """
        if event.button == 1 and event.inaxes in [self.axes] and self.drag_i:
            self.drag_i = None
            self.update_plot()

    #
    # def graph_settings_dialog(self):
    #     '''Show graph settings dialog.
    #     '''
    #     TofeGraphSettingsWidget(self)
    #
    # def remove_selected(self):
    #     '''Remove selected selection.
    #     '''
    #     self.elementSelectDeleteButton.setEnabled(False)
    #     self.__on_draw_legend()
    #     self.canvas.draw_idle()
    #     self.__emit_selections_changed()
    #
    # def undo_point(self):
    #     '''Undo last point in open selection.
    #     '''
    #     # self.measurement.undo_point()
    #     self.canvas.draw_idle()