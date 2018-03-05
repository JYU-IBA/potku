# coding=utf-8
"""
Created on 5.3.2018
Updated on

#TODO Description of Potku and copyright
#TODO Lisence

"""
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"
__versio__ = "2.0"

from os.path import join
from PyQt5 import QtCore, uic, QtWidgets

from Widgets.MatplotlibWidget import MatplotlibWidget

class SimulationDepthProfileWidget(MatplotlibWidget):
    '''Widget used to draw simulated energy spectra.
    '''

    def __init__(self, histed_files, legend):
        '''Inits Simulated Energy Spectrum widget.

        Args:
            histed_files: List of calculated energy spectrum files.
            legend: Boolean representing whether to draw legend or not.
        '''
        super().__init__()
        self.ui = uic.loadUi(join("ui_files", "ui_energy_spectrum_simu_widget.ui"), self)
        self.__set_shortcuts()
        self.ui.setWindowTitle("Simulated Energy Spectra")

        # Canvas
        self.canvas.manager.set_title("Energy Spectrum")

        # Save spectra button
        self.__button_ignores = QtWidgets.QToolButton(self)
        self.__button_ignores.clicked.connect(self.__save_spectra())
        self.__button_ignores.setToolTip("Save energy spectra.")
        self.__icon_manager.set_icon(self.__button_save, "save_all.svg")
        self.mpl_toolbar.addWidget(self.__button_save)

    def on_draw(self):
        '''Draw method for matplotlib.
        '''
        # Values for zoom
        x_min, x_max = self.axes.get_xlim()
        y_min, y_max = self.axes.get_ylim()

        self.axes.clear()  # Clear old stuff

        self.axes.set_ylabel("Yield (counts)")
        self.axes.set_xlabel("Energy (MeV)")

        # element_counts = {}
        # keys = [item[0] for item in sorted(self.histed_files.items(),
        #                                    key=lambda x: self.__sortt(x[0]))]
        # for key in keys:
        #     cut_file = key.split('.')
        #     cut = self.histed_files[key]
        #     element_object = Element(cut_file[0])  # Yeah...
        #     element, isotope = element_object.get_element_and_isotope()
        #     if key in self.__ignore_elements:
        #         continue
        #
        #     # Check RBS selection
        #     rbs_string = ""
        #     if len(cut_file) == 2:
        #         if key + ".cut" in self.__rbs_list.keys():
        #             element_object = self.__rbs_list[key + ".cut"]
        #             element, isotope = element_object.get_element_and_isotope()
        #             rbs_string = "*"
        #     else:
        #         if key in self.__rbs_list.keys():
        #             element_object = self.__rbs_list[key]
        #             element, isotope = element_object.get_element_and_isotope()
        #             rbs_string = "*"
        #
        #     x = tuple(float(pair[0]) for pair in cut)
        #     y = tuple(float(pair[1]) for pair in cut)
        #
        #     # Get color for selection
        #     dirtyinteger = 0
        #     while "{0}{1}{2}".format(isotope, element, dirtyinteger) in element_counts:
        #         dirtyinteger += 1
        #     color_string = "{0}{1}{2}".format(isotope, element, dirtyinteger)
        #     element_counts[color_string] = 1
        #     if not color_string in self.__selection_colors:
        #         color = "red"
        #     else:
        #         color = self.__selection_colors[color_string]
        #
        #     if len(cut_file) == 2:
        #         label = r"$^{" + str(isotope) + "}$" + element + rbs_string
        #     else:
        #         label = r"$^{" + str(isotope) + "}$" + element + rbs_string \
        #                 + "$_{split: " + cut_file[2] + "}$"
        #     self.axes.plot(x, y,
        #                    color=color,
        #                    label=label)
        #
        # if self.draw_legend:
        #     if not self.__initiated_box:
        #         self.fig.tight_layout(pad=0.5)
        #         box = self.axes.get_position()
        #         self.axes.set_position([box.x0, box.y0,
        #                                 box.width * 0.9, box.height])
        #         self.__initiated_box = True
        #
        #     handles, labels = self.axes.get_legend_handles_labels()
        #     leg = self.axes.legend(handles,
        #                            labels,
        #                            loc=3,
        #                            bbox_to_anchor=(1, 0),
        #                            borderaxespad=0,
        #                            prop={'size':12})
        #     for handle in leg.legendHandles:
        #         handle.set_linewidth(3.0)
        #
        # if x_max > 0.09 and x_max < 1.01:  # This works...
        #     x_max = self.axes.get_xlim()[1]
        # if y_max > 0.09 and y_max < 1.01:
        #     y_max = self.axes.get_ylim()[1]
        #
        # # Set limits accordingly
        # self.axes.set_ylim([y_min, y_max])
        # self.axes.set_xlim([x_min, x_max])
        #
        # if self.__log_scale:
        #     self.axes.set_yscale('symlog')

        # Remove axis ticks
        self.remove_axes_ticks()

        # Draw magic
        self.canvas.draw()

    #TODO
    def __save_spectra(self, unused_measurement):
        """Connect to saving cuts. Issue it to project for every other measurement.
        """
        # self.measurement.project.save_cuts(self.measurement)

    def __set_shortcuts(self):
        """Set shortcuts for the ToF-E histogram.
        """
        # # X axis
        # self.__sc_comp_x_inc = QtWidgets.QShortcut(self)
        # self.__sc_comp_x_inc.setKey(QtCore.Qt.Key_Q)
        # self.__sc_comp_x_inc.activated.connect(
        #     lambda: self.matplotlib.sc_comp_inc(0))
        # self.__sc_comp_x_dec = QtWidgets.QShortcut(self)
        # self.__sc_comp_x_dec.setKey(QtCore.Qt.Key_W)
        # self.__sc_comp_x_dec.activated.connect(
        #     lambda: self.matplotlib.sc_comp_dec(0))
        # # Y axis
        # self.__sc_comp_y_inc = QtWidgets.QShortcut(self)
        # self.__sc_comp_y_inc.setKey(QtCore.Qt.Key_Z)
        # self.__sc_comp_y_inc.activated.connect(
        #     lambda: self.matplotlib.sc_comp_inc(1))
        # self.__sc_comp_y_dec = QtWidgets.QShortcut(self)
        # self.__sc_comp_y_dec.setKey(QtCore.Qt.Key_X)
        # self.__sc_comp_y_dec.activated.connect(
        #     lambda: self.matplotlib.sc_comp_dec(1))
        # # Both axes
        # self.__sc_comp_inc = QtWidgets.QShortcut(self)
        # self.__sc_comp_inc.setKey(QtCore.Qt.Key_A)
        # self.__sc_comp_inc.activated.connect(
        #     lambda: self.matplotlib.sc_comp_inc(2))
        # self.__sc_comp_dec = QtWidgets.QShortcut(self)
        # self.__sc_comp_dec.setKey(QtCore.Qt.Key_S)
        # self.__sc_comp_dec.activated.connect(
        #     lambda: self.matplotlib.sc_comp_dec(2))
