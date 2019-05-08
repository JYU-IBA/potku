# coding=utf-8
"""
Created on 7.5.2019
Updated on 8.5.2019

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
import os

from modules.general_functions import read_espe_file
from modules.general_functions import uniform_espe_lists
from modules.recoil_element import RecoilElement
from modules.point import Point

from shapely.geometry import Polygon


class Nsgaii:
    """
    Class that handles the NSGA-II optimization. This needs to handle both
    fluence and recoil element optimization. Recoil element optimization
    needs to handle at least two different types (one box or two boxes).
    """
    def __init__(self, eva, element_simulation=None, pop_size=10, sol_size=5,
                 upper_limits=[120, 1],
                 lower_limits=[0,0],
                 optimize_recoil=True, recoil_type="box",
                 starting_solutions=None, number_of_processes=1):
        self.evaluations = eva
        self.element_simulation = element_simulation  # Holds other needed
        # information including recoil points and access to simulation settings
        self.pop_size = pop_size
        self.sol_size = sol_size
        self.upper_limits = upper_limits
        self.lower_limits = lower_limits
        self.opt_recoil = optimize_recoil
        self.rec_type = recoil_type
        self.number_of_processes = number_of_processes

        # TODO: dynamic hist file
        hist_file = r"C:\Users\Heta\potku\requests\gradu_testi.potku" \
                         r"\Sample_01-s1\Measurement_01-m1\Energy_spectra\m1" \
                         r".16O.ERD.0.hist"
        results = []
        with open(hist_file, "r") as measu:
            results = measu.readlines()
        self.measured_espe = [
            (float(line.strip().split()[0]),
             float(line.strip().split()[1])) for line in results]

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
        objective_values = np.zeros((self.pop_size, 2))
        if self.opt_recoil:
            # Form points from first solution. First solution will always
            # cover the whole x axis range between lower and upper values ->
            # mcerd never needs to be run again
            if self.sol_size == 5:  # box that starts at the surface
                points = []
                sol = sols[0]
                point = (sol[0], sol[1])
                point_2 = (sol[2], sol[1])
                point_3 = (round(sol[2] + 0.01, 2), sol[3])
                point_4 = (sol[4], sol[3])
                points.append(Point(point))
                points.append(Point(point_2))
                points.append(Point(point_3))
                points.append(Point(point_4))

                # Form a recoil object
                current_recoil = RecoilElement(
                    self.element_simulation.recoil_elements[0].element, points,
                    "red", name="opt")
            else:
                # TODO: Handle other types of recoils
                current_recoil = None
            # Run mcerd for first solution
            self.element_simulation.optimization_recoils.append(current_recoil)
            self.element_simulation.start(self.number_of_processes, 201,
                                          optimize=True)

        j = 0
        for recoil in self.element_simulation.optimization_recoils:
            # Run get_espe
            self.element_simulation.calculate_espe(recoil,
                                optimize=True)
            # Read espe file
            espe_file = os.path.join(
                self.element_simulation.directory, recoil.prefix + "-" +
                recoil.name + ".simu")
            espe = read_espe_file(espe_file)
            # Change from string to float items
            espe = list(np.float_(espe))

            # Make spectra the same size
            espe, self.measured_espe = uniform_espe_lists(
                [espe, self.measured_espe],
                self.element_simulation.channel_width)

            # Find the area between simulated and measured energy spectra
            polygon_points = []
            for value in espe:
                polygon_points.append(value)

            for value in self.measured_espe[::-1]:
                polygon_points.append(value)

            # Add the first point again to close the rectangle
            polygon_points.append(polygon_points[0])

            polygon = Polygon(polygon_points)
            area = polygon.area
            # Find the summed distance between thw points of these two spectra
            sum_diff = 0
            i = 0
            for point in self.measured_espe:
                simu_point = espe[i]
                diff = abs(point[1] - simu_point[1])
                sum_diff += diff
                i += 1
            # TODO: Add created area and distance to objective values list
            j += 1
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
                # TODO: Needs checking to avoid indexoutofbounds error
                # TODO: Make this work for other than two y values
                x_upper = self.upper_limits[0]
                x_lower = self.lower_limits[0]
                y_lower = self.lower_limits[1]
                y_upper = self.upper_limits[1]

                # Create x coordinates
                x_coords = np.random.random_sample((self.pop_size - 1, 2)) * (
                    x_upper - x_lower) + x_lower
                # Add x0
                x_coords = np.insert(x_coords, 0, [0.0], axis=1)
                rounded_x = np.zeros((self.pop_size - 1, 3))

                # Create y coordinates
                y_coords = np.random.random_sample((2, self.pop_size - 1)) * (
                        y_upper - y_lower) + y_lower
                rounded_y = np.zeros((2, self.pop_size - 1))
                # Round coordinates accordingly
                for i in range(self.pop_size - 1):
                    rounded_x[i] = np.around(x_coords[i], decimals=2)
                for i in range(2):
                    rounded_y[i] = np.around(y_coords[i], decimals=4)

                # Sort x elements in ascending order
                rounded_x.sort(axis=1)
                # Add as first solution coordinate values that make simulation
                # concern the whole x coordinate range (with minimal y values
                # to speed up mcerd run
                first_x = np.array([0.0, round((x_upper - x_lower)/2, 2),
                                       x_upper])
                rounded_x_full = np.insert(rounded_x, 0, first_x, axis=0)
                first_y = np.array([0.0001, 0.0001])
                rounded_y_full = np.insert(rounded_y, 0, first_y, axis=1)

                i = 1
                j = 0
                init_sols = rounded_x_full
                while i < self.sol_size:
                    init_sols = np.insert(init_sols, i, rounded_y_full[j],
                                          axis=1)
                    i += 2
                    j += 1

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
