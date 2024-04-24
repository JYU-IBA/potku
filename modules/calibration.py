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
__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen " \
             "\n Samuli Rahkonen \n Miika Raunio \n Severi Jääskeläinen \n " \
             "Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"
__version__ = "2.0"

import collections
from typing import Optional

import numpy as np
import scipy.optimize as optimize
from math import sin, cos, sqrt, pi
from scipy.special import erf

from .run import Run
from .detector import Detector
from .ui_log_handlers import Logger
from . import general_functions as gf


class TOFCalibrationHistogram:
    """Class for creating a histogram based on a cut file data. Can make a curve
    fit to histogram's front edge.
    """

    def __init__(self, cut, bin_width: float, use_column=0):
        """Inits the class.

        Args:
            cut: CutFile that is used to make a histogram.
            bin_width: Created histograms bin width
            use_column: Which column of the CutFile's data is used to create a
                histogram.
        """
        self.cut = cut
        self.bin_width = bin_width
        self.use_column = use_column
        histed_file = gf.hist(
            self.cut.data, width=self.bin_width, col=self.use_column)

        self.histogram_x = [float(pair[0]) for pair in histed_file]
        self.histogram_y = [float(pair[1]) for pair in histed_file]

    def get_error_function_parameters(self, end_of_front_edge,
                                      start_of_front_edge=0):
        """Get the parameters of the fitted curve. Parameters are used to
        specify the range where the curve fit is made.

        Args:
            end_of_front_edge: End of the histogram's range in x axis.
            start_of_front_edge: Start of the histogram's range in x axis.

        Return:
            Tuple of fit function parameters (x0, A, k).
        """
        list_x = self.histogram_x[start_of_front_edge:end_of_front_edge]
        list_y = self.histogram_y[start_of_front_edge:end_of_front_edge]

        # Guess that x0 is the
        # Returns parameters as a tuple(x0, A, k)
        params = self.fit_error_function(list_x, list_y,
                                         list_x[-1], list_y[-1], 10)
        return params

    def error_function(self, x, params):
        """The function used for fit.

        Takes the function parameters as a "namedtuple" or "tuple".
        A * (erf((x - x0) / k) + 1) / 2

        Args:
            x: Float representing value on X axis.
            params: namedtuple or tuple that brings the used parameters
            ("x0 A k").

        Return:
            Returns calculated error function value for x.
        """
        x0, a, k = params
        return a * (erf((x - x0) / k) + 1) / 2

    def __residuals(self, p, x, y):
        return y - self.error_function(x, p)

    def fit_error_function(self, x, y, guess_x0, guess_a, guess_k):
        """Fits a error function to the given data.

        Args:
            x: data's x axis a list
            y: data's y axis a list
            guess_x0: Guess for the x_0's value
            guess_a: Guess for the A's value
            guess_k: Guess for the k's value

        Return:
            tuple(x0, A, k) of parameters of a fitted error function.
        """
        if len(x) < 2 or len(y) < 2:
            return None

        x = np.array(x)
        y = np.array(y)

        Param = collections.namedtuple("Param", "x0 a k")
        p_guess = Param(x0=guess_x0, a=guess_a, k=guess_k)
        try:
            p, unused_cov, unused_infodict, unused_mesg, unused_ier = \
                optimize.leastsq(self.__residuals, p_guess, args=(x, y),
                                 full_output=True)
            p = Param(*p)

            return p.x0, p.a, p.k
        except TypeError:
            return None

    def find_leading_edge_borders(self):
        """Finds the beginning and the end of the leading edge.

        Return:
            Returns a tuple of the beginning and end indexes of the leading
            edge.
        """
        # return self.histogram_y.index(max(self.histogram_y))
        # Find the "actual" beginning of the file, ignoring low values at the
        # beginning. Cut the size when using large amounts of data, since the
        # leading edge is in the first half of the data.
        threshold_mix = max(self.histogram_y) * 0.025
        threshold_min = max(self.histogram_y) * 0.05
        t_mix = 0
        for y in self.histogram_y:
            if y >= threshold_mix and t_mix == 0:
                if y >= threshold_min:
                    break
                t_mix = self.histogram_y.index(y)
        size = len(self.histogram_y)
        if size > 50:
            list_y = self.histogram_y[t_mix:t_mix + int(size / 4)]
        else:
            list_y = self.histogram_y
        y_max = max(list_y)
        threshold_max = y_max * 0.95
        t_min_over = False
        t_max_over = False
        t_min = 0  # Temporary indexes
        t_max = len(list_y) - 1  # Temporary indexes
        # Try to find index of which's value exceeds threshold minimum and
        # maximum to get the beginning and end of the leading edge.
        for y in list_y:
            if threshold_mix <= y <= threshold_min and t_mix == 0:
                t_mix = self.histogram_y.index(y)
            if y >= threshold_min and not t_min_over:
                t_min_over = True
                t_min = self.histogram_y.index(y)
            elif y <= threshold_min and not t_max_over:
                # Keep pushing min threshold until we've passed max threshold.
                t_min_over = False
            elif y >= threshold_max and not t_max_over:
                if not t_min_over:
                    t_min_over = True
                t_max_over = True
                t_max = self.histogram_y.index(y)
                break
        # If the data happens to be extremely small, we might need to increase
        # index values since SciPy will not appreciate when distance between
        # index values is under three. Error function requires a list with at
        # least three values.
        if t_min + 2 >= t_max:
            if t_max + 2 < len(list_y):
                t_max += 2
                t_min -= 1  # Always at least 1, this is fine.
            elif t_min - 2 > 0:
                t_min -= 2
        return t_min, t_max

    def get_curve_fit_points(self, params, points_in_range):
        """Generates points from the error function with the histogram's range

        Args:
            params: tuple of parameters (x0, A, k)
            points_in_range: Points in range of the histogram.

        Return:
            tuple(xp, pxp) of generated lists of axis data (x and y axis)
        """
        x_values = np.linspace(
            self.histogram_x[0], self.histogram_x[-1], points_in_range)
        y_values = self.error_function(x_values, params)
        return x_values, y_values


