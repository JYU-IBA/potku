"""
Created on 20.09.2021

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2021 Tuomas Pitkänen

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
__author__ = "Tuomas Pitkänen"
__version__ = "2.0"

import abc
import copy
import subprocess
from pathlib import Path
from timeit import default_timer as timer
from typing import Tuple, List, Optional

import numpy as np
import scipy as sp
from scipy import optimize

from . import file_paths as fp
from . import general_functions as gf
from . import math_functions as mf
from . import optimization as opt
from .element_simulation import ElementSimulation
from .energy_spectrum import EnergySpectrum
from .enums import OptimizationState, IonDivision
from .enums import OptimizationType
from .parsing import CSVParser


# TODO:
#  - documentation
#  - unit tests
#  - type annotations
from .point import Point
from .recoil_element import RecoilElement


class LinearOptimization(opt.BaseOptimizer):
    """Class that handles linear optimization for Optimize Recoils or
    Fluence."""
    pass

    def __init__(self, element_simulation: ElementSimulation = None,
                 sol_size=5, upper_limits=None, lower_limits=None,
                 optimization_type=OptimizationType.RECOIL, recoil_type="box",
                 number_of_processes=1, stop_percent=0.3, check_time=20,
                 ch=0.025, measurement=None, cut_file=None, check_max=900,
                 check_min=0, skip_simulation=False, use_efficiency=False,
                 optimize_by_area=False, verbose=False,
                 **kwargs):  # TODO: Remove kwargs when this is fully integrated
        opt.BaseOptimizer.__init__(
            self,
            element_simulation=element_simulation,
            upper_limits=upper_limits,
            lower_limits=lower_limits,
            optimization_type=optimization_type,
            recoil_type=recoil_type,
            number_of_processes=number_of_processes,
            stop_percent=stop_percent,
            check_time=check_time,
            ch=ch,
            measurement=measurement,
            cut_file=cut_file,
            check_max=check_max,
            check_min=check_min,
            skip_simulation=skip_simulation,
            use_efficiency=use_efficiency,
            verbose=verbose,
            optimize_by_area=optimize_by_area
        )
        self.element_simulation = element_simulation

        self.sol_size = sol_size

        self.measured_peaks = []
        self.solution = None

    def _find_measured_peaks(self):
        # TODO: Find measured peaks
        #  - amount depends on sol_size (1 or 2)
        #  - convert measured MeV to simulated nm
        #  - save width too?

        # TODO: Maybe ask the user:
        #  - click on the spectrum or
        #  - input coordinates (x, maybe y)

        self.measured_peaks = [5.00, 70.00]

    def _prepare_optimization(self, initial_solution=None,
                              cancellation_token=None,
                              ion_division=IonDivision.BOTH):
        """Performs internal preparation before optimization begins.
        """
        # TODO: Reduce copy-paste
        self.element_simulation.optimization_recoils = []

        if self.measurement is None:
            raise ValueError(
                "Optimization could not be prepared, no measurement defined.")

        self.element_simulation.optimized_fluence = None

        self.prepare_measured_spectra()

        # TODO: Smoothen the measured spectrum

        # TODO: Is this needed?
        self.combine_previous_erd_files()

        # Modify measurement file to match the simulation file in regards to
        # the x coordinates -> they have matching values for ease of distance
        # counting
        self.modify_measurement()

        self._find_measured_peaks()

        if initial_solution is None:
            initial_solution = self.initialize_solution()

        if self.optimization_type is OptimizationType.RECOIL:
            # Empty the list of optimization recoils

            # Form points from first solution. First solution of first
            # population will always cover the whole x axis range between
            # lower and upper values -> MCERD never needs to be run again
            self.element_simulation.optimization_recoils = [
                self.form_recoil(initial_solution)
            ]

        if not self._skip_simulation:
            self.run_initial_simulation(cancellation_token, ion_division)

        self.solution = initial_solution

        # TODO: Is something like this needed?
        # self.population = self.evaluate_solutions(initial_pop)

    def _get_spectra_difference(self, optim_espe) -> float:
        """Returns the difference between spectra points or area.

        self.optimize_by_area defines which result to get.
        """
        # Make spectra the same size
        optim_espe, measured_espe = gf.uniform_espe_lists(
            optim_espe, self.measured_espe,
            channel_width=self.element_simulation.channel_width)

        # Find the area between simulated and measured energy spectra
        if self.optimize_by_area:
            return mf.calculate_area(optim_espe, measured_espe)

        # Find the mean squared error between simulated and measured
        # energy spectra y values
        diff = [(opt_p[1] - mesu_p[1])**2
                for opt_p, mesu_p in zip(optim_espe, measured_espe)]
        sum_diff = sum(diff) / len(diff)

        return sum_diff

    def form_recoil(self, current_solution, name="") -> RecoilElement:
        if not name:
            name = "opt"

        recoil = RecoilElement(
            self.element_simulation.get_main_recoil().element,
            current_solution.points,
            color="red", name=name)

        return recoil

        # raise NotImplementedError

    def initialize_solution(self):
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

            # TODO: Copy elif's and else's from Nsgaii
            if self.rec_type == "box":
                if self.sol_size == 5:  # 4-point recoil
                    raise NotImplementedError
                elif self.sol_size == 7:  # 6-point recoil
                    raise NotImplementedError
                else:
                    raise ValueError(
                        f"Unsupported sol_size {self.sol_size} for recoil type {self.rec_type}")
            elif self.rec_type == "two-peak":  # Two-peak recoil
                if self.sol_size == 9:  # First peak at the surface
                    # coords = [
                    #     (0.0, 0.5),
                    #     (30.0, 0.5),
                    #     (30.01, 0.0001),
                    #     (59.99, 0.0001),
                    #     (60.0, 0.5),
                    #     (89.99, 0.5),
                    #     (90.0, 0.0001),
                    #     (120.0, 0.0001)
                    # ]

                    coords = [
                        (0.0, 0.0001),
                        (30.0, 0.0001),
                        (30.01, 0.0001),
                        (59.99, 0.0001),
                        (60.0, 0.0001),
                        (89.99, 0.0001),
                        (90.0, 0.0001),
                        (120.0, 0.0001)
                    ]

                    points = [Point(xy) for xy in coords]
                    solution = SolutionPeak8(points)
                elif self.sol_size == 11:  # First peak not at the surface
                    raise NotImplementedError
                else:
                    raise ValueError(
                        f"Unsupported sol_size {self.sol_size} for recoil type {self.rec_type}")
            else:
                raise ValueError(
                    f"Unknown recoil type {self.rec_type}")

        elif self.optimization_type is OptimizationType.FLUENCE:
            raise NotImplementedError

        else:
            raise ValueError(
                f"Unknown optimization type {self.optimization_type}")

        return solution

    def evaluate_solution(self, solution) -> float:
        if self.optimization_type is OptimizationType.RECOIL:
            self.element_simulation.optimization_recoils = [
                self.form_recoil(solution)
            ]

            espe, _ = self.element_simulation.calculate_espe(
                self.element_simulation.optimization_recoils[0],
                verbose=self.verbose,
                optimization_type=self.optimization_type,
                ch=self.channel_width,
                write_to_file=False)
            objective_value = self._get_spectra_difference(espe)
        elif self.optimization_type is OptimizationType.FLUENCE:
            raise NotImplementedError
        else:
            raise ValueError(
                f"Unknown optimization type {self.optimization_type}")

        return objective_value

    @staticmethod
    def _optimize_func(points, *args) -> float:
        # Function for scipy.optimize.minimize

        # optimize.minimize doesn't support calling objects' methods directly
        self = args[0]

        # Function:
        # fun(x, *args) -> float
        # where x is an 1-D array with shape (n,) and args is a tuple of the
        # fixed parameters needed to completely specify the function.

        objective_value = self.evaluate_solution(points)

        return objective_value

    def _get_bounds(self):
        # TODO: Select by type, use real values
        x_ub = 120.0
        x_lb = 0.01

        y_ub = 1.0000
        y_lb = 0.0001

        x_bounds = [
            (0.0, 0.0),
            (x_lb, x_ub),
            (x_lb, x_ub),
            (x_lb, x_ub),
            (x_lb, x_ub),
            (x_lb, x_ub),
            (x_lb, x_ub),
            (120.0, 120.0)
        ]

        y_bounds = [
            (y_lb, y_ub),
            (y_lb, y_ub),
            (y_lb, y_ub),
            (y_lb, y_ub),
            (y_lb, y_ub),
            (y_lb, y_ub),
            (0.0001, 0.0001),
            (y_lb, y_ub)
        ]

        # TODO: namedtuple
        return x_bounds, y_bounds

    def _fit_simulation_peaks(self, solution, bounds):
        initial_solution = copy.deepcopy(solution)
        initial_objective_value = self.evaluate_solution(solution)

        # for i, peak in enumerate(solution.peaks):
        #     # TODO: search peak centers -> widths -> heights
        #     pass

        peak = solution.peaks[1]

        initial_x = peak.center.get_x()
        initial_y = peak.center.get_y()

        peak.set_y(1.0)
        objective_values = {}
        linear_space = np.linspace(
            peak.prev_point.get_x(), peak.next_point.get_x(), 7)[1:-1]
        for x in linear_space:
            peak.set_x(x)
            objective_values[x] = self.evaluate_solution(solution)

        best_x = min(objective_values, key=objective_values.get)

        peak.set_x(initial_x)
        peak.set_y(initial_y)

        print(objective_values)
        print(f"Best x: {best_x}, best value: {objective_values[best_x]}")

        raise NotImplementedError

    def _fit_simulation_valleys(self, solution, bounds):
        for i, valley in enumerate(solution.valleys):
            # TODO: search valley heights
            pass

        raise NotImplementedError

    def _optimize(self):
        points = copy.deepcopy(self.solution.points)
        solution = SolutionPeak8_2(points)
        bounds = self._get_bounds()

        self._fit_simulation_peaks(solution, bounds)
        self._fit_simulation_valleys(solution, bounds)

        return solution

    # TODO: Are starting_solutions and ion_division needed?
    def start_optimization(self, starting_solutions=None,
                           cancellation_token=None,
                           ion_division=IonDivision.BOTH):
        # TODO: Maybe?
        # self.on_next(self._get_message(
        #     OptimizationState.PREPARING, evaluatiations_left=self.evaluations))

        try:
            self._prepare_optimization(
                starting_solutions, cancellation_token, ion_division)
        except (OSError, ValueError, subprocess.SubprocessError) as e:
            self.on_error(self._get_message(
                OptimizationState.FINISHED,
                error=f"Preparation for optimization failed: {e}"))
            self.clean_up(cancellation_token)
            return

        pass

        start_time = timer()

        # self.on_next(self._get_message(
        #     OptimizationState.RUNNING, evaluations_left=self.evaluations))

        result = self._optimize()

        if self.optimization_type is OptimizationType.RECOIL:
            first_sol = self.solution
            med_sol = self.solution  # TODO: Add something sensible here
            last_sol = result

            self.element_simulation.optimization_recoils = [
                self.form_recoil(first_sol, "optfirst"),
                self.form_recoil(med_sol, "optmed"),
                self.form_recoil(last_sol, "optlast")
            ]
        else:
            raise NotImplementedError

        self.clean_up(cancellation_token)
        self.element_simulation.optimization_results_to_file(self.cut_file)

        self.on_completed(self._get_message(
            OptimizationState.FINISHED,
            evaluations_done="Unknown"))  # TODO: Proper value


PeakType = List[Point]
ValleyType = List[Point]


# TODO: Combine Valley with Peak (move_left_valley, move_right_valley)?
# TODO: Parametric representation (width, center_point, prev_point/next_point)?
class Peak:
    def __init__(
            self, lh: Point, rh: Point, ll: Point = None, rl: Point = None,
            prev_point: Point = None, next_point: Point = None):
        # left/right low/high
        self.ll: Optional[Point] = ll
        self.lh: Point = lh
        self.rh: Point = rh
        self.rl: Optional[Point] = rl

        # TODO: Check these for limits,
        #       maybe add a list of boundaries too (create BoundedPoint class?)
        self.prev_point = prev_point
        self.next_point = next_point

    # TODO: Is this useful?
    @property
    def center(self) -> Point:
        x = (self.lh.get_x() + self.rh.get_x()) / 2
        y = (self.lh.get_y() + self.rh.get_y()) / 2
        return Point(x, y)

    @property
    def points(self) -> List[Point]:
        return [self.prev_point, self.ll, self.lh,
                self.rh, self.rl, self.next_point]

    # TODO: Use this and move the points' x in order based on amount's sign
    #       (negative: left to right, positive: right to left)
    #       (prevents overlapping)
    @staticmethod
    def _move_point(point, x=0.0, y=0.0,
                    prev_point=None, next_point=None) -> bool:
        clipped = False

        if x != 0.0:
            new_x = point.get_x() + x
            clipped_x = np.clip(
                new_x, a_min=prev_point.get_x(), a_max=next_point.get_x())
            if new_x != clipped_x:
                clipped = True

            point.set_x(clipped_x)

        if y != 0.0:
            new_y = point.get_y() + y
            clipped_y = np.clip(
                new_y, a_min=prev_point.get_y(), a_max=next_point.get_y())
            if new_y != clipped_y:
                clipped = True

            point.set_y(clipped_y)

        return clipped

    def move_x(self, amount: float) -> None:
        if amount >= 0.0:
            if self.prev_point and self.ll:
                self.ll.set_x(self.ll.get_x() + amount)
                self.lh.set_x(self.lh.get_x() + amount)
            if self.next_point and self.rl:
                self.rh.set_x(self.rh.get_x() + amount)
                self.rl.set_x(self.rl.get_x() + amount)

    def move_y(self, amount: float) -> None:
        self.lh.set_y(self.lh.get_y() + amount)
        self.rh.set_y(self.rh.get_y() + amount)

    def set_x(self, x: float) -> None:
        amount = x - self.center.get_x()
        self.move_x(amount)

    def set_y(self, y: float) -> None:
        amount = y - self.center.get_y()
        self.move_y(amount)

    def scale(self) -> None:
        raise NotImplementedError


class Valley:
    def __init__(
            self, ll: Point, rl: Point,
            prev_point: Point = None, next_point: Point = None):
        # left/right low
        self.ll: Point = ll
        self.rl: Point = rl

        self.prev_point = prev_point
        self.next_point = next_point

    @property
    def center(self) -> Point:
        x = (self.ll.get_x() + self.rl.get_x()) / 2
        y = (self.ll.get_y() + self.rl.get_y()) / 2
        return Point(x, y)

    @property
    def points(self) -> List[Point]:
        return [self.prev_point, self.ll, self.rl, self.next_point]

    def move_y(self, amount: float) -> None:
        if amount:
            self.ll.set_y(self.ll.get_y() + amount)
            self.rl.set_y(self.rl.get_y() + amount)

    def set_y(self, y: float) -> None:
        amount = y - self.center.get_y()
        self.move_y(amount)

    def scale(self) -> None:
        raise NotImplementedError


class BaseSolution2:
    def __init__(self, points: List[Point], peaks: List[Peak],
                 valleys: List[Valley]):
        self.points = points
        self.peaks = peaks
        self.valleys = valleys


# TODO: ABC?
# TODO: Save boundaries?
class BaseSolution:
    """Base class for optimization solutions."""
    def __init__(self, size: int, peak_slices: List[slice],
                 valley_slices: List[slice],
                 points: List[Point] = None):
        self._SIZE = size
        self._PEAK_SLICES = peak_slices
        self._VALLEY_SLICES = valley_slices

        self.points = points

        if not self.points:
            self.points = [Point(0.0, 0.0001) for _ in range(self._SIZE)]

        if len(self.points) != self._SIZE:
            raise ValueError(
                f"Length of points must be {self._SIZE}, was {len(self.points)}")

    # TODO: Add methods for manipulating peaks/valleys?
    #       E.g. change width, height, move left/right

    @property
    def peaks(self) -> List[PeakType]:
        return [self.points[s] for s in self._PEAK_SLICES]

    # TODO: Is this useful for performance?
    # def get_peak(self, peak_number: int) -> PeakType:
    #     return self.points[slice(*self._PEAK_SLICES[peak_number])]

    def move_peak(self, peak_number: int,
                  x_move=0.0, y_move=0.0) -> None:
        # Original:
        # peak = self.peaks[peak_number]
        #
        # if x_move:
        #     for point in peak:
        #         point.set_x(point.get_x() + x_move)
        #
        # if y_move:
        #     for point in peak:
        #         # TODO: Leave valleys untouched
        #         point.set_y(point.get_y() + y_move)

        # TODO: Calculate ends and corners once, or maybe just input
        #  them manually

        peak_slice = self._PEAK_SLICES[peak_number]
        ends = {0, self._SIZE}
        x_indexes = [i for i in range(peak_slice.start, peak_slice.stop)
                     if i not in ends]

        corners = set()
        # TODO: What about just adding (slice.start) and (slice.end - 1)?
        for valley_slice in self._VALLEY_SLICES:
            if valley_slice.start == 0:
                corners.add(1)
            else:
                corners.add(valley_slice.start)

            if valley_slice.stop == self._SIZE:
                pass
            else:
                corners.add(valley_slice.stop - 1)

        y_indexes = [i for i in range(peak_slice.start, peak_slice.stop)
                     if i not in corners]

        # TODO: Check boundaries (x, y)
        #  and continuity (x values must be in order)

        if x_move:
            for i in x_indexes:
                point = self.points[i]
                point.set_x(point.get_x() + x_move)

        if y_move:
            for i in y_indexes:
                point = self.points[i]
                point.set_y(point.get_y() + y_move)

    # TODO: Is this useful?
    def scale_peak(self, peak_number: int, x_scale=1.0, y_scale=1.0) -> None:
        peak = self.peaks[peak_number]

        if x_scale != 1.0:
            for point in peak:
                raise NotImplementedError

        if y_scale != 1.0:
            for point in peak:
                # TODO: Leave valleys untouched
                raise NotImplementedError

        raise NotImplementedError

    @property
    def valleys(self):
        return [self.points[s] for s in self._VALLEY_SLICES]

    def move_valley(self, valley_number: int,
                    # x_move=0.0,
                    y_move=0.0) -> None:
        valley = self.valleys[valley_number]

        # TODO: Check boundaries (x, y)
        #  and continuity (x values must be in order)

        # if x_move:
        #     for point in valley:
        #         point.set_x(point.get_x() + x_move)

        # TODO: Only move valleys that are between peaks?

        if y_move:
            for point in valley:
                point.set_y(point.get_y() + y_move)

    # def scale_valley(self, valley_number: int, x_scale=0.0, y_scale=0.0) -> None:
    #     raise NotImplementedError


class SolutionBox4(BaseSolution):
    def __init__(self, points: Optional[List[Point]] = None):
        peaks = [slice(0, 3)]
        valleys = [slice(2, 4)]
        super().__init__(4, peaks, valleys, points)


class SolutionBox6(BaseSolution):
    def __init__(self, points: Optional[List[Point]] = None):
        peaks = [slice(1, 5)]
        valleys = [slice(0, 2), slice(4, 6)]
        super().__init__(6, peaks, valleys, points)


class SolutionPeak8(BaseSolution):
    def __init__(self, points: Optional[List[Point]] = None):
        peaks = [slice(0, 3), slice(3, 7)]
        valleys = [slice(2, 4), slice(6, 8)]
        super().__init__(8, peaks, valleys, points)


class SolutionPeak8_2(BaseSolution2):
    def __init__(self, points: List[Point]):
        peak1 = Peak(ll=None, lh=points[0], rh=points[1], rl=points[2],
                     prev_point=None, next_point=points[3])
        valley1 = Valley(ll=points[2], rl=points[3],
                         prev_point=points[1], next_point=points[4])
        peak2 = Peak(ll=points[3], lh=points[4], rh=points[5], rl=points[6],
                     prev_point=points[2], next_point=points[7])
        valley2 = Valley(ll=points[6], rl=points[7],
                         prev_point=points[5], next_point=None)

        peaks = [peak1, peak2]
        valleys = [valley1, valley2]

        super().__init__(points, peaks, valleys)


class SolutionPeak10(BaseSolution):
    def __init__(self, points: Optional[List[Point]] = None):
        peaks = [slice(1, 5), slice(5, 9)]
        valleys = [slice(0, 2), slice(4, 6), slice(8, 10)]
        super().__init__(10, peaks, valleys, points)
