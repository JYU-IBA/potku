# coding=utf-8
"""
Created on 21.3.2013
Updated on 29.8.2018

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
from modules.measurement import Measurement

__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen " \
             "\n Samuli Rahkonen \n Miika Raunio \n Severi Jääskeläinen \n " \
             "Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"
__version__ = "2.0"

from PyQt5 import QtWidgets

from dialogs.graph_ignore_elements import GraphIgnoreElements
from modules.element import Element
from widgets.matplotlib.base import MatplotlibWidget
import modules.masses as masses


class MatplotlibEnergySpectrumWidget(MatplotlibWidget):
    """Energy spectrum widget
    """

    def __init__(self, parent, histed_files, rbs_list, spectrum_type,
                 legend=True):
        """Inits Energy Spectrum widget.

        Args:
            parent: EnergySpectrumWidget class object.
            histed_files: List of calculated energy spectrum files.
            rbs_list: A dictionary of RBS selection elements containing
                      scatter elements.
            legend: Boolean representing whether to draw legend or not.
        """
        super().__init__(parent)
        super().fork_toolbar_buttons()
        self.parent = parent
        self.draw_legend = legend
        self.histed_files = histed_files
        self.__rbs_list = rbs_list
        self.__icon_manager = parent.icon_manager
        if isinstance(parent.parent.obj, Measurement):
            self.__selection_colors = parent.parent.obj.selector.get_colors()

        self.__initiated_box = False
        self.__ignore_elements = []
        self.__log_scale = False

        self.canvas.manager.set_title("Energy Spectrum")
        self.axes.fmt_xdata = lambda x: "{0:1.2f}".format(x)
        self.axes.fmt_ydata = lambda y: "{0:1.0f}".format(y)

        self.mpl_toolbar.addSeparator()
        self.__button_toggle_log = QtWidgets.QToolButton(self)
        self.__button_toggle_log.clicked.connect(self.__toggle_log_scale)
        self.__button_toggle_log.setCheckable(True)
        self.__button_toggle_log.setToolTip("Toggle logarithmic Y axis scaling")
        self.__icon_manager.set_icon(self.__button_toggle_log,
                                     "monitoring_section.svg")
        self.mpl_toolbar.addWidget(self.__button_toggle_log)

        if spectrum_type == "measurement":
            self.__button_ignores = QtWidgets.QToolButton(self)
            self.__button_ignores.clicked.connect(
                self.__ignore_elements_from_graph)
            self.__button_ignores.setToolTip(
                "Select elements which are included in" + \
                " the graph.")
            self.__icon_manager.set_icon(self.__button_ignores, "gear.svg")
            self.mpl_toolbar.addWidget(self.__button_ignores)

        self.on_draw()

    def __sortt(self, key):
        cut_file = key.split('.')
        element_object = Element.from_string(cut_file[0].strip())
        element = element_object.symbol
        isotope = element_object.isotope
        if not isotope:
            isotope = masses.get_standard_isotope(element)
        return isotope

    def on_draw(self):
        """Draw method for matplotlib.
        """
        # Values for zoom
        x_min, x_max = self.axes.get_xlim()
        y_min, y_max = self.axes.get_ylim()

        self.axes.clear()  # Clear old stuff

        self.axes.set_ylabel("Yield (counts)")
        self.axes.set_xlabel("Energy (MeV)")

        if isinstance(self.parent.parent.obj, Measurement):
            element_counts = {}
            keys = [item[0] for item in sorted(self.histed_files.items(),
                                               key=lambda x: self.__sortt(
                                                   x[0]))]
            for key in keys:
                cut_file = key.split('.')
                cut = self.histed_files[key]
                element_object = Element.from_string(cut_file[0])  # Yeah...
                element, isotope = element_object.get_element_and_isotope()
                if key in self.__ignore_elements:
                    continue

                # Check RBS selection
                rbs_string = ""
                if len(cut_file) == 2:
                    if key + ".cut" in self.__rbs_list.keys():
                        element_object = self.__rbs_list[key + ".cut"]
                        element = element_object.element.symbol
                        isotope = element_object.element.isotope
                        rbs_string = "*"
                else:
                    if key in self.__rbs_list.keys():
                        element_object = self.__rbs_list[key]
                        element = element_object.element.symbol
                        isotope = element_object.element.isotope
                        rbs_string = "*"

                x = tuple(float(pair[0]) for pair in cut)
                y = tuple(float(pair[1]) for pair in cut)

                # Get color for selection
                dirtyinteger = 0
                while "{0}{1}{2}".format(isotope, element,
                                         dirtyinteger) in element_counts:
                    dirtyinteger += 1
                color_string = "{0}{1}{2}".format(isotope, element,
                                                  dirtyinteger)
                element_counts[color_string] = 1
                if color_string not in self.__selection_colors:
                    color = "red"
                else:
                    color = self.__selection_colors[color_string]

                if len(cut_file) == 2:
                    label = r"$^{" + str(isotope) + "}$" + element + rbs_string
                else:
                    label = r"$^{" + str(isotope) + "}$" + element \
                            + rbs_string + "$_{split: " + cut_file[2] + "}$"
                self.axes.plot(x, y,
                               color=color,
                               label=label)
        else:
            for data in self.histed_files.values():
                x = tuple(float(pair[0]) for pair in data)
                y = tuple(float(pair[1]) for pair in data)
                self.axes.plot(x, y)

        if self.draw_legend:
            if not self.__initiated_box:
                self.fig.tight_layout(pad=0.5)
                box = self.axes.get_position()
                self.axes.set_position([box.x0, box.y0,
                                        box.width * 0.9, box.height])
                self.__initiated_box = True

            handles, labels = self.axes.get_legend_handles_labels()
            leg = self.axes.legend(handles,
                                   labels,
                                   loc=3,
                                   bbox_to_anchor=(1, 0),
                                   borderaxespad=0,
                                   prop={'size': 12})
            for handle in leg.legendHandles:
                handle.set_linewidth(3.0)

        if 0.09 < x_max < 1.01:  # This works...
            x_max = self.axes.get_xlim()[1]
        if 0.09 < y_max < 1.01:
            y_max = self.axes.get_ylim()[1]

        # Set limits accordingly
        self.axes.set_ylim([y_min, y_max])
        self.axes.set_xlim([x_min, x_max])

        if self.__log_scale:
            self.axes.set_yscale('symlog')

        # Remove axis ticks
        self.remove_axes_ticks()

        # Draw magic
        self.canvas.draw()

    def __toggle_log_scale(self):
        """Toggle log scaling for Y axis in depth profile graph.
        """
        self.__log_scale = self.__button_toggle_log.isChecked()
        self.on_draw()

    def __ignore_elements_from_graph(self):
        """Ignore elements from elements ratio calculation.
        """
        elements = [item[0] for item in sorted(self.histed_files.items(),
                                               key=lambda x: self.__sortt(
                                                   x[0]))]
        dialog = GraphIgnoreElements(elements, self.__ignore_elements)
        self.__ignore_elements = dialog.ignored_elements
        self.on_draw()
