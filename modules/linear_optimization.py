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
from scipy import signal
from scipy.interpolate import interpolate
from scipy.ndimage import filters

from . import file_paths as fp
from . import general_functions as gf
from . import math_functions as mf
from . import optimization as opt
from .base import Espe
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

        self.measured_espe_x = None
        self.measured_espe_y = None

        self.mev_to_nm_params = None
        self._mev_to_nm_function = None

        self.measured_peaks_mev = None
        self.measured_peaks_nm = None

        self.solution = None

    def _split_measured_espe(self) -> None:
        """Split measured espe to numpy arrays."""
        x, y = zip(*self.measured_espe)
        self.measured_espe_x = np.array(x)
        self.measured_espe_y = np.array(y)

    def _generate_mev_to_nm_function(
            self, peak_count: int = 12, peak_width: float = 3.0,
            min_prominence_factor: float = 0.1) -> None:
        """Generate an interpolation function for `_convert_mev_to_nm`.

        Simulates peaks at different points (in nm) to determine the function
        parameters (based on MeV). Stops once peaks are not prominent enough or
        maximum peak count is reached.

        Args:
            peak_count: number of peaks to simulate
            peak_width: widths for peaks
            min_prominence_factor: minimum fraction of average peak
                prominences to include peak in results
        """
        mev_range = self.measured_espe_x.min(), self.measured_espe_x.max()

        nm_range = (self.lower_limits[0], self.upper_limits[0] - peak_width)
        nm_points = np.linspace(*nm_range, peak_count)

        nm_step = nm_points[1] - nm_points[0]
        if peak_width > nm_step:
            raise ValueError(
                f"peak_width {peak_width} is wider than nm_step {nm_step}")

        smoothing_width = round(self.measured_espe_x.shape[0] / 30)

        mevs = []
        prominences = []
        for i, nm in enumerate(nm_points):  # TODO: multi-thread this
            solution = get_solution6(
                nm, nm + peak_width, self.lower_limits, self.upper_limits)
            espe = self._run_solution(solution)
            espe_x, espe_y = zip(*espe)

            peak_i, peak_info = signal.find_peaks(espe_y, width=smoothing_width)

            # Find the largest peak prominence
            prominence_i = peak_info["prominences"].argmax()
            prominence = peak_info["prominences"][prominence_i]
            if prominences:
                prominence_threshold = (sum(prominences) / len(prominences)
                                        * min_prominence_factor)
                if prominence < prominence_threshold:
                    break

            prominences.append(prominence)
            mevs.append(espe_x[peak_i[prominence_i]])

        if len(mevs) <= 1:
            raise ValueError("Could not generate a nm-to-MeV function."
                             " Not enough significant data points.")

        mevs = np.array(mevs)
        prominences = np.array(prominences)
        # Pick matching points, centered
        nms = nm_points[:mevs.shape[0]] + peak_width / 2

        # TODO: Params are probably not needed after creating the function
        self.mev_to_nm_params = {
            "nm": nms,
            "mev": mevs,
            "prominences": prominences,
            "peak_width": peak_width
        }
        self._mev_to_nm_function = interpolate.interp1d(
            mevs, nms, fill_value="extrapolate", assume_sorted=True)

    def _convert_mev_to_nm(self, mev: float) -> float:
        """Interpolate/extrapolate a depth from MeV to nm.

        Run `_generate_mev_to_nm_table` before using.

        Args:
            mev: value to convert (in MeV)

        Returns:
            Converted value (in nm)
        """
        if self._mev_to_nm_function is None:
            # TODO: Better error type
            raise ValueError("Generate the MeV-to-nm conversion function first")

        return float(self._mev_to_nm_function(mev))

    def _find_measured_peaks(self, peak_count: int) -> None:
        """Determine measured energy spectrum's peaks,
        both in MeV (real) and nm (interpolated).

        Args:
            peak_count: Amount of peaks to find
        """
        # TODO: resize width until `peak_count` peaks are found
        width = round(self.measured_espe_y.shape[0] / 30)
        indexes, info = signal.find_peaks(self.measured_espe_y, width=width)

        most_prominent_indexes = (-info["prominences"]).argsort()[:peak_count]
        most_prominent_indexes.sort()  # Keep peaks in their original order
        if most_prominent_indexes.shape[0] < peak_count:
            raise NotImplementedError(
                "Too few measured peaks detected using default values."
                " Retrying not implemented.")

        peaks_mev = []
        for i in most_prominent_indexes:
            left_i = round(info["left_ips"][i])
            center_i = indexes[i]
            right_i = round(info["right_ips"][i])

            peak = tuple(self.measured_espe_x[[left_i, center_i, right_i]])
            peaks_mev.append(peak)
        self.measured_peaks_mev = peaks_mev

        peaks_nm = []
        # Reverse nm peaks to keep them in ascending order
        for peak in peaks_mev[::-1]:
            converted = tuple(
                reversed([self._convert_mev_to_nm(mev) for mev in peak]))

            left_correction = self.lower_limits[0] - converted[0]
            exceeds_left = left_correction > 0.0

            right_correction = self.upper_limits[0] - converted[-1]
            exceeds_right = right_correction < 0.0

            corrected = None
            if exceeds_left and exceeds_right:
                # TODO: does it make sense to clip left and right?
                raise NotImplementedError("Detected peak exceeded both limits.")
            elif exceeds_left:
                corrected = tuple(nm + left_correction for nm in converted)
                if corrected[-1] > self.upper_limits[0]:
                    # TODO: clip right?
                    raise NotImplementedError
            elif exceeds_right:
                corrected = tuple(nm + right_correction for nm in converted)
                if corrected[0] < self.lower_limits[0]:
                    # TODO: clip left?
                    raise NotImplementedError

            peaks_nm.append(corrected if corrected else converted)

        self.measured_peaks_nm = peaks_nm

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
        self._split_measured_espe()

        self._generate_mev_to_nm_function()

        # TODO: Get peak count from solution shape
        self._find_measured_peaks(2)

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

    def initialize_solution(self):
        if self.optimization_type is OptimizationType.RECOIL:
            x_min, y_min = self.lower_limits
            x_max, y_max = self.upper_limits
            gap = 0.01  # TODO: Save this as a constant
            # TODO: Copy elif's and else's from Nsgaii
            # TODO: Create inverse solutions too (swap peak & valley heights)?
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
                    peak0 = self.measured_peaks_nm[0]
                    peak1 = self.measured_peaks_nm[1]

                    points = [
                        Point(x_min,            y_max),
                        Point(peak0[-1],        y_max),
                        Point(peak0[-1] + gap,  y_min),
                        Point(peak1[0] - gap,   y_min),
                        Point(peak1[0],         y_max),
                        Point(peak1[-1],        y_max),
                        Point(peak1[-1] + gap,  y_min),
                        Point(x_max,            y_min)
                    ]
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

    def _run_solution(self, solution) -> Espe:
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
        elif self.optimization_type is OptimizationType.FLUENCE:
            raise NotImplementedError
        else:
            raise ValueError(
                f"Unknown optimization type {self.optimization_type}")

        return espe

    def evaluate_solution(self, solution) -> float:
        espe = self._run_solution(solution)

        if self.optimization_type is OptimizationType.RECOIL:
            objective_value = self._get_spectra_difference(espe)
        elif self.optimization_type is OptimizationType.FLUENCE:
            raise NotImplementedError
        else:
            raise ValueError(
                f"Unknown optimization type {self.optimization_type}")

        return objective_value

    # TODO: Is this needed?
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

    def _fit_simulation(self, bounds):
        # TODO: Compare to measured and move points in pairs accordingly
        raise NotImplementedError

    def _optimize(self):
        points = copy.deepcopy(self.solution.points)
        bounds = self._get_bounds()

        optimized = self._fit_simulation(bounds)

        return optimized

    # TODO: Are starting_solutions and ion_division needed?
    def start_optimization(self, starting_solutions=None,
                           cancellation_token=None,
                           ion_division=IonDivision.BOTH):
        # TODO: Messages aren't visible, probably because they
        #  don't carry information about evaluations
        self.on_next(self._get_message(OptimizationState.PREPARING))

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

        self.on_next(self._get_message(OptimizationState.RUNNING))

        result = self.solution  # TODO: Replace with _optimize
        # result = self._optimize() # TODO

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

        self.on_completed(self._get_message(OptimizationState.FINISHED))


