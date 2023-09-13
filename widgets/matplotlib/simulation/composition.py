# coding=utf-8
"""
Created on 25.4.2018
Updated on 13.4.2023

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2018 Severi Jääskeläinen, Samuel Kaiponen, Heta Rekilä and
Sinikka Siironen, 2023 Sami Voutilainen

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
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä " \
             "\n Sinikka Siironen \n Sami Voutilainen"
__version__ = "2.0"

import matplotlib
import os
import widgets

import dialogs.dialog_functions as df

from widgets.matplotlib import mpl_utils
from pathlib import Path

from dialogs.simulation.layer_properties import LayerPropertiesDialog
from dialogs.simulation.target_info_dialog import TargetInfoDialog

from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal

from widgets.matplotlib.base import MatplotlibWidget


class _CompositionWidget(MatplotlibWidget):
    """This class works as a basis for TargetCompositionWidget and
    FoilCompositionWidget classes. Using this widget the user can edit
    the layers of the target or the foil. This class should not be used
    as such.
    """
    # Signal that is emitted when layers are modified
    layers_changed = pyqtSignal()

    def __init__(self, parent, layers, icon_manager, foil_behaviour=False):
        """Initialize a CompositionWidget.

        Args:
            parent:       Either a TargetWidget or FoilWidget object, which
                          works as a parent of this Matplotlib widget.
            layers:       Layers of the target or the foil.
            icon_manager: An icon manager class object.
            foil_behaviour: Whether to have foil specific behaviour or not.
        """
        super().__init__(parent)

        # Remove Y-axis ticks and label
        self.axes.yaxis.set_tick_params("both", left=False, labelleft=False)
        self.axes.format_coord = mpl_utils.format_x
        self.name_x_axis = "Depth [nm]"
        self.foil_behaviour = foil_behaviour

        self.parent = parent

        self.__icon_manager = icon_manager
        self.__selected_layer = None
        self.__layer_selector = None
        self.__layer_actions = []
        self.__annotations = []

        self.simulation = None
        if type(self.parent) is widgets.simulation.target.TargetWidget:
            self.simulation = self.parent.simulation

        self.__fork_toolbar_buttons()

        self.layers = layers
        self.canvas.mpl_connect('button_press_event', self.on_click)
        self.ylim = self.axes.get_ylim()
        self.trans = matplotlib.transforms.blended_transform_factory(
            self.axes.transData, self.axes.transAxes)
        self.canvas.mpl_connect('draw_event', self.change_annotation_place)

        self.on_draw()

        if self.layers:
            self.__update_figure(True)

    def on_click(self, event):
        """
        Find if click corresponds to any layer and put it as selected layer.
        """
        # Don't do anything if drag tool or zoom tool is active.
        if self.__button_drag.isChecked() or self.__button_zoom.isChecked():
            return
        # Only inside the actual graph axes, else do nothing.
        if event.inaxes != self.axes:
            return
        if event.button == 1:  # Left click
            for layer in self.layers:
                if layer.click_is_inside(event.xdata):
                    self.__selected_layer = layer
                    self.__update_selected_layer()
                    self.__enable_layer_buttons()
                    break

    def __enable_layer_buttons(self):
        """
        Enable buttons for modifying and deleting layers.
        """
        for action in self.__layer_actions:
            action.setEnabled(True)

    def __delete_layer(self):
        """
        Delete selected layer.
        """
        reply = QtWidgets.QMessageBox.question(self, "Confirmation",
                                               "Are you sure you want to "
                                               "delete selected layer?",
                                               QtWidgets.QMessageBox.Yes |
                                               QtWidgets.QMessageBox.No |
                                               QtWidgets.QMessageBox.Cancel,
                                               QtWidgets.QMessageBox.Cancel)
        if reply == QtWidgets.QMessageBox.No or reply == \
                QtWidgets.QMessageBox.Cancel:
            return

        # If clicked Yes, then check if current simulation has any running or
        # finished element simulations and confirm whether these should be
        # deleted as well.
        if self.simulation is not None:
            if not df.delete_element_simulations(self,
                                                 self.simulation,
                                                 tab=self.parent.tab,
                                                 msg="target"):
                return

        # Delete from layers list
        if self.__selected_layer in self.layers:
            self.layers.remove(self.__selected_layer)
        # Remove as selected and remove selector
        self.__layer_selector.set_visible(False)
        self.__layer_selector = None
        self.__selected_layer = None
        # Update layer start depths
        self.update_start_depths()

        self.simulation.target.reference_density.update_layers(self.layers)

        self.update_target_info_labels()

        # Update canvas
        self.__update_figure(zoom_to_bottom=True)

        if self.simulation and not self.layers:
            self.parent.recoilRadioButton.setEnabled(False)

    def __modify_layer(self):
        """
        Open a layer properties dialog for modifying the selected layer.
        """
        if self.__selected_layer:
            tab = None
            if type(self.parent) is widgets.simulation.target.TargetWidget:
                tab = self.parent.tab

            # Old layer thickness
            layer_thickness = 0
            for layer in self.layers:
                layer_thickness += layer.thickness

            dialog = LayerPropertiesDialog(tab,
                                           self.__selected_layer,
                                           modify=True,
                                           simulation=self.simulation)
            if dialog.ok_pressed:
                self.update_start_depths()

                # New layer thickness
                layer_thickness_new = 0
                for layer in self.layers:
                    layer_thickness_new += layer.thickness
                zoom_to_bottom = False
                if layer_thickness > layer_thickness_new:
                    zoom_to_bottom = True

                if self.foil_behaviour:
                    zoom_to_bottom = True

                self.simulation.target.reference_density.update_layers(
                    self.layers)

                self.update_target_info_labels()

                self.__update_figure(zoom_to_bottom=zoom_to_bottom)

    def __update_selected_layer(self):
        """
        Put the selector on top of the selected layer. Remove old one.
        """
        layer = self.__selected_layer
        if not layer:
            return
        if self.__layer_selector:
            self.__layer_selector.set_visible(False)
            self.__layer_selector = None
        x_lim = self.axes.get_xlim()
        layer_patch = self.axes.axvspan(
            layer.start_depth, layer.start_depth + layer.thickness,
            facecolor='b', alpha=0.2)
        if x_lim != self.axes.get_xlim():
            self.axes.set_xbound(*x_lim)
        # layer_patch = matplotlib.patches.Rectangle(
        #     (layer.start_depth, 0),
        #     layer.thickness, 1,
        #     color='b', alpha=0.2)
        self.__layer_selector = layer_patch
        self.axes.add_patch(layer_patch)

        self.canvas.draw_idle()

    def on_draw(self):
        """Draw method for matplotlib.
        """
        self.axes.clear()  # Clear old stuff
        self.axes.set_xlabel(self.name_x_axis)

        # Remove axis ticks and draw
        self.remove_axes_ticks()
        self.canvas.draw()

    def update_start_depths(self):
        """
        Update layers' start depths.
        """
        depth = 0.0
        for layer in self.layers:
            layer.start_depth = depth
            depth += layer.thickness

    def update_target_info_labels(self):
        """Update recoil element info labels.
        """
        self.parent.referenceDensityLabel.setText(
            f"Reference density: "
            f"{self.simulation.target.reference_density.get_value():1.2e} at./cm\xb3"
        )

    def __toggle_tool_drag(self):
        """Toggles the drag tool."""
        if self.__button_drag.isChecked():
            self.mpl_toolbar.mode_tool = 1
        else:
            self.mpl_toolbar.mode_tool = 0
        self.canvas.draw_idle()

    def __toggle_tool_zoom(self):
        """Toggles the zoom tool."""
        if self.__button_zoom.isChecked():
            self.mpl_toolbar.mode_tool = 2
        else:
            self.mpl_toolbar.mode_tool = 0
        self.canvas.draw_idle()

    def __fork_toolbar_buttons(self):
        """
        Forks the toolbar into custom buttons.
        """
        self.mpl_toolbar.mode_tool = 0
        self.__tool_label, self.__button_drag, self.__button_zoom = \
            mpl_utils.get_toolbar_elements(
                self.mpl_toolbar, drag_callback=self.__toggle_tool_drag,
                zoom_callback=self.__toggle_tool_zoom)

        # Make own buttons
        self.mpl_toolbar.addSeparator()

        # Black magic to make the following action work
        temp_button = QtWidgets.QToolButton(self)
        temp_button.clicked.connect(lambda: self.__add_layer())
        self.mpl_toolbar.removeAction(self.mpl_toolbar.addWidget(temp_button))

        # Action for adding a new layer
        action_add_layer = QtWidgets.QAction("Add layer", self)
        action_add_layer.triggered.connect(lambda: self.__add_layer())
        action_add_layer.setToolTip("Add layer")
        # TODO: Change icon!
        self.__icon_manager.set_icon(action_add_layer, "add.png")
        self.mpl_toolbar.addAction(action_add_layer)

        # Action for modifying the selected layer
        action_modify_layer = QtWidgets.QAction("Modify selected layer", self)
        action_modify_layer.triggered.connect(lambda: self.__modify_layer())
        action_modify_layer.setToolTip("Modify selected layer")
        self.__icon_manager.set_icon(action_modify_layer, "amarok_edit.svg")
        action_modify_layer.setEnabled(False)
        self.mpl_toolbar.addAction(action_modify_layer)

        self.__layer_actions.append(action_modify_layer)

        # Action for deleting the selected layer
        action_delete_layer = QtWidgets.QAction("Delete selected layer", self)
        action_delete_layer.triggered.connect(lambda: self.__delete_layer())
        action_delete_layer.setToolTip("Delete the selected layer")
        self.__icon_manager.set_icon(action_delete_layer, "del.png")
        action_delete_layer.setEnabled(False)
        self.mpl_toolbar.addAction(action_delete_layer)

        self.__layer_actions.append(action_delete_layer)

    def __add_layer(self, position=-1):
        """Adds a new layer to the list of layers.

        Args:
            position: A position where the layer should be added. If negative
                      value is given, the layer is added to the end of the list.
        """
        if position > len(self.layers):
            ValueError("There are not that many layers.")

        if not self.layers:
            first = True
        else:
            first = False

        tab = None
        if type(self.parent) is widgets.simulation.target.TargetWidget:
            tab = self.parent.tab

        dialog = LayerPropertiesDialog(
            tab, simulation=self.simulation, first_layer=first)

        if dialog.layer and dialog.placement_under and not self.__selected_layer:
            # Add the first layer
            depth = sum(layer.thickness for layer in self.layers)
            dialog.layer.start_depth = depth
            self.layers.append(dialog.layer)
            self.__selected_layer = dialog.layer
            self.__update_figure(zoom_to_bottom=True)
            # position = self.layers.index(self.__selected_layer) + 1
            # self.layers.insert(position, dialog.layer)
            # self.update_start_depths()
            # self.__selected_layer = dialog.layer
            # self.__update_figure(add=True)
        elif dialog.layer and not dialog.placement_under and \
                self.__selected_layer:
            # Add layer on top of selected layer
            position = self.layers.index(self.__selected_layer)
            self.layers.insert(position, dialog.layer)
            self.update_start_depths()
            self.__selected_layer = dialog.layer
            self.__update_figure(zoom_to_bottom=True)
        elif dialog.layer and position < 0 and self.__selected_layer:
            # Add other layer under selected
            position = self.layers.index(self.__selected_layer) + 1
            self.layers.insert(position, dialog.layer)
            self.update_start_depths()
            self.__selected_layer = dialog.layer
            self.__update_figure(zoom_to_bottom=True)

        self.simulation.target.reference_density.update_layers(self.layers)

        self.update_target_info_labels()

        if type(self.parent) is widgets.simulation.target.TargetWidget:
            self.parent.recoilRadioButton.setEnabled(True)

    def __update_figure(self, init=False, zoom_to_bottom=False):
        """Updates the figure to match the information of the layers.

        Args:
            init: If view is being initialized.
            zoom_to_bottom: If view is updated because of adding a new layer
            or deleting one.
        """
        x_bounds = self.axes.get_xbound()
        self.axes.clear()
        for a in self.__annotations:
            a.set_visible(False)
        self.__annotations = []
        next_layer_position = 0  # Position where the next layer will be drawn.

        # This variable is used to alternate between the darker and lighter
        # colors of grey.
        is_next_color_dark = True

        y = 0.95

        # Draw the layers.
        for layer in self.layers:
            if is_next_color_dark:
                color = (0.85, 0.85, 0.85)
            else:
                color = (0.9, 0.9, 0.9)

            # Draw a rectangular patch that will have the thickness of the
            # layer and a height of 1.
            self.axes.axvspan(layer.start_depth,
                              next_layer_position + layer.thickness,
                              facecolor=color)

            # Alternate the color.
            if is_next_color_dark:
                is_next_color_dark = False
            else:
                is_next_color_dark = True

            annotation = self.axes.text(layer.start_depth, y,
                                        layer.name,
                                        transform=self.trans,
                                        fontsize=10,
                                        ha="left")
            y = y - 0.05
            if y <= 0.1:
                y = 0.95
            self.__annotations.append(annotation)

            # Move the position where the next layer starts.
            next_layer_position += layer.thickness

        if init:
            if self.foil_behaviour:
                self.axes.set_xbound(0, next_layer_position)
            else:
                self.axes.set_xbound(-1, next_layer_position)
        else:
            self.axes.set_xbound(x_bounds[0], x_bounds[1])

        if zoom_to_bottom:
            # Set right bound to bottom of new layer
            view_bound = 0
            for layer in self.layers:
                view_bound += layer.thickness
            self.axes.set_xbound(x_bounds[0], view_bound)

        if not self.__selected_layer and self.layers:
            self.__selected_layer = self.layers[0]
        self.__update_selected_layer()

        if self.__selected_layer:
            self.__enable_layer_buttons()
        self.canvas.draw_idle()
        self.mpl_toolbar.update()

        self.layers_changed.emit()

    def change_annotation_place(self, event):
        """
        If ylim has changed, replace the annotations
        """
        if self.ylim != self.axes.get_ylim():
            y = 0.95
            for a in self.__annotations:
                a.set_visible(False)
            self.__annotations = []
            for layer in self.layers:
                annotation = self.axes.text(layer.start_depth, y,
                                            layer.name,
                                            transform=self.trans,
                                            fontsize=10,
                                            ha="left")
                y = y - 0.05
                if y <= 0.1:
                    y = 0.95
                self.__annotations.append(annotation)
            self.ylim = self.axes.get_ylim()


class TargetCompositionWidget(_CompositionWidget):
    """This widget is used to display the visual presentation of the target
    layers to the user. Using this widget user can also modify the layers of the
    target.
    """
    def __init__(self, parent, target, icon_manager, simulation):
        """Initializes a TargetCompositionWidget object.

        Args:
            parent:       A TargetWidget object, which works as a parent of this
                          widget.
            target:       A Target object. This is needed in order to get
                          the current state of the target layers.
            icon_manager: An icon manager class object.
            simulation:   A Simulation that has the Target object.
        """
        _CompositionWidget.__init__(self, parent, target.layers, icon_manager)

        self.target = target
        self.simulation = simulation
        self.canvas.manager.set_title("Target composition")

        self.parent.targetNameLabel.setText(f"Name: {target.name}")

        self.parent.editTargetInfoButton.clicked.connect(self.edit_target_info)
        self.layers_changed.connect(self._save_target)
        self.update_target_info_button()
        self.update_target_info_labels()

    def edit_target_info(self):
        """
        Open a dialog to edit Target information.
        """
        dialog = TargetInfoDialog(self.target)

        if dialog.isOk:
            old_target = Path(self.simulation.directory,
                              f"{self.target.name}.target")
            try:
                os.remove(old_target)
            except FileNotFoundError:
                pass
            self.target.name = dialog.name
            self.target.description = dialog.description
            self.parent.targetNameLabel.setText(self.target.name)
            self.target.reference_density.use_user_value = dialog.use_user_value
            if dialog.use_user_value:
                self.target.reference_density.manual_density = \
                    dialog.manual_value
            self.update_target_info_labels()
            self.update_target_info_button()
            self._save_target()

    def _save_target(self):
        """Saves the Target object to a file.
        """
        target_path = Path(self.simulation.directory,
                           f"{self.target.name}.target")
        self.target.to_file(target_path)

    def update_target_info_button(self):
        """Changes target info button's color to yellow when using manual
        reference density values. Otherwise keep it uncolored.
        """
        if self.simulation.target.reference_density.use_user_value:
            self.parent.editTargetInfoButton.setStyleSheet("background-color: yellow")
        else:
            self.parent.editTargetInfoButton.setStyleSheet("")


class FoilCompositionWidget(_CompositionWidget):
    """This widget is used to display the visual presentation of the foil
    layers to the user. Using this widget user can also modify the layers of the
    foil.
    """

    def __init__(self, parent, foil, icon_manager):
        """Initializes a FoilCompositionWidget object.

        Args:
            parent:       A FoilDialog object, which works as a parent of this
                          widget.
            foil:         A foil object. This is needed in order to get the
                          current state of the foil layers.
            icon_manager: An icon manager class object.
        """
        _CompositionWidget.__init__(self, parent, foil.layers,
                                    icon_manager, foil_behaviour=True)

        self.canvas.manager.set_title("Foil composition")
