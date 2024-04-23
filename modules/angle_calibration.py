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
from scipy.optimize import curve_fit
from scipy import exp


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
        self.data = []
        with open(asc,"r") as f:
            for line in f:
                self.data.append(1*float(line.split()[2]))
        self.bin_width = bin_width
        self.use_column = use_column
        self.bins = int((max(self.data)-min(self.data))/self.bin_width)

        histed_file = np.histogram(self.data, bins=self.bins)

        self.histogram_x = [(histed_file[1][i] + histed_file[1][i + 1]) / 2 for i in range(len(histed_file[1]) - 1)]
        self.histogram_y = histed_file[0]

    def gaussian_dist(self, X, C, X_mean, sigma):
        return C * exp(-(X - X_mean) ** 2 / (2 * sigma ** 2))

    def fit_normal_distribution(self):
        """ Fit Gaussian distribution to histogram
        """

        mean_0 = sum(self.histogram_x*self.histogram_y)/sum(self.histogram_y)
        sigma_0 = sum(self.histogram_y*(self.histogram_x-mean_0)**2)/sum(self.histogram_y)
        self.fitted_params, _ = curve_fit(self.gaussian_dist, self.histogram_x, self.histogram_y, p0=(max(self.histogram_y), mean_0, sigma_0), maxfev=5000)

        self.gauss_x = np.linspace(min(self.data),max(self.data),num=256)
        self.gauss_y = [self.gaussian_dist(x, *self.fitted_params) for x in self.gauss_x]




