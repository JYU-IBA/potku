# coding=utf-8
"""
Created on 25.4.2018
Updated on 1.6.2018

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
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä " \
             "\n Sinikka Siironen"
__version__ = "2.0"

import matplotlib

from dialogs.simulation.layer_properties import LayerPropertiesDialog
from PyQt5 import QtWidgets
from widgets.matplotlib.base import MatplotlibWidget


class _CompositionWidget(MatplotlibWidget):
    """This class works as a basis for TargetCompositionWidget and
    FoilCompositionWidget classes. Using this widget the user can edit
    the layers of the target or the foil. This class should not be used
    as such.
    """
    def __init__(self, parent, layers, icon_manager):
        """Initialize a CompositionWidget.

        Args:
            parent:       Either a TargetWidget or FoilWidget object, which
                          works as a parent of this Matplotlib widget.
            layers:       Layers of the target or the foil.
            icon_manager: An icon manager class object.
        """
        super().__init__(parent)

        # Remove Y-axis ticks and label
        self.axes.yaxis.set_tick_params("both", left="off", labelleft="off")
        self.axes.fmt_xdata = lambda x: "{0:1.0f}".format(x)
        self.name_x_axis = "Depth [nm]"

        self.__icon_manager = icon_manager
        self.__fork_toolbar_buttons()

        self.layers = layers
        self.on_draw()

        if self.layers:
            self.__update_figure()

    def on_draw(self):
        """Draw method for matplotlib.
        """
        self.axes.clear()  # Clear old stuff
        self.axes.set_xlabel(self.name_x_axis)

        # Remove axis ticks and draw
        self.remove_axes_ticks()
        self.canvas.draw()

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

    def __toggle_drag_zoom(self):
        """
        Toggles the drag zoom.
        """
        self.__tool_label.setText("")
        if self.__button_drag.isChecked():
            self.mpl_toolbar.pan()
        if self.__button_zoom.isChecked():
            self.mpl_toolbar.zoom()
        self.__button_drag.setChecked(False)
        self.__button_zoom.setChecked(False)

    def __fork_toolbar_buttons(self):
        """
        Forks the toolbar into custom buttons.
        """
        super().fork_toolbar_buttons()
        self.mpl_toolbar.mode_tool = 0
        self.__tool_label = self.mpl_toolbar.children()[24]
        self.__button_drag = self.mpl_toolbar.children()[12]
        self.__button_zoom = self.mpl_toolbar.children()[14]
        self.__button_drag.clicked.connect(self.__toggle_tool_drag)
        self.__button_zoom.clicked.connect(self.__toggle_tool_zoom)

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

    def __add_layer(self, position=-1):
        """Adds a new layer to the list of layers.

        Args:
            position: A position where the layer should be added. If negative
                      value is given, the layer is added to the end of the list.
        """
        if position > len(self.layers):
            ValueError("There are not that many layers.")

        dialog = LayerPropertiesDialog()

        if dialog.layer and position < 0:
            self.layers.append(dialog.layer)
            self.__update_figure()
        elif dialog.layer:
            self.layers.insert(position, dialog.layer)
            self.__update_figure()

    def __update_figure(self):
        """Updates the figure to match the information of the layers."""
        next_layer_position = 0  # Position where the next layer will be drawn.

        # This variable is used to alternate between the darker and lighter
        # colors of grey.
        is_next_color_dark = True

        # Draw the layers.
        for layer in self.layers:

            # Draw a rectangular patch that will have the thickness of the
            # layer and a height of 1.
            layer_patch = matplotlib.patches.Rectangle(
                (next_layer_position, 0),
                layer.thickness, 1,
                color=(0.85, 0.85, 0.85) if is_next_color_dark else
                (0.9, 0.9, 0.9)
            )

            # Alternate the color.
            if is_next_color_dark:
                is_next_color_dark = False
            else:
                is_next_color_dark = True

            self.axes.add_patch(layer_patch)

            # Put annotation in the middle of the rectangular patch.
            self.axes.annotate(layer.name,
                               (next_layer_position + layer.thickness / 2, 0.5),
                               ha="center")

            # Move the position where the next layer starts.
            next_layer_position += layer.thickness

        self.axes.set_xbound(0, next_layer_position)
        self.canvas.draw_idle()
        self.mpl_toolbar.update()


class TargetCompositionWidget(_CompositionWidget):
    """This widget is used to display the visual presentation of the target
    layers to the user. Using this widget user can also modify the layers of the
    target.
    """
    def __init__(self, parent, target, icon_manager):
        """Initializes a TargetCompositionWidget object.

        Args:
            parent:       A TargetWidget object, which works as a parent of this
                          widget.
            target:       A Target object. This is needed in order to get
                          the current state of the target layers.
            icon_manager: An icon manager class object.
        """
        _CompositionWidget.__init__(self, parent, target.layers,
                                    icon_manager)

        self.layers = target.layers
        self.canvas.manager.set_title("Target composition")


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
                                    icon_manager)

        self.layers = foil.layers
        self.canvas.manager.set_title("Foil composition")
