# coding=utf-8
"""
Created on 18.5.2021
Updated on 15.6.2021

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2013-2018 Jarkko Aalto, Severi Jääskeläinen, Samuel Kaiponen,
Timo Konu, Samuli Kärkkäinen, Samuli Rahkonen, Miika Raunio, Heta Rekilä and
Sinikka Siironen, 2020 Juhani Sundell, 2021 Aleksi Kauppi

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

__author__ = "Aleksi Kauppi"
__version__ = "2.0"

import os
import numpy as np
from itertools import cycle
from widgets.matplotlib.base import MatplotlibWidget

class MatplotlibEfficiencyWidget(MatplotlibWidget):
    """Efficiency matplotlibwidget
    """

    def __init__(self, parent, efficiency_files):
        """Inits MatplotlibEfficiencywidget

        Args:
            parent: EfficiencyWidget class object.
            efficiency_files: Paths to .eff files
        """
        super().__init__(parent)
        self.parent = parent
        self.eff_data = []
        self.efficiency_files = efficiency_files
    
        self.canvas.manager.set_title("Efficiency Files")
        self.axes.fmt_xdata = lambda x: "{0:1.2f}".format(x)
        self.axes.fmt_ydata = lambda y: "{0:1.0f}".format(y)
        self.on_draw()

    def on_draw(self):
        """Draw method for matplotlib.
        """

        self.axes.clear()

        self.axes.set_ylabel("Efficiency")
        self.axes.set_xlabel("Energy (MeV)")
        
        #Cycling linestyles and linewidth for better visibility of overlapping files
        lines=["-","--",":"]
        linecycler=cycle(lines)
        i=0
        for file in self.efficiency_files:
            file_name=str(file).split(os.sep)
            self.eff_data = np.loadtxt(file,dtype=float)
            self.axes.plot(self.eff_data[:,0],
                           self.eff_data[:,1],
                           next(linecycler),
                           linewidth=i+2-0.1,
                           label=file_name[-1])
            i=+1
        # Remove axis ticks
        self.remove_axes_ticks()
        self.axes.legend(loc=3, bbox_to_anchor=(1, 0), borderaxespad=0, prop={'size': 12})

        # Draw magic
        self.canvas.draw()