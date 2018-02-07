# coding=utf-8
'''
Created on 19.4.2013
Updated on 23.5.2013

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
'''
__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen \n Samuli Rahkonen \n Miika Raunio"
__versio__ = "1.0"

from Modules.Functions import hist, carbon_stopping
from Modules.Functions import convert_mev_to_joule, convert_amu_to_kg
from scipy import cos, sin, sqrt, pi

import scipy.optimize as optimize
from scipy.special import erf
from numpy import array, linspace
import collections

class TOFCalibrationHistogram:
    """Class for creating a histogram based on a cut file data. Can make a curve 
    fit to histogram's front edge.
    """
    def __init__(self, cut, bin_width, use_column=1):
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
        histed_file = hist(self.cut.data, self.bin_width, self.use_column)
        
        self.histogram_x = [float(pair[0]) for pair in histed_file]
        self.histogram_y = [float(pair[1]) for pair in histed_file]


    def get_error_function_parameters(self, end_of_front_edge,
                                      start_of_front_edge=0):
        """Get the parameters of the fitted curve. Parameters are used to specify 
        the range where the curve fit is made.
        
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
            params: namedtuple or tuple that brings the used parameters ("x0 A k").
            
        Return:
            Returns calculated error function value for x.
        """
        x0, A, k = params
        return A * (erf((x - x0) / k) + 1) / 2


    def __residuals(self, p, x, y):
        return y - self.error_function(x, p)


    def fit_error_function(self, x, y, guess_x0, guess_A, guess_k):
        """Fits a error function to the given data.
        
        Args:
            x: data's x axis a list
            y: data's y axis a list
            guess_x0: Guess for the x_0's value
            guess_A: Guess for the A's value
            guess_k: Guess for the k's value
            
        Return:
            tuple(x0, A, k) of parameters of a fitted error function. 
        """
        if len(x) < 2 or len(y) < 2:
            return None
        
        x = array(x)  # Numpy array
        y = array(y)

        Param = collections.namedtuple("Param", "x0 A k")
        p_guess = Param(x0=guess_x0, A=guess_A, k=guess_k)
        p, unused_cov, unused_infodict, unused_mesg, unused_ier = optimize.leastsq(
            self.__residuals, p_guess, args=(x, y), full_output=True)
        p = Param(*p)        

        return p.x0, p.A, p.k


    def find_middle(self):
        """
        Finds the point at x axis that is somewhere in the middle of the histogram.
        This is very inaccurate way.
        
        Return:
            The value at the histogram's x axis that is somewhere in the middle of 
            the top of the graph.
        """
        # Just take the biggest value.
        return self.histogram_y.index(max(self.histogram_y))
    
    
    def get_curve_fit_points(self, params, points_in_range):
        """Generates points from the error function with the histogram's range
        
        Args:
            params: tuple of parameters (x0, A, k)
            
        Return:
            tuple(xp, pxp) of generated lists of axis data (x and y axis)
        """
        x_values = linspace(self.histogram_x[0],
                            self.histogram_x[-1],
                            points_in_range)
        y_values = self.error_function(x_values, params)
        return x_values, y_values




class TOFCalibration:
    """Class for holding list of TOFCalibrationPoints and creating a linear fit 
    of their values.
    """
    def __init__(self):
        """Inits the class
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
        '''Removes a TOFCalibrationPoint from ToF Calibration
        
        Args:
            tof_calibration_point: TOFCalibrationPoint class object.
        
        Return:
            Returns True if point was removed. False otherwise.
        '''
        if self.point_exists(tof_calibration_point):
            self.tof_points.remove(tof_calibration_point)
            return True
        return False
                
        
    def point_exists(self, tof_calibration_point):
        '''Check if point exists in ToF Calibration.
        
        Args:
            tof_calibration_point: TOFCalibrationPoint class object.
            
        Return:
            Returns True if point exists. False otherwise.
        '''
        return tof_calibration_point in self.tof_points
        
        
    def get_points(self):
        """Returns TOFCalibrationPoints that have the point_used property set True.
        
        Return:
            tuple(x,y, name) of lists containing used points for the linear fit.
        """
        x = [point.time_of_flight_channel 
             for point in self.tof_points if point.point_used]
        y = [point.time_of_flight_seconds 
             for point in self.tof_points if point.point_used]
        name = [str(point.cut.element) 
                for point in self.tof_points if point.point_used]
        return x, y, name
        
        
    def linear_function(self, x, params):
        """The function used for linear fit. Takes the function parameters as a "namedtuple" or "tuple".
        a*x + b
        
        Args:
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
            guess_x0: Guess for the a's value
            guess_A: Guess for the b's value
            
        Returns:
            tuple(a, b) of parameters of a fitted linear function.
        """
        if len(x) < 2 or len(y) < 2:
            self.slope = None
            self.offset = None
            return None, None
        
        x = array(x)  # Numpy array
        y = array(y)
        
        Param = collections.namedtuple('Param', 'a b')
        p_guess = Param(a=guess_a, b=guess_b)
        try:
            p, unused_cov, unused_info, unused_mesg, unused_ier = optimize.leastsq(
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
            tuple(x_values, y_values) of generated lists of axis data (x and y axis)
        """
        x_values = linspace(x_min, x_max, points_in_range)
        y_values = self.linear_function(x_values, params)
        return x_values, y_values
        
        
    def get_fit_parameters(self):
        '''Get fit parameters.
        
        Return:
            Returns Slope and Offset of calibration.
        '''
        return self.slope, self.offset
        
        
        

