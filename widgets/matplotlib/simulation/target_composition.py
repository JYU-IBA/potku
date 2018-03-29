# coding=utf-8
"""
Created on 26.3.2018
Updated on 28.3.2018
"""
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä " \
             "\n Sinikka Siironen"

from PyQt5 import QtCore, QtWidgets
import matplotlib.patches as patches

from dialogs.simulation.layer_properties import LayerPropertiesDialog
from widgets.matplotlib.base import MatplotlibWidget
from modules.layer import Layer

class TargetCompositionWidget(MatplotlibWidget):
    """Matplotlib target composition widget. Using this widget, the user
    can edit target composition for the simulation.
    """

    def __init__(self, parent, icon_manager):
        """Inits

        Args:
            parent: A SimulationDepthProfileWidget class object.
            icon_manager: An iconmanager class object.
        """
        super().__init__(parent)
        self.canvas.manager.set_title("Target Composition")
        self.axes.fmt_xdata = lambda x: "{0:1.0f}".format(x)
        self.axes.fmt_ydata = lambda y: "{0:1.0f}".format(y)
        self.__icon_manager = icon_manager

        self.__fork_toolbar_buttons()

        self.name_y_axis = "Concentration"
        self.name_x_axis = "Depth"

        self.on_draw()

    def on_draw(self):
        """Draw method for matplotlib.
        """
        self.axes.clear()  # Clear old stuff

        self.axes.set_ylabel(self.name_y_axis.title())
        self.axes.set_xlabel(self.name_x_axis.title())

        # Remove axis ticks and draw
        self.remove_axes_ticks()
        self.canvas.draw()

    # def add_layer(self):
    #     """Adds a layer in the target composition.
    #     """
    #     layer = patches.Rectangle(
    #             (0.0, 0.0),  # (x,y)
    #             0.3,  # width
    #             1.0,  # height
    #         )
    #     self.axes.add_patch(layer)
    #     self.canvas.draw_idle()


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
        # super().fork_toolbar_buttons()
        self.mpl_toolbar.mode_tool = 0
        self.__tool_label = self.mpl_toolbar.children()[24]
        self.__button_drag = self.mpl_toolbar.children()[12]
        self.__button_zoom = self.mpl_toolbar.children()[14]
        self.__button_drag.clicked.connect(self.__toggle_tool_drag)
        self.__button_zoom.clicked.connect(self.__toggle_tool_zoom)

        # Make own buttons
        self.mpl_toolbar.addSeparator()

        # Button for adding a new layer
        self.button_add_layer = QtWidgets.QToolButton(self)
        self.button_add_layer.clicked.connect(lambda: self.add_layer())
        self.__icon_manager.set_icon(self.button_add_layer, "del.png") # TODO: Change icon!
        self.mpl_toolbar.addWidget(self.button_add_layer)

    def add_layer(self):
        dialog = LayerPropertiesDialog()