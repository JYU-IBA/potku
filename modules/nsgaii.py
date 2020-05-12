# coding=utf-8
"""
Created on 7.5.2019
Updated on 27.5.2019

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
import collections
import rx
import subprocess
import math

import modules.optimization as opt
import modules.general_functions as gf
import modules.file_paths as fp
import modules.math_functions as mf

from pathlib import Path
from timeit import default_timer as timer
from rx import operators as ops

from modules.recoil_element import RecoilElement
from modules.point import Point
from modules.parsing import CSVParser
from modules.energy_spectrum import EnergySpectrum
from modules.observing import Observable
from modules.concurrency import CancellationToken
from modules.enums import OptimizationType
from modules.enums import OptimizationState


class Nsgaii(Observable):
    """
    Class that handles the NSGA-II optimization. This needs to handle both
    fluence and recoil element optimization. Recoil element optimization
    needs to handle at least two different types (one box or two boxes).
    NSGA-II implementation has been influenced by the original paper (Deb,
    2002), a paper by Seshadri (2006) and a Python implementation by Hust
    (https://github.com/ChengHust/NSGA-II).
    """

    def __init__(self, gen, element_simulation=None, pop_size=100, sol_size=5,
                 upper_limits=None, lower_limits=None,
                 optimization_type=OptimizationType.RECOIL,
                 recoil_type="box", number_of_processes=1, cross_p=0.9, mut_p=1,
                 stop_percent=0.3, check_time=20, ch=0.025,
                 measurement=None, cut_file=None, dis_c=20,
                 dis_m=20, check_max=900, check_min=0, skip_simulation=False):
        """
        Initialize the NSGA-II algorithm with needed parameters and start
        running it.

        Args:
            gen: Number of generations to be done.
            element_simulation: ElementSimulation object that is optimized.
            pop_size: Population size.
            sol_size: Amount of variables in one solution.
            upper_limits: Upper limit(s) for variables in a solution.
            lower_limits: Lower limit(s) for a variable in a solution.
            optimization_type: Whether to optimize recoil or fluence.
            recoil_type: Type of recoil: either "box" (4 points or 5),
                "two-peak" (high areas at both ends of recoil, low in the
                middle) or "free" (no limits to the shape of the recoil).
                number_of_processes: How many processes are used in MCERD
                calculation.
            cross_p: Crossover probability.
            mut_p: Mutation probability, should be something small.
            stop_percent: When to stop running MCERD (based on the ratio in
            average change between checkups).
            check_time: Time interval for checking if MCERD should be stopped.
            ch: Channel with for running get_espe.
                used in comparing the simulated energy spectra.
            dis_c: Distribution index for crossover. When this is big,
                a new solution is close to its parents.
            dis_m: Distribution for mutation.
            check_max: Maximum time for running a simulation.
            check_min: Minimum time for running a simulation.
            skip_simulation: whether simulation is skipped altogether
        """
        # TODO separate the two optimization types into two classes
        Observable.__init__(self)
        self.evaluations = gen * pop_size
        self.element_simulation = element_simulation  # Holds other needed
        # information including recoil points and access to simulation settings
        self.pop_size = pop_size
        self.sol_size = sol_size
        self.upper_limits = upper_limits
        if not self.upper_limits:
            self.upper_limits = [120, 1]
        self.lower_limits = lower_limits
        if self.lower_limits is None:
            self.lower_limits = [0.01, 0.0001]
        self.optimization_type = optimization_type
        self.rec_type = recoil_type

        # MCERd specific parameters
        self.number_of_processes = number_of_processes
        self._skip_simulation = skip_simulation
        self.stop_percent = stop_percent
        self.check_time = check_time
        self.check_max = check_max
        self.check_min = check_min

        self.channel_width = ch

        # Crossover and mutation parameters
        self.cross_p = cross_p
        self.dis_c = dis_c
        self.mut_p = mut_p
        self.dis_m = dis_m
        self.__const_var_i = []
        self.bit_length_x = 0
        self.bit_length_y = 0

        self.measurement = measurement
        self.cut_file = Path(cut_file)

        self.population = None
        self.measured_espe = None

    def __prepare_optimization(self, initial_pop=None, cancellation_token=None):
        """Performs internal preparation before optimization begins.
        """
        # Calculate the energy spectrum that the optimized solutions are
        # compared to.
        if self.measurement is None:
            raise ValueError("Optimization could not be prepared, "
                             "no measurement defined.")

        self.element_simulation.optimized_fluence = None

        es = EnergySpectrum(self.measurement, [self.cut_file],
                            self.channel_width, no_foil=True)

        # TODO maybe just use he value returned by calc_spectrum?
        x = es.calculate_spectrum(no_foil=True)
        # Add result files
        hist_file = Path(self.measurement.directory_energy_spectra,
                         f"{self.cut_file.stem}.no_foil.hist")

        parser = CSVParser((0, float), (1, float))
        self.measured_espe = list(parser.parse_file(hist_file, method="row"))

        # Previous erd files are used as the starting point so combine them
        # into a single file
        erd_file_name = fp.get_erd_file_name(
            self.element_simulation.recoil_elements[0], "combined",
            optim_mode=self.optimization_type)

        gf.combine_files(self.element_simulation.get_erd_files(),
                         Path(self.element_simulation.directory,
                              erd_file_name))

        # Modify measurement file to match the simulation file in regards to
        # the x coordinates -> they have matching values for ease of distance
        # counting
        self.modify_measurement()

        # Create initial population
        if initial_pop is None:
            initial_pop = self.initialize_population()

        # Find bit variable lengths if necessary
        if self.optimization_type is OptimizationType.RECOIL:
            self.find_bit_variable_lengths()
            # Empty the list of optimization recoils

            # Form points from first solution. First solution of first
            # population will always cover the whole x axis range between
            # lower and upper values -> mcerd never needs to be run again
            self.element_simulation.optimization_recoils = [
                self.form_recoil(initial_pop[0])
            ]

        if not self._skip_simulation:
            def stop_if_cancelled(optim_ct, mcerd_ct):
                if optim_ct.is_cancellation_requested():
                    mcerd_ct.request_cancellation()
                return mcerd_ct.is_cancellation_requested()

            ct = CancellationToken()
            observable = self.element_simulation.start(
                self.number_of_processes, start_value=201,
                optimization_type=self.optimization_type,
                cancellation_token=ct,
                print_to_console=True, max_time=self.check_max)

            if observable is not None:
                self.on_next(self._get_message(
                    OptimizationState.SIMULATING,
                    evaluations_left=self.evaluations))

                ct_check = rx.timer(0, 0.2).pipe(
                    ops.take_while(lambda _: not stop_if_cancelled(
                        cancellation_token, ct)),
                    ops.filter(lambda _: False),
                )

                spectra_chk = rx.timer(self.check_min, self.check_time).pipe(
                    ops.merge(ct_check),
                    ops.map(lambda _: get_optim_espe(
                        self.element_simulation, self.optimization_type)),
                    ops.scan(
                        lambda prev_espe, next_espe: (prev_espe[1], next_espe),
                        seed=[None, None]),
                    ops.map(lambda espes: calculate_change(
                        *espes, self.element_simulation.channel_width)),
                    ops.take_while(
                        lambda change: change > self.stop_percent and not
                        ct.is_cancellation_requested()
                    ),
                    ops.do_action(
                        on_completed=ct.request_cancellation)
                )
                merged = rx.merge(observable, spectra_chk).pipe(
                    ops.take_while(
                        lambda x: not isinstance(x, dict) or x["is_running"],
                        inclusive=True)
                )
                # Simulation needs to finish before optimization can start
                # so we run this synchronously.
                # TODO use callback instead of running sync
                merged.run()
                # TODO should not have to call this manually
                self.element_simulation._clean_up(ct)

            else:
                raise ValueError(
                    "Could not start simulation. Check that simulation is not "
                    "currently running.")

        self.population = self.evaluate_solutions(initial_pop)

    @staticmethod
    def _get_message(state, **kwargs):
        """Returns a dictionary with the state of the optimization and
        other """
        return {
            "state": state,
            **kwargs
        }

    @classmethod
    def crowding_distance(cls, front_no, objective_values):
        """
        Calculate crowding distnce for each solution in the population, by the
        Pareto front it belongs to.

        Args:
            front_no: Front numbers for all solutions.
            objective_values: collection of objective values

        Return:
            Array that holds crowding distances for all solutions.
        """
        pop_obj = np.array(objective_values)
        n, m = np.shape(pop_obj)
        crowd_dis = np.zeros(n)
        # Get all front numbers.
        front_unique = np.unique(front_no)
        fronts = front_unique[front_unique != np.inf]
        for f in range(len(fronts)):
            # All the indices corresponding to solutions belonging to front f
            front = np.array(
                [k for k in range(len(front_no)) if front_no[k] == fronts[f]])
            # Find min and max values for objective functions
            f_max = pop_obj[front, :].max(0)
            f_min = pop_obj[front, :].min(0)
            for i in range(m):
                # Sort the front's solutions according to its ith objective.
                # rank[i] tells the index in front -> front[rank[i]] tells the
                # index in pop_obj
                rank = np.argsort(pop_obj[front, i])
                # Current front's first and last get infinitive crowding
                # distance values
                crowd_dis[front[rank[0]]] = np.inf
                crowd_dis[front[rank[-1]]] = np.inf
                for j in range(1, len(front) - 1):
                    ind_pop = front[rank[j]]
                    ind_front_next = front[rank[j + 1]]
                    ind_front_prev = front[rank[j - 1]]
                    # Normalize the objective function values
                    dist = pop_obj[(ind_front_next, i)] - \
                        pop_obj[(ind_front_prev, i)]
                    if dist == 0:
                        current_distance = 0
                    else:
                        # TODO raises RuntimeWarning here if simulation time
                        #  outs before presim ends
                        current_distance = dist / (f_max[i] - f_min[i])
                    crowd_dis[ind_pop] = crowd_dis[ind_pop] + current_distance
        return crowd_dis

    def evaluate_solutions(self, sols):
        """
        Calculate objective function values for given solutions.

        Args:
             sols: List of solutions.

        Return:
            Solutions and their objective function values.
        """
        objective_values = []
        if self.optimization_type is OptimizationType.RECOIL:
            self.element_simulation.optimization_recoils = [
                self.form_recoil(solution) for solution in sols
            ]

            for recoil in self.element_simulation.optimization_recoils:
                # Run get_espe
                espe_file = self.element_simulation.calculate_espe(
                    recoil, optimization_type=self.optimization_type,
                    ch=self.channel_width)
                objective_values.append(self.get_objective_values(espe_file))

        else:  # Evaluate fluence
            recoil = self.element_simulation.recoil_elements[0]
            for solution in sols:
                # Round solution appropriately
                sol_fluence = gf.round_value_by_four_biggest(solution[0])
                # Run get_espe
                espe_file = self.element_simulation.calculate_espe(
                    recoil, optimization_type=self.optimization_type,
                    ch=self.channel_width, fluence=sol_fluence)
                objective_values.append(self.get_objective_values(espe_file))

        pop = collections.namedtuple("Population",
                                     ("solutions", "objective_values"))
        return pop(sols, objective_values)

    def get_objective_values(self, espe_file):
        """Calculates the objective values and returns them as a np.array.
        """
        obj_values = collections.namedtuple("ObjectiveValues",
                                            ("area", "sum_distance"))
        optim_espe = gf.read_espe_file(espe_file)
        if optim_espe:
            # Make spectra the same size
            optim_espe, measured_espe = gf.uniform_espe_lists(
                [optim_espe, self.measured_espe],
                self.element_simulation.channel_width)

            # Find the area between simulated and measured energy
            # spectra
            area = mf.calculate_area(optim_espe, measured_espe)

            # Find the summed distance between thw points of these two
            # spectra
            sum_diff = sum(abs(opt_p[1] - mesu_p[1])
                           for opt_p, mesu_p in zip(optim_espe, measured_espe))

            return obj_values(area, sum_diff)
        # If failed to create energy spectrum
        return obj_values(np.inf, np.inf)

    def find_bit_variable_lengths(self):
        # Find needed size to hold x and y in binary
        size_of_x = (self.upper_limits[0] - self.lower_limits[0]) * 100
        size_bin_x = bin(int(size_of_x))
        try:
            b_index = size_bin_x.index("b")
            len_of_x = len(size_bin_x[b_index + 1:])
        except ValueError:
            len_of_x = len(size_bin_x)

        size_of_y = (self.upper_limits[1] - self.lower_limits[1]) * 10000
        size_bin_y = bin(int(size_of_y))
        try:
            b_index = size_bin_y.index("b")
            len_of_y = len(size_bin_y[b_index + 1:])
        except ValueError:
            len_of_y = len(size_bin_y)

        self.bit_length_x = len_of_x
        self.bit_length_y = len_of_y

    def form_recoil(self, current_solution, name=""):
        """
        Form recoil based on solution size.

        Args:
            current_solution: Solution which holds the information needed t
            form the recoil.
            name: Possible name for recoil element.

        Return:
             Recoil Element.
        """
        points = []
        if self.sol_size == 5:  # box that starts at the surface
            # Find which x coordinate is smaller
            if current_solution[2] < current_solution[4]:
                x_2 = current_solution[2]
                x_4 = current_solution[4]
            else:
                x_2 = current_solution[4]
                x_4 = current_solution[2]
            point = (current_solution[0], current_solution[1])
            point_2 = (x_2, current_solution[1])

            x_3 = round(x_2 + 0.01, 2)
            point_3 = (x_3, current_solution[3])

            point_4 = (x_4, current_solution[3])

            points.append(Point(point))
            points.append(Point(point_2))
            points.append(Point(point_3))
            points.append(Point(point_4))

        elif self.sol_size == 7:  # 6-point recoil, doesn't start at the surface
            # Order x:s in ascending way
            xs = [current_solution[2], current_solution[4], current_solution[6]]
            xs.sort()
            point_1 = (current_solution[0], current_solution[1])
            point_2 = (xs[0], current_solution[1])

            x_3 = round(xs[0] + 0.01, 2)
            point_3 = (x_3, current_solution[3])
            point_4 = (xs[1], current_solution[3])

            x_5 = round(xs[1] + 0.01, 2)
            point_5 = (x_5, current_solution[5])
            point_6 = (xs[2], current_solution[5])

            points.append(Point(point_1))
            points.append(Point(point_2))
            points.append(Point(point_3))
            points.append(Point(point_4))
            points.append(Point(point_5))
            points.append(Point(point_6))
        # For these two, the y coordinate between peaks should eb lower than
        # the peaks' y coordinates -> make adjustment like in x
        elif self.sol_size == 9:  # 8-point two peak recoil, starts at the
            # surface
            xs = [current_solution[2], current_solution[4], current_solution[
                6], current_solution[8]]
            xs.sort()
            # Find second smallest y value, use it for y1 (smallest is last y)
            second_smallest = current_solution[1]
            i = 3
            ss_i = 1
            while i in range(len(current_solution)):
                if i == 7:  # Last y doesn't count
                    break
                sol = current_solution[i]
                if sol < second_smallest:
                    ss_i = i
                    second_smallest = sol
                i += 2

            if ss_i == 1:
                point_1 = (current_solution[0], current_solution[3])
                point_2 = (xs[0], current_solution[3])
            else:
                point_1 = (current_solution[0], current_solution[1])
                point_2 = (xs[0], current_solution[1])

            x_3 = round(xs[0] + 0.01, 2)
            if ss_i == 3:
                point_3 = (x_3, current_solution[3])
                point_4 = (xs[1], current_solution[3])
            else:
                point_3 = (x_3, second_smallest)
                point_4 = (xs[1], second_smallest)

            x_5 = round(xs[1] + 0.01, 2)
            if ss_i == 5:
                point_5 = (x_5, current_solution[3])
                point_6 = (xs[2], current_solution[3])
            else:
                point_5 = (x_5, current_solution[5])
                point_6 = (xs[2], current_solution[5])

            x_7 = round(xs[2] + 0.01, 2)
            if ss_i == 7:
                point_7 = (x_7, current_solution[3])
                point_8 = (xs[3], current_solution[3])
            else:
                point_7 = (x_7, current_solution[7])
                point_8 = (xs[3], current_solution[7])

            points.append(Point(point_1))
            points.append(Point(point_2))
            points.append(Point(point_3))
            points.append(Point(point_4))
            points.append(Point(point_5))
            points.append(Point(point_6))
            points.append(Point(point_7))
            points.append(Point(point_8))
        else:  # 10-point two peak recoil, doesn't start at the surface
            xs = [current_solution[2], current_solution[4], current_solution[
                6], current_solution[8], current_solution[10]]
            xs.sort()
            # Find second smallest y value, use it for y1 (smallest is last y)
            second_smallest = current_solution[3]
            i = 5
            ss_i = 3
            while i in range(len(current_solution)):
                if i == 9:  # Last y doesn't count
                    break
                sol = current_solution[i]
                if sol < second_smallest:
                    ss_i = i
                    second_smallest = sol
                i += 2

            point_1 = (current_solution[0], current_solution[1])
            point_2 = (xs[0], current_solution[1])

            x_3 = round(xs[0] + 0.01, 2)
            if ss_i == 3:
                point_3 = (x_3, current_solution[5])
                point_4 = (xs[1], current_solution[5])
            else:
                point_3 = (x_3, current_solution[3])
                point_4 = (xs[1], current_solution[3])

            x_5 = round(xs[1] + 0.01, 2)
            if ss_i == 5:
                point_5 = (x_5, current_solution[5])
                point_6 = (xs[2], current_solution[5])
            else:
                point_5 = (x_5, second_smallest)
                point_6 = (xs[2], second_smallest)

            x_7 = round(xs[2] + 0.01, 2)
            if ss_i == 7:
                point_7 = (x_7, current_solution[5])
                point_8 = (xs[3], current_solution[5])
            else:
                point_7 = (x_7, current_solution[7])
                point_8 = (xs[3], current_solution[7])

            x_9 = round(xs[3] + 0.01, 2)
            if ss_i == 9:
                point_9 = (x_9, current_solution[5])
                point_10 = (xs[4], current_solution[5])
            else:
                point_9 = (x_9, current_solution[9])
                point_10 = (xs[4], current_solution[9])

            points.append(Point(point_1))
            points.append(Point(point_2))
            points.append(Point(point_3))
            points.append(Point(point_4))
            points.append(Point(point_5))
            points.append(Point(point_6))
            points.append(Point(point_7))
            points.append(Point(point_8))
            points.append(Point(point_9))
            points.append(Point(point_10))

        # Form a recoil object
        if not name:
            name = "opt"
        else:
            name = name

        recoil = RecoilElement(
            self.element_simulation.recoil_elements[0].element, points,
            color="red", name=name)

        return recoil

    def initialize_population(self):
        """
        Create a new starting population.

        Return:
            Created population with solutions and objective function values.
        """
        if self.optimization_type is OptimizationType.RECOIL:
            if len(self.upper_limits) < 2:
                x_upper = 1.0
                y_upper = 1.0
            else:
                x_upper = self.upper_limits[0]
                y_upper = self.upper_limits[1]
            if len(self.lower_limits) < 2:
                x_lower = 0.0
                y_lower = 0.0
            else:
                x_lower = self.lower_limits[0]
                y_lower = self.lower_limits[1]
            if self.rec_type == "box":
                if self.sol_size == 5:  # 4-point recoil
                    # Needed variables per solution for 4-point recoil:
                    # x0, y0, x1, y1, x2 (x0, y1 and x2 constants)

                    x_coords = get_xs(x_lower, x_upper, self.pop_size)

                    self.__const_var_i.append(0)
                    self.__const_var_i.append(4)

                    y_coords = get_ys(y_lower, y_upper, self.pop_size)

                    # Add y1 to constants
                    self.__const_var_i.append(3)

                    # Sort x elements in ascending order
                    x_coords.sort(axis=1)

                    # Add as first solution coordinate values that make
                    # simulation concern the whole x coordinate range
                    first_x = np.array([0.0, round((x_upper - x_lower)/2, 2),
                                       x_upper])
                    x_coords_full = np.insert(x_coords, 0, first_x, axis=0)
                    first_y = np.array([round((y_upper - y_lower)/2, 4),
                                        0.0001])
                    y_coords_full = np.insert(y_coords, 0, first_y, axis=1)

                else:  # Handle 6-point recoil
                    # Needed variables per solution for 6-point recoil:
                    # x0, y0, x1, y1, x2, y2, x3 (x0, y0, y2 and x3 constants)
                    x_coords = get_xs(x_lower, x_upper, self.pop_size, 2)

                    # Add x0 index to constant variables
                    self.__const_var_i.append(0)
                    self.__const_var_i.append(6)

                    y_coords = get_ys(y_lower, y_upper, self.pop_size,
                                      lower_limit_at_first=True)

                    # Add y0 and y2 to constants
                    self.__const_var_i.append(1)
                    self.__const_var_i.append(5)

                    # Sort x elements in ascending order
                    x_coords.sort(axis=1)

                    # Add as first solution coordinate values that make
                    # simulation concern the whole x coordinate range
                    first_x = np.array([0.0,
                                        round((x_upper - x_lower) / 3, 2),
                                        round(2 * ((x_upper - x_lower) / 3), 2),
                                        x_upper])
                    x_coords_full = np.insert(x_coords, 0, first_x, axis=0)
                    first_y = np.array([0.0001,
                                        round((y_upper - y_lower) / 2, 4),
                                        0.0001])
                    y_coords_full = np.insert(y_coords, 0, first_y, axis=1)

            else:  # Two-peak recoil
                if self.sol_size == 9:  # First peak at the surface
                    # Needed variables per solution for 6-point recoil:
                    # x0, y0, x1, y1, x2, y2, x3, y3, x4
                    # (x0, y3 and x4 constants)
                    x_coords = get_xs(x_lower, x_upper, self.pop_size, 3)

                    # Add x0 index to constant variables
                    self.__const_var_i.append(0)
                    self.__const_var_i.append(8)

                    y_coords = get_ys(y_lower, y_upper, self.pop_size, z=3)

                    # Add y3 to constants
                    self.__const_var_i.append(7)

                    # Sort x elements in ascending order
                    x_coords.sort(axis=1)

                    # Add as first solution coordinate values that make
                    # simulation concern the whole x coordinate range
                    first_x = np.array([0.0,
                                        round((x_upper - x_lower) / 4, 2),
                                        round((x_upper - x_lower) / 2, 2),
                                        round(3 * ((x_upper - x_lower) / 4), 2),
                                        x_upper])
                    x_coords_full = np.insert(x_coords, 0, first_x, axis=0)
                    first_y = np.array([round((y_upper - y_lower) / 2, 4),
                                        0.0001,
                                       round((y_upper - y_lower) / 2, 4),
                                        0.0001])
                    y_coords_full = np.insert(y_coords, 0, first_y, axis=1)
                else:  # First peak not at the surface
                    # Needed variables per solution for 6-point recoil:
                    # x0, y0, x1, y1, x2, y2, x3, y3, x4, y4, x5
                    # (x0, y0, y4 and x5 constants)
                    x_coords = get_xs(x_lower, x_upper, self.pop_size, 4)

                    self.__const_var_i.append(0)
                    self.__const_var_i.append(10)

                    y_coords = get_ys(y_lower, y_upper, self.pop_size, z=3,
                                      lower_limit_at_first=True)

                    # Add y0 and y4 to constants
                    self.__const_var_i.append(1)
                    self.__const_var_i.append(9)

                    # Sort x elements in ascending order
                    x_coords.sort(axis=1)

                    # Add as first solution coordinate values that make
                    # simulation concern the whole x coordinate range
                    first_x = np.array([0.0,
                                        round((x_upper - x_lower) / 5, 2),
                                        round(2 * (x_upper - x_lower) / 5, 2),
                                        round(3 * ((x_upper - x_lower) / 5), 2),
                                        round(4 * ((x_upper - x_lower) / 5), 2),
                                        x_upper])
                    x_coords_full = np.insert(x_coords, 0, first_x, axis=0)
                    first_y = np.array([0.0001,
                                        round((y_upper - y_lower) / 2, 4),
                                        0.0001,
                                        round((y_upper - y_lower) / 2, 4),
                                        0.0001])
                    y_coords_full = np.insert(y_coords, 0, first_y, axis=1)

            i = 1
            j = 0
            init_sols = x_coords_full
            # init_sols will be x, y, x, y, x (4-point recoil)
            # x, y, x, y, x, y, x (6-point recoil)
            while i < self.sol_size:
                init_sols = np.insert(init_sols, i, y_coords_full[j],
                                      axis=1)
                i += 2
                j += 1
        else:  # Initialize a population for fluence
            # Change upper and lower limits to have individual indices
            #  for each solution (makes variation easier for real values)
            upper_limits = np.zeros((1, self.sol_size))
            lower_limits = np.zeros((1, self.sol_size))
            k = 0
            while k in range(self.sol_size):
                upper_limits[k] = self.upper_limits
                lower_limits[k] = self.lower_limits
                k += 1
            self.lower_limits = lower_limits
            self.upper_limits = upper_limits

            # Create a random population
            init_sols = np.random.random_sample(
                (self.pop_size, self.sol_size)) * \
                (self.upper_limits - self.lower_limits) \
                + self.lower_limits

        return init_sols

    def modify_measurement(self):
        """
        Modify measured energy spectrum to match the simulated in regards to
        the x coordinates.
        """
        new = []
        i = 0
        # Add zero points to start and end to get correct mean values
        first_x = self.measured_espe[0][0]
        last_x = self.measured_espe[-1][0]

        # TODO could use deque for quicker inserts
        self.measured_espe.insert(
            0, (round(first_x - self.element_simulation.channel_width, 4), 0.0))
        self.measured_espe.append(
            (round(last_x + self.element_simulation.channel_width, 4), 0.0))

        while i < len(self.measured_espe) - 1:  # Do nothing to the last point
            current_point = self.measured_espe[i]
            next_point = self.measured_espe[i + 1]

            new_x = round((next_point[0] + current_point[0]) / 2, 4)
            new_y = round((next_point[1] + current_point[1]) / 2, 5)
            new.append((new_x, new_y))
            i += 1
        self.measured_espe = new

    @classmethod
    def nd_sort(cls, pop_obj, n, r_n=np.inf):
        """
        Sort population pop_obj according to non-domination.

        Args:
            pop_obj: Solutions (objective function values).
            n: Size of the current population to be sorted.
            r_n: How many elements fit inside the resulting population.

        Return:
            List with front numbers, corresponding to pop_obj indices, number of
            last front found.
        """
        if r_n == np.inf:
            r_n = n
        # Coded according to algorithm given by Deb(2002)
        # Go through all solutions
        front_no = np.inf * np.ones(n)
        fronts = 0
        front_1 = []  # Holds pop_obj and index in one element
        added_solutions = 0
        s_i = [i for i in range(n)]  # s_p holds pop_obj and its index in one
        # element
        n_i = np.zeros(n)
        # front_no, pop_obj and s_i plus n_i -> all have corresponding indices
        for i in range(len(pop_obj)):
            p = pop_obj[i]
            s_p = []
            n_p = 0
            for h in range(len(pop_obj)):
                q = pop_obj[h]
                if np.array_equal(p, q):
                    continue
                if opt.dominates(p, q):
                    s_p.append((q, h))
                elif opt.dominates(q, p):
                    n_p += 1
            if n_p == 0:
                front_no[i] = 1
                front_1.append((p, i))
                added_solutions += 1
            s_i[i] = s_p
            n_i[i] = n_p
        fronts += 1

        current_front = front_1
        f_n = 1
        while current_front:
            if added_solutions >= r_n:
                break
            new_front = []
            for j in range(len(current_front)):
                p = current_front[j]
                p_i = p[1]
                s_p = s_i[p_i]
                for k in range(len(s_p)):
                    q = s_p[k][0]
                    index = s_p[k][1]
                    n_q = n_i[index]
                    n_q -= 1
                    n_i[index] = n_q
                    if n_q == 0:
                        front_no[index] = f_n + 1
                        new_front.append((q, index))
                        added_solutions += 1
            f_n += 1
            current_front = new_front
            fronts += 1
        return front_no, fronts

    @classmethod
    def new_population_selection(cls, population, pop_size):
        """
        Select individuals to a new population based on crowded comparison
        operator.

        Args:
            population: Current intermediate population.
            pop_size: TODO

        Return:
            Next generation population.
        """
        pop_n, t = np.shape(population[0])
        # Sort intermediate population based on non-domination
        front_no, last_front_no = Nsgaii.nd_sort(population[1], pop_n, pop_size)
        include_in_next = [False for _ in range(front_no.size)]
        # Find all individuals that belong to better fronts, except the last one
        # that doesn't fit
        for i in range(front_no.size):
            if front_no[i] < last_front_no:
                include_in_next[i] = True
        # Calculate crowding distance for all individuals
        crowd_dis = Nsgaii.crowding_distance(front_no, population[1])

        # Find last front that maybe doesn't fit properly
        last = [i for i in range(len(front_no)) if front_no[i] == last_front_no]
        # Rank holds the indices corresponding to last that have crowding
        # distance from biggest to smallest
        rank = np.argsort(-crowd_dis[last])
        delta_n = rank[: (pop_size - int(np.sum(include_in_next)))]
        # Get indices corresponding to population for individuals to be included
        #  in the next generation.
        rest = [last[i] for i in delta_n]
        for i in rest:
            include_in_next[i] = True
        index = np.array(
            [i for i in range(len(include_in_next)) if include_in_next[i]])
        next_pop = [population[0][index, :], population[1][index, :]]

        return next_pop, front_no[index], crowd_dis[index]

    def start_optimization(self, starting_solutions=None,
                           cancellation_token=None):
        """
        Start the optimization. This includes sorting based on
        non-domination and crowding distance, creating offspring population
        by crossover and mutation, and selecting individuals to the new
        population.

        Args:
            starting_solutions: First solutions used in optimization. If
                None, initialize new solutions.
            cancellation_token: CancellationToken that is used to stop the
                optimization before all evaluations have been evaluated.
        """
        self.on_next(self._get_message(
            OptimizationState.PREPARING, evaluations_left=self.evaluations))
        try:
            self.__prepare_optimization(starting_solutions, cancellation_token)
        except (OSError, ValueError, subprocess.SubprocessError) as e:
            self.on_error(self._get_message(
                OptimizationState.FINISHED,
                error=f"Preparation for optimization failed: {e}"))
            self.clean_up(cancellation_token)
            return

        start_time = timer()

        self.on_next(self._get_message(
            OptimizationState.RUNNING, evaluations_left=self.evaluations))

        # Sort the initial population according to non-domination
        front_no, last_front_no = self.nd_sort(self.population[1],
                                               self.pop_size)
        # Initial population is sorted according to non-domination, without
        # crowding distance. crowd_dis is still needed when initial population
        # is joined with the offspring population.
        crowd_dis = self.crowding_distance(front_no, self.population[1])
        # In a loop until number of evaluations is reached:
        evaluations = self.evaluations
        while evaluations > 0:
            if cancellation_token is not None:
                if cancellation_token.is_cancellation_requested():
                    break
            # Join front_no and crowd_dis with transpose to get one array
            fit = np.vstack((front_no, crowd_dis)).T
            # Select group of parents (mating pool) by binary_tournament,
            # usually number of parents is half of population.
            pool_size = round(self.pop_size / 2)

            try:
                pool_ind = opt.tournament_allow_doubles(2, pool_size, fit)
            except IndexError:
                self.on_error(self._get_message(
                    OptimizationState.FINISHED,
                    error="Ensure that there is simulated data for this recoil "
                          "element before starting optimization."))
                self.clean_up(cancellation_token)
                return
            pop_sol, pop_obj = np.array(self.population[0]), \
                np.array(self.population[1])
            pool = [pop_sol[pool_ind, :], pop_obj[pool_ind, :]]
            # Form offspring solutions with this pool, and do variation on them
            offspring = self.variation(pool[0])
            # Evaluate offspring solutions to get offspring population
            offspring_pop = self.evaluate_solutions(offspring)
            # Join parent population and offspring population
            joined_sols = np.vstack((self.population[0], offspring_pop[0]))
            joined_objs = np.vstack((self.population[1], offspring_pop[1]))
            intermediate_population = [joined_sols, joined_objs]
            # Select solutions (and objective function values) to new
            # population (size self.pop_size) based on non-domination and
            # crowding distance
            new_population, front_no, crowd_dis = self.new_population_selection(
                intermediate_population, self.pop_size)
            # Change surrent population to new population
            self.population = new_population

            # Update the amount of evaluation left
            evaluations -= self.pop_size

            elapsed_time = timer() - start_time
            self.on_next(self._get_message(
                OptimizationState.RUNNING, evaluations_left=evaluations,
                pareto_front=self.population[1][front_no == 1, :],
                elapsed=elapsed_time))

            # Temporary prints
            if evaluations % (10*self.evaluations/self.pop_size) == 0:
                percent = 100*(self.evaluations - evaluations)/self.evaluations
                print(
                    'Running time %10.2f, percentage %s, done %f' % (
                        elapsed_time - start_time, percent, self.evaluations -
                        evaluations))

        # Finally, sort by non-domination
        front_no, last_front_no = self.nd_sort(self.population[1],
                                               self.pop_size)
        # Find first front
        try:
            pareto_optimal_sols = self.population[0][front_no == 1, :]
            pareto_optimal_objs = self.population[1][front_no == 1, :]
        except TypeError:
            self.on_error(self._get_message(
                OptimizationState.FINISHED,
                error="Could not form the Pareto front. Optimization may have "
                      "been stopped before any solutions were evaluated."))
            self.clean_up(cancellation_token)
            return

        if self.optimization_type is OptimizationType.RECOIL:
            first_sol, med_sol, last_sol = pick_final_solutions(
                pareto_optimal_objs, pareto_optimal_sols, count=3)

            # Save the three pareto solutions as recoils
            self.element_simulation.optimization_recoils = []
            first_recoil = self.form_recoil(first_sol, "optfirst")
            self.element_simulation.optimization_recoils.append(first_recoil)
            med_recoil = self.form_recoil(med_sol, "optmed")
            self.element_simulation.optimization_recoils.append(med_recoil)
            last_recoil = self.form_recoil(last_sol, "optlast")
            self.element_simulation.optimization_recoils.append(last_recoil)
        else:
            # Calculate average of found fluences
            f_sum = 0
            for sol in pareto_optimal_sols:
                f_sum += sol[0]
            avg = f_sum / len(pareto_optimal_sols)
            self.element_simulation.optimized_fluence = avg

        self.clean_up(cancellation_token)
        self.save_results_to_file()

        self.on_completed(self._get_message(
            OptimizationState.FINISHED,
            evaluations_done=self.evaluations - evaluations))

    def clean_up(self, cancellation_token):
        if cancellation_token is not None:
            cancellation_token.request_cancellation()
        self.delete_temp_files()

    def delete_temp_files(self):
        # Remove unnecessary opt.recoil file
        for file in os.listdir(self.element_simulation.directory):
            # TODO better method for determining which files to delete
            if file.endswith("opt.recoil") or "optfl" in file:
                try:
                    os.remove(Path(self.element_simulation.directory, file))
                except OSError:
                    pass

    def save_results_to_file(self):
        if self.optimization_type is OptimizationType.RECOIL:
            # Save optimized recoils
            for recoil in self.element_simulation.optimization_recoils:
                recoil.to_file(self.element_simulation.directory)
            save_file_name = f"{self.element_simulation.name_prefix}" \
                             f"-opt.measured"
            with open(Path(self.element_simulation.directory, save_file_name),
                      "w") as f:
                f.write(self.cut_file.stem)
        elif self.element_simulation.optimized_fluence != 0:
            # save found fluence value
            file_name = f"{self.element_simulation.name_prefix}-optfl.result"
            with open(Path(self.element_simulation.directory, file_name),
                      "w") as f:
                f.write(str(self.element_simulation.optimized_fluence))

    def variation(self, pop_sols):
        """
        Generate offspring population using SBX and polynomial mutation for
        fluence, and simple binary crossover and binary
        mutation for recoil element points.

        Args:
            pop_sols: Solutions that are used to create offspring population.

        Return:
            Offspring size self.pop_size.
        """
        offspring = []
        pop_dec_n, t = np.shape(pop_sols)
        p = 0  # How many solutions have been added to offspring

        # Crossover
        while p in range(self.pop_size):
            # Find two random unique indices for two parents.
            p_1 = np.random.randint(pop_dec_n)
            p_2 = np.random.randint(pop_dec_n)
            parent_1 = pop_sols[p_1]
            parent_2 = pop_sols[p_2]
            while (parent_1 == parent_2).all():
                p_2 = np.random.randint(pop_dec_n)
                parent_2 = pop_sols[p_2]

            binary_parent_1 = []
            binary_parent_2 = []
            # If no crossover, parents are used in mutation
            if self.optimization_type is OptimizationType.RECOIL:
                # Transform child 1 and 2 into binary mode, to match the
                # possible values when taking decimal precision into account
                # Transform variables into binary
                binary_parent_1 = solution_to_binary(parent_1,
                                                     self.bit_length_x,
                                                     self.bit_length_y)
                binary_parent_2 = solution_to_binary(parent_2,
                                                     self.bit_length_x,
                                                     self.bit_length_y)
                child_1 = binary_parent_1
                child_2 = binary_parent_2
            else:
                child_1 = parent_1
                child_2 = parent_2
            if np.random.uniform() <= self.cross_p:  # Do crossover.
                # Select between real coded of binary handling
                if self.optimization_type is OptimizationType.RECOIL:
                    child_1, child_2 = opt.single_point_crossover(
                        binary_parent_1, binary_parent_2)

                else:  # Fluence finding crossover
                    child_1, child_2 = opt.simulated_binary_crossover(
                        parent_1, parent_2, self.lower_limits,
                        self.upper_limits, self.dis_c, self.sol_size
                    )

            offspring.append(child_1)
            p += 1
            if p >= self.pop_size:
                break
            else:
                offspring.append(child_2)
                p += 1

        if self.optimization_type is OptimizationType.RECOIL:
            # Do binary mutation
            # Calculate length of one solution (number of bits)
            sol_length = 0
            for var in offspring[0]:
                sol_length += len(var)

            # Do mutation for offspring population
            do_mutation = np.ones((self.pop_size, sol_length),
                                  dtype=bool)
            # Avoid mutating constants
            bit_index = 0
            for i in range(self.sol_size):
                if i % 2 == 0:
                    length = self.bit_length_x
                else:
                    length = self.bit_length_y
                if i in self.__const_var_i:
                    do_mutation[:, bit_index: bit_index + length] = False
                bit_index += length

            # Indicate mutation for all variables that have a random number
            # over mut_p / sol_length
            do_mutation_prob = np.random.random_sample(
                (self.pop_size,  sol_length)) < self.mut_p / sol_length
            total_mutation_bool = np.logical_and(do_mutation, do_mutation_prob)

            # Change offspring array that holds each binary string in an array
            for i in range(self.pop_size):
                for j in range(self.sol_size):
                    r = offspring[i][j]
                    int_list = [int(x) for x in list(r)]
                    offspring[i][j] = np.array(int_list)
                # Flatten the row
                offspring[i] = np.ndarray.flatten(np.array(offspring[i]))
            # Transform offspring into numpy arrya
            offspring = np.array(offspring)
            # Use mutation mask
            offspring[total_mutation_bool] = offspring[total_mutation_bool] ^ 1

            # Change variables back to decimal
            dec_offspring = []
            for k in range(self.pop_size):
                sol = []
                b_i = 0
                for h in range(self.sol_size):
                    if h % 2 == 0:
                        # Make one variable list into string
                        str_bin = ''.join(
                            str(b) for b in offspring[k][b_i:b_i +
                                                         self.bit_length_x])
                        b_i += self.bit_length_x
                        # Turn variable back into decimal
                        dec = round(int(str_bin, 2)/100, 2)
                        if h not in self.__const_var_i:
                            # Check of out of limits, not for constants
                            if dec < self.lower_limits[0]:
                                dec = self.lower_limits[0]
                            if dec > self.upper_limits[0]:
                                dec = self.upper_limits[0]
                    else:
                        # Make one variable list into string
                        str_bin = ''.join(
                            str(b) for b in offspring[k][b_i:b_i +
                                                         self.bit_length_y])
                        b_i += self.bit_length_y
                        # Turn variable back into decimal
                        dec = round(int(str_bin, 2)/10000, 4)
                        # Don't do anything to constants
                        if h not in self.__const_var_i:
                            if dec < self.lower_limits[1]:
                                dec = self.lower_limits[1]
                            if dec > self.upper_limits[1]:
                                dec = self.upper_limits[1]
                    sol.append(dec)
                dec_offspring.append(np.array(sol))

            offspring = np.array(dec_offspring)

        else:  # Real coded mutation
            # Indicate mutation for all variables that have a random number
            # over mut_p / self.sol_size
            do_mutation_prob = np.random.random_sample(
                (self.pop_size, self.sol_size)) < self.mut_p / self.sol_size

            # Polynomial mutation.
            # r = np.random.uniform()
            # if r < 0.5:
            #     delta = (2*r)**(1/(self.dis_m + 1)) - 1
            # else:
            #     delta = 1 - (2*(1 - r))**(1/(self.dis_m + 1))
            # c = parent[i] + delta*(self.upper_limits[i] -
            #                        self.lower_limits[i])

            r = np.random.random_sample((self.pop_size, self.sol_size))
            # Define which solution use which delta value
            use_r_smaller = do_mutation_prob & (r < 0.5)

            upper = np.tile(self.upper_limits[0], (self.pop_size, 1))
            lower = np.tile(self.lower_limits[0], (self.pop_size, 1))

            # Change offspring to numpy array
            off = [np.array([item]) for item in offspring]
            offspring = np.array(off)

            # delta = np.power(2*r[use_r_smaller], (1 / (self.dis_m + 1))) - 1
            #
            #
            # offspring[use_r_smaller] += (upper[use_r_smaller] -
            #                              lower[use_r_smaller]) * delta
            #
            # use_r_bigger = do_mutation_prob & (r >= 0.5)
            # delta = 1 - np.power(2*(1 - r[use_r_bigger]),
            #                      (1 / (self.dis_m + 1)))
            # offspring[use_r_bigger] += (upper[use_r_bigger] -
            #                             lower[use_r_bigger]) * delta
            norm = (offspring[use_r_smaller] - lower[use_r_smaller]) / (
                        upper[use_r_smaller] - lower[use_r_smaller])
            offspring[use_r_smaller] += (upper[use_r_smaller] - lower[use_r_smaller]) * \
                                   (np.power(2. * r[use_r_smaller] + (
                                               1. - 2. * r[use_r_smaller]) * np.power(
                                       1. - norm, self.dis_m + 1.),
                                             1. / (self.dis_m + 1)) - 1.)
            use_r_bigger = do_mutation_prob & (r >= 0.5)
            norm = (upper[use_r_bigger] - offspring[use_r_bigger]) / (
                        upper[use_r_bigger] - lower[use_r_bigger])
            offspring[use_r_bigger] += (upper[use_r_bigger] - lower[use_r_bigger]) * \
                                   (1. - np.power(
                                       2. * (1. - r[use_r_bigger]) + 2. * (
                                                   r[use_r_bigger] - 0.5) * np.power(
                                           1. - norm, self.dis_m + 1.),
                                       1. / (self.dis_m + 1.)))
            offspring_limits = np.maximum(np.minimum(offspring, upper), lower)
            offspring = offspring_limits

        return np.array(offspring)


def solution_to_binary(solution, bit_length_x, bit_length_y):
    """Returns a binary representation of a solution.
    """
    bin_sol = []
    for i in range(len(solution)):
        if i % 2 == 0:
            # Get rid of decimals
            var = int(solution[i] * 100)
            format_x = gf.format_to_binary(var, bit_length_x)
            bin_sol.append(format_x)
        else:
            # Get rid of decimals
            var = int(solution[i] * 10000)
            format_y = gf.format_to_binary(var, bit_length_y)
            bin_sol.append(format_y)
    return bin_sol


def pick_final_solutions(objective_values, solutions, count=2):
    """Picks solutions from the given set of solutions based on the
    corresponding objective values.

    Args:
        objective_values: collections of objective values
        solutions: collections of solutions
        count: how many solutions to return (2 or 3)

    Returns:
        tuple of solutions. Either (first solution, last solution) or
        (first solution, median solution, last solution) depending on
        the count parameter.
    """
    # Find front's first and last individual: these two are the
    # solutions the user needs
    if not 2 <= count <= 3:
        raise ValueError("Solution count must be either 2 or 3.")

    zipped = list(zip(objective_values, solutions))

    # TODO if we assume that the solutions are pareto optimal, only one
    #  sorting is enough
    sorted_by_area = sorted(zipped, key=lambda tpl: tpl[0][0])
    sorted_by_distance = sorted(zipped, key=lambda tpl: tpl[0][1])

    first, last = sorted_by_area[0][1], sorted_by_distance[0][1]

    if count == 3:
        return first, sorted_by_distance[len(sorted_by_distance) // 2][1], last
    return first, last


def get_xs(x_lower, x_upper, pop_size, z=None):
    """Returns x coordinates for all initial solutions.
    """
    if z is None:
        size = pop_size - 1
    else:
        size = (pop_size - 1, z)
    # Create x coordinates (ints)
    x_coords = np.random.randint(int(x_lower * 100),
                                 int(x_upper * 100) + 1,
                                 size=size)
    # Make x coords have the correct decimal precision
    x_coords = np.around(x_coords / 100, 2)
    # Add x0
    zeros = np.zeros(pop_size - 1)
    if z is None:
        x_coords = np.vstack((zeros, x_coords)).T
    else:
        x_coords = np.insert(x_coords, 0, zeros, axis=1)

    # Make last x match the upper limit, add to constants
    x_lasts = np.full((pop_size - 1, 1), x_upper)
    return np.append(x_coords, x_lasts, axis=1)


def get_ys(y_lower, y_upper, pop_size, z=None, lower_limit_at_first=False):
    """Returns y coordinates for all initial solutions.
    """
    if z is None:
        size = pop_size - 1
    else:
        size = (z, pop_size - 1)
    # Create y coordinates
    y_coords = np.random.randint(int(y_lower * 10000),
                                 int(y_upper * 10000) + 1,
                                 size=size)
    # Make y coords have the correct decimal precision
    y_coords = np.around(y_coords / 10000, 4)
    # Make y2 coords be lower limit
    low_limit = np.full(pop_size - 1, y_lower)

    if z is None:
        # Make y0 coords be lower limit
        if lower_limit_at_first:
            return np.array([low_limit, y_coords, low_limit])
        else:
            return np.array([y_coords, low_limit])
    else:
        if lower_limit_at_first:
            return np.array([low_limit, y_coords[0], y_coords[1],
                             y_coords[2], low_limit])
    return np.array([y_coords[0], y_coords[1], y_coords[2], low_limit])


def get_optim_espe(elem_sim, optimization_type):
    if optimization_type is OptimizationType.RECOIL:
        recoil = elem_sim.optimization_recoils[0]
    else:
        recoil = elem_sim.recoil_elements[0]

    espe_file = elem_sim.calculate_espe(
        recoil, optimization_type=optimization_type)
    return gf.read_espe_file(espe_file)


def calculate_change(espe1, espe2, channel_width):
    if not espe1 or not espe2:
        return math.inf
    uniespe1, uniespe2 = gf.uniform_espe_lists([espe1, espe2], channel_width)

    # Calculate distance between energy spectra
    # TODO move this to math_functions
    sum_diff = 0
    amount = 0
    for point1, point2 in zip(uniespe1, uniespe2):
        if point1[1] != 0 or point2[1] != 0:
            amount += 1
            sum_diff += abs(point1[1] - point2[1])
    # Take average of sum_diff (non-zero diffs)
    if amount:
        return sum_diff / amount
    else:
        return math.inf
