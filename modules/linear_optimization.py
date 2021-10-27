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

import subprocess
from pathlib import Path
from timeit import default_timer as timer
from typing import Tuple

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
                 optimize_by_area=True, verbose=False,
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

        self.solution = None

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

        # TODO: Is this needed?
        self.combine_previous_erd_files()

        # Modify measurement file to match the simulation file in regards to
        # the x coordinates -> they have matching values for ease of distance
        # counting
        self.modify_measurement()

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
        points = []

        # TODO: implement properly: check sol_size and order points

        size = current_solution.size // 2
        for i in range(size):
            point = Point(current_solution[i], current_solution[i + size])
            points.append(point)

        if not name:
            name = "opt"

        recoil = RecoilElement(
            self.element_simulation.get_main_recoil().element, points,
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
                    x_coords = np.array(
                        [0.0, 30.0, 30.01, 59.99, 60.0, 89.99, 90.0, 120.0])
                    y_coords = np.array(
                        [0.5, 0.5, 0.0001, 0.0001, 0.5, 0.5, 0.0001, 0.0001])
                elif self.sol_size == 11:  # First peak not at the surface
                    raise NotImplementedError
                else:
                    raise ValueError(
                        f"Unsupported sol_size {self.sol_size} for recoil type {self.rec_type}")
            else:
                raise ValueError(
                    f"Unknown recoil type {self.rec_type}")

            # TODO: Should x and y be combined or separate?
            solution = np.append(x_coords, y_coords)

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

    @staticmethod
    def _check_optimize_end(points, state: optimize.OptimizeResult) -> bool:
        """Checks if optimization can be ended.

        Args:
            points: current optimized points
            state: current optimization state, with same fields as the result

        Returns:
            True if optimization can be ended, False otherwise
        """
        # TODO: remove
        # print(points)
        print(state.x)
        print(state.fun, state.jac)
        print(state.nfev, state.njev)
        print()

        # https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.OptimizeResult.html
        # x: solution
        # success: done/not
        # status: termination status
        # message: termination cause
        # fun, jac, hess: values of objective function, Jacobian, Hessian
        # hess_inv: inverse of Hessian, if available
        # nfev, njev, nhev: number of evaluations
        # nit: number of iterations
        # maxcv: maximum constraint violation

        # TODO: Better check
        return state.fun < 12.0

    def _get_bounds(self):
        # TODO: Select by type, use real values
        x_ub = 120.0
        x_lb = 0.01

        y_ub = 1.0000
        y_lb = 0.0001

        x_limits = [
            (0.0, 0.0),
            (x_lb, x_ub),
            (x_lb, x_ub),
            (x_lb, x_ub),
            (x_lb, x_ub),
            (x_lb, x_ub),
            (x_lb, x_ub),
            (120.0, 120.0)
        ]

        y_limits = [
            (y_lb, y_ub),
            (y_lb, y_ub),
            (y_lb, y_ub),
            (y_lb, y_ub),
            (y_lb, y_ub),
            (y_lb, y_ub),
            (0.0001, 0.0001),
            (y_lb, y_ub)
        ]

        lower_bounds = [x[0] for x in x_limits] + [y[0] for y in y_limits]
        upper_bounds = [x[1] for x in x_limits] + [y[1] for y in y_limits]

        return lower_bounds, upper_bounds

    def _optimize(self):
        # https://docs.scipy.org/doc/scipy/tutorial/optimize.html#constrained-minimization-of-multivariate-scalar-functions-minimize

        func = self._optimize_func
        initial = self.solution
        args = (self,)
        method = "trust-constr"  # trust-constr, SLSQP, COBYLA

        lower_bounds, upper_bounds = self._get_bounds()
        bounds = optimize.Bounds(lower_bounds, upper_bounds)
        callback = self._check_optimize_end
        options = {
            "gtol": 0.0,  # 1e-16,  # Default: 1e-8
            "xtol": 0.0   # 1e-16   # Default: 1e-8
        }

        # TODO: Would this work better with bigger initial values?
        result = optimize.minimize(
            func, initial, args=args, method=method, bounds=bounds,
            callback=callback,  # TODO: tol(erance) instead of callback?
            options=options)

        # TODO: remove
        print(result)
        print(result.x)

        return result.x

        # TODO: Or this?
        # https://docs.scipy.org/doc/scipy/tutorial/optimize.html#global-optimization

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

    # TODO: use this or a custom solver for scipy
    def variation(self, solution: np.ndarray) -> np.ndarray:
        # TODO: vary more than one solution at once
        # TODO: "learn" from previous solutions
        raise NotImplementedError
