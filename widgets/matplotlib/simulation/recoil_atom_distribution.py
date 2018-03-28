# coding=utf-8
"""
Created on 1.3.2018
Updated on 28.3.2018
"""
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"

from matplotlib import cm
from matplotlib.colors import LogNorm
import matplotlib.lines as lines
from PyQt5 import QtCore, QtWidgets, QtGui

from widgets.matplotlib.base import MatplotlibWidget
from matplotlib.widgets import RectangleSelector
import numpy.random


class Point:
    def __init__(self, xy):
        self._x = xy[0]
        self._y = xy[1]

    def __lt__(self, other):
        return self.get_x() < other.get_x()

    def get_coordinates(self):
        return self._x, self._y

    def get_x(self):
        return self._x

    def get_y(self):
        return self._y

    def set_coordinates(self, xy):
        self._x = xy[0]
        self._y = xy[1]


class Element:
    def __init__(self, name, points):
        self._name = name
        self._points = sorted(points)
        # sorted_points = sorted(list(zip(xs, ys)), key=lambda x: x[0])

    def _sort_points(self):
        self._points.sort()
        self._xs = [point.get_x() for point in self._points]
        self._ys = [point.get_y() for point in self._points]

    def get_xs(self):
        return [point.get_x() for point in self._points]

    def get_ys(self):
        return [point.get_y() for point in self._points]

    def get_name(self):
        return self.name

    def get_point_i(self, i):
        return self._points[i]

    def get_points(self):
        return self._points

    # def set_xs(self, xs):
    #     self._xs = xs
    #
    # def set_ys(self, ys):
    #     self._ys = ys

    def set_point(self, i, point):
        self._points[i] = point
        self._sort_points()

    def set_points(self, points):
        self._points = sorted(points)

    def add_point(self, point):
        self._points.append(point)
        self._sort_points()

    def remove_point_i(self, i):
        del self._points[i]

    def remove_point(self, point):
        self._points.remove(point)


# xs = (100 * numpy.random.rand(20)).tolist()
# ys = (100 * numpy.random.rand(20)).tolist()
# xys = list(zip(xs, ys))
# points = []
# for xy in xys:
#     points.append(Point(xy))
# elements = [Element("He", points)]
# coords = []
# for point in elements[0].get_points():
#     coords.append(point.get_point())
# print(coords)
# elements[0].add_point((25, 10))
# coords2 = []
# for point in elements[0].get_points():
#     coords2.append(point.get_point())
# print(coords2)
# print(elements[0].get_xs())

