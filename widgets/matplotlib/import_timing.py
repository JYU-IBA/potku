# coding=utf-8
"""
Created on 6.6.2013
Updated on 20.11.2018

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2013-2018 Severi Jääskeläinen, Samuel Kaiponen, Timo Konu,
Heta Rekilä and Sinikka Siironen

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
__author__ = "Timo Konu \n Severi Jääskeläinen \n Samuel Kaiponen \n Heta " \
             "Rekilä \n Sinikka Siironen"
__version__ = "2.0"

from PyQt5 import QtWidgets

from widgets.matplotlib.base import MatplotlibWidget
from widgets.matplotlib import mpl_utils

from modules.parsing import CSVParser


class MatplotlibImportTimingWidget(MatplotlibWidget):
    """
    A MatplotlibImportTimingWidget class.
    """
    def __init__(self, parent, data, icon_manager, timing):
        """Inits import timings widget

        Args:
            parent: An ImportTimingGraphDialog class object.
            data: Time difference data as a List.
            icon_manager: An IconManager class object.
            timing: A tuple representing low & high timing limits.
        """
        super().__init__(parent)
        self.canvas.manager.set_title("Import coincidence timing")
        self.icon_manager = icon_manager
        # TODO: Multiple timings ?
        timing_key = list(timing.keys())[0]
        self.__limit_low, self.__limit_high = timing[timing_key]
        self.__title = self.main_frame.windowTitle()
        self.__fork_toolbar_buttons()
        self.canvas.mpl_connect('button_press_event', self.on_click)
        self.main_frame.setWindowTitle("{0} - Timing: ADC {3} ({1},{2})".format(
            self.__title,
            self.__limit_low,
            self.__limit_high,
            timing_key))
        self.__limit_prev = 0
        parser = CSVParser((0, int))
        self.data = [
            timediff for timediff, in
            parser.parse_strs(
                data, separator=" ", method=parser.ROW, ignore=parser.EMPTY)
        ]
        self.on_draw()

    def on_draw(self):
        """Draws the timings graph
        """
        self.axes.clear()

        self.axes.hist(self.data, 200, facecolor='green', histtype='stepfilled')
        self.axes.set_yscale('log', nonpositive='clip')

        self.axes.set_xlabel("Timedifference (µs?)")
        self.axes.set_ylabel("Count (?)")

        if self.__limit_low:
            self.axes.axvline(self.__limit_low, linestyle="--")
        if self.__limit_high:
            self.axes.axvline(self.__limit_high, linestyle="--")

        self.remove_axes_ticks()
        self.canvas.draw_idle()

    def on_click(self, event):
        """Handles clicks on the graph.

        Args:
            event: A click event on the graph
        """
        if event.button == 1 and self.limButton.isChecked():
            value = int(event.xdata)
            if value == self.__limit_high or value == self.__limit_low:
                return
            if self.__limit_prev:
                self.__limit_high = value
                self.__limit_prev = 0
            else:
                self.__limit_low = value
                self.__limit_prev = 1

            # Check these values are correctly ordered
            if self.__limit_high < self.__limit_low:
                self.__limit_low, self.__limit_high = \
                    self.__limit_high, self.__limit_low

            # Set values to parent dialog (main_frame = ImportTimingGraphDialog)
            self.main_frame.timing_low.setValue(self.__limit_low)
            self.main_frame.timing_high.setValue(self.__limit_high)
            self.main_frame.setWindowTitle("{0} - Timing: ({1},{2})".format(
                self.__title,
                self.__limit_low,
                self.__limit_high))
            self.on_draw()

    def __fork_toolbar_buttons(self):
        """Custom toolbar buttons be here.
        """
        self.__tool_label, self.__button_drag, self.__button_zoom = \
            mpl_utils.get_toolbar_elements(
                self.mpl_toolbar, drag_callback=self.__uncheck_custom_buttons,
                zoom_callback=self.__uncheck_custom_buttons)

        self.limButton = QtWidgets.QToolButton(self)
        self.limButton.clicked.connect(self.__limit_button_click)
        self.limButton.setCheckable(True)
        self.limButton.setToolTip(
            "Change timing's low and high limits for more accurate coincidence "
            "reading.")
        self.icon_manager.set_icon(self.limButton, "amarok_edit.svg")
        self.mpl_toolbar.addWidget(self.limButton)

    def __limit_button_click(self):
        """Click event on limit button.
        """
        if self.limButton.isChecked():
            self.__uncheck_built_in_buttons()
            self.__tool_label.setText("timing limit tool")
            self.mpl_toolbar.mode = "timing limit tool"
        else:
            self.__tool_label.setText("")
            self.mpl_toolbar.mode = ""

    def __uncheck_custom_buttons(self):
        """
        Uncheck cusotm buttons.
        """
        self.limButton.setChecked(False)

    def __uncheck_built_in_buttons(self):
        """
        Uncheck built-in buttons.
        """
        self.__button_drag.setChecked(False)
        self.__button_zoom.setChecked(False)
        self.__tool_label.setText("")
        self.mpl_toolbar.mode = ""
