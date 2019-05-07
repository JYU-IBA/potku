# coding=utf-8
"""
Created on 7.5.2019

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2019 Heta Rekilä

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
__author__ = "Heta Rekilä"
__version__ = "2.0"

import numpy as np

from modules.recoil_element import RecoilElement


class Nsgaii:
    """
    Class that handles the NSGA-II optimization. This needs to handle both
    fluence and recoil element optimization. Recoil element optimization
    needs to handle at least two different types (one box or two boxes).
    """
    def __init__(self, eva, element_simulation=None, pop_size=10, sol_size=4,
                 upper_limits=[120, 1],
                 lower_limits=[0,0],
                 optimize_recoil=True, recoil_type="box",
                 starting_solutions=None):
        self.evaluations = eva
        self.element_simulation = element_simulation  # Holds other needed
        # information including recoil points and access to simulation settings
        self.pop_size = pop_size
        self.sol_size = sol_size
        self.upper_limits = upper_limits
        self.lower_limits = lower_limits
        self.opt_recoil = optimize_recoil
        self.rec_type = recoil_type
        # Create initial population
        if starting_solutions:
            # Change pop_size and sol_size to match given solutions
            self.population = self.evaluate_solutions(starting_solutions)
        else:
            self.population = self.initialize_population()
        self.start_optimization()

    def evaluate_solutions(self, sols):
        """
        Calculate objective function values for given solutions.

        Args:
             sols: List of solutions.

        Return:
            Solutions and their objective function values.
        """
        if self.opt_recoil:
            # Form points from first solution
            points = []
            for i in range(len(sols[0])):
                pass
            # Form a recoil object
            current_recoil = RecoilElement(
                self.element_simulation.recoil_elements[0].element, points,
                "red")
            zero_intervals = self.find_zero_intervals(current_recoil)
        for sol in sols:
            # This requires running mcerd and get_espe (see modefrontier
            # workflow)

            # Find the area between simulated and measured energy spectra
            # Find the summed distance between thw points of these two spectra
            pass
        return sols

    def find_zero_intervals(self, recoil):
        """
        Find zero intervals on the x axis.

        Args:
            Formed recoil.

        Return:
            List of zero intervals.
        """
        return []

    def initialize_population(self):
        """
        Create a new starting population.

        Return:
            Created population with solutions and objective function values.
        """
        init_sols = None
        if self.opt_recoil:  # Optimize recoil element
            if self.rec_type == "box":
                # Needed variables per solution: y0, x1, y1, x2 (x0 always 0)
                # For x decimal 0.01, for y 0.0001
                # Needs checking to avoid indexoutofbounds error
                x_upper = self.upper_limits[0]
                x_lower = self.lower_limits[0]
                y_lower = self.lower_limits[1]
                y_upper = self.upper_limits[1]
                # Create x coordinates
                x_coords = np.random.random_sample((self.pop_size - 1, 2)) * (
                    x_upper - x_lower) + x_lower
                rounded_x = np.zeros((self.pop_size - 1, 2))
                # Create y coordinates
                y_coords = np.random.random_sample((self.pop_size - 1, 2)) * (
                        y_upper - y_lower) + y_lower
                rounded_y = np.zeros((self.pop_size - 1, 2))
                # Round coordinates accordingly
                for i in range(self.pop_size - 1):
                    rounded_x[i] = np.around(x_coords[i], decimals=2)
                    rounded_y[i] = np.around(y_coords[i], decimals=4)
                # Add as first solution coordinate values that make simulation
                # concern the whole x coordinate range (with minimal y values
                # to speed up mcerd run
                first_x = np.array([round((x_upper - x_lower)/2, 2), x_upper])
                rounded_x_full = np.insert(rounded_x, 0, first_x, axis=0)
                first_y = np.array([0.0001, 0.0001])
                rounded_y_full = np.insert(rounded_y, 0, first_y, axis=0)

                # Join x and y to form the population
                # TODO: Fix this to work for other sized arrays
                init_sols = np.insert(rounded_x_full, 1, rounded_y_full[0],
                                      axis=1)
                init_sols = np.append(init_sols, rounded_y[1])
        pop = self.evaluate_solutions(init_sols)
        return pop

    def start_optimization(self):
        """
        Start the optimization. This includes sorting based on
        non-domination and crowding distance, creating offspring population
        by crossover and mutation, and selecting individuals to the new
        population.
        """
        # Sort the initial population according to non-domination
        # Calculate crowding distance for this population
        # In a loop until number of evaluations is reached:
        while self.evaluations >= 0:
            # Form mating pool
            # Select group of parents by binary_tournament
            # Form offspring population with this gropu
            # Do variation on offspring
            # Join parent population and offspring
            # Select individuals to new population based on non-domination
            # and crowding distance
            pass
        # Finally, sort by dodn-domination
        # Find first front and its first and last individual: these two are
        # the solutions that the user needs