class RecoilAtomDistributionWidget(MatplotlibWidget):
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

    def __init__(self, parent, icon_manager):
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
        self.__icon_manager = icon_manager

        # self.list_points = []
        # self.elements = { "He": [[0.00, 50.00], [50.00, 50.00]] }
        # self.xs.sort()
        # self.xys = sorted(self.xys, key=lambda x: x[0])
        self.xs = (100 * numpy.random.rand(20)).tolist()
        self.ys = (100 * numpy.random.rand(20)).tolist()
        self.xys = list(zip(self.xs, self.ys))
        self.points = []
        for xy in self.xys:
            self.points.append(Point(xy))

        self.elements = [Element("He", self.points)]

        self.lines = None
        self.markers = None
        self.selected = None
        self.drag_i = None
        self.selected_points = []
        self.lastind = -1
        self.text = None

        self.rectangle_selector = RectangleSelector(self.axes, self.onselect, drawtype='box', useblit=True)
        self.rectangle_selector.set_active(False)

        # Connections and setup
        self.canvas.mpl_connect('button_press_event', self.on_click)
        self.canvas.mpl_connect('button_release_event', self.on_release)
        self.canvas.mpl_connect('motion_notify_event', self.on_motion)
        # self.canvas.mpl_connect('key_press_event', self.handle_key_press)


        # self.buttonshortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+O"), self)
        # self.buttonshortcut.setKey(QtCore.Qt.Key_Q)
        # self.buttonshortcut.activated.connect(self.tulostele)

        self.canvas.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.canvas.setFocus()
        # self.canvas.mpl_connect('pick_event', self.onpick2)
        # self.canvas.mpl_connect('pick_event', self.onpick1)


        # This customizes the toolbar buttons
        self.__fork_toolbar_buttons()

        # Put all x-coordinates to one list and all y-coordinates to one list.
        # There are needed later when we calculates the range of the axes.
        # self.__x_data = []
        # self.__y_data = []
        # for points in self.elements.values():
        #     for point in points:
        #         self.__x_data.append(point[0])
        #         self.__y_data.append(point[1])

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
        # line1 = self.elements["He"]
        # line1_xs, line1_ys = zip(*line1) # Divide the coordinate data into x and y data
        # self.list_points.append(Point(self, line1_xs[0], line1_ys[0], 1))
        # self.list_points.append(Point(self, line1_xs[1], line1_ys[1], 1))

        # self.axes.set_title('ToF Histogram\n\n')
        self.axes.set_ylabel(self.name_y_axis.title())
        self.axes.set_xlabel(self.name_x_axis.title())

        self.lines, = self.axes.plot(self.elements[0].get_xs(), self.elements[0].get_ys(), color="blue")
        self.markers, = self.axes.plot(self.elements[0].get_xs(), self.elements[0].get_ys(), color="blue", marker="o", markersize=10, picker=5,
                                       linestyle="None")
        self.selected, = self.axes.plot(0, 0, marker="o", markersize=10, linestyle="None",
                                        color='yellow', visible=False)

        # self.axes.set_xlim(-10, 110)
        # self.axes.set_ylim(-10, 110)
        self.axes.autoscale(enable=False)
        # self.text = self.fig.text(0.1, 0.9, "Selected point coordinates:",
        #                           transform=self.fig.transFigure, va="top", ha="left")

        # Remove axis ticks and draw
        self.remove_axes_ticks()
        self.canvas.draw()

    # def __fix_axes_range(self, axes_range, compression):
    #     """Fixes axes' range to be divisible by compression.
    #     """
    #     rmin, rmax = axes_range
    #     mod = (rmax - rmin) % compression
    #     if mod == 0:  # Everything is fine, return.
    #         return axes_range
    #     # More data > less data
    #     rmax += compression - mod
    #     return rmin, rmax
    #
    # def __set_y_axis_on_right(self, yes):
    #     if yes:
    #         # self.axes.spines['left'].set_color('none')
    #         self.axes.spines['right'].set_color('black')
    #         self.axes.yaxis.tick_right()
    #         self.axes.yaxis.set_label_position("right")
    #     else:
    #         self.axes.spines['left'].set_color('black')
    #         # self.axes.spines['right'].set_color('none')
    #         self.axes.yaxis.tick_left()
    #         self.axes.yaxis.set_label_position("left")
    #
    # def __set_x_axis_on_top(self, yes):
    #     if yes:
    #         # self.axes.spines['bottom'].set_color('none')
    #         self.axes.spines['top'].set_color('black')
    #         self.axes.xaxis.tick_top()
    #         self.axes.xaxis.set_label_position("top")
    #     else:
    #         self.axes.spines['bottom'].set_color('black')
    #         # self.axes.spines['top'].set_color('none')
    #         self.axes.xaxis.tick_bottom()
    #         self.axes.xaxis.set_label_position("bottom")

    def __toggle_tool_drag(self):
        if self.__button_drag.isChecked():
            self.mpl_toolbar.mode_tool = 1
        else:
            self.mpl_toolbar.mode_tool = 0
            # self.elementSelectionButton.setChecked(False)
        self.rectangle_select_button.setChecked(False)
        self.rectangle_selector.set_active(False)
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
        self.rectangle_select_button.setChecked(False)
        self.rectangle_selector.set_active(False)
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
        # super().fork_toolbar_buttons()
        self.mpl_toolbar.mode_tool = 0
        self.__tool_label = self.mpl_toolbar.children()[24]
        self.__button_drag = self.mpl_toolbar.children()[12]
        self.__button_zoom = self.mpl_toolbar.children()[14]
        self.__button_drag.clicked.connect(self.__toggle_tool_drag)
        self.__button_zoom.clicked.connect(self.__toggle_tool_zoom)

        # Make own buttons
        self.mpl_toolbar.addSeparator()

        # Rectangle selector button
        self.rectangle_select_button = QtWidgets.QToolButton(self)
        self.rectangle_select_button.clicked.connect(self.toggle_rectangle_selector)
        self.rectangle_select_button.setCheckable(True)
        # TODO: Temporary icon
        self.__icon_manager.set_icon(self.rectangle_select_button, "depth_profile_lim_all.svg")
        self.rectangle_select_button.setToolTip("Rectangle select")
        self.mpl_toolbar.addWidget(self.rectangle_select_button)

        # Point removal button
        self.point_remove_button = QtWidgets.QToolButton(self)
        self.point_remove_button.clicked.connect(self.remove_points)
        # TODO: Temporary icon
        self.__icon_manager.set_icon(self.point_remove_button, "del.png")
        self.point_remove_button.setToolTip("Remove selected points")
        self.mpl_toolbar.addWidget(self.point_remove_button)


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
        # TODO: Implement a separate selection mode for moving multiple points or a line
        # Don't do anything if rectangle selector, drag tool or zoom tool is active.
        if self.rectangle_selector.active or self.mpl_toolbar.children()[12].isChecked() \
                or self.mpl_toolbar.children()[14].isChecked():
            return
        # Only inside the actual graph axes, else do nothing.
        if event.inaxes != self.axes:
            return
        if event.button == 1:  # Left click
            contains, info = self.markers.contains(event)
            if contains:
                i = info['ind'][0]
                self.selected_points = [self.elements[0].get_point_i(i)]
                # self.lastind = i
                self.update_plot()
                self.drag_i = i
            else:
                self.selected_points.clear()
                self.update_plot()
                line_contains, line_info = self.lines.contains(event)
                if line_contains:
                    x = event.xdata
                    y = event.ydata
                    self.add_point_on_click((x, y))
        # elif event.button == 3:  # Right click
        #     contains, info = self.markers.contains(event)
        #     if contains:
        #         i = info['ind'][0]
        #         self.remove_point(i)


    def add_point_on_click(self, point):
        """ Adds a point to the list when clicked close enough to a line. """
        new_point = Point(point)
        self.elements[0].add_point(new_point)
        self.selected_points = [new_point]
        # i = bisect.bisect(self.xs, x)
        # self.xs.insert(i, x)
        # self.ys.insert(i, y)

        self.update_plot()

    # def add_point_on_motion(self, x, y=None):
    #     """ Adds a point to the list when it is moved.
    #     """
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

        # if self.lastind is None:
        #     return
        #
        # dataind = self.lastind

        self.markers.set_data(self.elements[0].get_xs(), self.elements[0].get_ys())
        self.lines.set_data(self.elements[0].get_xs(), self.elements[0].get_ys())

        # if self.lastind != -1:
        #     self.selected.set_visible(True)
        #     self.selected.set_data(self.elements[0].get_point(dataind).get_x(),
        #                            self.elements[0].get_point(dataind).get_y())
        if self.selected_points:
            self.selected.set_visible(True)
            selected_xs = []
            selected_ys = []
            for point in self.selected_points:
                selected_xs.append(point.get_x())
                selected_ys.append(point.get_y())
            self.selected.set_data(selected_xs, selected_ys)
            # self.text.set_text('selected: %d %d' % (self.selected_points[0].get_coordinates()[0],
            #                                     self.selected_points[0].get_coordinates()[1]))
        else:
            self.selected.set_visible(False)

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
        if self.rectangle_selector.active or self.mpl_toolbar.children()[12].isChecked() \
                or self.mpl_toolbar.children()[14].isChecked():
            return
        if event.inaxes != self.axes:
            return
        if self.drag_i is None:
            return
        if self.drag_i == 0:
            if len(self.elements[0].get_points()) == 1:
                self.update_location(event)
            elif event.xdata < self.elements[0].get_point_i(self.drag_i + 1).get_x():
                self.update_location(event)
        elif self.drag_i == len(self.elements[0].get_points()) - 1:
            if len(self.elements[0].get_points()) == 1:
                self.update_location(event)
            elif event.xdata > self.elements[0].get_point_i(self.drag_i - 1).get_x():
                self.update_location(event)
        elif self.elements[0].get_point_i(self.drag_i - 1).get_x() \
                < event.xdata < self.elements[0].get_point_i(self.drag_i + 1).get_x():
                self.update_location(event)

    def update_location(self, event):
        self.elements[0].get_point_i(self.drag_i).set_coordinates((event.xdata, event.ydata))
        # print(self.drag_i)
        # print(self.elements[0].get_point(self.drag_i).get_coordinates())
        self.update_plot()

    def remove_points(self):
        if len(self.elements[0].get_points()) - len(self.selected_points) < 2:
            # TODO: Add an error message text label
            print("There must always be at least two points")
        else:
            for sel_point in self.selected_points:
                self.elements[0].remove_point(sel_point)
            self.selected_points.clear()
            self.update_plot()

    def on_release(self, event):
        """ callback method for mouse release event

        Args:
            event: A MPL MouseEvent
        """
        if self.rectangle_selector.active or self.mpl_toolbar.children()[12].isChecked() \
                or self.mpl_toolbar.children()[14].isChecked():
            return
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
        sel_xs = []
        sel_ys = []
        sel_points = []
        for point in self.elements[0].get_points():
            if xmin <= point.get_x() <= xmax and ymin <= point.get_y() < ymax:
                sel_xs.append(point.get_x())
                sel_ys.append(point.get_y())
                sel_points.append(point)
        self.selected_points = sel_points
        self.update_plot()

    def toggle_rectangle_selector(self):
        '''Enable rectangle selection.
        '''
        if self.rectangle_selector.active:
            self.__tool_label.setText("")
            self.mpl_toolbar.mode_tool = 0
            self.mpl_toolbar.mode = ""
            self.rectangle_selector.set_active(False)
            self.rectangle_select_button.setChecked(False)
            self.canvas.draw_idle()
        else:
            self.__toggle_drag_zoom()
            self.mpl_toolbar.mode_tool = 3
            str_tool = self.tool_modes[self.mpl_toolbar.mode_tool]
            self.__tool_label.setText(str_tool)
            self.mpl_toolbar.mode = str_tool
            self.rectangle_selector.set_active(True)
            self.rectangle_select_button.setChecked(True)
            self.canvas.draw_idle()
