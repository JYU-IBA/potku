# coding=utf-8
"""
Created on 7.5.2019
Updated on 9.5.2019

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
import time

from modules.general_functions import dominates
from modules.general_functions import read_espe_file
from modules.general_functions import tournament_allow_doubles
from modules.general_functions import uniform_espe_lists
from modules.recoil_element import RecoilElement
from modules.point import Point

from shapely.geometry import Polygon


class Nsgaii:
    """
    Class that handles the NSGA-II optimization. This needs to handle both
    fluence and recoil element optimization. Recoil element optimization
    needs to handle at least two different types (one box or two boxes).
    NSGA-II implementation has been influenced by the original paper (Deb,
    2002), a paper by Seshadri (2006) and a Python implementation by Hust
    (https://github.com/ChengHust/NSGA-II).
    """
    def __init__(self, gen, element_simulation=None, pop_size=100, sol_size=5,
                 upper_limits=None, lower_limits=None, optimize_recoil=True,
                 recoil_type="box", starting_solutions=None,
                 number_of_processes=1, cross_p=0.9, mut_p=1, dis_c=20,
                 dis_m=20):
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
            optimize_recoil: Whether to optimize recoil or fluence.
            recoil_type: Type of recoil: either "box" (4 points or 5),
            "two_peak" (high areas at both ends of recoil, low in the middle)
             or "free" (no limits to the shape of the recoil).
            starting_solutions: First solutions used in optimization. If
            none, initialize new solutions.
            number_of_processes: How many processes are used in MCERD
            calculation.
            cross_p: Crossover probability.
            mut_p: Mutation probability, should be something small.
            dis_c: Distribution index for crossover. When this is big,
            a  new solution is close to its parents.
            dis_m: Distribution for mutation.
        """
        self.evaluations = gen * pop_size
        self.element_simulation = element_simulation  # Holds other needed
        # information including recoil points and access to simulation settings
        self.pop_size = pop_size
        self.sol_size = sol_size
        self.upper_limits = upper_limits
        if not self.upper_limits:
            self.upper_limits = [120, 1]
        self.lower_limits = lower_limits
        if not self.lower_limits:
            self.lower_limits = [0, 0]
        self.opt_recoil = optimize_recoil
        self.rec_type = recoil_type
        self.number_of_processes = number_of_processes
        self.mcerd_run = False

        # Crossover and mutation parameters
        self.cross_p = cross_p
        self.dis_c = dis_c
        self.mut_p = mut_p
        self.dis_m = dis_m
        self.__start = None

        # TODO: dynamic hist file
        hist_file = r"C:\Users\Heta\potku\requests\gradu_testi.potku" \
                         r"\Sample_01-s1\Measurement_01-m1\Energy_spectra\m1" \
                         r".16O.ERD.0.hist"

        with open(hist_file, "r") as measu:
            results = measu.readlines()
        self.measured_espe = [
            (float(line.strip().split()[0]),
             float(line.strip().split()[1])) for line in results]

        # Modify measurement file to match the simulation file in regards to
        # the x coordinates -> they have matching values for ease of distance
        # counting
        self.modify_measurement()

        # Create initial population
        if starting_solutions:
            # Change pop_size and sol_size to match given solutions
            self.__start = time.clock()
            self.population = self.evaluate_solutions(starting_solutions)
        else:
            self.population = self.initialize_population()
        self.start_optimization()

    def crowding_distance(self, front_no, pop_obj=None):
        """
        Calculate crowding distnce for each solution in the population, by the
        Pareto front it belongs to.

        Args:
            front_no: Front numbers for all solutions.

        Return:
            Array that holds crowding distances for all solutions.
        """
        if pop_obj is None:
            pop_obj = self.population[1]
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
                    current_distance = (pop_obj[(ind_front_next, i)] -
                                        pop_obj[(ind_front_prev, i)]) / (
                                                   f_max[i] - f_min[i]
                                                   )
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
        size = len(sols)
        objective_values = np.zeros((size, 2))
        if self.opt_recoil:
            # Empty the list of optimization recoils
            self.element_simulation.optimization_recoils = []

            # Form points from first solution. First solution of first
            # population will always cover the whole x axis range between
            # lower and upper values -> mcerd never needs to be run again
            current_recoil = self.form_recoil(sols[0])
            # TODO: Handle other types of recoils
            # Run mcerd for first solution
            self.element_simulation.optimization_recoils.append(current_recoil)
            if not self.mcerd_run:
                self.element_simulation.start(self.number_of_processes, 201,
                                              optimize=True)
                self.mcerd_run = True

            # Create other recoils
            for solution in sols[1:]:
                recoil = self.form_recoil(solution)
                self.element_simulation.optimization_recoils.append(recoil)

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
            if espe:
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
                # Find the summed distance between thw points of these two
                # spectra
                sum_diff = 0
                i = 0
                for point in self.measured_espe:
                    simu_point = espe[i]
                    diff = abs(point[1] - simu_point[1])
                    sum_diff += diff
                    i += 1
                objective_values[j] = np.array([area, sum_diff])
            else:  # If failed to create energy spectrum
                objective_values[j] = np.array([np.inf, np.inf])
            j += 1

        population = [sols, objective_values]
        return population

    def form_recoil(self, current_solution):
        """
        Form recoil based on solution size.

        Args:
            current_solution: Solution which holds the information needed t
            form the recoil.

        Return:
             Recoil Element.
        """
        points = []
        if self.sol_size == 5:  # box that starts at the surface
            point = (current_solution[0], current_solution[1])
            point_2 = (current_solution[2], current_solution[1])

            x_3 = round(current_solution[2] + 0.01, 2)
            point_3 = (x_3, current_solution[3])

            point_4 = (current_solution[4], current_solution[3])

            points.append(Point(point))
            points.append(Point(point_2))
            points.append(Point(point_3))
            points.append(Point(point_4))

        # Form a recoil object
        recoil = RecoilElement(
            self.element_simulation.recoil_elements[0].element, points,
            "red", name="opt")
        return recoil

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
                # TODO: Make this work for other than two y values
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
                # concern the whole x coordinate range
                first_x = np.array([0.0, round((x_upper - x_lower)/2, 2),
                                       x_upper])
                rounded_x_full = np.insert(rounded_x, 0, first_x, axis=0)
                first_y = np.array([round((y_upper - y_lower)/2, 2), 0.0001])
                rounded_y_full = np.insert(rounded_y, 0, first_y, axis=1)

                i = 1
                j = 0
                init_sols = rounded_x_full
                # init_sols will be x, y, x, y, x (4-point recoil)
                while i < self.sol_size:
                    init_sols = np.insert(init_sols, i, rounded_y_full[j],
                                          axis=1)
                    i += 2
                    j += 1
                # Change upper and lower limits to have individual indices
                #  for each solution (makes variation easier)
                self.upper_limits = []
                self.lower_limits = []
                k = 0
                while k in range(self.sol_size):
                    self.upper_limits.append(x_upper)
                    self.lower_limits.append(x_lower)
                    k += 1
                    if k == self.sol_size:
                        break
                    else:
                        self.upper_limits.append(y_upper)
                        self.lower_limits.append(y_lower)
                        k += 1

        self.__start = time.clock()
        pop = self.evaluate_solutions(init_sols)
        return pop

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
        self.measured_espe.insert(0, (round(first_x - 0.025, 4), 0.0))
        self.measured_espe.append((round(last_x + 0.025, 4), 0.0))

        while i < len(self.measured_espe) - 1:  # Do nothing to the last point
            current_point = self.measured_espe[i]
            next_point = self.measured_espe[i + 1]

            new_x = round((next_point[0] + current_point[0]) / 2, 4)
            new_y = round((next_point[1] + current_point[1]) / 2, 5)
            new.append((new_x, new_y))
            i += 1
        self.measured_espe = new

    def nd_sort(self, pop_obj, n, r_n=np.inf):
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
            r_n = self.pop_size
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
                if dominates(p, q):
                    s_p.append((q, h))
                elif dominates(q, p):
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

    def new_population_selection(self, population):
        """
        Select individuals to a new population based on crowded comparison
        operator.

        Args:
            population: Current intermediate population.

        Return:
            Next generation population.
        """
        pop_n, t = np.shape(population[0])
        # Sort intermediate population based on non-domination
        front_no, last_front_no = self.nd_sort(population[1], pop_n,
                                               self.pop_size)
        include_in_next = [False for i in range(front_no.size)]
        # Find all individuals that belong to better fronts, except the last one
        # that doesn't fit
        for i in range(front_no.size):
            if front_no[i] < last_front_no:
                include_in_next[i] = True
        # Calculate crowding distance for all individuals
        crowd_dis = self.crowding_distance(front_no, population[1])

        # Find last front that maybe doesn't fit properly
        last = [i for i in range(len(front_no)) if front_no[i] == last_front_no]
        # Rank holds the indices corresponding to last that have crowding
        # distance from biggest to smallest
        rank = np.argsort(-crowd_dis[last])
        delta_n = rank[: (self.pop_size - int(np.sum(include_in_next)))]
        # Get indices corresponding to population for individuals to be included
        #  in the next generation.
        rest = [last[i] for i in delta_n]
        for i in rest:
            include_in_next[i] = True
        index = np.array(
            [i for i in range(len(include_in_next)) if include_in_next[i]])
        next_pop = [population[0][index, :], population[1][index, :]]

        return next_pop, front_no[index], crowd_dis[index]

    def start_optimization(self):
        """
        Start the optimization. This includes sorting based on
        non-domination and crowding distance, creating offspring population
        by crossover and mutation, and selecting individuals to the new
        population.
        """
        # Sort the initial population according to non-domination
        front_no, last_front_no = self.nd_sort(self.population[1],
                                               self.pop_size)
        # Initial population is sorted according to non-domination, without
        # crowding distance. crowd_dis is still needed when initial population
        # is joined with the offspring population.
        crowd_dis = self.crowding_distance(front_no)
        # In a loop until number of evaluations is reached:
        evaluations = self.evaluations
        while evaluations > 0:
            # Join front_no and crowd_dis with transpose to get one array
            fit = np.vstack((front_no, crowd_dis)).T
            # Select group of parents (mating pool) by binary_tournament,
            # usually number of parents is half of population.
            # TODO: mating pool size user-determined
            pool_size = round(self.pop_size / 2)
            pool_ind = tournament_allow_doubles(2, pool_size, fit)
            pop_sol, pop_obj = self.population[0], self.population[1]
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
                intermediate_population)
            # Change surrent population to new population
            self.population = new_population

            # Update the amount of evaluation left
            evaluations -= self.pop_size

            # Temporary prints
            if evaluations % (10*self.evaluations/self.pop_size) == 0:

                end = time.clock()
                percent = 100*(self.evaluations - evaluations)/self.evaluations
                print(
                    'Running time %10.2f, percentage %s, done %f' % (
                        end-self.__start, percent, self.evaluations -
                        evaluations))

        # Finally, sort by non-domination
        front_no, last_front_no = self.nd_sort(self.population[1],
                                               self.pop_size)
        # Find first front
        pareto_optimal_sols = self.population[0][front_no == 1, :]
        pareto_optimal_objs = self.population[1][front_no == 1, :]
        # Find front's first and last individual: these two are the solutions
        # the user needs
        first = pareto_optimal_objs[0]
        last = pareto_optimal_objs[-1]
        f_i = 0
        l_i = len(pareto_optimal_objs) - 1
        for i in range(1, len(pareto_optimal_objs)):
            current = pareto_optimal_objs[i]
            if current[0] > last[0]:
                last = current
                l_i = i
            elif current[1] > first[1]:
                first = current
                f_i = i

        first_sol  = pareto_optimal_sols[f_i]
        last_solution = pareto_optimal_sols[l_i]

    def variation(self, pop_sols):
        """
        Generate offspring population using SBX and polynomial mutation.

        Args:
            pop_sols: Solutions that are used to create offspring population.

        Return:
            Offspring size self.pop_size.
        """
        offspring = []
        pop_dec_n, t = np.shape(pop_sols)
        p = 0
        while p in range(self.pop_size):
            was_crossover = False
            was_mutation = False
            if np.random.uniform() <= self.cross_p:  # Do crossover.
                # Find two random unique indices for two parents.
                p_1 = np.random.randint(pop_dec_n)
                p_2 = np.random.randint(pop_dec_n)
                parent_1 = pop_sols[p_1]
                parent_2 = pop_sols[p_2]
                while (parent_1 == parent_2).all():
                    p_2 = np.random.randint(pop_dec_n)
                    parent_2 = pop_sols[p_2]

                child_1 = []
                child_2 = []
                for j in range(self.sol_size):
                    # Simulated Binary Crossover - SBX
                    u = np.random.uniform()
                    if u <= 0.5:
                        beta = (2*u) ** (1/(self.dis_c + 1))
                    else:
                        beta = (1/(2*(1 - u)))**(1/(self.dis_c + 1))
                    c_1 = 0.5*((1 + beta)*parent_1[j] +
                                   (1 - beta)*parent_2[j])
                    c_2 = 0.5*((1 - beta)*parent_1[j] +
                                   (1 + beta)*parent_2[j])
                    if c_1 > self.upper_limits[j]:
                        c_1 = self.upper_limits[j]
                    elif c_1 < self.lower_limits[j]:
                        c_1 = self.lower_limits[j]
                    if c_2 > self.upper_limits[j]:
                        c_2 = self.upper_limits[j]
                    elif c_2 < self.lower_limits[j]:
                        c_2 = self.lower_limits[j]

                    # Add child variables to children.
                    child_1.append(c_1)
                    child_2.append(c_2)

                was_crossover = True
                offspring.append(np.array(child_1))
                p += 1
                # Add only n amount children to get the right sized offspring
                #  population.
                if p >= self.pop_size:
                    break
                offspring.append(np.array(child_2))
                p += 1
            if np.random.uniform() <= self.mut_p:  # Do mutation.
                p_i = np.random.randint(pop_dec_n)
                parent = pop_sols[p_i]
                child = []
                for i in range(self.sol_size):
                    # Polynomial mutation.
                    r = np.random.uniform()
                    if r < 0.5:
                        delta = (2*r)**(1/(self.dis_m + 1)) - 1
                    else:
                        delta = 1 - (2*(1 - r))**(1/(self.dis_m + 1))
                    c = parent[i] + delta*(self.upper_limits[i] -
                                           self.lower_limits[i])
                    if c > self.upper_limits[i]:
                        c = self.upper_limits[i]
                    elif c < self.lower_limits[i]:
                        c = self.lower_limits[i]

                    # Add child variable to mutated child.
                    child.append(c)

                offspring.append(np.array(child))
                was_mutation = True
                p += 1
            if not was_crossover and not was_mutation:
                # If no crossover or mutation was done, still need to add a
                # new child to offspring.
                p_i = np.random.randint(pop_dec_n)
                child = pop_sols[p_i]
                offspring.append(np.array(child))
                p += 1

        return np.array(offspring)
