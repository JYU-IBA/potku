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

import copy
import subprocess
from collections import namedtuple
from typing import Tuple, List, Optional

import numpy as np
from scipy import signal
from scipy.interpolate import interpolate

from . import general_functions as gf
from . import math_functions as mf
from . import optimization as opt
from .base import Espe
from .element_simulation import ElementSimulation
from .enums import OptimizationState, IonDivision
from .enums import OptimizationType
from .point import Point
from .recoil_element import RecoilElement


PeakInfo = namedtuple("PeakInfo", ("peaks", "info"))


class LinearOptimization(opt.BaseOptimizer):
    """Class that handles linear optimization for Optimize Recoils or
    Fluence.
    """
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

        self._mev_to_nm_function = None

        self.measured_peak_info: Optional[PeakInfo] = None
        self.measured_peaks_mev: Optional[List[Tuple[float]]] = None
        self.measured_peaks_nm: Optional[List[Tuple[float]]] = None
        self.measured_max_height: Optional[float] = None
        self.measured_valley_intervals: Optional[List[slice]] = None
        self.measured_valley_heights: Optional[List[Tuple[float]]] = None

        # TODO: Ask user
        self.is_skewed = False

        self.peak_count = None
        if self.rec_type == "box":
            self.peak_count = 1
        elif self.rec_type == "two-peak":
            self.peak_count = 2

        self.solution = None

    def _generate_mev_to_nm_function(
            self, sample_count: int = 12, sample_width: float = 3.0,
            min_prominence_factor: float = 0.1) -> None:
        """Generate an interpolation function for `_convert_mev_to_nm`.

        Samples thin, simulated peaks at different points (in nm) to determine
        the function parameters (based on MeV). Stops once peaks are not
        prominent enough or maximum sample count is reached.

        Args:
            sample_count: number of peaks to simulate
            sample_width: widths for peaks
            min_prominence_factor: minimum fraction of average peak
                prominences to include peak in results
        """
        nm_range = (self.lower_limits[0], self.upper_limits[0] - sample_width)
        nm_points = np.linspace(*nm_range, sample_count)

        nm_step = nm_points[1] - nm_points[0]
        if sample_width > nm_step:
            raise ValueError(
                f"sample_width {sample_width} is wider than nm_step {nm_step}")

        smoothing_width = round(self.measured_espe_x.shape[0] / 30)

        mevs = []
        prominences = []
        for nm in nm_points:  # TODO: multi-thread this
            solution = get_solution6(
                nm, nm + sample_width, self.lower_limits, self.upper_limits)
            espe = self._run_solution(solution)
            if not espe:
                raise ValueError(
                    "Ensure that there is simulated data for this recoil "
                    "element before starting optimization.")

            espe_x, espe_y = split_espe(espe)

            try:
                peak_info = self._get_peak_info(
                    espe_y, 1, peak_width=smoothing_width, retry_count=0)
            except ValueError:
                break

            prominence = peak_info.info["prominences"][0]
            if prominences:
                prominence_threshold = (sum(prominences) / len(prominences)
                                        * min_prominence_factor)
                if prominence < prominence_threshold:
                    break

            prominences.append(prominence)
            mevs.append(espe_x[peak_info.peaks[0]])

        if len(mevs) <= 1:
            raise ValueError("Could not generate a nm-to-MeV function."
                             " Not enough significant data points.")

        mevs = np.array(mevs)
        # Pick matching points, centered
        nms = nm_points[:mevs.shape[0]] + sample_width / 2

        mevs_diff = np.diff(mevs)
        if not np.all(mevs_diff <= 0):
            # TODO: Remove non-monotonous parts from start and end.
            #   Note that mevs_diff.shape[0] == mevs.shape[0] - 1
            raise ValueError("Simulated MeV values were non-monotonous.")

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
            raise ValueError("Generate the MeV-to-nm conversion function first")

        return float(self._mev_to_nm_function(mev))

    def _get_peak_info(self, y: np.ndarray,
                       peak_count: int,
                       peak_width: int = None,
                       retry_count: int = 10) -> PeakInfo:
        """Get information about Espe peaks.

        Args:
            y: Espe y values
            peak_count: amount of peaks to find
            peak_width: minimum width of peaks (in data points)
            retry_count: amount of tries to retry if an incorrect amount
                of peaks were found

        Raises:
            ValueError: if not enough peaks could be found

        Returns:
            Information about peaks
        """
        if peak_width is None:
            peak_width = round(y.shape[0] / 30)

        found = None
        # TODO: Change threshold instead?
        next_height = 1.0
        low = None
        high = None

        for _ in range(retry_count + 1):  # First round is not a retry
            indexes, info = signal.find_peaks(y, height=next_height, width=peak_width)
            length = indexes.shape[0]

            if length > peak_count:
                low = next_height
                next_height = low * 4 if high is None else (low + high) / 2
                found = indexes, info
            elif length < peak_count:
                high = next_height
                next_height = high / 4 if low is None else (low + high) / 2
            else:
                found = indexes, info
                break

        if found is None:
            raise ValueError(f"None or too few peaks found")

        indexes, info = found

        if indexes.shape[0] == peak_count:
            return PeakInfo(indexes, info)

        # Remove extra peaks

        most_prominent_indexes = (-info["prominences"]).argsort()[:peak_count]
        most_prominent_indexes.sort()  # Keep peaks in their original order

        new_info = {}
        for key, value in info.items():
            new_info[key] = value[most_prominent_indexes]
        new_indexes = indexes[most_prominent_indexes]

        return PeakInfo(new_indexes, new_info)

    def _get_mev_peaks(self, x: np.ndarray, peak_info: PeakInfo) -> List[Tuple[float]]:
        """Get Espe's MeV peak x locations based on `peak_info`

        Args:
            x: Espe x values
            peak_info: peak information

        Returns:
            List of peaks (points: left, center, right)
        """
        peaks_mev = []
        for i, _ in enumerate(peak_info.peaks):
            left_i = round(peak_info.info["left_ips"][i])
            center_i = peak_info.peaks[i]
            right_i = round(peak_info.info["right_ips"][i])

            peak = tuple(x[[left_i, center_i, right_i]])
            peaks_mev.append(peak)

        return peaks_mev

    def _convert_peaks_to_nm(self, mev_peaks: List[Tuple[float]]) -> List[Tuple[float]]:
        """Convert peak x values from MeV to nm.

        If peaks would exceed limits, they are corrected.

        Args:
            mev_peaks: peaks to convert (in MeV)

        Returns:
            Peaks converted to nm (points: left, center, right)
        """
        peaks_nm = []
        # Reverse nm peaks to keep them in ascending order
        for peak in mev_peaks[::-1]:
            converted = tuple(reversed([self._convert_mev_to_nm(mev) for mev in peak]))

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

        return peaks_nm

    def _find_measured_peaks(self) -> None:
        """Determine measured energy spectrum's peaks,
        both in MeV (real) and nm (interpolated).
        """
        self.measured_peak_info = self._get_peak_info(
            self.measured_espe_y, self.peak_count)

        self.measured_peaks_mev = self._get_mev_peaks(
            self.measured_espe_x, self.measured_peak_info)

        self.measured_peaks_nm = self._convert_peaks_to_nm(
            self.measured_peaks_mev)

        # Percentile reduces the impact of outliers
        self.measured_max_height = np.percentile(self.measured_espe_y, 98)

    def _get_valley_intervals(self, peak_info: PeakInfo,
                              include_start: bool = False,
                              include_end: bool = False) -> List[slice]:
        """Get valley intervals (indexes) between peaks and/or start and end.

        Args:
            peak_info: peak information
            include_start:
            include_end:

        Returns:
            Valley indexes as slices
        """
        left_ips = np.rint(peak_info.info["left_ips"]).astype(np.int64)
        right_ips = np.rint(peak_info.info["right_ips"]).astype(np.int64)

        intervals = []

        if include_start:
            lower = 0
            upper = left_ips[0]
            intervals.append(slice(lower, upper))

        for i in range(len(left_ips) - 1):
            lower = right_ips[i]
            upper = left_ips[i + 1]
            intervals.append(slice(lower, upper))

        if include_end:
            lower = right_ips[-1]
            upper = None
            intervals.append(slice(lower, upper))

        return intervals

    def _get_valley_heights(self, y: np.ndarray, intervals: List[slice]) -> List[Tuple[float]]:
        """Get valley heights in intervals.

        Height is based on medians.

        Args:
            y: y coordinates
            intervals: valley ranges

        Returns:
            Valley heights as pairs.
        """
        heights = []

        if not self.is_skewed:
            for interval in intervals:
                # TODO: Ignore outermost pieces like in the other branch
                height = float(np.median(y[interval]))
                heights.append((height, height))
        else:
            for interval in intervals:
                # Ignore outermost pieces because they are likely affected by
                # peaks
                # FIXME: This won't work if the interval is too small
                pieces = np.array_split(y[interval], 4)[1:3]

                piece_heights = tuple(float(np.median(piece)) for piece in pieces)
                heights.append(piece_heights)

        return heights

    def _find_measured_valleys(self):
        """Find valleys between peaks in measured espe.
        """
        # TODO: Get include_start and include_end from solution shape.
        self.measured_valley_intervals = self._get_valley_intervals(
            self.measured_peak_info, include_start=True, include_end=False)

        self.measured_valley_heights = self._get_valley_heights(
            self.measured_espe_y, self.measured_valley_intervals)

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

        self.combine_previous_erd_files()

        # Modify measurement file to match the simulation file in regards to
        # the x coordinates -> they have matching values for ease of distance
        # counting
        self.modify_measurement()
        self.measured_espe_x, self.measured_espe_y = split_espe(self.measured_espe)

        self._generate_mev_to_nm_function()
        self._find_measured_peaks()
        self._find_measured_valleys()

        if initial_solution is None:
            initial_solution = self.initialize_solution()

        if self.optimization_type is OptimizationType.RECOIL:
            # Empty the list of optimization recoils

            # Form points from initial solution. The solution covers the
            # whole x axis range between lower and upper values -> MCERD
            # never needs to be run again
            self.element_simulation.optimization_recoils = [
                self.form_recoil(initial_solution)
            ]

        if not self._skip_simulation:
            self.run_initial_simulation(cancellation_token, ion_division)

        self.solution = initial_solution

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
        """Create a recoil element based on given solution.
        """
        if not name:
            name = "opt"

        recoil = RecoilElement(
            self.element_simulation.get_main_recoil().element,
            current_solution.points,
            color="red", name=name)

        return recoil

    def initialize_solution(self):
        """Create a starting solution.
        """
        if self.optimization_type is OptimizationType.RECOIL:
            x_min, y_min = self.lower_limits
            x_max, y_max = self.upper_limits
            gap = 0.01  # TODO: Save this as a constant
            if self.rec_type == "box":
                if self.sol_size == 5:  # 4-point recoil
                    peak0 = self.measured_peaks_nm[0]

                    points = [
                        Point(x_min,            y_max),
                        Point(peak0[-1],        y_max),
                        Point(peak0[-1] + gap,  y_min),
                        Point(x_max,            y_min)
                    ]
                    solution = SolutionBox4(points)
                elif self.sol_size == 7:  # 6-point recoil
                    peak0 = self.measured_peaks_nm[0]

                    points = [
                        Point(x_min,            y_min),
                        Point(peak0[0] - gap,   y_min),
                        Point(peak0[0],         y_max),
                        Point(peak0[-1],        y_max),
                        Point(peak0[-1] + gap,  y_min),
                        Point(x_max,            y_min)
                    ]
                    solution = SolutionBox6(points)
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
                    peak0 = self.measured_peaks_nm[0]
                    peak1 = self.measured_peaks_nm[1]

                    points = [
                        Point(x_min,            y_min),
                        Point(peak0[0] - gap,   y_min),
                        Point(peak0[0],         y_max),
                        Point(peak0[-1],        y_max),
                        Point(peak0[-1] + gap,  y_min),
                        Point(peak1[0] - gap,   y_min),
                        Point(peak1[0],         y_max),
                        Point(peak1[-1],        y_max),
                        Point(peak1[-1] + gap,  y_min),
                        Point(x_max,            y_min)
                    ]
                    solution = SolutionPeak10(points)
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
        """Form a recoil based on the given solution and return its espe."""
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

    # TODO: Unused, remove if not needed for fluence optimization
    def evaluate_solution(self, solution) -> float:
        """Evaluate solution based on its difference from measured espe.
        """
        espe = self._run_solution(solution)

        if self.optimization_type is OptimizationType.RECOIL:
            objective_value = self._get_spectra_difference(espe)
        elif self.optimization_type is OptimizationType.FLUENCE:
            raise NotImplementedError
        else:
            raise ValueError(
                f"Unknown optimization type {self.optimization_type}")

        return objective_value

    # TODO: Unify with BaseOptimizer.modify_measurement?
    def _resize_simulated_espe(
            self, espe_x, espe_y, step_decimals=4) -> Tuple[np.ndarray, np.ndarray]:
        """Pad and/or slice simulated espe so that it has the same x axis
         values as the measured espe.

         x is padded with even steps, y is padded with zeros.

         This method is similar to BaseOptimizer.modify_measurement but
         it modifies simulated espe, possibly extends the range of x values
         and uses a different algorithm.

        Args:
            espe_x: simulated espe x
            espe_y: simulated espe y
            step_decimals: maximum number of decimals in the computed step size

        Returns:
            Resized espe x and y. x values may be slightly off because
            numpy.linspace

        """
        simu_longer_left = espe_x[0] <= self.measured_espe_x[0]
        simu_longer_right = espe_x[-1] >= self.measured_espe_x[-1]

        step = round(espe_x[1] - espe_x[0], step_decimals)

        left_start = self.measured_espe_x[0]
        left_end = espe_x[0]
        if simu_longer_left:
            left_pad = 0  # Don't pad left
            left_i = find_closest_index(self.measured_espe_x[0], espe_x)
        else:
            left_pad = round((left_end - left_start) / step)
            left_i = None  # Don't slice left

        right_start = espe_x[-1]
        right_end = self.measured_espe_x[-1]
        if simu_longer_right:
            right_pad = 0  # Don't pad right
            right_i = find_closest_index(self.measured_espe_x[-1], espe_x) + 1
        else:
            right_pad = round((right_end - right_start) / step)
            right_i = None  # Don't slice right

        pad_width = (left_pad, right_pad)

        resized_x = np.pad(espe_x[left_i:right_i], pad_width, "linear_ramp",
                           end_values=(left_start, right_end))
        resized_y = np.pad(espe_y[left_i:right_i], pad_width, "constant",
                           constant_values=0)

        return resized_x, resized_y

    def _fit_simulation(self, solution: "BaseSolution"):
        """Fit solution to simulation.

        Fitting scales peak and valley heights, and widens peaks.
        The fitting attempts to replicate the measured espe.

        Args:
            solution: starting point for fitting. solution is mutated.

        Returns:
            Fitted solution
        """
        espe = self._run_solution(solution)
        espe_x, espe_y = split_espe(espe)

        resized_espe_x, resized_espe_y = self._resize_simulated_espe(espe_x, espe_y)
        peak_info = self._get_peak_info(resized_espe_y, self.peak_count)

        # Scale peak heights

        height_corrections = ((self.measured_peak_info.info["peak_heights"]
                              - peak_info.info["peak_heights"])
                             / peak_info.info["peak_heights"] + 1)

        for i, peak in enumerate(solution.peaks[::-1]):
            peak.scale_height(height_corrections[i])

        # Scale valley heights

        valley_intervals = self._get_valley_intervals(
            peak_info, include_start=True, include_end=False)
        valley_heights = self._get_valley_heights(
            resized_espe_y, valley_intervals)

        for i, valley in enumerate(solution.valleys[::-1]):
            differences = np.array(self.measured_valley_heights[i]) - np.array(valley_heights[i])
            corrections = differences / self.measured_max_height
            if not self.is_skewed:
                valley.move_y(corrections[0])
            else:
                # Reversed order because of the Mev -> nm difference
                valley.rl.set_y(valley.rl.get_y() + corrections[0])
                valley.ll.set_y(valley.ll.get_y() + corrections[-1])

        # Widen and lower peaks if necessary to stay under the max y value
        # TODO: Skewed top
        max_y = self.upper_limits[1]
        for i, peak in enumerate(solution.peaks):
            normalized_height = peak.center.get_y() / max_y
            if normalized_height > 1.0:
                peak.scale_width(normalized_height)
                peak.scale_height(1 / normalized_height)

        self._fix_and_check_solution(solution)

        return solution

    def _fix_and_check_solution(self, solution) -> bool:
        """Check and correct the solution if it has overlapping peaks or
        it exceeds the beginning or the end.

        Args:
            solution: solution to check and correct (in place)

        Raises:
            ValueError: if the solution required correcting but could
                not be corrected.

        Returns:
            True if the solution was corrected, False if it stayed as-is.
        """
        solution_corrected = False
        valley_gap = 0.1  # TODO: Save this as a constant
        valley_gap_2 = valley_gap / 2

        # Check start
        first_point = solution.points[0]
        if first_point.get_x() != self.lower_limits[0]:
            if first_point is solution.peaks[0].lh:
                difference = self.lower_limits[0] - first_point.get_x()
                solution.peaks[0].move_left_x(difference)
                solution.peaks[0].move_right_x(difference)

                solution_corrected = True
            elif first_point is solution.valleys[0].ll:
                first_point.set_x(self.lower_limits[0])

                solution_corrected = True
            else:
                raise ValueError(
                    "Optimized solution did not start with a peak or valley.")

        # Check end
        # TODO: Does the last point ever get moved anyway?
        last_point = solution.points[-1]
        if last_point.get_x() != self.upper_limits[0]:
            if last_point is not solution.valleys[-1].rl:
                raise ValueError(
                    "Optimized solution did not end with a valley.")
            last_point.set_x(self.upper_limits[0])

            solution_corrected = True

        # Check last peak end
        difference = last_point.get_x() - solution.peaks[-1].rightmost_point.get_x() - valley_gap
        if difference < 0:
            solution.peaks[-1].move_right_x(difference)

            solution_corrected = True

        # Check peak overlaps
        prev_peak = None
        for cur_peak in solution.peaks:
            if prev_peak is None:
                pass
            else:
                prev_left = prev_peak.leftmost_point.get_x()
                prev_right = prev_peak.rightmost_point.get_x()
                cur_left = cur_peak.leftmost_point.get_x()
                cur_right = cur_peak.rightmost_point.get_x()

                if prev_left >= cur_right or prev_right >= cur_right or prev_left >= cur_left:
                    raise ValueError(
                        "Completely overlapping peaks in optimized solution")

                if prev_right >= cur_left:
                    # Cut previous and current peaks overlaps

                    real_width = cur_right - prev_left  # No overlap

                    prev_width = prev_peak.width
                    cur_width = cur_peak.width
                    relative_width = prev_width + cur_width  # Partial overlap

                    prev_ratio = prev_width / relative_width
                    new_prev_right = prev_left + prev_ratio * real_width - valley_gap_2
                    prev_move = prev_right - new_prev_right
                    prev_peak.move_right_x(prev_move)

                    cur_ratio = cur_width / relative_width
                    new_cur_right = cur_right - cur_ratio * real_width + valley_gap_2
                    cur_move = cur_left - new_cur_right
                    cur_peak.move_left_x(cur_move)

                    solution_corrected = True

            prev_peak = cur_peak

        # Check point order
        prev_point = None
        for cur_point in solution.points:
            if prev_point is None:
                pass
            else:
                if prev_point.get_x() > cur_point.get_x():
                    raise ValueError(
                        "Points are in wrong order in optimized solution")

            prev_point = cur_point

        return solution_corrected

    def _optimize(self):
        """Run _fit_simulation several times.
        """
        solution = copy.deepcopy(self.solution)

        try:
            optimized1 = self._fit_simulation(solution)
        except ValueError as e:
            return str(e), None

        optimized_copy = copy.deepcopy(optimized1)
        try:
            optimized2 = self._fit_simulation(optimized_copy)
        except ValueError as e:
            return optimized1, str(e)

        return optimized1, optimized2

    # TODO: Change starting_solutions to starting_solution
    def start_optimization(self, starting_solutions=None,
                           cancellation_token=None,
                           ion_division=IonDivision.BOTH) -> None:
        """Run optimization from start to finish.

        Args:
            starting_solutions: possible starting solution(s)
            cancellation_token: token for cancelling the optimization
            ion_division: how to divide ions over multiple MCERD processes
        """
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

        self.on_next(self._get_message(OptimizationState.RUNNING))

        # TODO: handle possible str return types
        result1, result2 = self._optimize()
        if self.optimization_type is OptimizationType.RECOIL:
            first_sol = self.solution
            med_sol = result1
            last_sol = result2

            self.element_simulation.optimization_recoils = [
                self.form_recoil(first_sol, "optfirst"),
                self.form_recoil(med_sol, "optmed") if hasattr(med_sol, "points") else None,  # TODO: Display message instead
                self.form_recoil(last_sol, "optlast") if hasattr(last_sol, "points") else None  # TODO: Display message instead
            ]
        else:
            raise NotImplementedError

        self.clean_up(cancellation_token)
        self.element_simulation.optimization_results_to_file(self.cut_file)

        self.on_completed(self._get_message(OptimizationState.FINISHED))


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

    @property
    def center(self) -> Point:
        """Return (calculated) center point"""
        x = (self.lh.get_x() + self.rh.get_x()) / 2
        y = (self.lh.get_y() + self.rh.get_y()) / 2
        return Point(x, y)

    @property
    def points(self) -> List[Point]:
        """Return all points"""
        return [self.prev_point, self.ll, self.lh,
                self.rh, self.rl, self.next_point]

    @property
    def leftmost_point(self) -> Point:
        """Return leftmost point (ll or lh)"""
        return self.ll if self.ll is not None else self.lh

    @property
    def rightmost_point(self) -> Point:
        """Return rightmost point (rl or rh)"""
        return self.rl if self.rl is not None else self.rh

    @property
    def width(self) -> float:
        left = self.leftmost_point
        right = self.rightmost_point
        return right.get_x() - left.get_x()

    def move_left_x(self, amount: float) -> None:
        """Move left half of peak"""
        if self.ll:
            self.ll.set_x(self.ll.get_x() + amount)
        self.lh.set_x(self.lh.get_x() + amount)

    def move_right_x(self, amount: float) -> None:
        """Move right half of peak"""
        self.rh.set_x(self.rh.get_x() + amount)
        if self.rl:
            self.rl.set_x(self.rl.get_x() + amount)

    def move_y(self, amount: float) -> None:
        """Move peak height"""
        self.lh.set_y(self.lh.get_y() + amount)
        self.rh.set_y(self.rh.get_y() + amount)

    def scale_width(self, factor: float, scale_gap: bool = False) -> None:
        """Scale peak's width (x values)

        Args:
            factor: scaling factor
            scale_gap: whether to scale the gap between low and high points
                (True) or keep it constant (False)
        """
        lh = self.lh.get_x()
        rh = self.rh.get_x()
        center = self.center.get_x()

        left_width = lh - center
        right_width = rh - center
        lh_new = center + left_width * factor
        rh_new = center + right_width * factor

        self.lh.set_x(lh_new)
        self.rh.set_x(rh_new)

        if self.ll:
            left_gap = self.ll.get_x() - lh
            ll_new = lh_new + left_gap if not scale_gap else lh_new + left_gap * factor
            self.ll.set_x(ll_new)

        if self.rl:
            right_gap = self.rl.get_x() - rh
            rl_new = rh_new + right_gap if not scale_gap else rh_new + right_gap * factor
            self.rl.set_x(rl_new)

    def scale_height(self, factor: float) -> None:
        """Scale peak's height (y values)

        Args:
            factor: scaling factor
        """
        self.lh.set_y(self.lh.get_y() * factor)
        self.rh.set_y(self.rh.get_y() * factor)


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


