# coding=utf-8
"""
Created on 18.4.2013
Updated on 20.11.2018

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
"""
__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen " \
             "\n Samuli Rahkonen \n Miika Raunio \n Severi Jääskeläinen \n " \
             "Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen \n Timo Leppälä"
__version__ = "2.0"

import widgets.icon_manager as icons

from modules.detector import Detector
from modules.run import Run
from modules.calibration import TOFCalibrationPoint
from modules.angle_calibration import AngleCalibrationHistogram
from widgets.matplotlib.base import MatplotlibWidget

from PyQt5 import QtWidgets


class MatplotlibAngleSelectorWidget(MatplotlibWidget):
    """Energy spectrum widget
    """

    def __init__(self, parent, detector: Detector, asc,
                 run: Run, bin_width=2.0, column=0, dialog=None):
        """Inits Energy Spectrum widget.

        Args:
            parent: CalibrationCurveFittingWidget
            detector: Detector class object.
            asc: ASCFile class object.
            run: Run object.
            bin_width: Histograms bin width
            column: Which column of the CutFile's data is used to create a
                    histogram.
            dialog: parent's parent dialog.
        """
        super().__init__(parent)
        self.canvas.manager.set_title("Angle selector")
        self.__fork_toolbar_buttons()
        self.dialog = dialog
        self.detector = detector
        self.asc = asc
        self.bin_width = bin_width
        self.use_column = column
        self.run = run

        self.angle_histogram = None
        self._calibration_point = None
        self.selection_given_manually = False
        self.__limit_prev = 0
        self.__limit_low = 0
        self.__limit_high = 0
        self.auto_calibration = False
        self.auto_limit_high = 0
        self.auto_limit_low = 0

        self.canvas.mpl_connect('button_press_event', self.onclick)
        self.on_draw()

    def onclick(self, event):
        """ Handles clicks on the graph

        Args:
            event: Mouse click event.
        """
        if not self.selection_given_manually:
            return
        if event.button == 1:
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

        self.calculate_fit()
        if self.__limit_high and self.__limit_low :
            self.dialog.angleGroupBox.setTitle(f"Angle selector ({self.__limit_low}, {self.__limit_high})")
        self.on_draw()

    def change_asc(self, asc):
        """Changes the cut file to be drawn and analyzed
        """
        if self.asc != asc:
            self.asc = asc
            self.selectButton.setChecked(False)
            self.selection_given_manually = False
        self.on_draw()

    def change_bin_width(self, bin_width):
        """Change histogram bin width.

        Args:
            bin_width: Float representing graph bin width.
        """
        self.bin_width = bin_width

    def on_draw(self):
        """Draw method for matplotlib.
        """
        if self.asc is None:
            return

        self.axes.clear()

        if self.asc != None:
            self.angle_histogram = AngleCalibrationHistogram(
                self.asc, self.bin_width, self.use_column)

            self.axes.plot(self.angle_histogram.histogram_x,
                           self.angle_histogram.histogram_y)
            if self.auto_calibration:
                self.update_auto()
                self.axes.plot(self.angle_histogram.gauss_x,
                            self.angle_histogram.gauss_y)


        self.axes.set_ylabel("Counts")
        self.axes.set_xlabel("Time diff [channel]")

        if self.auto_calibration:
            self.axes.axvline(self.__limit_low, linestyle="--", color='Orange')
            self.axes.axvline(self.__limit_high, linestyle="--", color='Orange')
        else:
            if self.__limit_low:
                self.axes.axvline(self.__limit_low, linestyle="--")
            if self.__limit_high:
                self.axes.axvline(self.__limit_high, linestyle="--")


        # Remove axis ticks
        self.remove_axes_ticks()

        # Draw magic
        self.canvas.draw()
        self.canvas.flush_events()

    def toggle_clicks(self):
        """Toggle between manual ToF channel (x axis) selection.
        """
        self.auto_calibration = False
        self.selection_given_manually = not self.selection_given_manually
        self.on_draw()

    def __fork_toolbar_buttons(self):
        """Custom toolbar buttons be here.
        """
        self.selectButton = QtWidgets.QToolButton(self)
        self.selectButton.clicked.connect(self.toggle_clicks)
        self.selectButton.setCheckable(True)
        self.selectButton.setIcon(icons.get_reinhardt_icon("amarok_edit.svg"))
        self.selectButton.setToolTip("Select the edges manually.")
        self.mpl_toolbar.addWidget(self.selectButton)

    def get_edges(self):
        if not (self.__limit_high and self.__limit_low):
            return None
        return (self.__limit_low, self.__limit_high)

    def calculate_fit(self):
        offset = (self.__limit_high+self.__limit_low)/2
        #foil_size = self.detector.foils[-1].size[0]
        foil_size = self.dialog.foilWidthSpinBox.value()
        #foil_distance = self.detector.foils[-1].distance
        foil_distance = self.dialog.foilDistanceSpinBox.value()
        slope = (foil_size/foil_distance)/(self.__limit_high-self.__limit_low)
        self.dialog.angleOffsetLineEdit.setText(str(offset))
        self.dialog.angleSlopeLineEdit.setText(str(slope))

    def set_auto_calibration(self):
        self.auto_calibration = True
        self.selection_given_manually = False
        self.selectButton.setChecked(False)
        self.update_auto()
        self.on_draw()

    def set_auto_limits(self):
        width = 1.2
        params = self.angle_histogram.fitted_params
        self.__limit_high = params[1] + abs(params[2] * width)
        self.__limit_low = params[1] - abs(params[2] * width)

    def update_auto(self):
        self.angle_histogram.fit_normal_distribution()
        self.set_auto_limits()
        self.calculate_fit()
        self.dialog.angleGroupBox.setTitle(f"Angle selector ({self.__limit_low}, {self.__limit_high})")