class TOFCalibration:
    """Class for holding list of TOFCalibrationPoints and creating a linear fit
    of their values.
    """

    def __init__(self):
        """Initializes the class
        """
        self.slope = None
        self.offset = None
        self.tof_points = []

    def add_point(self, tof_calibration_point):
        """Adds a TOFCalibrationPoint to ToF Calibration

        Args:
            tof_calibration_point: TOFCalibrationPoint class object.
        """
        self.tof_points.append(tof_calibration_point)

    def remove_point(self, tof_calibration_point):
        """Removes a TOFCalibrationPoint from ToF Calibration

        Args:
            tof_calibration_point: TOFCalibrationPoint class object.

        Return:
            Returns True if point was removed. False otherwise.
        """
        if self.point_exists(tof_calibration_point):
            self.tof_points.remove(tof_calibration_point)
            return True
        return False

    def point_exists(self, tof_calibration_point):
        """Check if point exists in ToF Calibration.

        Args:
            tof_calibration_point: TOFCalibrationPoint class object.

        Return:
            Returns True if point exists. False otherwise.
        """
        return tof_calibration_point in self.tof_points

    def get_points(self):
        """Returns TOFCalibrationPoints that have the point_used property set
        True.

        Return:
            tuple(x,y, name) of lists containing used points for the linear fit.
        """
        x = [point.time_of_flight_channel
             for point in self.tof_points if point.point_used]
        y = [point.time_of_flight_seconds
             for point in self.tof_points if point.point_used]
        name = []
        for point in self.tof_points:
            if not point.point_used:
                continue
            if point.type == "ERD":
                name.append(str(point.cut.element))
            else:
                name.append(str(point.cut.element_scatter) + "*")
        # name = [str(point.cut.element)
        #         for point in self.tof_points if point.point_used]
        return x, y, name

    def linear_function(self, x, params):
        """The function used for linear fit. Takes the function parameters as a
        "namedtuple" or "tuple".
        a*x + b

        Args:
            x: point x.
            params: namedtuple or tuple that brings the used parameters ("a b")

        Return:
            Returns linear function value from the given point x.
        """
        a, b = params
        return a * x + b

    def __residuals(self, p, x, y):
        return y - self.linear_function(x, p)

    def fit_linear_function(self, x, y, guess_a, guess_b):
        """Fits a linear function to the given data.
        a*x + b

        Args:
            x: data's x axis as a list
            y: data's y axis as a list
            guess_a: Guess for the a's value
            guess_b: Guess for the b's value

        Returns:
            tuple(a, b) of parameters of a fitted linear function.
        """
        if len(x) < 2 or len(y) < 2:
            self.slope = None
            self.offset = None
            return None, None

        x = np.array(x)
        y = np.array(y)

        Param = collections.namedtuple('Param', 'a b')
        p_guess = Param(a=guess_a, b=guess_b)
        try:
            p, unused_cov, unused_info, unused_mesg, unused_ier = \
                optimize.leastsq(
                    self.__residuals, p_guess, args=(x, y), full_output=True)
            p = Param(*p)
        except:
            print("Invalid fit parameters")
            self.slope = None
            self.offset = None
            return None, None

        self.slope = p.a
        self.offset = p.b
        return p.a, p.b

    def get_linear_fit_points(self, params, x_min, x_max, points_in_range):
        """Generates points from the linear function with given range and
        number of points.

        Args:
            params: tuple of parameters (x0, A, k)
            x_min:
            x_max:
            points_in_range:

        Returns:
            tuple(x_values, y_values) of generated lists of axis data (x and y
            axis).
        """
        x_values = np.linspace(x_min, x_max, points_in_range)
        y_values = self.linear_function(x_values, params)
        return x_values, y_values

    def get_fit_parameters(self):
        """Get fit parameters.

        Return:
            Returns Slope and Offset of calibration.
        """
        return self.slope, self.offset


