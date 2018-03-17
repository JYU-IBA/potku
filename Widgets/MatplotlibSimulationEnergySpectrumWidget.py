# coding=utf-8
'''
Created on 15.3.2018
Updated on 17.3.2018
'''
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"

from PyQt5 import QtWidgets

from Dialogs.GraphIgnoreElements import GraphIgnoreElements
from Modules.Element import Element
from Widgets.MatplotlibWidget import MatplotlibWidget


class MatplotlibSimulationEnergySpectrumWidget(MatplotlibWidget):
    '''Energy spectrum widget
    '''
    def __init__(self, parent, data):
        '''Inits Energy Spectrum widget.
        
        Args:
            parent: EnergySpectrumWidget class object.
            data: Energy spectrum data.
        '''
        super().__init__(parent)
        super().fork_toolbar_buttons()
        # self.draw_legend = legend
        self.energy_spectrum_data = data
        # self.__rbs_list = rbs_list
        self.__icon_manager = parent.icon_manager
        self.__masses = parent.parent.masses
        # self.__selection_colors = parent.measurement.selector.get_colors()
        
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
        
        self.__button_ignores = QtWidgets.QToolButton(self)
        self.__button_ignores.clicked.connect(self.__ignore_elements_from_graph)
        self.__button_ignores.setToolTip("Select elements which are included in" + \
                                         " the graph.")
        self.__icon_manager.set_icon(self.__button_ignores, "gear.svg")
        self.mpl_toolbar.addWidget(self.__button_ignores)
        
        self.on_draw()


    def __sortt(self, key):
        cut_file = key.split('.')
        element_object = Element(cut_file[0].strip())
        element, isotope = element_object.get_element_and_isotope()
        mass = str(isotope)
        if not mass:
            mass = self.__masses.get_standard_isotope(element)
        else:
            mass = float(mass)
        return mass

    def on_draw(self):
        '''Draw method for matplotlib.
        '''
        # Values for zoom
        x_min, x_max = self.axes.get_xlim()
        y_min, y_max = self.axes.get_ylim()

        self.axes.clear()  # Clear old stuff

        self.axes.set_ylabel("Yield (counts)")
        self.axes.set_xlabel("Energy (MeV)")

        x = tuple(float(pair[0]) for pair in self.energy_spectrum_data)
        y = tuple(float(pair[1]) for pair in self.energy_spectrum_data)

        self.axes.plot(x, y)

        if x_max > 0.09 and x_max < 1.01:  # This works...
            x_max = self.axes.get_xlim()[1]
        if y_max > 0.09 and y_max < 1.01:
            y_max = self.axes.get_ylim()[1]

        # Set limits accordingly
        self.axes.set_ylim([y_min, y_max])
        self.axes.set_xlim([x_min, x_max])

        # Remove axis ticks
        self.remove_axes_ticks()

        # Draw magic
        self.canvas.draw()

    def __toggle_log_scale(self):
        '''Toggle log scaling for Y axis in depth profile graph.
        '''
        self.__log_scale = self.__button_toggle_log.isChecked()
        self.on_draw()
        
        
    def __ignore_elements_from_graph(self):
        '''Ignore elements from elements ratio calculation.
        '''
        elements = [item[0] for item in sorted(self.histed_files.items(),
                                           key=lambda x: self.__sortt(x[0]))]
        dialog = GraphIgnoreElements(elements, self.__ignore_elements)
        self.__ignore_elements = dialog.ignored_elements
        self.on_draw()
        
        
        
        
