# coding=utf-8
"""
Created on 29.1.2020

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2013-2018 Heta Rekilä, 2020 Juhani Sundell,
2021 Tuomas Pitkänen

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

Optimization module contains functions used in NSGA2 algorithm
"""

__author__ = "Heta Rekilä \n Juhani Sundell \n Tuomas Pitkänen"
__version__ = "2.0"

import os
import abc
import math
from pathlib import Path
from typing import Any

import numpy as np
import rx
from rx import operators as ops

from . import file_paths as fp
from . import general_functions as gf
from .concurrency import CancellationToken
from .element_simulation import ElementSimulation
from .energy_spectrum import EnergySpectrum
from .enums import IonDivision
from .enums import OptimizationState
from .enums import OptimizationType
from .mcerd import MCERD
from .observing import Observable
from .parsing import CSVParser


class BaseOptimizer(abc.ABC, Observable):
    """A base class for optimizers.
    """

    def __init__(self, evaluations=None,
                 element_simulation: ElementSimulation = None,
                 upper_limits=None, lower_limits=None,
                 optimization_type=OptimizationType.RECOIL, recoil_type="box",
                 number_of_processes=1, stop_percent=0.3, check_time=20,
                 ch=0.025, measurement=None, cut_file=None, check_max=900,
                 check_min=0, skip_simulation=False, use_efficiency=False,
                 verbose=False, optimize_by_area=True) -> None:
        """Initialize a BaseOptimizer.

        Args:
            evaluations: Number of evaluations to be done.
            element_simulation: ElementSimulation object that is optimized.
            upper_limits: Upper limit(s) for variables in a solution.
            lower_limits: Lower limit(s) for a variable in a solution.
            recoil_type: Type of recoil: either "box" (4 points or 5),
                "two-peak" (high areas at both ends of recoil, low in the
                middle) or "free" (no limits to the shape of the recoil).
                number_of_processes: How many processes are used in MCERD
                calculation.
            optimization_type: Whether to optimize recoil or fluence.
            stop_percent: When to stop running MCERD (based on the ratio in
                average change between checkups).
            check_time: Time interval for checking if MCERD should be stopped.
            ch: Channel with (?) for running get_espe.  # TODO: What?
                used in comparing the simulated energy spectra.
            check_max: Maximum time for running a simulation.
            check_min: Minimum time for running a simulation.
            skip_simulation: whether simulation is skipped altogether
            use_efficiency: whether to use efficiency for pre-calculated
                spectrum.
        """
        Observable.__init__(self)

        # TODO: Remove evaluations? It's only used for a status message.
        self.evaluations = evaluations
        self.element_simulation = element_simulation  # Holds other needed
        # information including recoil points and access to simulation settings

        self.upper_limits = upper_limits
        if not self.upper_limits:
            self.upper_limits = [120, 1]
        self.lower_limits = lower_limits
        if not self.lower_limits:
            self.lower_limits = [0.01, 0.0001]
        self.optimization_type = optimization_type
        self.rec_type = recoil_type

        # MCERD-specific parameters
        self.number_of_processes = number_of_processes
        self._skip_simulation = skip_simulation
        self.stop_percent = stop_percent
        self.check_time = check_time
        self.check_max = check_max
        self.check_min = check_min

        self.channel_width = ch

        self.measurement = measurement
        self.cut_file = Path(cut_file)

        self.measured_espe = None
        self.use_efficiency = use_efficiency
        self.verbose = verbose
        self.optimize_by_area = optimize_by_area

    @staticmethod
    def _get_message(state: OptimizationState, **kwargs) -> dict:
        """Returns a dictionary with the state of the optimization and
        other information.
        """
        return {
            "state": state,
            **kwargs
        }

    def prepare_measured_spectra(self) -> None:
        """Calculate measured spectra and parse it.

        Optimized solutions are compared to the measured spectra.
        """
        EnergySpectrum.calculate_measured_spectra(
            self.measurement, [self.cut_file], self.channel_width,
            no_foil=True, use_efficiency=self.use_efficiency)

        # TODO maybe just use the value returned by calc_spectrum?
        # Add result files
        hist_file = Path(self.measurement.get_energy_spectra_dir(),
                         f"{self.cut_file.stem}.no_foil.hist")

        parser = CSVParser((0, float), (1, float))
        self.measured_espe = list(parser.parse_file(hist_file, method="row"))

    def combine_previous_erd_files(self) -> None:
        """Combine previous erd files to used as the starting point."""
        erd_file_name = fp.get_erd_file_name(
            self.element_simulation.get_main_recoil(), "combined",
            optim_mode=self.optimization_type)

        gf.combine_files(self.element_simulation.get_erd_files(),
                         Path(self.element_simulation.directory,
                              erd_file_name))

    def run_initial_simulation(self,
                               cancellation_token: CancellationToken,
                               ion_division: IonDivision) -> None:
        """Run initial element simulation.
        """

        def stop_if_cancelled(
                optim_ct: CancellationToken, mcerd_ct: CancellationToken):
            optim_ct.stop_if_cancelled(mcerd_ct)
            return mcerd_ct.is_cancellation_requested()

        ct = CancellationToken()
        observable = self.element_simulation.start(
            self.number_of_processes, start_value=201,
            optimization_type=self.optimization_type,
            ct=ct, print_output=True, max_time=self.check_max,
            ion_division=ion_division)

        if observable is not None:
            self.on_next(self._get_message(
                OptimizationState.SIMULATING,
                evaluations_left=self.evaluations))

            ct_check = rx.timer(0, 0.2).pipe(
                ops.take_while(lambda _: not stop_if_cancelled(
                    cancellation_token, ct)),
                ops.filter(lambda _: False),
            )
            # FIXME spectra_chk should only be performed when pre-simulation
            #   has finished, otherwise there will be no new observed atoms
            #   and the difference between the two spectra is 0
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
                    lambda x: not isinstance(x, dict) or x[
                        MCERD.IS_RUNNING],
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

    # TODO: maybe?
    # @abc.abstractmethod
    # def evaluate_solutions(self, sols):
    #     pass

    # TODO: maybe? How to deal with different call signatures?
    # @abc.abstractmethod
    # def get_objective_values(self, optim_espe):
    #     pass

    def modify_measurement(self) -> None:
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

    # TODO: Should starting_solutions be typed list or np.ndarray?
    @abc.abstractmethod
    def start_optimization(self, starting_solutions: list = None,
                           cancellation_token: CancellationToken = None,
                           ion_division=IonDivision.BOTH) -> None:
        """Start the optimization.

        Args:
            starting_solutions: First solutions used in optimization. If
                None, initialize new solutions.
            cancellation_token: CancellationToken that is used to stop the
                optimization before all evaluations have been evaluated.
            ion_division: ion division mode used when simulating
        """
        pass

    def clean_up(self, cancellation_token: CancellationToken) -> None:
        if cancellation_token is not None:
            cancellation_token.request_cancellation()
        self._delete_temp_files()

    def _delete_temp_files(self) -> None:
        # Remove unnecessary opt.recoil file
        for file in os.listdir(self.element_simulation.directory):
            # TODO better method for determining which files to delete
            if file.endswith("opt.recoil") or "optfl" in file:
                try:
                    os.remove(Path(self.element_simulation.directory, file))
                except OSError:
                    pass