# TODO: Generalize:

class GeneralSolution:
    def __init__(self, points: List[Point], peak_first: bool):
        self.points = points
        self.peak_first = peak_first  # or starts_at_surface
        self.x_pairs = ...
        self.y_pairs = ...


class BaseSolution:
    """Base class for solutions."""
    def __init__(self, points: List[Point], peaks: List[Peak],
                 valleys: List[Valley]):
        self.points = points
        self.peaks = peaks
        self.valleys = valleys


class SolutionBox4(BaseSolution):
    """Box that starts at surface."""
    def __init__(self, points: List[Point]):
        peak1 = Peak(ll=None, lh=points[0], rh=points[1], rl=points[2],
                     prev_point=None, next_point=points[3])
        valley1 = Valley(ll=points[2], rl=points[3],
                         prev_point=points[1], next_point=None)

        peaks = [peak1]
        valleys = [valley1]

        super().__init__(points, peaks, valleys)


class SolutionBox6(BaseSolution):
    """Box that doesn't start at surface."""
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
    """Twin-peak that starts at surface."""
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
    """Twin-peak that doesn't start at the surface."""
    def __init__(self, points: List[Point]):
        valley1 = Valley(ll=points[0], rl=points[1],
                         prev_point=None, next_point=points[2])
        peak1 = Peak(ll=points[1], lh=points[2], rh=points[3], rl=points[4],
                     prev_point=points[0], next_point=points[5])
        valley2 = Valley(ll=points[4], rl=points[5],
                         prev_point=points[3], next_point=points[6])
        peak2 = Peak(ll=points[4], lh=points[5], rh=points[6], rl=points[7],
                     prev_point=points[3], next_point=points[8])
        valley3 = Valley(ll=points[8], rl=points[9],
                         prev_point=points[7], next_point=None)

        peaks = [peak1, peak2]
        valleys = [valley1, valley2, valley3]

        super().__init__(points, peaks, valleys)


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


def split_espe(espe: Espe) -> Tuple[np.ndarray, np.ndarray]:
    """Unpack Espe to x and y NumPy arrays."""
    x, y = zip(*espe)
    x = np.array(x)
    y = np.array(y)
    return x, y


def find_closest_index(value: float, array: np.ndarray) -> int:
    """Find the index of a value that is the closest to the given value in the
    array.
    """
    return np.abs(value - array).argmin()
