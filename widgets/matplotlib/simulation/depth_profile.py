# coding=utf-8
"""
Created on 1.3.2018
Updated on 26.3.2018
"""
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"

from matplotlib import cm
from matplotlib.colors import LogNorm
import matplotlib.lines as lines
from PyQt5 import QtCore, QtWidgets, QtGui

from dialogs.measurement.selection import SelectionSettingsDialog
from dialogs.graph_settings import TofeGraphSettingsWidget
from modules.general_functions import open_file_dialog
from widgets.matplotlib.base import MatplotlibWidget
from matplotlib.backend_bases import MouseEvent
import math
import numpy as np
from numpy.random import rand
from matplotlib.lines import Line2D
import bisect
from matplotlib.widgets import RectangleSelector
from pylab import *


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
                  3: "rectangle selection tool"
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
        self.xys = list(zip(self.xs, self.ys))
        # self.xys = sorted(self.xys, key=lambda x: x[0])

        self.lines = None
        self.points = None
        self.selected = None
        self.drag_i = None
        self.lastind = -1
        self.text = None

        self.rectangle_selector = RectangleSelector(self.axes, self.onselect, drawtype='box', useblit=True)
        self.rectangle_selector.set_active(False)

        # Connections and setup
        self.canvas.mpl_connect('button_press_event', self.on_click)
        self.canvas.mpl_connect('button_release_event', self.on_release)
        self.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.canvas.mpl_connect('key_press_event', self.toggle_rectangle_selector)

        # self.buttonshortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+O"), self)
        # # self.buttonshortcut.setKey(QtCore.Qt.Key_Q)
        # self.buttonshortcut.activated.connect(self.tulostele)
        self.canvas.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.canvas.setFocus()
        # self.canvas.mpl_connect('pick_event', self.onpick2)
        # self.canvas.mpl_connect('pick_event', self.onpick1)


        # This customizes the toolbar buttons
        self.__fork_toolbar_buttons()

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

        # self.axes.set_title('ToF Histogram\n\n')
        self.axes.set_ylabel(self.name_y_axis.title())
        self.axes.set_xlabel(self.name_x_axis.title())

        self.lines, = self.axes.plot(self.xs, self.ys, color="blue")
        self.points, = self.axes.plot(self.xs, self.ys, color="blue", marker="o", markersize=10, picker=5,
                                      linestyle="None")
        self.selected, = self.axes.plot(0, 0, marker="o", markersize=10, linestyle="None",
                                        color='yellow', visible=False)

        # self.axes.set_xlim(-10, 110)
        # self.axes.set_ylim(-10, 110)
        self.axes.autoscale(enable=False)
        # self.text = self.fig.text(0.1, 0.9, "Mode: Point editing",
        #                           transform=self.fig.transFigure, va="top", ha="left")

        # Remove axis ticks and draw
        self.remove_axes_ticks()
        self.canvas.draw()

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

        self.rectangle_select_button = QtWidgets.QToolButton(self)
        self.rectangle_select_button.clicked.connect(self.toggle_rectangle_selector)
        self.rectangle_select_button.setCheckable(True)
        # Temporary icon
        self.__icon_manager.set_icon(self.rectangle_select_button, "depth_profile_lim_all.svg")
        self.rectangle_select_button.setToolTip("Rectangle select")
        self.mpl_toolbar.addWidget(self.rectangle_select_button)
        #
        # # Selection undo button
        # self.elementSelectUndoButton = QtWidgets.QToolButton(self)
        # self.elementSelectUndoButton.clicked.connect(self.undo_point)
        # self.__icon_manager.set_icon(self.elementSelectUndoButton, "undo.png")
        # self.elementSelectUndoButton.setToolTip(
        #     "Undo last point in open selection")
        # self.elementSelectUndoButton.setEnabled(False)
        # self.mpl_toolbar.addWidget(self.elementSelectUndoButton)
        # self.mpl_toolbar.addSeparator()
        #
        # # Selection delete button
        # self.elementSelectDeleteButton = QtWidgets.QToolButton(self)
        # self.elementSelectDeleteButton.setEnabled(False)
        # self.elementSelectDeleteButton.clicked.connect(self.remove_selected)
        # self.__icon_manager.set_icon(self.elementSelectDeleteButton, "del.png")
        # self.elementSelectDeleteButton.setToolTip("Delete selected selection")
        # self.mpl_toolbar.addWidget(self.elementSelectDeleteButton)
        # self.mpl_toolbar.addSeparator()

    # def find_clicked_point(self, x, y):
    #     """ If an existing point is clicked, return it.
    #     Args:
    #         x: x coordinate of click
    #         y: y coordinate of click
    #     """
    #     # xlim = self.axes.get_xlim()
    #     # xrange = xlim[1] - xlim[0]
    #     # ylim = self.axes.get_ylim()
    #     # yrange = ylim[1]-ylim[0]
    #
    #     # Display coordinates (relative to the screen)
    #     x_y_disp = self.axes.transData.transform((x, y))
    #     for p in self.elements["He"]:
    #         elem_x_y_disp = self.axes.transData.transform((p[0], p[1]))
    #         if self.distance(elem_x_y_disp[0], elem_x_y_disp[1], x_y_disp[0], x_y_disp[1]) < 20:
    #             # if abs(elem_x_y_disp[0] - x_y_disp[0]) < 100 and abs(elem_x_y_disp[1] - x_y_disp[1]) < 100:
    #             return p
    #     return None

    def on_click(self, event):
        """ On click event above graph.

        Args:
            event: A MPL MouseEvent
        """
        # TODO: Implement removing points
        # TODO: Implement a separate selection mode for moving multiple points or a line
        # TODO: Check that e.g. zoom tool isn't on
        # Only inside the actual graph axes, else do nothing.
        if self.rectangle_selector.active:
            return
        if event.inaxes != self.axes:
            return
        contains, info = self.points.contains(event)
        if contains:
            i = info['ind'][0]
            self.lastind = i
            self.update_plot()
            self.drag_i = i
        else:
            line_contains, line_info = self.lines.contains(event)
            if line_contains:
                x = event.xdata
                y = event.ydata
                self.add_point_on_click(x, y)

    def add_point_on_click(self, x, y=None):
        """ Adds a point to the list when clicked close enough to a line. """
        i = bisect.bisect(self.xs, x)
        self.xs.insert(i, x)
        self.ys.insert(i, y)

        self.update_plot()

    # def add_point_on_motion(self, x, y=None):
    #     """ Adds a point to the list when it is moved.
    #     """
    #     # TODO: Maybe there could be an index as a parameter, so we know the place of the point immediately?
    #     if isinstance(x, MouseEvent):
    #         x, y = x.xdata, x.ydata
    #     point = [x, y]
    #     # If the x coord of the point to be added is less than the x coord of
    #     # any of the existing points, this loop catches it
    #     for index, p in enumerate(self.elements["He"]):
    #         if p[0] > x:
    #             self.elements["He"].insert(index, point)
    #             return point
    #     # Otherwise the point is added to the end of the list
    #     self.elements["He"].append(point)
    #     return point

    def update_plot(self):
        """ Updates point data and redraws the plot. """
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

        # TODO: Make a separate variable for selected point coordinates. If it's empty, hide the plot.
        if self.lastind != -1:
            self.selected.set_visible(True)
            self.selected.set_data(self.xs[dataind], self.ys[dataind])
        # self.text.set_text('selected: %d' % dataind)

        self.fig.canvas.draw()

    # def line_picker(self, line, mouseevent):
    #     """
    #     find the points within a certain distance from the mouseclick in
    #     data coords and attach some extra attributes, pickx and picky
    #     which are the data points that were picked
    #     """
    #     if mouseevent.xdata is None:
    #         return False, dict()
    #     xdata = line.get_xdata()
    #     ydata = line.get_ydata()
    #     maxd = self.fig.dpi / 72. * 5
    #     d = np.sqrt((xdata - mouseevent.xdata)**2. + (ydata - mouseevent.ydata)**2.)
    #
    #     ind = np.nonzero(np.less_equal(d, maxd))
    #     if len(ind):
    #         pickx = np.take(xdata, ind)
    #         picky = np.take(ydata, ind)
    #         props = dict(ind=ind, pickx=pickx, picky=picky)
    #         return True, props
    #     else:
    #         return False, dict()
    #
    # def onpick2(self, event):
    #     print('onpick2 line:', event.pickx, event.picky)
    #     self.selected_x = event.pickx
    #     self.selected_y = event.picky
    #
    # def onpick1(self, event):
    #     if event.artist != self.points:
    #         return True
    #
    #     N = len(event.ind)
    #     if not N:
    #         return True
    #
    #     print(self.xs[event.ind], self.ys[event.ind])
    #     # the click locations
    #     x = event.mouseevent.xdata
    #     y = event.mouseevent.ydata
    #
    #     distances = np.hypot(x - self.xs[event.ind], y - self.ys[event.ind])
    #     indmin = distances.argmin()
    #     dataind = event.ind[indmin]
    #
    #     self.lastind = dataind
    #     self.update_plot()
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
        if self.rectangle_selector.active:
            return
        if event.inaxes != self.axes:
            return
        if self.drag_i is None:
            return
        if self.drag_i == 0:
            if len(self.xs) == 1:
                self.update_location(event)
            elif event.xdata < self.xs[self.drag_i + 1]:
                self.update_location(event)
        elif self.drag_i == len(self.xs) - 1:
            if len(self.xs) == 1:
                self.update_location(event)
            elif event.xdata > self.xs[self.drag_i - 1]:
                self.update_location(event)
        elif self.xs[self.drag_i - 1] < event.xdata < self.xs[self.drag_i + 1]:
                self.update_location(event)

    def update_location(self, event):
        self.xs[self.drag_i] = event.xdata
        self.ys[self.drag_i] = event.ydata
        self.update_plot()

    # def remove_point(self, point):
    #     """ Removes a point from the list. """
    #     if point in self.elements["He"]:
    #         self.elements["He"].remove(point)

    def on_release(self, event):
        """ callback method for mouse release event

        Args:
            event: A MPL MouseEvent
        """
        if self.rectangle_selector.active:
            return
        # TODO: If no point is selected, don't update plot
        if event.button == 1:
            self.drag_i = None
            self.update_plot()

    def onselect(self, eclick, erelease):
        'eclick and erelease are matplotlib events at press and release'
        extents = self.rectangle_selector.extents
        xmin = extents[0]
        xmax = extents[1]
        ymin = extents[2]
        ymax = extents[3]
        selected_xs = []
        selected_ys = []
        for xy in self.xys:
            if xmin <= xy[0] <= xmax and ymin <= xy[1] < ymax:
                selected_xs.append(xy[0])
                selected_ys.append(xy[1])
        if selected_xs and selected_ys:
            self.selected.set_data(selected_xs, selected_ys)
            self.selected.set_visible(True)
            self.fig.canvas.draw()
        else:
            self.selected.set_visible(False)
            self.fig.canvas.draw()

    # def toggle_selector_old(self, event):
    #     if event.key in ['S', 's'] and self.selector.active:
    #         self.selector.set_active(False)
    #         self.fig.canvas.draw()
    #     elif event.key in ['S', 's'] and not self.selector.active:
    #         self.selector.set_active(True)
    #         self.selected.set_visible(False)
    #         self.text.set_text("Mode: Rectangle select")
    #         self.fig.canvas.draw()

    def toggle_rectangle_selector(self):
        '''Enable rectangle selection.
        '''
        if self.rectangle_selector.active:
            self.rectangle_selector.set_active(False)
        else:
            self.rectangle_selector.set_active(True)
            self.selected.set_visible(False)

        if self.rectangle_select_button.isChecked():  # if button is enabled
            # One cannot choose selection while selecting
            self.__toggle_drag_zoom()
            self.mpl_toolbar.mode_tool = 3
            str_tool = self.tool_modes[self.mpl_toolbar.mode_tool]
            self.__tool_label.setText(str_tool)
            self.mpl_toolbar.mode = str_tool
        else:
            self.__tool_label.setText("")
            self.mpl_toolbar.mode_tool = 0
            self.mpl_toolbar.mode = ""
            self.canvas.draw_idle()