# TODO: Probably needlessly complicated now, just move points up/down in pairs
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


class BaseSolution:
    def __init__(self, points: List[Point], peaks: List[Peak],
                 valleys: List[Valley]):
        self.points = points
        self.peaks = peaks
        self.valleys = valleys


class SolutionBox4(BaseSolution):
    def __init__(self, points: List[Point]):
        raise NotImplementedError
        # peaks = [slice(0, 3)]
        # valleys = [slice(2, 4)]
        # super().__init__(4, peaks, valleys, points)


class SolutionBox6(BaseSolution):
    def __init__(self, points):
        valley1 = Valley(ll=points[0], rl=points[1],
                         prev_point=None, next_point=points[2])
        peak1 = Peak(ll=points[1], lh=points[2], rh=points[3], rl=points[4],
                     prev_point=points[0], next_point=points[5])
        valley2 = Valley(ll=points[4], rl=points[5],
                         prev_point=points[3], next_point=None)

        peaks = [peak1]
        valleys = [valley1, valley2]

        super().__init__(points, peaks, valleys)


class SolutionPeak8(BaseSolution):
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
    def __init__(self, points: List[Point]):
        raise NotImplementedError
        # peaks = [slice(1, 5), slice(5, 9)]
        # valleys = [slice(0, 2), slice(4, 6), slice(8, 10)]
        # super().__init__(10, peaks, valleys, points)



def get_solution6(
        x1: float, x2: float, lower_limits, upper_limits) -> SolutionBox6:
    """Return a SolutionBox6 with max values from x1 to x2"""
    min_x, min_y = lower_limits
    max_x, max_y = upper_limits
    gap = 0.01

    points = [
        Point(min_x,      min_y),
        Point(x1,         min_y),
        Point(x1 + gap,  max_y),
        Point(x2 - gap,  max_y),
        Point(x2,         min_y),
        Point(max_x,      min_y),
    ]
    solution = SolutionBox6(points)

    return solution
