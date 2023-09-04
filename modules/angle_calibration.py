# coding=utf-8
"""
Created on 19.4.2013
Updated on 17.12.2018

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
__author__ = "Timo Leppälä"
__version__ = "2.0"

import collections
from typing import Optional

import numpy as np



class AngleCalibrationHistogram:
    """Class for creating a histogram based on a asc-file data.
    """

    def __init__(self, asc, bin_width: float, use_column=0):
        """Inits the class.

        Args:
            asc: CutFile that is used to make a histogram.
            bin_width: Created histograms bin width
            use_column: Which column of the CutFile's data is used to create a
                histogram.
        """
        self.cut = asc
        self.data = []
        with open(asc,"r") as f:
            for line in f:
                self.data.append(-1*float(line.split()[2]))
        self.bin_width = bin_width
        self.use_column = use_column
        self.bins = int((max(self.data)-min(self.data))/self.bin_width)
        #histed_file = gf.hist(
        #    self.cut.data, width=self.bin_width, col=self.use_column)

        histed_file = np.histogram(self.data, bins=self.bins)

        #self.histogram_x = [float(pair[0]) for pair in histed_file]
        #self.histogram_y = [float(pair[1]) for pair in histed_file]

        self.histogram_x = -histed_file[1][0:-1]
        self.histogram_y = histed_file[0]
