# coding=utf-8
"""
Created on 18.4.2013
Updated on 27.11.2018

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2013-2018 Jarkko Aalto, Severi Jääskeläinen, Samuel Kaiponen,
Timo Konu, Samuli Kärkkäinen, Samuli Rahkonen, Miika Raunio, Heta Rekilä and
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
__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen \n " \
             "Samuli Rahkonen \n Miika Raunio \n Severi Jääskeläinen \n " \
             "Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"
__version__ = "2.0"

import os
from pathlib import Path
import modules.math_functions as mf
import modules.general_functions as gf

import widgets.gui_utils as gutils

from modules.enums import ToFEColorScheme
from modules.measurement import Measurement
from dialogs.energy_spectrum import EnergySpectrumWidget
from dialogs.graph_settings import TofeGraphSettingsWidget
from dialogs.measurement.depth_profile import DepthProfileWidget
from dialogs.measurement.element_losses import ElementLossesWidget
from dialogs.measurement.selection import SelectionSettingsDialog
import dialogs.file_dialogs as fdialogs

from matplotlib import cm
from matplotlib.colors import LogNorm

from PyQt5 import QtCore
from PyQt5 import QtWidgets

from widgets.matplotlib.base import MatplotlibWidget
from widgets.gui_utils import StatusBarHandler
from widgets.matplotlib import mpl_utils

import numpy as np
from PIL import Image

class MatplotlibHistogramWidget(MatplotlibWidget):
    """Matplotlib histogram widget, used to graph "bananas" (ToF-E).
    """
    MAX_BIN_COUNT = 8000
    selectionsChanged = QtCore.pyqtSignal("PyQt_PyObject")
    saveCuts = QtCore.pyqtSignal("PyQt_PyObject")

    tool_modes = {0: "",
                  1: "pan/zoom",  # Matplotlib's drag
                  2: "zoom rect",  # Matplotlib's zoom
                  3: "selection tool",
                  4: "selection select tool"
                  }

    def __init__(self, parent, measurement: Measurement, icon_manager,
                 statusbar=None):
        """Inits histogram widget

        Args:https://www.stack.nl/~dimitri/doxygen/manual/starting.html#step2
            parent: A TofeHistogramWidget class object.
            measurement: a Measurement object.
            icon_manager: IconManager class object.
            icon_manager: An iconmanager class object.
        """
        super().__init__(parent)
        self.canvas.manager.set_title("ToF-E Histogram")
        self.axes.fmt_xdata = lambda x: "{0:1.0f}".format(x)
        self.axes.fmt_ydata = lambda y: "{0:1.0f}".format(y)
        self.__icon_manager = icon_manager
        self.parent = parent
        self.statusbar = statusbar
        
        # Set default filename for saving figure
        default_filename = "ToF-E_Histogram_" + measurement.name
        self.canvas.get_default_filename = lambda: default_filename 

        # Connections and setup
        self.canvas.mpl_connect('button_press_event', self.on_click)
        self.canvas.mpl_connect('motion_notify_event', self.__on_motion)
        self.__fork_toolbar_buttons()

        self.measurement = measurement
        self.__x_data = [x[0] for x in self.measurement.data]
        self.__y_data = [x[1] for x in self.measurement.data]

        self.__x_data_max = max(self.__x_data) # max x-value of data
        self.__y_data_max = max(self.__y_data) # max y-value of data
        self.__x_data_min = min(self.__x_data)  # min x-value of data
        self.__y_data_min = min(self.__y_data)  # min y-value of data

        # Manually setting the limits for data
        self.axes.set_xlim(0, max(self.__x_data))
        self.axes.set_ylim(0, max(self.__y_data))

        # 2D histogram image and histogram
        self.__2d_hist = None # 2D histogram
        self.__2d_hist_im = None # image of histogram
        self.__2d_hist_cx = None # x-compress value, used to trigger recomputing histogram
        self.__2d_hist_cy = None # y-compress value, used to trigger recomputing histogram
        self.__2d_hist_tr = False # histogram axis transposed, used to trigger recompute

        # Variables
        self.__inverted_Y = False
        self.__inverted_X = False
        self.__transposed = False
        self.__inited = False
        self.__range_mode_automated = False

        # Get settings from global settings
        self.__global_settings = self.main_frame.measurement.request\
            .global_settings
        self.invert_Y = self.__global_settings.get_tofe_invert_y()
        self.invert_X = self.__global_settings.get_tofe_invert_x()
        self.transpose_axes = self.__global_settings.get_tofe_transposed()
        self.color_scheme = self.__global_settings.get_tofe_color()
        self.compression_x = self.__global_settings.get_tofe_compression_x()
        self.compression_y = self.__global_settings.get_tofe_compression_y()
        self.axes_range_mode = self.__global_settings.get_tofe_bin_range_mode()
        self.axes_range = (self.__global_settings.get_tofe_bin_range_x(),
                           self.__global_settings.get_tofe_bin_range_y())

        self.name_y_axis = "Energy (Ch)"
        self.name_x_axis = "time of flight (Ch)"

        self.on_draw()

    def on_draw(self):
        """Draw method for matplotlib.
        """
        # Values for zoom
        x_min, x_max = self.axes.get_xlim()
        y_min, y_max = self.axes.get_ylim()

        x_data = self.__x_data
        y_data = self.__y_data

        # Transpose
        if self.transpose_axes:
            x_data, y_data = y_data, x_data  # Always transpose data if checked.
            if not self.__transposed:
                self.__transposed = True
                self.measurement.selector.transpose(True)
                # Switch axes names
                self.name_x_axis, self.name_y_axis = (self.name_y_axis,
                                                      self.name_x_axis)
                # Switch min & max values
                x_min, x_max, y_min, y_max = y_min, y_max, x_min, x_max
                # Switch inverts
                self.invert_X, self.invert_Y = self.invert_Y, self.invert_X
        if not self.transpose_axes and self.__transposed:
            self.__transposed = False
            self.measurement.selector.transpose(False)
            # Switch axes names
            self.name_x_axis, self.name_y_axis \
                = self.name_y_axis, self.name_x_axis
            # Switch min & max values
            x_min, x_max, y_min, y_max = y_min, y_max, x_min, x_max
            # Switch inverts
            self.invert_X, self.invert_Y = self.invert_Y, self.invert_X

        # Clear old stuff
        self.axes.clear()

        # Check bin counts and axes ranges
        # If bin count too high -> it will crash the program, use 3500
        # If 10 000, tofe_65 example can have compression as 1, but REALLY
        # slow. Usually, bin count around 8000
        if self.axes_range_mode == 1:
            # Manual axe range mode
            bin_counts, msg = mf.calculate_bin_counts(
                self.axes_range, self.compression_x, self.compression_y,
                max_count=MatplotlibHistogramWidget.MAX_BIN_COUNT
            )
            axes_range = self.axes_range
        else:
            # Automatic mode
            bin_counts, msg = mf.calculate_bin_counts(
                [x_data, y_data], self.compression_x, self.compression_y,
                max_count=MatplotlibHistogramWidget.MAX_BIN_COUNT)
            axes_range = None

        if msg is not None:
            # Message is displayed when bin count was too high and had to be
            # lowered
            QtWidgets.QMessageBox.warning(
                self.parent, "Warning", msg,
                QtWidgets.QMessageBox.Ok,
                QtWidgets.QMessageBox.Ok)

        colormap = cm.get_cmap(self.color_scheme.value)
        
        self.axes.set_ylim([y_min, y_max])
        self.axes.set_xlim([x_min, x_max]) 

        # if changes in compress values, recompute 2d histogram and histogram image
        if (self.__2d_hist_cx != self.compression_x) \
                or (self.__2d_hist_cy != self.compression_y) or (self.transpose_axes != self.__2d_hist_tr):
            self.__2d_hist_cx = self.compression_x
            self.__2d_hist_cy = self.compression_y
            self.__2d_hist_tr = self.transpose_axes
            # Minimum and maximum values used to position image in plot
            self.__x_data_max = max(x_data)
            self.__y_data_max = max(y_data)
            self.__x_data_min = min(x_data)
            self.__y_data_min = min(y_data)
            self.__2d_hist = np.histogram2d(y_data, x_data,
                                            bins = (int(self.__y_data_max/self.__2d_hist_cy),int(self.__x_data_max/self.__2d_hist_cx)))
            # self.__2d_hist_im = Image.fromarray(np.uint8(cm.gist_gray_r(np.log(self.__2d_hist[0])/np.amax(np.log(self.__2d_hist[0]))) * 255))
            self.__2d_hist_im = Image.fromarray(np.uint8(255*self.__2d_hist[0]/np.amax(self.__2d_hist[0])))
            # self.axes.imshow(self.__2d_hist_im, extent=(self.__x_data_min,self.__x_data_max,self.__y_data_min, self.__y_data_max), origin='bottom')
        self.axes.imshow(self.__2d_hist_im, norm = LogNorm(), cmap='jet',
                         extent=(self.__x_data_min, self.__x_data_max, self.__y_data_min, self.__y_data_max),
                         origin='bottom', interpolation='none')

        self.__on_draw_legend()

        # Change zoom limits if compression factor was changed (or new graph).
        if not self.__range_mode_automated and self.axes_range_mode == 0 \
                or self.axes_range_mode == 1:
            # self.__range_mode_automated and self.axes_range_mode == 1
            tx_min, tx_max = self.axes.get_xlim()
            ty_min, ty_max = self.axes.get_ylim()
            # If user has zoomed the graph, change the home position to new max.
            # Else reset the graph to new ranges and clear zoom levels.
            if self.mpl_toolbar._views:
                self.mpl_toolbar._views[0][0] = (tx_min, tx_max, ty_min, ty_max)
            else:
                x_min, x_max = tx_min, tx_max
                y_min, y_max = ty_min, ty_max
                self.mpl_toolbar.update()
        self.__range_mode_automated = self.axes_range_mode == 0 
        
        self.measurement.draw_selection()
        
        # Invert axis
        if self.invert_Y and not self.__inverted_Y:
            self.axes.set_ylim(self.axes.get_ylim()[::-1])
            self.__inverted_Y = True
        elif not self.invert_Y and self.__inverted_Y:
            self.axes.set_ylim(self.axes.get_ylim()[::-1])
            self.__inverted_Y = False
        if self.invert_X and not self.__inverted_X:
            self.axes.set_xlim(self.axes.get_xlim()[::-1])
            self.__inverted_X = True
        elif not self.invert_X and self.__inverted_X:
            self.axes.set_xlim(self.axes.get_xlim()[::-1])
            self.__inverted_X = False
        # [::-1] is elegant reverse. Slice sequence with step of -1.
        # http://stackoverflow.com/questions/3705670/
        # best-way-to-create-a-reversed-list-in-python

        # self.axes.set_title('ToF Histogram\n\n')
        self.axes.set_ylabel(self.name_y_axis.title())
        self.axes.set_xlabel(self.name_x_axis.title())

        # Remove axis ticks and draw
        self.remove_axes_ticks()
        self.canvas.draw()

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

    def __on_draw_legend(self):
        self.axes.legend_ = None
        if not self.measurement.selector.selections:
            return
        if not self.__inited:  # Do this only once.
            self.fig.tight_layout(pad=0.5)
            box = self.axes.get_position()
            self.axes.set_position([box.x0,
                                    box.y0,
                                    box.width * 0.9,
                                    box.height])
            self.__inited = True
        selection_legend = {}

        # Get selections for legend
        for sel in self.measurement.selector.selections:
            rbs_string = ""
            element = sel.element
            if sel.type == "RBS":
                element = sel.element_scatter
                rbs_string = "*"
            sel.points.set_marker(None)  # Remove markers for legend.
            dirtyinteger = 0
            key_string = "{0}{1}".format(element.symbol, dirtyinteger)
            while key_string in selection_legend:
                key_string = "{0}{1}".format(element.symbol, dirtyinteger)
                dirtyinteger += 1

            if element.isotope:
                isotope_str = str(int(element.isotope))
                add = r"$^{" + isotope_str + "}$"
            else:
                isotope_str = str(round(element.get_st_mass()))
                add = ""

            label = add + element.symbol + rbs_string

            selection_legend[key_string] = (label, isotope_str, sel.points,
                                            element)

        # Sort legend text
        sel_text = []
        sel_points = []

        items = sorted(selection_legend.items(), key=lambda x: x[1][3])
        for item in items:
            # [0] is the key of the item.
            sel_text.append(item[1][0])
            sel_points.append(item[1][2])

        leg = self.axes.legend(sel_points,
                               sel_text,
                               loc=3,
                               bbox_to_anchor=(1, 0),
                               borderaxespad=0,
                               prop={'size': 12})
        for handle in leg.legendHandles:
            handle.set_linewidth(3.0)

        # Set the markers back to original.
        for sel in self.measurement.selector.selections:
            sel.points.set_marker(sel.LINE_MARKER)

    def __toggle_tool_drag(self):
        if self.__button_drag.isChecked():
            self.mpl_toolbar.mode_tool = 1
        else:
            self.mpl_toolbar.mode_tool = 0
            # self.elementSelectionButton.setChecked(False)
        # self.elementSelectUndoButton.setEnabled(False)
        self.elementSelectionSelectButton.setChecked(False)
        # self.measurement.purge_selection()
        # self.measurement.reset_select()
        self.canvas.draw_idle()

    def __toggle_tool_zoom(self):
        if self.__button_zoom.isChecked():
            self.mpl_toolbar.mode_tool = 2
        else:
            self.mpl_toolbar.mode_tool = 0
            # self.elementSelectionButton.setChecked(False)
        # self.elementSelectUndoButton.setEnabled(False)
        self.elementSelectionSelectButton.setChecked(False)
        # self.measurement.purge_selection()
        # self.measurement.reset_select()
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
        self.mpl_toolbar.mode_tool = 0
        self.__tool_label, self.__button_drag, self.__button_zoom = \
            mpl_utils.get_toolbar_elements(
                self.mpl_toolbar, drag_callback=self.__toggle_tool_drag,
                zoom_callback=self.__toggle_tool_zoom)

        # Make own buttons
        self.mpl_toolbar.addSeparator()
        self.elementSelectionButton = QtWidgets.QToolButton(self)
        self.elementSelectionButton.clicked.connect(
            self.enable_element_selection)
        self.elementSelectionButton.setCheckable(True)
        self.__icon_manager.set_icon(self.elementSelectionButton, "select.png")
        self.elementSelectionButton.setToolTip("Select element area")
        self.mpl_toolbar.addWidget(self.elementSelectionButton)

        # Selection undo button
        self.elementSelectUndoButton = QtWidgets.QToolButton(self)
        self.elementSelectUndoButton.clicked.connect(self.undo_point)
        self.__icon_manager.set_icon(self.elementSelectUndoButton, "undo.png")
        self.elementSelectUndoButton.setToolTip(
            "Undo last point in open selection")
        self.elementSelectUndoButton.setEnabled(False)
        self.mpl_toolbar.addWidget(self.elementSelectUndoButton)
        self.mpl_toolbar.addSeparator()

        # Element Selection selecting tool
        self.elementSelectionSelectButton = QtWidgets.QToolButton(self)
        self.elementSelectionSelectButton.clicked.connect(
            self.enable_selection_select)
        self.elementSelectionSelectButton.setCheckable(True)
        self.elementSelectionSelectButton.setEnabled(False)
        self.__icon_manager.set_icon(self.elementSelectionSelectButton,
                                     "selectcursor.png")
        self.elementSelectionSelectButton.setToolTip("Select element selection")
        self.mpl_toolbar.addWidget(self.elementSelectionSelectButton)

        # Selection delete button
        self.elementSelectDeleteButton = QtWidgets.QToolButton(self)
        self.elementSelectDeleteButton.setEnabled(False)
        self.elementSelectDeleteButton.clicked.connect(self.remove_selected)
        self.__icon_manager.set_icon(self.elementSelectDeleteButton, "del.png")
        self.elementSelectDeleteButton.setToolTip("Delete selected selection")
        self.mpl_toolbar.addWidget(self.elementSelectDeleteButton)
        self.mpl_toolbar.addSeparator()

        # Selection delete all -button
        self.elementSelectionDeleteButton = QtWidgets.QToolButton(self)
        self.elementSelectionDeleteButton.clicked.connect(
            self.remove_all_selections)
        self.__icon_manager.set_icon(self.elementSelectionDeleteButton,
                                     "delall.png")
        self.elementSelectionDeleteButton.setToolTip("Delete all selections")
        self.mpl_toolbar.addWidget(self.elementSelectionDeleteButton)

    def on_click(self, event):
        """On click event above graph.

        Args:
            event: A MPL MouseEvent
        """
        # Only inside the actual graph axes, else do nothing.
        if event.inaxes != self.axes:
            return
        # Allow dragging and zooming while selection is on but ignore clicks.
        if self.__button_drag.isChecked() or self.__button_zoom.isChecked():
            return
        cursor_location = [int(event.xdata), int(event.ydata)]
        # TODO: Possible switch to QtCore's mouseclicks
        # buttond = {QtCore.Qt.LeftButton  : 1,
        #       QtCore.Qt.MidButton   : 2,
        #       QtCore.Qt.RightButton : 3,
        #       # QtCore.Qt.XButton1 : None,
        #       # QtCore.Qt.XButton2 : None,
        #       }
        # However, QtCore.Qt.RightButton is actually middle button (wheel) on 
        # windows. So we'll use the numbers instead since they actually work
        # cross-platform just fine.
        # [DEBUG] Middle mouse button to debug current zoom levels or position.
        # if event.button == 2:
        #    print()
        #    print("VIEWS:")
        #    for item in self.mpl_toolbar._views:
        #        print("\t{0}".format(item))
        #    print("POSITIONS:")
        #    for item in self.mpl_toolbar._positions:
        #        print("\t{0}".format(item))
        if event.button == 1:  # Left click
            if self.elementSelectionSelectButton.isChecked():
                if self.measurement.selection_select(cursor_location) == 1:
                    # self.elementSelectDeleteButton.setChecked(True)
                    self.elementSelectDeleteButton.setEnabled(True)
                    self.canvas.draw_idle()
                    self.__on_draw_legend()
            # If selection is enabled:
            if self.elementSelectionButton.isChecked():
                if self.measurement.add_point(cursor_location, self.canvas) \
                        == 1:
                    self.__on_draw_legend()
                    self.__emit_selections_changed()
                self.canvas.draw_idle()  # Draw selection points
        if event.button == 3:  # Right click
            # Return if matplotlib tools are in use.
            if self.__button_drag.isChecked():
                return
            if self.__button_zoom.isChecked():
                return

            # If selection is enabled
            if self.elementSelectionButton.isChecked():
                if self.measurement.end_open_selection(self.canvas):
                    self.elementSelectionSelectButton.setEnabled(True)
                    self.canvas.draw_idle()
                    self.__on_draw_legend()
                    self.__emit_selections_changed()
                return  # We don't want menu to be shown also
            self.__context_menu(event, cursor_location)
            self.canvas.draw_idle()
            self.__on_draw_legend()

    def __emit_selections_changed(self):
        """Emits a 'selectionsChanged' signal with the selections list as a
        parameter.
        """
        # self.emit(QtCore.SIGNAL("selectionsChanged(PyQt_PyObject)"),
        # self.measurement.selector.selections)
        self.selectionsChanged.emit(self.measurement.selector.selections)

    def __emit_save_cuts(self):
        """Emits a 'selectionsChanged' signal with the selections list as a
        parameter.
        """
        # self.emit(QtCore.SIGNAL("saveCuts(PyQt_PyObject)"), self.measurement)
        self.saveCuts.emit(self.measurement.selector.selections)

    def __context_menu(self, event, cursor_location):
        menu = QtWidgets.QMenu(self)

        action = QtWidgets.QAction(self.tr("Graph Settings..."), self)
        action.triggered.connect(self.graph_settings_dialog)
        menu.addAction(action)

        if self.measurement.selection_select(cursor_location,
                                             highlight=False) == 1:
            action = QtWidgets.QAction(self.tr("Selection settings..."), self)
            action.triggered.connect(self.selection_settings_dialog)
            menu.addAction(action)

        menu.addSeparator()
        action = QtWidgets.QAction(self.tr("Load selections..."), self)
        action.triggered.connect(self.load_selections)
        menu.addAction(action)

        action = QtWidgets.QAction(self.tr("Save cuts"), self)
        action.triggered.connect(self.save_cuts)
        menu.addAction(action)
        if len(self.measurement.selector.selections) == 0:
            action.setEnabled(False)

        coords = self.canvas.geometry().getCoords()
        point = QtCore.QPoint(event.x, coords[3] - event.y - coords[1])
        # coords[1] from spacing
        menu.exec_(self.canvas.mapToGlobal(point))

    def graph_settings_dialog(self):
        """Show graph settings dialog.
        """
        TofeGraphSettingsWidget(self)

    def selection_settings_dialog(self):
        """Show selection settings dialog.
        """
        selection = self.measurement.selector.get_selected()
        SelectionSettingsDialog(selection)
        self.measurement.selector.auto_save()
        self.on_draw()
        self.__emit_selections_changed()

    def load_selections(self):
        """Show dialog to load selections.
        """
        filename = fdialogs.open_file_dialog(
            self, self.measurement.directory, "Load Element Selection",
            "Selection file (*.selections)")
        if filename is not None:
            sbh = StatusBarHandler(self.statusbar)
            sbh.reporter.report(40)

            self.measurement.load_selection(
                filename, progress=sbh.reporter.get_sub_reporter(
                    lambda x: 40 + 0.6 * x
                ))
            self.on_draw()
            self.elementSelectionSelectButton.setEnabled(True)

            sbh.reporter.report(100)

        self.__emit_selections_changed()

    def save_cuts(self):
        """Save measurement cuts.
        """
        sbh = StatusBarHandler(self.statusbar)
        self.measurement.save_cuts(progress=sbh.reporter)
        self.__emit_save_cuts()

    def enable_element_selection(self):
        """Enable element selection.
        """
        self.elementSelectUndoButton.setEnabled(
            self.elementSelectionButton.isChecked())
        if self.elementSelectionButton.isChecked():  # if button is enabled
            # One cannot choose selection while selecting
            self.elementSelectionSelectButton.setChecked(False)
            self.__toggle_drag_zoom()
            self.mpl_toolbar.mode_tool = 3
            str_tool = self.tool_modes[self.mpl_toolbar.mode_tool]
            self.__tool_label.setText(str_tool)
            self.mpl_toolbar.mode = str_tool
        else:
            self.__tool_label.setText("")
            self.mpl_toolbar.mode_tool = 0
            self.mpl_toolbar.mode = ""
            # Remove hanging selection points
            self.measurement.purge_selection()
            self.measurement.reset_select()
            self.canvas.draw_idle()
            self.__on_draw_legend()

    def enable_selection_select(self):
        """Enable selection selecting tool.
        """
        if self.elementSelectionSelectButton.isChecked():
            self.measurement.purge_selection()
            self.canvas.draw_idle()
            # One cannot make new selection while choosing selection
            self.elementSelectionButton.setChecked(False)
            self.elementSelectUndoButton.setEnabled(False)
            self.__toggle_drag_zoom()
            self.mpl_toolbar.mode_tool = 4
            str_tool = self.tool_modes[self.mpl_toolbar.mode_tool]
            self.__tool_label.setText(str_tool)
            self.mpl_toolbar.mode = str_tool
        else:
            self.elementSelectDeleteButton.setEnabled(False)
            self.__tool_label.setText("")
            self.mpl_toolbar.mode_tool = 0
            self.mpl_toolbar.mode = ""
            self.measurement.reset_select()
            self.__on_draw_legend()
            self.canvas.draw_idle()

    def remove_selected(self):
        """Remove selected selection.
        """
        reply = QtWidgets.QMessageBox.question(self, "Confirmation",
                                               "Deleting this selection will "
                                               "delete possible cut and split "
                                               "files.\n\n"
                                               "Are you sure you want to "
                                               "delete selected selection?",
                                               QtWidgets.QMessageBox.Yes |
                                               QtWidgets.QMessageBox.No |
                                               QtWidgets.QMessageBox.Cancel,
                                               QtWidgets.QMessageBox.Cancel)
        if reply == QtWidgets.QMessageBox.No or reply == \
                QtWidgets.QMessageBox.Cancel:
            return  # If clicked Yes, then continue normally

        self.measurement.remove_selected()
        self.measurement.reset_select()  # Nothing is now selected, reset colors
        self.measurement.selector.auto_save()

        self.measurement.save_cuts()
        # Update energy spectrum
        es_widget = self.parent.tab.energy_spectrum_widget
        if es_widget:
            delete_es = False
            for cut in es_widget.use_cuts:
                if not os.path.exists(cut):
                    delete_es = True
                    # Remove unnecessary tof_list and hist files
                    # TODO check that also no_foil.hist file is removed
                    cut_file_name = Path(cut).stem
                    gf.remove_matching_files(
                        self.measurement.get_energy_spectra_dir(),
                        exts={".hist", ".tof_list"},
                        filter_func=lambda f: Path(f).stem == cut_file_name)
            if delete_es:
                save_file = os.path.join(
                    self.measurement.get_energy_spectra_dir(),
                    es_widget.save_file)
                if os.path.exists(save_file):
                    os.remove(save_file)
                self.parent.tab.del_widget(es_widget)

        # Update depth profile
        delete_depth = False
        depth_widget = self.parent.tab.depth_profile_widget
        if depth_widget:
            for cut in depth_widget.use_cuts:
                if not os.path.exists(cut):
                    delete_depth = True
                    # TODO: Delete depth files
            if delete_depth:
                gf.remove_files(
                    self.measurement.get_depth_profile_dir() /
                    depth_widget.save_file
                )
                self.parent.tab.del_widget(depth_widget)

        # Update composition changes
        delete_comp = False
        comp_widget = self.parent.tab.elemental_losses_widget
        if comp_widget:
            for cut in comp_widget.checked_cuts:
                if not os.path.exists(cut):
                    delete_comp = True
            if delete_comp:
                gf.remove_files(
                    self.measurement.get_composition_changes_dir() /
                    comp_widget.save_file)
                self.parent.tab.del_widget(comp_widget)

        self.elementSelectDeleteButton.setEnabled(False)
        self.__on_draw_legend()
        self.canvas.draw_idle()
        self.__emit_selections_changed()

    def remove_all_selections(self):
        """Remove all selections.
        """
        reply = QtWidgets.QMessageBox.question(self,
                                               "Delete all selections",
                                               "If you delete all selections, "
                                               "all possible cut and split "
                                               "files will be deleted.\n\n"
                                               "Do you want to delete all "
                                               "selections anyway?",
                                               QtWidgets.QMessageBox.Yes,
                                               QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            self.measurement.remove_all()
            # Delete files and widgets
            self.measurement.save_cuts()

            es_widget = self.parent.tab.energy_spectrum_widget
            if es_widget:
                save_file = Path(
                    self.measurement.get_energy_spectra_dir(),
                    es_widget.save_file)
                self.parent.tab.del_widget(es_widget)
            else:
                save_file = Path(
                    self.measurement.get_energy_spectra_dir(),
                    EnergySpectrumWidget.save_file)
            gf.remove_files(save_file)

            comp_widget = self.parent.tab.elemental_losses_widget
            if comp_widget:
                save_file = Path(
                    self.measurement.get_composition_changes_dir(),
                    comp_widget.save_file)
                self.parent.tab.del_widget(comp_widget)
            else:
                save_file = Path(
                    self.measurement.get_composition_changes_dir(),
                    ElementLossesWidget.save_file)
            gf.remove_files(save_file)

            depth_widget = self.parent.tab.depth_profile_widget
            if depth_widget:
                save_file = Path(
                    self.measurement.get_depth_profile_dir(),
                    depth_widget.save_file)
                self.parent.tab.del_widget(depth_widget)
            else:
                save_file = Path(
                    self.measurement.get_depth_profile_dir(),
                    DepthProfileWidget.save_file)
            gf.remove_files(save_file)

            self.__on_draw_legend()
            self.canvas.draw_idle()
            self.__emit_selections_changed()

    def undo_point(self):
        """Undo last point in open selection.
        """
        self.measurement.undo_point()
        self.canvas.draw_idle()

    def show_yourself(self, dialog):
        """Show current ToF-E histogram settings in dialog.

        Args:
            dialog: A TofeGraphSettingsWidget.
        """
        gutils.fill_combobox(dialog.colorbox, ToFEColorScheme)
        dialog.color_scheme = self.color_scheme

        # Get values
        dialog.bin_x.setValue(self.compression_x)
        dialog.bin_y.setValue(self.compression_y)
        dialog.invert_x.setChecked(self.invert_X)
        dialog.invert_y.setChecked(self.invert_Y)
        dialog.axes_ticks.setChecked(self.show_axis_ticks)
        dialog.transposeAxesCheckBox.setChecked(self.transpose_axes)
        dialog.radio_range_auto.setChecked(self.axes_range_mode == 0)
        dialog.radio_range_manual.setChecked(self.axes_range_mode == 1)
        dialog.spin_range_x_min.setValue(self.axes_range[0][0])
        dialog.spin_range_x_max.setValue(self.axes_range[0][1])
        dialog.spin_range_y_min.setValue(self.axes_range[1][0])
        dialog.spin_range_y_max.setValue(self.axes_range[1][1])

    def __on_motion(self, event):
        """Function to handle hovering over matplotlib's graph.

        Args:
            event: A MPL MouseEvent
        """
        event.button = -1  # Fix for printing.
        if event.inaxes != self.axes:
            return
        if event.xdata is None and event.ydata is None:
            return

        in_selection = False
        points = 0
        point = [int(event.xdata), int(event.ydata)]
        if self.measurement.selector.axes_limits.is_inside(point):
            for selection in self.measurement.selector.selections:
                if selection.point_inside(point):
                    points = selection.get_event_count()
                    in_selection = True
                    break
        if in_selection:
            if self.mpl_toolbar.mode_tool:
                str_tool = self.tool_modes[self.mpl_toolbar.mode_tool]
                str_text = str_tool + "; points in selection: {0}".format(
                    points)
            else:
                str_text = "points in selection: {0}".format(points)
            self.mpl_toolbar.mode = str_text
        else:
            if self.mpl_toolbar.mode_tool:
                self.mpl_toolbar.mode = self.tool_modes[
                    self.mpl_toolbar.mode_tool]
            else:
                self.mpl_toolbar.mode = ""

    def sc_comp_inc(self, mode):
        """Shortcut to increase compression factor.
        
        Args:
            mode: An integer representing axis or axes to change.
        """
        if (mode == 0 or mode == 2) and self.compression_x < 3000:
            self.compression_x += 1
        if (mode == 1 or mode == 2) and self.compression_y < 3000:
            self.compression_y += 1
        self.on_draw()

    def sc_comp_dec(self, mode):
        """Shortcut to decrease compression factor.
        
        Args:
            mode: An integer representing axis or axes to change.
        """
        if (mode == 0 or mode == 2) and self.compression_x > 1:
            self.compression_x -= 1
        if (mode == 1 or mode == 2) and self.compression_y > 1:
            self.compression_y -= 1
        self.on_draw()
