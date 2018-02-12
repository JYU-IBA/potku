﻿# coding=utf-8
'''
Created on 18.4.2013
Updated on 30.8.2013

Potku is a graphical user interface for analyzation and 
visualization of measurement data collected from a ToF-ERD 
telescope. For physics calculations Potku uses external 
analyzation components.  
Copyright (C) Jarkko Aalto, Timo Konu, Samuli Kärkkäinen, Samuli Rahkonen and 
Miika Raunio

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
'''
__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen \n Samuli Rahkonen \n Miika Raunio"
__versio__ = "1.0"

from matplotlib import cm
from matplotlib.colors import LogNorm
from PyQt4 import QtCore, QtGui

from Dialogs.SelectionDialog import SelectionSettingsDialog
from Dialogs.GraphSettingsDialog import TofeGraphSettingsWidget
from Modules.Functions import open_file_dialog
from Widgets.MatplotlibWidget import MatplotlibWidget

class MatplotlibHistogramWidget(MatplotlibWidget):
    '''Matplotlib histogram widget, used to graph "bananas" (ToF-E).
    '''
    color_scheme = {"Default color":"jet",
                    "Greyscale":"Greys",
                    "Greyscale (inverted)":"gray"}
    
    tool_modes = { 0 : "",
                   1 : "pan/zoom",  # Matplotlib's drag
                   2 : "zoom rect",  # Matplotlib's zoom
                   3 : "selection tool",
                   4 : "selection select tool"
                  }
    
    def __init__(self, parent, measurement_data, masses, icon_manager):
        '''Inits histogram widget
        
        Args:
            parent: A TofeHistogramWidget class object.
            measurement_data: A list of data points.
            icon_manager: IconManager class object.
            masses: A masses class object.
            icon_manager: An iconmanager class object.
        '''
        super().__init__(parent)
        self.canvas.manager.set_title("ToF-E Histogram")
        self.axes.fmt_xdata = lambda x: "{0:1.0f}".format(x)
        self.axes.fmt_ydata = lambda y: "{0:1.0f}".format(y)
        self.__masses = masses
        self.__icon_manager = icon_manager
        
        # Connections and setup
        self.canvas.mpl_connect('button_press_event', self.on_click)
        self.canvas.mpl_connect('motion_notify_event', self.__on_motion)
        self.__fork_toolbar_buttons()     
           
        self.measurement = measurement_data 
        self.__x_data = [x[0] for x in self.measurement.data]
        self.__y_data = [x[1] for x in self.measurement.data]
        
        # Variables
        self.__inverted_Y = False
        self.__inverted_X = False
        self.__transposed = False        
        self.__inited__ = False 
        self.__range_mode_automated = False
        
        # Get settings from global settings
        self.__global_settings = self.main_frame.measurement.project.global_settings
        self.invert_Y = self.__global_settings.get_tofe_invert_y()
        self.invert_X = self.__global_settings.get_tofe_invert_x()
        self.transpose_axes = self.__global_settings.get_tofe_transposed()
        self.measurement.color_scheme = self.__global_settings.get_tofe_color()
        self.compression_x = self.__global_settings.get_tofe_compression_x()
        self.compression_y = self.__global_settings.get_tofe_compression_y()
        self.axes_range_mode = self.__global_settings.get_tofe_bin_range_mode()
        x_range = self.__global_settings.get_tofe_bin_range_x()
        y_range = self.__global_settings.get_tofe_bin_range_y()
        self.axes_range = [x_range, y_range]
        
        self.__x_data_min, self.__x_data_max = self.__fix_axes_range(
                                 (min(self.__x_data), max(self.__x_data)),
                                 self.compression_x)
        self.__y_data_min, self.__y_data_max = self.__fix_axes_range(
                                 (min(self.__y_data), max(self.__y_data)),
                                 self.compression_y)
         
        self.name_y_axis = "Energy (Ch)"
        self.name_x_axis = "time of flight (Ch)"

        self.on_draw()

        
    def on_draw(self):
        '''Draw method for matplotlib.
        '''
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
            self.name_x_axis, self.name_y_axis = self.name_y_axis, self.name_x_axis
            # Switch min & max values
            x_min, x_max, y_min, y_max = y_min, y_max, x_min, x_max
            # Switch inverts
            self.invert_X, self.invert_Y = self.invert_Y, self.invert_X
            
        self.axes.clear()  # Clear old stuff
        
        # Check values for graph
        axes_range = None
        bin_counts = ((self.__x_data_max - self.__x_data_min) / self.compression_x,
                      (self.__y_data_max - self.__y_data_min) / self.compression_y)
        if self.axes_range_mode == 1:
            axes_range = list(self.axes_range)
            axes_range[0] = self.__fix_axes_range(axes_range[0], self.compression_x)
            axes_range[1] = self.__fix_axes_range(axes_range[1], self.compression_y)
            x_length = axes_range[0][1] - axes_range[0][0]
            y_length = axes_range[1][1] - axes_range[1][0]
            bin_counts = (x_length / self.compression_x,
                          y_length / self.compression_y)

        # If bin count too high -> it will crash the program
        if bin_counts[0] > 3500:
            old_count = bin_counts[0]
            bin_counts = (3500, bin_counts[1])
            # TODO: Better location for message?
            print("[WARNING] {0}: X axis bin count ({2}) above 3500. {1}".format(
                       self.measurement.measurement_name,
                       "Limiting to prevent crash.",
                       old_count))  
        if bin_counts[1] > 3500:
            old_count = bin_counts[1]
            bin_counts = (bin_counts[0], 3500)
            print("[WARNING] {0}: Y axis bin count ({2}) above 3500. {1}".format(
                       self.measurement.measurement_name,
                       "Limiting to prevent crash.",
                       old_count))
        
        use_color_scheme = self.measurement.color_scheme
        color_scheme = MatplotlibHistogramWidget.color_scheme[use_color_scheme]
        colormap = cm.get_cmap(color_scheme)
        self.axes.hist2d(x_data,
                         y_data,
                         bins=bin_counts,
                         norm=LogNorm(),
                         range=axes_range,
                         cmap=colormap)
        
        self.__on_draw_legend()
        
        if (x_max > 0.09 and x_max < 1.01):  # This works..
            x_min, x_max = self.axes.get_xlim()
        if (y_max > 0.09 and y_max < 1.01):  #  or self.axes_range_mode
            y_min, y_max = self.axes.get_ylim()
            
        # Change zoom limits if compression factor was changed (or new graph).
        if (not self.__range_mode_automated and self.axes_range_mode == 0) \
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
        # print(self.axes.get_xlim())
        # Set limits accordingly
        self.axes.set_ylim([y_min, y_max])
        self.axes.set_xlim([x_min, x_max])
        
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
    
    
    def __on_draw_legend(self):
        self.axes.legend_ = None
        if not self.measurement.selector.selections:
            return
        if not self.__inited__:  # Do this only once.
            self.fig.tight_layout(pad=0.5)
            box = self.axes.get_position()
            self.axes.set_position([box.x0,
                                    box.y0,
                                    box.width * 0.9,
                                    box.height])
            self.__inited__ = True
        selection_legend = {}
        
        # Get selections for legend
        for sel in self.measurement.selector.selections:
            rbs_string = ""
            if sel.type == "ERD":
                element_object = sel.element
            elif sel.type == "RBS":
                element_object = sel.element_scatter
                rbs_string = "*"
            sel.points.set_marker(None)  # Remove markers for legend.
            dirtyinteger = 0
            key_string = "{0}{1}".format(element_object, dirtyinteger)
            while key_string in selection_legend.keys():
                dirtyinteger += 1
                key_string = "{0}{1}".format(element_object,
                                             dirtyinteger)
                
            element, isotope = element_object.get_element_and_isotope()
            label = r"$^{" + str(isotope) + "}$" + element + rbs_string
            mass = str(isotope)
            if not mass:
                mass = self.__masses.get_standard_isotope(element)
            else:
                mass = float(mass)
            selection_legend[key_string] = (label, mass, sel.points)
        
        # Sort legend text
        sel_text = []
        sel_points = []
        # keys = sorted(selection_legend.keys())
        items = sorted(selection_legend.items(), key=lambda x: x[1][1])
        for item in items:
            # [0] is the key of the item.
            sel_text.append(item[1][0])
            sel_points.append(item[1][2])

        leg = self.axes.legend(sel_points,
                               sel_text,
                               loc=3,
                               bbox_to_anchor=(1, 0),
                               borderaxespad=0,
                               prop={'size':12})
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
        super().fork_toolbar_buttons()
        self.mpl_toolbar.mode_tool = 0
        self.__tool_label = self.mpl_toolbar.children()[24]
        self.__button_drag = self.mpl_toolbar.children()[12]
        self.__button_zoom = self.mpl_toolbar.children()[14]
        self.__button_drag.clicked.connect(self.__toggle_tool_drag)
        self.__button_zoom.clicked.connect(self.__toggle_tool_zoom)
        
        # Make own buttons
        self.mpl_toolbar.addSeparator()
        self.elementSelectionButton = QtGui.QToolButton(self)
        self.elementSelectionButton.clicked.connect(self.enable_element_selection)
        self.elementSelectionButton.setCheckable(True)
        self.__icon_manager.set_icon(self.elementSelectionButton, "select.png")
        self.elementSelectionButton.setToolTip("Select element area")
        self.mpl_toolbar.addWidget(self.elementSelectionButton)
        
        # Selection undo button
        self.elementSelectUndoButton = QtGui.QToolButton(self)
        self.elementSelectUndoButton.clicked.connect(self.undo_point)
        self.__icon_manager.set_icon(self.elementSelectUndoButton, "undo.png")
        self.elementSelectUndoButton.setToolTip("Undo last point in open selection")
        self.elementSelectUndoButton.setEnabled(False)
        self.mpl_toolbar.addWidget(self.elementSelectUndoButton)
        self.mpl_toolbar.addSeparator()
        
        # Element Selection selecting tool
        self.elementSelectionSelectButton = QtGui.QToolButton(self)
        self.elementSelectionSelectButton.clicked.connect(
                                                      self.enable_selection_select)
        self.elementSelectionSelectButton.setCheckable(True)
        self.elementSelectionSelectButton.setEnabled(False)
        self.__icon_manager.set_icon(self.elementSelectionSelectButton,
                                   "selectcursor.png")
        self.elementSelectionSelectButton.setToolTip("Select element selection")
        self.mpl_toolbar.addWidget(self.elementSelectionSelectButton)
        
        # Selection delete button
        self.elementSelectDeleteButton = QtGui.QToolButton(self)
        self.elementSelectDeleteButton.setEnabled(False)
        self.elementSelectDeleteButton.clicked.connect(self.remove_selected)
        self.__icon_manager.set_icon(self.elementSelectDeleteButton, "del.png")
        self.elementSelectDeleteButton.setToolTip("Delete selected selection")
        self.mpl_toolbar.addWidget(self.elementSelectDeleteButton)
        self.mpl_toolbar.addSeparator()
        
        # Selection delete all -button
        self.elementSelectionDeleteButton = QtGui.QToolButton(self)
        self.elementSelectionDeleteButton.clicked.connect(
                                                      self.remove_all_selections)
        self.__icon_manager.set_icon(self.elementSelectionDeleteButton,
                                     "delall.png")
        self.elementSelectionDeleteButton.setToolTip("Delete all selections")
        self.mpl_toolbar.addWidget(self.elementSelectionDeleteButton)
        
        
    def on_click(self, event):
        '''On click event above graph.
        
        Args:
            event: A MPL MouseEvent
        '''
        # Only inside the actual graph axes, else do nothing.
        if event.inaxes != self.axes: 
            return
        # Allow dragging and zooming while selection is on but ignore clicks.
        if self.__button_drag.isChecked() or self.__button_zoom.isChecked(): 
            return
        cursorlocation = [int(event.xdata), int(event.ydata)]
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
                if self.measurement.selection_select(cursorlocation) == 1:
                    # self.elementSelectDeleteButton.setChecked(True)
                    self.elementSelectDeleteButton.setEnabled(True)
                    self.canvas.draw_idle()
                    self.__on_draw_legend()
            if self.elementSelectionButton.isChecked():  # If selection is enabled
                if self.measurement.add_point(cursorlocation, self.canvas) == 1:
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
            self.__context_menu(event, cursorlocation)
            self.canvas.draw_idle()
            self.__on_draw_legend()
    
    
    def __emit_selections_changed(self):
        """Emits a 'selectionsChanged' signal with the selections list as a parameter. 
        """
        self.emit(QtCore.SIGNAL("selectionsChanged(PyQt_PyObject)"),
                  self.measurement.selector.selections)
    
    
    def __emit_save_cuts(self):
        """Emits a 'selectionsChanged' signal with the selections list as a parameter. 
        """
        self.emit(QtCore.SIGNAL("saveCuts(PyQt_PyObject)"), self.measurement)
    
    
    def __context_menu(self, event, cursorlocation):
            menu = QtGui.QMenu(self)
            
            Action = QtGui.QAction(self.tr("Graph Settings..."), self)
            Action.triggered.connect(self.graph_settings_dialog)
            menu.addAction(Action)
            
            if self.measurement.selection_select(cursorlocation,
                                                 highlight=False) == 1:
                Action = QtGui.QAction(self.tr("Selection settings..."), self)
                Action.triggered.connect(self.selection_settings_dialog)
                menu.addAction(Action)
                
            menu.addSeparator()
            Action = QtGui.QAction(self.tr("Load selections..."), self)
            Action.triggered.connect(self.load_selections)
            menu.addAction(Action)

            Action = QtGui.QAction(self.tr("Save cuts"), self)
            Action.triggered.connect(self.save_cuts)
            menu.addAction(Action)
            if len(self.measurement.selector.selections) == 0:
                Action.setEnabled(False)
            
            coords = self.canvas.geometry().getCoords()
            point = QtCore.QPoint(event.x, coords[3] - event.y - coords[1])
            # coords[1] from spacing
            menu.exec_(self.canvas.mapToGlobal(point))


    def graph_settings_dialog(self):
        '''Show graph settings dialog.
        '''
        TofeGraphSettingsWidget(self)


    def selection_settings_dialog(self):
        '''Show selection settings dialog.
        '''
        selection = self.measurement.selector.get_selected()
        SelectionSettingsDialog(selection)
        self.measurement.selector.auto_save()
        self.on_draw()
        self.__emit_selections_changed()
        

    def load_selections(self):
        '''Show dialog to load selections.
        '''
        filename = open_file_dialog(self, self.measurement.directory,
                                    "Load Element Selection",
                                    "Selection file (*.sel)")
        if filename:
            self.measurement.load_selection(filename)
            self.on_draw()
            self.elementSelectionSelectButton.setEnabled(True)
        self.__emit_selections_changed()
    
    
    def save_cuts(self):
        '''Save measurement cuts.
        '''
        self.measurement.save_cuts()
        self.__emit_save_cuts()
        
    
    def enable_element_selection(self):
        '''Enable element selection.
        '''
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
            self.measurement.purge_selection()  # Remove hanging selection points
            self.measurement.reset_select()
            self.canvas.draw_idle()
            self.__on_draw_legend()
    
           
    def enable_selection_select(self):
        '''Enable selection selecting tool.
        '''
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
        '''Remove selected selection.
        '''
        self.measurement.remove_selected()
        self.measurement.reset_select()  # Nothing is now selected, reset colors
        self.measurement.selector.auto_save()
        self.elementSelectDeleteButton.setEnabled(False)
        self.__on_draw_legend()
        self.canvas.draw_idle()
        self.__emit_selections_changed()
    
    
    def remove_all_selections(self):
        '''Remove all selections.
        '''
        reply = QtGui.QMessageBox.question(self,
               "Delete all selections",
               "Do you want to delete all selections?\nThis cannot be reversed.",
               QtGui.QMessageBox.Yes,
               QtGui.QMessageBox.No)
        if reply == QtGui.QMessageBox.Yes:
            self.measurement.remove_all()
            self.__on_draw_legend()
            self.canvas.draw_idle()
        self.__emit_selections_changed()
    
    
    def undo_point(self):
        '''Undo last point in open selection.
        '''
        self.measurement.undo_point()
        self.canvas.draw_idle()
        
        
    def show_yourself(self, ui):
        '''Show ToF-E histogram settings in ui.
        
        Args:
            ui: A TofeGraphSettingsWidget's .ui file variable.
        '''
        # Populate colorbox
        dirtyinteger = 0
        colors = sorted(MatplotlibHistogramWidget.color_scheme.items())
        for k, unused_v in colors:  # Get keys from color scheme
            ui.colorbox.addItem(k)
            if k == self.measurement.color_scheme:
                ui.colorbox.setCurrentIndex(dirtyinteger)
            dirtyinteger += 1
 
        # Get values
        ui.bin_x.setValue(self.compression_x)
        ui.bin_y.setValue(self.compression_y)
        ui.invert_x.setChecked(self.invert_X)
        ui.invert_y.setChecked(self.invert_Y)
        ui.axes_ticks.setChecked(self.show_axis_ticks)
        ui.transposeAxesCheckBox.setChecked(self.transpose_axes)
        ui.radio_range_auto.setChecked(self.axes_range_mode == 0)
        ui.radio_range_manual.setChecked(self.axes_range_mode == 1)
        ui.spin_range_x_min.setValue(self.axes_range[0][0])
        ui.spin_range_x_max.setValue(self.axes_range[0][1])
        ui.spin_range_y_min.setValue(self.axes_range[1][0])
        ui.spin_range_y_max.setValue(self.axes_range[1][1])


    def __on_motion(self, event):
        '''Function to handle hovering over matplotlib's graph. 
        
        Args:
            event: A MPL MouseEvent
        '''
        event.button = -1  # Fix for printing.
        if event.inaxes != self.axes: 
            return
        if event.xdata == None and event.ydata == None: 
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
                str_text = str_tool + "; points in selection: {0}".format(points)
            else:
                str_text = "points in selection: {0}".format(points)
            self.mpl_toolbar.mode = str_text
        else:
            if self.mpl_toolbar.mode_tool:
                self.mpl_toolbar.mode = self.tool_modes[self.mpl_toolbar.mode_tool]
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
        
                
             
        