def get_optim_espe(elem_sim: ElementSimulation,
                   optimization_type: OptimizationType):
    if optimization_type is OptimizationType.RECOIL:
        recoil = elem_sim.optimization_recoils[0]
    else:
        recoil = elem_sim.get_main_recoil()

    espe, _ = elem_sim.calculate_espe(
        recoil, optimization_type=optimization_type, write_to_file=False)
    return espe


def calculate_change(espe1, espe2, channel_width):
    if not espe1 or not espe2:
        return math.inf
    uniespe1, uniespe2 = gf.uniform_espe_lists(
        espe1, espe2, channel_width=channel_width)

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


def dominates(a, b):
    """
    Check if solution a dominates solution b. Minimization. This is related
    to the NSGA-II optimization function (modules/nsgaii.py).

    Args:
        a: Solution (objective values) a.
        b: Solution (objective values) b.

    Return:
        Whether a dominates b.
    """
    is_better = False
    for ai, bi in zip(a, b):
        if ai > bi:
            return False
        if ai < bi:
            is_better = True
    return is_better


def tournament_allow_doubles(t, p, fit):
    """
    Tournament selection that allows one individual to be in the mating pool
    several times.

    Args:
        t: Number of solutions to be compared, size of tournament.
        p: Number of solutions to be selected as parents in the mating pool.
        fit: Fitness vectors.

    Return:
        Index of selected solutions.
    """
    n = len(fit)
    pool = []
    for i in range(p):
        candidates = []
        # Find k different candidates for tournament
        j = 0
        while j in range(t):
            candidate = np.random.randint(n)
            if candidate not in candidates:
                candidates.append(candidate)
                j += 1
        min_front = min([fit[i, 0] for i in candidates])
        min_candidates = [i for i in candidates if fit[i, 0] == min_front]
        number_of_mins = len(min_candidates)
        if number_of_mins > 1:  # If multiple candidates from the same front
            # Find the candidate with smallest crowding distance
            max_dist = max([fit[i, 1] for i in min_candidates])
            max_cands = [i for i in min_candidates if fit[i, 1] == max_dist]
            pool.append(max_cands[0])
        else:
            pool.append(min_candidates[0])

    return np.array(pool)


def single_point_crossover(parent1, parent2):
    # Find random point to do the cut
    rand_i = np.random.randint(0, len(parent1))
    # Create heads and tails
    head_1 = parent1[:rand_i]
    tail_1 = parent1[rand_i:]
    head_2 = parent2[:rand_i]
    tail_2 = parent2[rand_i:]
    # Join to make new children
    binary_child_1 = head_1 + tail_2
    binary_child_2 = head_2 + tail_1

    return binary_child_1, binary_child_2


def simulated_binary_crossover(parent1, parent2, lower_limits, upper_limits,
                               dis_c, sol_size):
    # TODO sol_size is probably always same as parent sizes?
    for j in range(sol_size):
        # Simulated Binary Crossover - SBX
        u = np.random.uniform()
        if u <= 0.5:
            beta = (2*u) ** (1/(dis_c + 1))
        else:
            beta = (1/(2*(1 - u)))**(1/(dis_c + 1))
        c_1 = 0.5*((1 + beta)*parent1[j] +
                   (1 - beta)*parent2[j])
        c_2 = 0.5*((1 - beta)*parent1[j] +
                   (1 + beta)*parent2[j])

        if c_1 > upper_limits[j]:
            c_1 = upper_limits[j]
        elif c_1 < lower_limits[j]:
            c_1 = lower_limits[j]
        if c_2 > upper_limits[j]:
            c_2 = upper_limits[j]
        elif c_2 < lower_limits[j]:
            c_2 = lower_limits[j]

    return c_1, c_2