class TOFCalibrationPoint:
    """ Class for the calculation of a theoretical time of flight.
    """

    def __init__(self, time_of_flight, cut, detector: Detector, run: Run,
                 logger: Optional[Logger] = None):
        """ Inits the class.

        Args:
            time_of_flight: An integer representing time of flight channel.
            cut: A CutFile class object.
            detector: A Detector class object.
            run: Run object.
        """
        self.cut = cut
        self.type = cut.type
        self.point_used = True
        time_of_flight_length = 0  # Needs to be m, foil distances are mm.
        i = len(detector.tof_foils) - 1
        while i - 1 >= 0:
            time_of_flight_length = detector.foils[
                                        detector.tof_foils[i]].distance - \
                                    detector.foils[
                                        detector.tof_foils[i - 1]].distance
            i = i - 1

        time_of_flight_length = time_of_flight_length / 1000

        # Timing foil can only be carbon and have one layer!!!
        carbon_foil_thickness_in_nm = 0
        layer = detector.foils[detector.tof_foils[0]].layers[0]
        carbon_foil_thickness_in_nm += layer.thickness
        density_in_g_per_cm3 = layer.density

        # Recoiled atoms' parameters
        # element = self.cut.element.symbol

        mass = self.cut.element.get_mass()
        if cut.element.isotope:
            isotope = cut.element.isotope
        else:
            isotope = self.cut.element.get_most_common_isotope()
        self.recoiled_mass = gf.convert_amu_to_kg(mass)

        if self.type == "RBS":
            mass_scatter = self.cut.element_scatter.get_mass()
            self.scatter_element_mass = gf.convert_amu_to_kg(mass_scatter)

        beam_mass = run.beam.ion.get_mass()
        self.beam_mass = gf.convert_amu_to_kg(beam_mass)
        self.beam_energy = gf.convert_mev_to_joule(run.beam.energy)
        self.length = time_of_flight_length
        # Target angle, same with both recoiled and scattered atoms when
        # using same hardware.
        self.theta = detector.detector_theta * pi / 180
        energy = self.__calculate_particle_energy(self.beam_energy)

        # Carbon stopping gives a list of different result values.
        # The last value is the stopping energy.
        try:
            carbon_energy_loss = gf.carbon_stopping(
                self.cut.element.symbol, isotope, energy,
                carbon_foil_thickness_in_nm, density_in_g_per_cm3)
        except Exception as e:
            error_msg = f"Carbon stopping doesn't work: {e}. Continuing " \
                        f"without it. Carbon stopping energy set to 0."
            if logger is not None:
                logger.log_error(error_msg)
            print(error_msg)
            carbon_energy_loss = 0
        self.energy_loss = carbon_energy_loss

        self.time_of_flight_channel = time_of_flight  # (CHANNEL)
        self.time_of_flight_seconds = self.calculate_time_of_flight()
        # (SECONDS)
        print("\nCut file type: " + str(self.type) +
              "\nRecoiled mass [kg]: " + str(self.recoiled_mass) +
              "\nRecoiled/scattered particle energy [J]: " + str(energy) +
              "\nBeam mass [kg]: " + str(self.beam_mass) +
              "\nBeam energy [J]: " + str(self.beam_energy) +
              "\nToF length [m]: " + str(self.length) +
              "\nRecoil/scattering angle [rads]" + str(self.theta) +
              "\nEnergy loss in foil [J]: " + str(self.energy_loss) +
              "\nTime of Flight [channel]: " + str(self.time_of_flight_channel) +
              "\nTime of Flight [seconds]: " + str(self.time_of_flight_seconds))

    def __calculate_particle_energy(self, beam_energy):
        """Calculates the energy of a particle that comes from the sample.
        Doesn't include the stopping energy.

        Return:
            Particle's energy as float or None if something went wrong.
        """
        k = self.__kinematic_factor(self.type)
        if k is not None:
            return k * beam_energy
        return None

    def get_tof_channel(self):
        """Get Time of Flight channel.

        Return:
            Returns Time of Flight channel.
        """
        return self.time_of_flight_channel

    def get_tof_seconds(self):
        """Get Time of Flight seconds.

        Return:
            Returns Time of Flight seconds.
        """
        return self.time_of_flight_seconds

    def get_name(self):
        """Get name of the used CutFile.

        Return:
            Returns name of the used CutFile.
        """
        if self.type == "ERD":
            return str(self.cut.element)
        else:
            return str(self.cut.element_scatter) + "*"

    def __kinematic_factor(self, selection_type):
        """ Calculates the kinematic factor.

        ERD: (4 * M_I * M_R * cos(a)^2) / (M_I + M_R)^2
        RBS: ((sqrt(( M_R^2 - M_I^2 * sin(a)^2)) + M_I * cos(a)) / (M_I +
        M_R))^2

        Args:
            selection_type: A string representing what type of selection
                            was detected.

        Return:
            Returns calculated kinematic factor based on selection type.
        """
        # TODO: Print -> Raise and/or logger.error
        # error_msg = "Impossible parameters for calculating kinematic factor."
        cosin = cos(self.theta)
        cosin2 = cosin * cosin
        sine = sin(self.theta)
        sine2 = sine * sine
        M_I = self.beam_mass
        if selection_type == "ERD":
            M_R = self.recoiled_mass
            mass_sum = M_I + M_R
            mass_sum2 = mass_sum * mass_sum
            if mass_sum == 0:
                raise ZeroDivisionError
            kinematic_factor = (4.0 * M_I * M_R * cosin2) / mass_sum2
            return kinematic_factor
        elif selection_type == "RBS":
            M_R = self.scatter_element_mass
            M_R2 = M_R * M_R
            M_I2 = M_I * M_I
            mass_sum = M_I + M_R
            square = M_R2 - M_I2 * sine2
            if square <= 0:
                raise ValueError(
                    f"Impossible parameters for calculating kinematic factor." +
                    f"\nm_recoil^2 - m_ion^2 * sine^2(target_angle) <= 0" +
                    f"\n({M_R2} - {M_I2} * {sine2} = {square} <= 0)")
            k = (sqrt(square) + M_I * cosin) / mass_sum
            kinematic_factor = k * k
            return kinematic_factor
        else:
            return None

    def calculate_time_of_flight(self):
        """ Calculates the time of flight.

        In case of ERD use:

        t = l / sqrt(2 * (k * (E_I0 - dE_RT1)) / M_R)
        where:

        E_I0 = beam energy
        dE_RT1 = stopping energy of the recoiled particle
        M_R = mass of the recoiled particle
        M_I = mass of the scattered particle
        k = kinetic factor, which is (4 * M_I * M_R * cos(a)^2) / (M_I + M_R)^2

        In case of RBS use:

        t = l / sqrt(2 * (k * (E_I0 - dE_IT1)) / M_R)
        where:

        dE_RT1 = stopping energy of the scattered particle
        M_R = mass of the recoiled particle
        M_I = mass of the scattered particle
        k = kinetic factor, which is ((sqrt( M_R^2 - M_I^2 * sin(a)^2) + M_I *
                cos(a)) / (M_I + M_R))^2


        Return:
            Calculated time of flight as float. None if the cut file's type is
            not either ERD or RBS.
        """
        kinematic_factor = self.__kinematic_factor(self.type)
        energy = kinematic_factor * self.beam_energy + self.energy_loss
        t = self.length / sqrt(2.0 * energy / self.recoiled_mass)
        # ERD: Uses recoiled_mass
        # RBS: Uses beam_mass, which is the same as recoiled_mass
        return t

    def get_point(self):
        """Get TOFCalibrationPoint values in tuple.

        Return:
            Returns TOFCalibrationPoint values in tuple.
        """
        return self.time_of_flight_channel, self.time_of_flight_seconds