class TOFCalibrationPoint:
    """ Class for the calculation of a theoretical time of flight.
    """
    def __init__(self, time_of_flight, cut, masses, settings):
        """ Inits the class.
        
        Args:
            time_of_flight:
            cut: CutFile class object.
            masses: Reference to Masses class object.
            settings: Settings class object.
        """
        self.cut = cut
        self.type = cut.type
        self.point_used = True
        self.masses = masses
        measuring_settings = settings.measuring_unit_settings
        
        # Recoiled atoms' parameters
        if cut.element.isotope.mass:
            mass = float(cut.element.isotope.mass)
        else:  # If the cut doesn't have a isotope, calculate standard atomic mass.
            mass = self.masses.get_standard_isotope(self.cut.element.name) 
        self.recoiled_mass = convert_amu_to_kg(mass) 
        standard_scatter_mass = self.masses.get_standard_isotope(
                                                         self.cut.element_scatter)
        
        # Measuring unit parameters
        beam_mass = float(measuring_settings.element.isotope.mass)
        # print("Beam mass: " + str(beam_mass))
        self.beam_mass = convert_amu_to_kg(beam_mass)
        self.beam_energy = convert_mev_to_joule(measuring_settings.energy)
        self.lenght = measuring_settings.time_of_flight_lenght
        # Target angle, same with both recoiled and scattered atoms when
        # using same hardware.
        self.target_angle = measuring_settings.detector_angle * pi / 180  
        self.scatter_element_mass_kg = convert_amu_to_kg(standard_scatter_mass)
        
        # print("Scatter mass: {0} amu {1} kg".format(standard_scatter_mass, 
        #                                            self.scatter_element_mass_kg))
        self.carbon_thickness = measuring_settings.carbon_foil_thickness
        
        # Calculate             
        energy = self.__calculate_particle_energy(self.beam_energy)
        
        isotope = self.cut.element.isotope.mass
        # If there's no isotope for the element, use the most common isotope
        if not isotope:  #
            isotope = self.masses.get_most_common_isotope(self.cut.element.name)[0]
            
        print(str(isotope))
        # Carbon stopping gives a list of different result values. 
        # The last value is the stopping energy. 
        try:
            carb_stop = carbon_stopping(self.cut.element.name,
                                              isotope,
                                              energy,
                                              self.carbon_thickness)
            carbon_stopping_energy = float(carb_stop[-1])
        except:
            error_msg = "Carbon stopping doesn't work. {0} {1}".format(
                                               "Continuing without it.",
                                               "Carbon stopping energy set to 0.")
            # logging.getLogger("").error(error_msg) # TODO: Add to error logger
            print(error_msg)
            carbon_stopping_energy = 0
    
        self.stopping_energy = convert_mev_to_joule(carbon_stopping_energy)
        
        
        print(self.stopping_energy)
        
        self.time_of_flight_channel = time_of_flight  # (CHANNEL)
        self.time_of_flight_seconds = self.calculate_time_of_flight()  # (SECONDS)
        print("\nCut file type: " + str(self.type) + 
              "\nRecoiled mass [kg]: " + str(self.recoiled_mass) + 
              "\nRecoiled/scattered particle energy [J]: " + str(energy) + 
              "\nBeam mass [kg]: " + str(self.beam_mass) + 
              "\nBeam energy [J]: " + str(self.beam_energy) + 
              "\nToF lenght [m]: " + str(self.lenght) + 
              "\nTarget angle [rads]" + str(self.recoiled_mass) + 
              "\nStopping energy [J]: " + str(self.stopping_energy) + 
              "\nTime of Flight [Channel]: " + str(self.time_of_flight_channel) + 
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
        '''Get Time of Flight channel.
        
        Return:
            Returns Time of Flight channel.
        '''
        return self.time_of_flight_channel
    
    
    def get_tof_seconds(self):
        '''Get Time of Flight seconds.
        
        Return:
            Returns Time of Flight seconds.
        '''
        return self.time_of_flight_seconds
    
    
    def get_name(self):
        '''Get name of the used CutFile.
        
        Return:
            Returns name of the used CutFile.
        '''
        return str(self.cut.element)
        
    
    def __kinematic_factor(self, selection_type):
        """ Calculates the kinematic factor.
        
        ERD: (4 * M_I * M_R * cos(a)^2) / (M_I + M_R)^2
        RBS: (sqrt(( M_R^2 - M_I^2 * cos(a)^2) + M_I * cos(a)) / (M_I + M_R))^2
        
        Args:
            selection_type: String representing what type of selection was detected.
        
        Return:
            Returns calculated kinematic factor based on selection type.
        """
        # TODO: Print -> Raise and/or logger.error
        error_msg = "Impossible parameters for calculating kinematic factor."
        if selection_type == "ERD":
            cosin = cos(self.target_angle)
            mass_sum = self.beam_mass + self.recoiled_mass
            if mass_sum == 0:
                raise
                print("{0}{1}".format(error_msg, "Division by zero."))
                return None
            kinematic_factor = 4 * self.beam_mass * self.recoiled_mass * cosin \
                * cosin / (mass_sum * mass_sum)
            return kinematic_factor
        elif selection_type == "RBS":
            cosin = cos(self.target_angle)
            sine = sin(self.target_angle)
            mass_sum = self.beam_mass + self.recoiled_mass
            square = self.recoiled_mass * self.recoiled_mass \
                - self.beam_mass * self.beam_mass * sine * sine
            if square <= 0:
                print("{0}".format(error_msg))
                return None
            k = (sqrt(square) + self.beam_mass * cosin) / mass_sum
            kinematic_factor = k * k
            return kinematic_factor
        else:
            return None
        
        
    def calculate_time_of_flight(self):
        """ Calculates the time of flight.
            In case of ERD use:
            
            t = l/(sqrt( 2 * (k * E_I0 - dE_RT1) / M_R))
            where:
            
            E_I0 = beam energy
            dE_RT1 = stopping energy of the recoiled particle
            M_R = mass of the recoiled particle
            M_I = mass of the scattered particle
            k = kinetic factor, which is (4 * M_I * M_R * cos(a)^2) / (M_I + M_R)^2
            
            In case of RBS use:
            
            t = l/(sqrt( 2 * (k * E_I0 - dE_IT1) / M_R))
            where:
            
            dE_RT1 = stopping energy of the scattered particle
            M_R = mass of the recoiled particle
            M_I = mass of the scattered particle
            k = kinetic factor, which is (sqrt(( M_R^2 - M_I^2 * cos(a)^2) + M_I * 
                    cos(a)) / (M_I + M_R))^2
            
            
            Return:
                Calculated time of flight as float. None if the cut file's type is 
                not either ERD or RBS.
        """
        # TODO: Print -> Raise and/or logger.error
        t = None
        if self.type == "ERD":
            cosin = cos(self.target_angle)
            mass_sum = self.beam_mass + self.recoiled_mass
            kinematic_factor = 4 * self.beam_mass * self.recoiled_mass * cosin \
                * cosin / (mass_sum * mass_sum)
            square = ((2.0 * (kinematic_factor * self.beam_energy) \
                - self.stopping_energy) / self.recoiled_mass)
            if square <= 0:
                print("Impossible parameters.")
                return None
            t = self.lenght / (sqrt(square))
        elif self.type == "RBS":
            cosin = cos(self.target_angle)
            sine = sin(self.target_angle)
            mass_sum = self.beam_mass + self.scatter_element_mass_kg
            square = self.scatter_element_mass_kg * self.scatter_element_mass_kg \
                - self.beam_mass * self.beam_mass * sine * sine
            if square <= 0:
                print("Impossible parameters.")
                return None
            k = (sqrt(square) + self.beam_mass * cosin) / mass_sum
            kinematic_factor = k * k
            
            t = self.lenght / (sqrt((2.0 * (kinematic_factor * self.beam_energy) \
                - self.stopping_energy) / self.beam_mass))
        return t
    
    
    def get_point(self):
        '''Get TOFCalibrationPoint values in tuple.
        
        Return:
            Returns TOFCalibrationPoint values in tuple.
        '''
        return tuple(self.time_of_flight_channel, self.time_of_flight_seconds)    
     
