# coding=utf-8
"""
Created on 18.4.2013
Updated on 20.11.2018

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

from widgets.matplotlib.base import MatplotlibWidget


class MatplotlibCalibrationLinearFittingWidget(MatplotlibWidget):
    """Energy spectrum widget
    """

    def __init__(self, parent, tof_calibration, dialog=None, old_params=None):
        """Inits Energy Spectrum widget.

        Args:
            parent: CalibrationCurveFittingWidget
            tof_calibration: TOFCalibration class object.
            dialog: parent's parent dialog.
            old_params: tuple of parameters (x0, A, k)
        """
        super().__init__(parent)
        self.canvas.manager.set_title("ToF-E Calibration - linear fitting")
        self.dialog = dialog
        self.old_params = old_params
        self.tof_calibration = tof_calibration
        self.__max_x_value = 0  # Used to as the maximum x value for the plot
        self.enable_selection_tool = False
        self.on_draw()

    def __update_dialog_values(self):
        """Updates the parent dialog's fields with the calculated values.
        """
        slope = self.tof_calibration.slope
        offset = self.tof_calibration.offset

        if slope is not None and offset is not None:
            self.dialog.slopeLineEdit.setText(str(slope))
            self.dialog.offsetLineEdit.setText(str(offset))
        else:
            self.dialog.slopeLineEdit.setText("")
            self.dialog.offsetLineEdit.setText("")

    def on_draw(self):
        """Draw method for matplotlib.
        """
        self.axes.clear()

        # Get the point set as a tuple(x, y). 
        points = self.tof_calibration.get_points()
        self.axes.plot(points[0], points[1], ".")

        # Draw point texts
        if points[0]:
            for i in range(len(points[0])):
                self.axes.text(points[0][i],
                               points[1][i],
                               s=" {0}".format(points[2][i]),
                               va="top",
                               ha="left")

        # Get axes limits, for linear fit drawing.
        x_min, x_max = self.axes.get_xlim()
        y_min, y_max = self.axes.get_ylim()

        # Draw selected points
        params = self.tof_calibration.fit_linear_function(points[0], points[1],
                                                          0, 0)
        if params[0] is not None and params[1] is not None:
            prms = self.tof_calibration.get_linear_fit_points(params, x_min,
                                                              x_max, 2)
            self.axes.plot(prms[0], prms[1], "-")

        # Draw old calibration
        if self.old_params:
            o_params = self.tof_calibration.get_linear_fit_points(
                self.old_params,
                x_min, x_max, 2)
            self.axes.plot(o_params[0], o_params[1], color="0.8",
                           linestyle="--")

        self.__update_dialog_values()

        # Set limits so we've appropriate looking graph.
        self.axes.set_ylim([y_min, y_max])
        self.axes.set_xlim([x_min, x_max])

        self.axes.set_ylabel("Time of Flight [s]")
        self.axes.set_xlabel("Channel Number [Ch]")

        # Remove axis ticks
        self.remove_axes_ticks()

        # Draw magic
        self.canvas.draw()
