# coding=utf-8
'''
Created on 18.4.2013
Updated on 23.5.2013

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
from PyQt5 import QtCore, QtWidgets
# from PyQt4 import QtGui

from Dialogs.SelectionDialog import SelectionSettingsDialog
from Dialogs.GraphSettingsDialog import TofeGraphSettingsWidget
from Modules.Element import Element
from Modules.Functions import open_file_dialog
from Widgets.MatplotlibWidget import MatplotlibWidget

class MatplotlibHistogramWidget(MatplotlibWidget):
    selectionsChanged = QtCore.pyqtSignal("PyQt_PyObject")
    '''Matplotlib histogram widget, used to graph "bananas" (ToF-E).
    '''
    color_scheme = {"Default color":"jet",
                    "Greyscale":"Greys",
                    "Greyscale (inverted)":"gray"}
    
    def __init__(self, parent, measurement_data, icon_manager):
        '''Inits histogram widget
        
        Args:
            parent: TofeHistogramWidget class object.
            measurement_data: List of data points.
            icon_manager: IconManager class object.
        '''
        super().__init__(parent)
        
        self.icon_manager = icon_manager
        
        # Connections and setup
        self.canvas.mpl_connect('button_press_event', self.on_click)
        self.__fork_toolbar_buttons()
        
        # Variables
        self.invert_Y = True  # Default True
        self.invert_X = False  # Default False
        self.transpose_axes = False
        self.bins = [750, 750]  # Compression factor if you may
        self.__inverted_Y = False
        self.__inverted_X = False
        self.__transposed = False
        
        self.__inited__ = False 
        
        self.name_y_axis = "Energy (Ch)"
        self.name_x_axis = "time of flight (Ch)"
        
        self.measurement = measurement_data 
        # Which color scheme is selected by default
        self.color_scheme_selected = "Default color"  
        self.on_draw()
    


        
    def on_draw(self):
        '''Draw method for matplotlib.
        '''
        # Values for zoom
        x_min, x_max = self.axes.get_xlim()
        y_min, y_max = self.axes.get_ylim()
        
        x_data = self.measurement.data[0]
        y_data = self.measurement.data[1]
        
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
        use_color_scheme = self.measurement.color_scheme
        color_scheme = MatplotlibHistogramWidget.color_scheme[use_color_scheme]
        colormap = cm.get_cmap(color_scheme)
        self.axes.hist2d(x_data,
                         y_data,
                         bins=self.bins,
                         norm=LogNorm(),
                         # We can cut the graph "automatically" this way
                         # range=[[1000,6000],[0,4000]], 
                         cmap=colormap)
        
        self.__on_draw_legend()
                
        if x_max > 0.09 and x_max < 1.01:  # This works...
            x_max = self.axes.get_xlim()[1]
        if y_max > 0.09 and y_max < 1.01:
            y_max = self.axes.get_ylim()[1]
        
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
        if self.invert_Y:
            self.axes.set_ylabel("Inverse " + self.name_y_axis)
        else:
            self.axes.set_ylabel(self.name_y_axis.title())
        if self.invert_X:
            self.axes.set_xlabel("Inverse " + self.name_x_axis)
        else:
            self.axes.set_xlabel(self.name_x_axis.title())
        
        # TODO: Do not remove opposite "axes", leave borders around the graph
        if self.transpose_axes:
            if self.invert_X:
                self.__set_x_axis_on_top(True)
            else:
                self.__set_x_axis_on_top(False)
            if self.invert_Y:
                self.__set_y_axis_on_right(True)
            else:
                self.__set_y_axis_on_right(False)
        else:
            if self.invert_Y:
                self.__set_x_axis_on_top(True)
            else:
                self.__set_x_axis_on_top(False)
            if self.invert_X:
                self.__set_y_axis_on_right(True)
            else:
                self.__set_y_axis_on_right(False)
            
        # Remove axis ticks
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
        if not self.__inited__:  # Do this only once.
            box = self.axes.get_position()
            self.axes.set_position([box.x0,
                                    box.y0,
                                    box.width * 0.85,
                                    box.height])
            self.__inited__ = True
        selection_legend = {}
        
        # Get selections for legend
        for sel in self.measurement.selector.selections:
            element, isotope = sel.element.get_element_and_isotope()
            sel.points.set_marker(None)  # Remove markers for legend.
            dirtyinteger = 0
            key_string = "{0}{1}".format(sel.element, dirtyinteger)
            while key_string in selection_legend.keys():
                dirtyinteger += 1
                key_string = "{0}{1}".format(sel.element,
                                             dirtyinteger)
            selection_legend[key_string] = sel.points
            
        # Sort legend text
        sel_text = []
        sel_points = []
        keys = sorted(selection_legend.keys())
        for key in keys:
            element_obj = Element(key)
            element, isotope = element_obj.get_element_and_isotope()
            sel_text.append(r"$^{" + str(isotope) + "}$" + element)
            sel_points.append(selection_legend[key])

        leg = self.axes.legend(sel_points,
                               sel_text,
                               loc=3,
                               bbox_to_anchor=(1.05, 0))
        for handle in leg.legendHandles:
            handle.set_linewidth(3.0)
        
        # Set the markers back to original.
        for sel in self.measurement.selector.selections:
            sel.points.set_marker(sel.LINE_MARKER)

        
    def __toggle_tool_drag(self):
        self.elementSelectionButton.setChecked(False)
        self.elementSelectionSelectButton.setChecked(False)
        self.measurement.purge_selection()
        self.canvas.draw_idle()
        
        
    def __toggle_tool_zoom(self):
        self.elementSelectionButton.setChecked(False)
        self.elementSelectionSelectButton.setChecked(False)
        self.measurement.purge_selection()
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
        self.__tool_label = self.mpl_toolbar.children()[24]
        self.__button_drag = self.mpl_toolbar.children()[12]
        self.__button_zoom = self.mpl_toolbar.children()[14]
        self.__button_drag.clicked.connect(self.__toggle_tool_drag)
        self.__button_zoom.clicked.connect(self.__toggle_tool_zoom)
        
        # Make own buttons
        self.mpl_toolbar.addSeparator()
        self.elementSelectionButton = QtWidgets.QToolButton(self)
        self.elementSelectionButton.clicked.connect(self.enable_element_selection)
        self.elementSelectionButton.setCheckable(True)
        self.icon_manager.set_icon(self.elementSelectionButton, "select.png")
        self.elementSelectionButton.setToolTip("Select element area")
        self.mpl_toolbar.addWidget(self.elementSelectionButton)
        
        # Selection undo button
        self.elementSelectUndoButton = QtWidgets.QToolButton(self)
        self.elementSelectUndoButton.clicked.connect(self.undo_point)
        self.icon_manager.set_icon(self.elementSelectUndoButton, "undo.png")
        self.elementSelectUndoButton.setToolTip("Undo last point in open selection")
        self.mpl_toolbar.addWidget(self.elementSelectUndoButton)
        self.mpl_toolbar.addSeparator()
        
        # Element Selection selecting tool
        self.elementSelectionSelectButton = QtWidgets.QToolButton(self)
        self.elementSelectionSelectButton.clicked.connect(
                                                      self.enable_selection_select)
        self.elementSelectionSelectButton.setCheckable(True)
        self.elementSelectionSelectButton.setEnabled(False)
        self.icon_manager.set_icon(self.elementSelectionSelectButton,
                                   "selectcursor.png")
        self.elementSelectionSelectButton.setToolTip("Select element selection")
        self.mpl_toolbar.addWidget(self.elementSelectionSelectButton)
        
        # Selection delete button
        self.elementSelectDeleteButton = QtWidgets.QToolButton(self)
        self.elementSelectDeleteButton.setEnabled(False)
        self.elementSelectDeleteButton.clicked.connect(self.remove_selected)
        self.icon_manager.set_icon(self.elementSelectDeleteButton, "del.png")
        self.elementSelectDeleteButton.setToolTip("Delete selected selection")
        self.mpl_toolbar.addWidget(self.elementSelectDeleteButton)
        self.mpl_toolbar.addSeparator()
        
        # Selection delete all -button
        self.elementSelectionDeleteButton = QtWidgets.QToolButton(self)
        self.elementSelectionDeleteButton.clicked.connect(
                                                      self.remove_all_selections)
        self.icon_manager.set_icon(self.elementSelectionDeleteButton, "delall.png")
        self.elementSelectionDeleteButton.setToolTip("Delete all selections")
        self.mpl_toolbar.addWidget(self.elementSelectionDeleteButton)
        
        
    def on_click(self, event):
        '''On click event above graph.
        '''
        # Only inside the actual graph axes, else do nothing.
        if event.inaxes != self.axes: return  
        cursorlocation = [int(event.xdata), int(event.ydata)]
        if event.button == 1:  # Left click TODO: event.left vakio Gt
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
        #self.emit(QtCore.SIGNAL("selectionsChanged(PyQt_PyObject)"), self.measurement.selector.selections)
        self.selectionsChanged.emit(self.measurement.selector.selections)
    
    
    def __context_menu(self, event, cursorlocation):
            menu = QtWidgets.QMenu(self)
            
            Action = QtWidgets.QAction(self.tr("Graph Settings..."), self)
            Action.triggered.connect(self.graph_settings_dialog)
            menu.addAction(Action)
            
            if self.measurement.selection_select(cursorlocation,
                                                 highlight=False) == 1:
                Action = QtWidgets.QAction(self.tr("Selection settings..."), self)
                Action.triggered.connect(self.selection_settings_dialog)
                menu.addAction(Action)
                
            menu.addSeparator()
            Action = QtWidgets.QAction(self.tr("Load selections..."), self)
            Action.triggered.connect(self.load_selections)
            menu.addAction(Action)

            Action = QtWidgets.QAction(self.tr("Save cuts"), self)
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

    
    def enable_element_selection(self):
        '''Enable element selection.
        '''
        if self.elementSelectionButton.isChecked():  # if button is enabled
            # One cannot choose selection while selecting
            self.elementSelectionSelectButton.setChecked(False)  
            self.__toggle_drag_zoom()
            self.__tool_label.setText("selection tool")
            self.mpl_toolbar.mode = "selection tool"
        else:
            self.__tool_label.setText("")
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
            self.__toggle_drag_zoom()
            self.__tool_label.setText("selection select tool")
            self.mpl_toolbar.mode = "selection select tool"
        else:
            self.elementSelectDeleteButton.setEnabled(False)
            self.__tool_label.setText("")
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
        reply = QtWidgets.QMessageBox.question(self,
               "Delete all selections",
               "Do you want to delete all selections?\nThis cannot be reversed.",
               QtWidgets.QMessageBox.Yes,
               QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
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
        ui.bin_x.setValue(self.bins[0])
        ui.bin_y.setValue(self.bins[1])
        ui.invert_x.setChecked(self.invert_X)
        ui.invert_y.setChecked(self.invert_Y)
        ui.axes_ticks.setChecked(self.show_axis_ticks)
        ui.transposeAxesCheckBox.setChecked(self.transpose_axes)
        
